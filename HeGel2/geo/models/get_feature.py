from pydantic import BaseModel
from geojson_pydantic import Point


class GeoFeature(BaseModel):
    point: Point
    is_intersection: bool = None
    street_name: str
    osm_id: int






