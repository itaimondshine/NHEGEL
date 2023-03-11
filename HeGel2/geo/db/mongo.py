from typing import Any, Dict

import pymongo

from HeGel2.geo.models.get_feature import PoiData

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["hegel"]
collection = db["TelAviv"]
collection.create_index("TelAviv")

Document = Dict[str, Any]


def _get_db():
    pass


def save_document():
    pass


def insert_document(poiData: PoiData) -> None:
    document = poiData.dict(by_alias=True, exclude_unset=True)
    collection.insert_one(document)





