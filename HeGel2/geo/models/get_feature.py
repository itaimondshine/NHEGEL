from typing import List, Set, Optional
from pydantic import BaseModel, Field

from pydantic import BaseModel
from geojson_pydantic import Point


class PoiData(BaseModel):
    osmid: int
    point: Point = Field(..., alias="location")
    street_names: List[str]
    is_junction: bool = None
    nearby_streets: Optional[Set[str]]
    neighbourhood: str
