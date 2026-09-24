import uuid
from datetime import datetime, timezone
from schemas import UnifiedData, ChatResponse, Evidence, Intent, Location, DataQuality, FinalLanguageOutput
from agents.conversation_agent import parse_user_query, detect_greeting, detect_language
from agents.planner import build_plan
from agents.ocean_api_agent import fetch_all, LocationResolutionError
from agents.web_research_agent import research
from agents.hazard_agent import gather_hazards
from agents.fusion_agent import fuse
from agents.final_agent import generate_final
from agents.analytics_agent import fishing_productivity
from tools.geofence import check_geofences


class Orchestrator:
    def __init__(self, session_store):
        self.sessions = session_store

    def run(self, message, conversation_id, supplied_location=None):
        request_id = f"orca_{uuid.uuid4().hex[:10]}"
        # The router always supplies one, but the orchestrator must not raise if
        # it is absent (first turn / direct call) — ChatResponse requires a str.
        conversation_id = conversation_id or f"conv_{uuid.uuid4().hex[:10]}"
        history = self.sessions.get(conversation_id, [])
        context = "\n".join(x["message"] for x in history[-6:])
        enriched = f"Previous context:\n{context}\n\nCurrent request:\n{message}" if context else message

        # Fast path: greetings & small talk. Never needs a location and never
        # calls the (slow, paid) Level-1 model — "hi"/"hello"/"thank you" reply
        # instantly instead of 500-ing on a missing location.
        greeting_reply = detect_greeting(message)
        if greeting_reply:
            intent = Intent(user_query=message, intent="greeting", language=detect_language(message))
            return self._reply(request_id, conversation_id, intent, greeting_reply,
                               location=Location(), user_message=message)

        # Last line of defence: ANY unexpected error (Gemini 429/rate-limit,
        # network, JSON, etc.) is converted into a valid 200 ChatResponse so the
        # app NEVER receives a 500.
        try:
            return self._answer(message, conversation_id, supplied_location,
                                request_id, enriched, history)
        except Exception as e:
            intent = Intent(user_query=message, intent="general", language=detect_language(message))
            summary, observations, recommendations = _graceful_error(e)
            return self._reply(request_id, conversation_id, intent, summary,
                               location=Location(), user_message=message,
                               observations=observations, recommendations=recommendations)

    def _answer(self, message, conversation_id, supplied_location, request_id, enriched, history):
        # Level-1 intent parse. If the model call itself fails (auth / network /
        # rate-limit / bad model), answer gracefully rather than surfacing a 500.
        try:
            intent = parse_user_query(enriched, supplied_location)
        except Exception:
            intent = Intent(user_query=message, intent="general", language=detect_language(message))
            return self._reply(
                request_id, conversation_id, intent,
                "I couldn't parse your request just now. Please try rephrasing "
                "it, or ask about a specific place (e.g. \"conditions near "
                "Kochi\").", location=Location(), user_message=message,
            )

        plan = build_plan(intent)

        try:
            location, conditions, live_sources, buoy = fetch_all(intent)
        except LocationResolutionError as e:
            if e.code == "no_location":
                return self._reply(
                    request_id, conversation_id, intent,
                    "I need a location to give you accurate marine data. Could "
                    "you tell me a place name (e.g. \"Kochi\", "
                    "\"Visakhapatnam\") or enable location access so I can use "
                    "your current position?",
                    location=Location(), user_message=message,
                )
            if e.code == "geocode_failed":
                return self._reply(
                    request_id, conversation_id, intent,
                    f"I couldn't locate \"{e.name}\". Could you try a nearby "
                    "coastal place, or share your current location so I can use "
                    "it?", location=Location(), user_message=message,
                )
            raise
        except Exception:
            return self._reply(
                request_id, conversation_id, intent,
                "I couldn't reach the marine data sources just now. Please try "
                "again in a moment.", location=Location(), user_message=message,
            )

        evidence, web_hazards, pfz = research(location, intent)
        hazard_evidence, runtime_hazards = gather_hazards(location, intent)
        evidence.extend(hazard_evidence)
        hazards = web_hazards + runtime_hazards

        geo_hits, geo_meta = check_geofences(location.latitude, location.longitude)
        route = None
        productivity = fishing_productivity(conditions) if intent.requires_productivity else {}

        quality, assessment = fuse(
            intent, location, conditions, hazards,
            pfz, geo_hits, route, evidence, live_sources,
        )

        unified = UnifiedData(
            intent=intent,
            location=location,
            conditions=conditions,
            hazards=hazards,
            pfz=pfz,
            geofences=geo_hits,
            route=route,
            productivity=productivity,
            quality=quality,
            assessment=assessment,
            evidence=evidence,
        )

        # Final natural-language wording. Guarded: if the Gemini call throws
        # (429 rate-limit, quota, network), fall back to a deterministic summary
        # built from the validated data so the user STILL gets a useful answer.
        language = self._finalize_language(unified, assessment)

        sources = list(live_sources)
        for e in evidence:
            sources.append({
                "name": e.source,
                "title": e.title,
                "url": e.url,
                "type": e.type,
                "confidence": e.confidence,
                "note": e.note,
            })
        sources = _dedupe_sources(sources)
        if geo_meta.get("status") == "ok":
            sources.append({"name": "Configured GeoJSON geofences", "url": "local:data/geofences.geojson", "type": "geospatial_boundary"})

        final = ChatResponse(
            request_id=request_id,
            conversation_id=conversation_id,
            language=intent.language,
            location=location,
            intent={**intent.model_dump(), "plan": plan.tasks},
            answer=language.model_dump(),
            ocean={k: v for k, v in conditions.model_dump().items() if k in {"sea_surface_temperature","wave_height","wave_period","wave_direction","current_speed","current_direction","sea_level","salinity","chlorophyll","mixed_layer_depth"}},
            weather={k: v for k, v in conditions.model_dump().items() if k in {"wind_speed","wind_direction","pressure","precipitation","weather_code"}},
            pfz=[p.model_dump() for p in pfz],
            hazards=[h.model_dump() for h in hazards],
            geofencing=geo_hits,
            route=route.model_dump() if route else None,
            productivity=productivity,
            data_quality=quality.model_dump(),
            evidence=[e.model_dump() for e in evidence],
            sources=sources,
            map={
                "center": {"latitude": location.latitude, "longitude": location.longitude},
                "markers": [{"type": "location", "latitude": location.latitude, "longitude": location.longitude, "label": location.name or "Selected location"}],
                "route": [],
                "layers": ["ocean_conditions", "weather", "hazards", "pfz", "geofences"],
            },
        )

        now = datetime.now(timezone.utc).isoformat()
        history.extend([
            {"role": "user", "message": message, "created_at": now},
            {"role": "assistant", "message": language.summary, "created_at": now},
        ])
        self.sessions[conversation_id] = history[-20:]
        return final

    def _finalize_language(self, unified, assessment):
        """Generate the final wording, tolerating LLM failures.

        If the Level-5 model call fails (quota, rate-limit, network), fall back
        to a deterministic summary from the validated data so the app still gets
        a meaningful answer — and crucially never a 500.
        """
        try:
            language = generate_final(unified)
            language.status = assessment.get("safety_assessment", language.status)
            return language
        except Exception:
            return _deterministic_language(unified, assessment)

    def _reply(self, request_id, conversation_id, intent, summary,
               location=None, observations=None, recommendations=None,
               user_message=None):
        """Build a minimal, valid ChatResponse for fast-path / graceful replies.

        Used for greetings and for requests that could not resolve a location,
        so the app never receives a 500 — it always gets a friendly message.
        """
        loc = location or Location()
        language = getattr(intent, "language", None) or "en"

        final = ChatResponse(
            request_id=request_id,
            conversation_id=conversation_id,
            language=language,
            location=loc,
            intent={**intent.model_dump()},
            answer={
                "status": "info",
                "summary": summary,
                "observations": observations or [],
                "recommendations": recommendations or [],
            },
            ocean={},
            weather={},
            pfz=[],
            hazards=[],
            geofencing=[],
            route=None,
            productivity={},
            data_quality=DataQuality(
                requested=0, available=0, completeness_percent=0.0,
                missing=[], source_count=0,
            ).model_dump(),
            evidence=[],
            sources=[],
            map={
                "center": {"latitude": loc.latitude, "longitude": loc.longitude},
                "markers": [],
                "route": [],
                "layers": [],
            },
        )

        # Persist the turn so follow-up questions keep conversation context.
        history = self.sessions.get(conversation_id, [])
        history.extend([
            {"role": "user", "message": user_message or summary},
            {"role": "assistant", "message": summary},
        ])
        self.sessions[conversation_id] = history[-20:]
        return final


def _graceful_error(e):
    """Map an unexpected backend exception to a friendly, non-500 reply."""
    msg = str(e).lower()
    if "429" in msg or "rate" in msg or "quota" in msg or "exhausted" in msg or "limit" in msg:
        return (
            "I'm getting a lot of questions right now and am briefly at "
            "capacity. Please try again in a moment.",
            ["Samudra AI is temporarily rate-limited."],
            ["Please retry your question in about a minute."],
        )
    if "network" in msg or "connection" in msg or "timeout" in msg or "unreachable" in msg:
        return (
            "I had trouble reaching my data sources. Please check your "
            "connection and try again.",
            ["A network error interrupted the response."],
            ["Check internet access and retry in a moment."],
        )
    return (
        "I couldn't complete that request just now. Please try rephrasing it.",
        ["An unexpected issue interrupted the response."],
        ["Please try again in a moment."],
    )


def _deterministic_language(unified, assessment):
    """Build a readable FinalLanguageOutput from validated data (no LLM)."""
    c = unified.conditions
    loc_name = unified.location.name or "your location"
    safety = assessment.get("safety_assessment", "unknown")

    def fmt(dp):
        if dp is None or dp.value is None:
            return None
        unit = f" {dp.unit}" if dp.unit else ""
        return f"{dp.value}{unit}"

    bits = []
    for label, dp in [("wave height", c.wave_height),
                      ("sea temperature", c.sea_surface_temperature),
                      ("wind", c.wind_speed),
                      ("current", c.current_speed)]:
        v = fmt(dp)
        if v is not None:
            bits.append(f"{label} {v}")

    summary = f"Conditions near {loc_name}: "
    summary += ", ".join(bits) + "." if bits else "some live data is currently unavailable."

    status_txt = {
        "low": "generally calm",
        "moderate": "moderately active",
        "high": "potentially hazardous",
        "unknown": "uncertain",
        "insufficient_data_for_safety_assessment": "insufficient data to fully assess safety",
    }.get(safety, safety)
    summary += f" The overall marine status is {status_txt}."

    observations = []
    for label, dp in [("Wave height", c.wave_height),
                      ("Sea temperature", c.sea_surface_temperature),
                      ("Wind speed", c.wind_speed),
                      ("Current speed", c.current_speed),
                      ("Sea level", c.sea_level)]:
        v = fmt(dp)
        if v is not None:
            observations.append(f"{label}: {v}")
    if not observations:
        observations.append("Live marine measurements are not available for this location right now.")

    recommendations = []
    if safety == "high":
        recommendations.append("Be cautious — conditions may be hazardous.")
    elif safety == "moderate":
        recommendations.append("Conditions are moderately active; exercise care.")
    elif safety == "insufficient_data_for_safety_assessment":
        recommendations.append("Some safety-critical data is missing; wait for more data before navigating.")
    if unified.hazards:
        top = unified.hazards[0]
        recommendations.append(f"An active advisory mentions {top.name}.")
    if not recommendations:
        recommendations.append("Current conditions appear favorable; keep monitoring official advisories.")

    return FinalLanguageOutput(
        status=safety,
        summary=summary,
        observations=observations,
        recommendations=recommendations,
    )


def _dedupe_sources(items):
    result, seen = [], set()
    for item in items:
        key = item.get("url") or item.get("name")
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
