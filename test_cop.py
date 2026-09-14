from pprint import pprint

from dotenv import load_dotenv

from tools.copernicus_service import (
    get_copernicus_marine_snapshot,
)


load_dotenv()


LATITUDE = 17.6935526
LONGITUDE = 83.2921297


result = get_copernicus_marine_snapshot(
    latitude=LATITUDE,
    longitude=LONGITUDE,
)


pprint(result, sort_dicts=False)