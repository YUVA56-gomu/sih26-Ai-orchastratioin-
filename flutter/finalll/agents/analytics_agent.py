from statistics import mean


def fishing_productivity(conditions):
    chl = conditions.chlorophyll.value
    sst = conditions.sea_surface_temperature.value
    if chl is None and sst is None:
        return {
            "status": "not_assessed",
            "reason": "No chlorophyll or SST evidence sufficient for productivity analysis."
        }
    indicators = {}
    if chl is not None:
        indicators["chlorophyll"] = {"value": chl, "interpretation": "higher chlorophyll generally indicates more phytoplankton biomass, but it is not a direct fish-abundance measurement"}
    if sst is not None:
        indicators["sst"] = {"value": sst, "interpretation": "SST provides thermal context; suitability depends on species and local seasonal baseline"}
    return {
        "status": "context_only",
        "indicators": indicators,
        "warning": "This is environmental context, not a fish-catch prediction. Historical species/catch data is required for causal productivity analysis."
    }
