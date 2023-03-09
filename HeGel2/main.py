import multiprocessing
import pymongo
from typing import Optional

from HeGel2 import settings
from HeGel2.geo.map_processor import regions
from HeGel2.geo.map_processor.map_structure import Map
from HeGel2.geo.extractors.extractor import GeoFeatures


REGION = "TelAvivSmall"
MAP_DIR = f"/home/nlp/itaimond1/Thesis/HeGEL/HeGel2/HeGel2/geo/map/{REGION}/"
MAP_DATA_DIR = f"{MAP_DIR}/{REGION}_paths.gpkg"

S2_LEVEL = 14
n_cpu = multiprocessing.cpu_count() - 1


def run_extractors(geo_feature: GeoFeatures, row: dict):
    geometry = row['geometry']
    osmid = row['osmid']
    street_name = geo_feature.get_streets(osmid)
    is_junction = geo_feature.is_poi_in_junction(osmid)
    lat, lon = geometry.x, geometry.y
    nearby_streets = geo_feature.get_nearby_streets(lat, lon, False)[0].names.iloc[0]
    return {'osmid': osmid,
            'geometry': geometry,
            'streets_names': street_name,
            "is_junction": is_junction,
            "nearby_streets": nearby_streets}


def process_batch(geo_feature: GeoFeatures, batch):
    with multiprocessing.Pool(multiprocessing.cpu_count() - 1) as pool:
        results = pool.map(run_extractors, (geo_feature, batch.to_dict(orient='records')))
    return results


def create_osm_graph(region: str, map_data_dir: Optional[str], s2_level: int = 14) -> Map:
    return Map(regions.get_region(region), s2_level, map_data_dir) if map_data_dir is not None else (
        Map(regions.get_region(region), s2_level))


def main():
    # 1. Create Map Object
    map: Map = create_osm_graph(REGION, MAP_DATA_DIR, S2_LEVEL)

    # if macos or windows - need to use 'fork'
    multiprocessing.set_start_method('fork', force=True)

    # 2. Extract geo features from POI-s
    geo_feature = GeoFeatures(map)
    for i in range(0, 50, settings.BATCH_SIZE):
        batch = map.nodes.iloc[i:i + settings.BATCH_SIZE]
        results = process_batch(geo_feature, batch)

    # Save results to MongoDB


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    main()