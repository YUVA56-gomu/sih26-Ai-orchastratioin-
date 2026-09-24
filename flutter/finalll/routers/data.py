from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tools.geocode import resolve_location
from tools.open_meteo import fetch_marine, fetch_weather
from tools.geofence import check_geofences
from tools.pfz import nearest_advisory
from tools.route import safest_route
from tools.imd import district_warnings, district_nowcast, cyclone_status

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/location/search")
def location_search(q: str):
    if not q.strip(): raise HTTPException(400, "q is required")
    return resolve_location(q)


@router.get("/ocean/current")
def ocean_current(latitude: float, longitude: float):
    return fetch_marine(latitude, longitude, 1)


@router.get("/weather/current")
def weather_current(latitude: float, longitude: float):
    return fetch_weather(latitude, longitude, 1)


@router.get("/hazards")
def hazards(location: str):
    w, wm = district_warnings(location)
    n, nm = district_nowcast(location)
    return {"district_warnings": w, "warning_meta": wm, "nowcast": n, "nowcast_meta": nm, "cyclone": cyclone_status()}


@router.get("/pfz/nearest")
def pfz_nearest(latitude: float, longitude: float):
    records, meta = nearest_advisory(latitude, longitude)
    return {"records": records, "meta": meta}


@router.get("/geofence/check")
def geofence(latitude: float, longitude: float):
    hits, meta = check_geofences(latitude, longitude)
    return {"hits": hits, "meta": meta}


class RouteRequest(BaseModel):
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float


@router.post("/route/safe")
def safe_route(req: RouteRequest):
    return safest_route((req.start_latitude, req.start_longitude), (req.end_latitude, req.end_longitude)).model_dump()
