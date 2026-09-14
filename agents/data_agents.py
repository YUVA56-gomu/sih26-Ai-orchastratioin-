from __future__ import annotations

import asyncio

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types

from state.schemas import key
from tools.location import resolve_location_query
from tools.copernicus_service import get_copernicus_marine_snapshot
from tools.weather_service import get_weather_conditions
from tools.geofence import check_geofence
from tools.marine_risk import calculate_marine_risk


class ResolveLocationAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        plan = ctx.session.state.get(key("plan"), "")
        result = await asyncio.to_thread(resolve_location_query, str(plan))
        ctx.session.state[key("location")] = result
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Location resolution complete: {result}")],
            ),
        )


class OceanDataAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        loc = ctx.session.state.get(key("location"), {})
        if loc.get("status") != "FOUND":
            result = {"status": "BLOCKED", "reason": "Location unavailable."}
        else:
            result = await asyncio.to_thread(
                get_copernicus_marine_snapshot,
                float(loc["latitude"]),
                float(loc["longitude"]),
            )
        ctx.session.state[key("ocean")] = result
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Ocean evidence collected: {result.get('status', result.get('data_status', 'UNKNOWN'))}")],
            ),
        )


class WeatherDataAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        loc = ctx.session.state.get(key("location"), {})
        plan = str(ctx.session.state.get(key("plan"), ""))
        if loc.get("status") != "FOUND":
            result = {"status": "BLOCKED", "reason": "Location unavailable."}
        else:
            # The planner marks future requests with tomorrow/future in the plan.
            days = 3 if any(word in plan.lower() for word in ("tomorrow", "future", "next")) else 1
            result = await asyncio.to_thread(
                get_weather_conditions,
                float(loc["latitude"]),
                float(loc["longitude"]),
                days,
            )
        ctx.session.state[key("weather")] = result
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Weather evidence collected: {result.get('data_status', result.get('status', 'UNKNOWN'))}")],
            ),
        )


class GeofenceDataAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        loc = ctx.session.state.get(key("location"), {})
        if loc.get("status") != "FOUND":
            result = {"status": "BLOCKED", "reason": "Location unavailable."}
        else:
            result = await asyncio.to_thread(
                check_geofence,
                float(loc["latitude"]),
                float(loc["longitude"]),
            )
        ctx.session.state[key("geofence")] = result
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Geospatial evidence collected: {result.get('status', 'UNKNOWN')}")],
            ),
        )


class RiskAssessmentAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        ocean = ctx.session.state.get(key("ocean"), {})
        weather = ctx.session.state.get(key("weather"), {})
        geofence = ctx.session.state.get(key("geofence"), {})
        result = calculate_marine_risk(ocean, weather, geofence)
        ctx.session.state[key("risk")] = result
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Risk calculation complete: {result['risk_level']} ({result['risk_score']}/100)")],
            ),
        )


class RecheckAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        review = str(ctx.session.state.get(key("review"), ""))
        lower = review.lower()

        if "pass" in lower and "recheck" not in lower.split("pass", 1)[0]:
            message = "No recheck required; review passed."
        elif "recheck" in lower:
            loc = ctx.session.state.get(key("location"), {})
            tasks = []
            if "weather" in lower or "wind" in lower or "forecast" in lower:
                if loc.get("status") == "FOUND":
                    tasks.append(asyncio.to_thread(
                        get_weather_conditions,
                        float(loc["latitude"]),
                        float(loc["longitude"]),
                        3,
                    ))
            if "ocean" in lower or "wave" in lower or "current" in lower:
                if loc.get("status") == "FOUND":
                    tasks.append(asyncio.to_thread(
                        get_copernicus_marine_snapshot,
                        float(loc["latitude"]),
                        float(loc["longitude"]),
                    ))
            if "geofence" in lower or "restriction" in lower:
                if loc.get("status") == "FOUND":
                    tasks.append(asyncio.to_thread(
                        check_geofence,
                        float(loc["latitude"]),
                        float(loc["longitude"]),
                    ))

            results = await asyncio.gather(*tasks) if tasks else []
            idx = 0
            if "weather" in lower or "wind" in lower or "forecast" in lower:
                if idx < len(results):
                    ctx.session.state[key("weather")] = results[idx]
                    idx += 1
            if "ocean" in lower or "wave" in lower or "current" in lower:
                if idx < len(results):
                    ctx.session.state[key("ocean")] = results[idx]
                    idx += 1
            if "geofence" in lower or "restriction" in lower:
                if idx < len(results):
                    ctx.session.state[key("geofence")] = results[idx]
            message = f"Recheck completed for requested domains. Retrieved {len(results)} data payload(s)."
        else:
            message = "No actionable recheck request found; continuing with available evidence."

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=message)],
            ),
        )


class ReviewGateAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        review = str(ctx.session.state.get(key("review"), "")).lower()
        should_stop = (
            "pass" in review
            or "blocked" in review
            or "insufficient" in review
        ) and "recheck" not in review

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text="Review loop complete." if should_stop else "Review requires another evidence pass.")],
            ),
            actions=__import__("google.adk.events", fromlist=["EventActions"]).EventActions(
                escalate=should_stop
            ),
        )
