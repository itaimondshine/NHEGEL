from typing import List, Optional
from pydantic import BaseModel, Field
from geojson_pydantic import Point


class PoiData(BaseModel):
    osmid: int
    point: Point = Field(..., alias="location")
    street_names: List[str]
    is_junction: bool = None
    nearby_to_non_primery_streets: Optional[List[str]]
    nearby_to_primery_streets: Optional[List[str]]
    relation_in_street: Optional[str]
    neighbourhood: Optional[str]
    cardinal_direction_to_city_center: str
    distance_from_city_center: int