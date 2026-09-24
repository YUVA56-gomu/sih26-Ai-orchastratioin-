from schemas import Evidence, Hazard
from tools.imd import district_warnings, district_nowcast, cyclone_status


def gather_hazards(location, intent):
    evidence = []
    hazards = []

    warn, meta = district_warnings(location.name or "")
    if meta.get("status") == "ok":
        evidence.append(Evidence(
            id="src_imd_district_warning",
            title="IMD District Warning API",
            source="India Meteorological Department",
            url=meta["source_url"],
            type="official_warning_api",
            parameters=["weather", "hazards"],
            confidence=0.95,
        ))
        for item in warn:
            text = str(item).lower()
            severity = "high" if any(x in text for x in ["red", "warning", "severe", "very heavy", "cyclone"]) else "moderate" if any(x in text for x in ["orange", "alert", "heavy", "watch", "thunderstorm", "lightning"]) else "low"
            hazards.append(Hazard(
                name="district_weather_warning",
                status="active",
                severity=severity,
                source="India Meteorological Department",
                source_url=meta["source_url"],
                details=str(item)[:1000],
            ))

    now, nmeta = district_nowcast(location.name or "")
    if nmeta.get("status") == "ok":
        evidence.append(Evidence(
            id="src_imd_nowcast",
            title="IMD District Nowcast API",
            source="India Meteorological Department",
            url=nmeta["source_url"],
            type="official_nowcast_api",
            parameters=["lightning", "thunderstorm", "nowcast"],
            confidence=0.92,
        ))
        for item in now:
            text = str(item).lower()
            severe = any(x in text for x in ["lightning", "thunder", "squall", "hail", "warning"])
            if severe:
                hazards.append(Hazard(
                    name="nowcast",
                    status="active",
                    severity="high" if any(x in text for x in ["warning", "severe"]) else "moderate",
                    source="India Meteorological Department",
                    source_url=nmeta["source_url"],
                    details=str(item)[:1000],
                ))

    cyc = cyclone_status()
    evidence.append(Evidence(
        id="src_imd_cyclone",
        title="IMD Cyclone Information",
        source="India Meteorological Department",
        url=cyc["source_url"],
        type="official_cyclone_portal",
        parameters=["cyclone"],
        confidence=0.95,
        note=cyc.get("status"),
    ))
    if cyc.get("status") == "page_available":
        txt = cyc.get("summary", "").lower()
        if "cyclone" in txt and any(x in txt for x in ["warning", "alert", "depression"]):
            hazards.append(Hazard(
                name="cyclone_information",
                status="review_required",
                severity="moderate",
                source="India Meteorological Department",
                source_url=cyc["source_url"],
                details=cyc["summary"][:1500],
            ))

    return evidence, hazards
