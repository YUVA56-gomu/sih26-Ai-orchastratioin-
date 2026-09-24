from schemas import Evidence, Hazard, PFZRecord
from tools.pfz import nearest_advisory
from config import PFZ_URL


def research(location, intent):
    evidence = []
    hazards = []
    pfz = []

    evidence.append(Evidence(
        id="src_incois_pfz",
        title="INCOIS Potential Fishing Zone Advisory",
        source="INCOIS",
        url=PFZ_URL,
        type="official_advisory",
        parameters=["pfz"],
        confidence=0.95,
        note="Official PFZ advisory portal; exact PFZ geometry requires the WebGIS/GIS layer.",
    ))

    if intent.requires_pfz:
        records, meta = nearest_advisory(location.latitude, location.longitude)
        for item in records:
            pfz.append(PFZRecord.model_validate(item))
        if meta.get("status"):
            evidence.append(Evidence(
                id="src_incois_pfz_runtime",
                title="INCOIS PFZ runtime advisory page",
                source="INCOIS",
                url=meta.get("source_url", PFZ_URL),
                type="official_web",
                parameters=["pfz"],
                confidence=0.90,
                note=meta["status"],
            ))

    if "cyclone" in intent.hazards:
        evidence.append(Evidence(
            id="src_incois_hazard",
            title="INCOIS marine hazard services",
            source="INCOIS",
            url="https://incois.gov.in/",
            type="official_hazard_portal",
            parameters=["cyclone"],
            confidence=0.90,
        ))
        hazards.append(Hazard(
            name="cyclone",
            status="requires_live_official_advisory_check",
            severity="unknown",
            source="INCOIS",
            source_url="https://incois.gov.in/",
        ))
    return evidence, hazards, pfz
