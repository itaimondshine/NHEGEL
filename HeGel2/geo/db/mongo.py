import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["hegel"]
collection = db["geoFeatures"]
collection.create_index("TelAviv")


def _get_db():
    pass


def save_document():
    pass


def insert_document():



