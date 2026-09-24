import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# NOTE: the older "gemini-2.5-flash*" models were deprecated and return
# "model not available to new users" errors (HTTP 500). These newer aliases are
# accepted by the GenAI SDK and are not deprecated.
GEMINI_MODEL_L1 = os.getenv("GEMINI_MODEL_L1", "gemini-3.5-flash-lite")
GEMINI_MODEL_L5 = os.getenv("GEMINI_MODEL_L5", "gemini-3.5-flash")
CORS_ORIGINS = [x.strip() for x in os.getenv("ORCA_CORS_ORIGINS", "*").split(",") if x.strip()]
ORCA_GEOFENCE_FILE = os.getenv("ORCA_GEOFENCE_FILE", "data/geofences.geojson")
INCOIS_ERDDAP_BASE = os.getenv("INCOIS_ERDDAP_BASE", "https://erddap.incois.gov.in/erddap")
INCOIS_SST_DATASET = os.getenv("INCOIS_SST_DATASET", "NOAA_AVHRR_AMSR_datasets")
INCOIS_CHL_DATASET = os.getenv("INCOIS_CHL_DATASET", "IRS_chlorophyll_datasets")
INCOIS_MLD_DATASET = os.getenv("INCOIS_MLD_DATASET", "incois_valueadded_products_datasets")
PFZ_URL = os.getenv("PFZ_URL", "https://iioe-2.incois.gov.in/MarineFisheries/TextDataHome?mfid=1&request_locale=en")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in .env")
