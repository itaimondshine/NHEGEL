import multiprocessing
from typing import Optional
from HeGel2 import settings
from geojson_pydantic import Point
from HeGel2.geo.db.mongo import insert_document
from HeGel2.geo.map_processor import regions
from HeGel2.geo.map_processor.map_structure import Map
from HeGel2.geo.extractors.extractor import GeoFeatures
from HeGel2.geo.models.get_feature import PoiData


def create_osm_graph(region: str, map_data_dir: Optional[str], s2_level: int = 14) -> Map:
    return Map(regions.get_region(region), s2_level, map_data_dir) if map_data_dir is not None else (
        Map(regions.get_region(region), s2_level))


class BaseRun:

    def __init__(self, map: Map):
        self.map = map
        self.map_nodes = map.poi
        self.geo_features = GeoFeatures('Tel_Aviv', map)

    def run_extractors(self, row, sema, return_dict):
        name = row['name'] if row['name'] else row['wikipedia']
        amenity = row['amenity'] if row['amenity'] else row['tourism'] if row['tourism'] else row['building'] if row[
            'building'] else row['description']
        geometry = row['centroid']
        osmid = row['osmid']
        print(f"{name}: {amenity}")
        street_names = self.geo_features.get_streets(osmid)
        is_junction = self.geo_features.is_poi_in_junction(osmid)
        lat, lon = geometry.x, geometry.y
        no_primery_nearby_streets = self.geo_features.get_nearby_streets(lat, lon, is_primery=False)
        primery_nearby_streets = self.geo_features.get_nearby_streets(lat, lon, is_primery=True)
        relation = self.geo_features.get_relation_in_street(osmid, geometry)
        distance, bearing = self.geo_features.get_distance_from_city_center(geometry)
        neighbourhood = self.geo_features.get_neighborhood(geometry)
        nearby_landmarks = self.geo_features.get_top_k_nearest_landmarks(point=geometry)

        print(nearby_landmarks)
        doc = PoiData(osmid=osmid,
                      name=name,
                      amenity=amenity,
                      location=Point(coordinates=[geometry.x, geometry.y]),
                      is_junction=is_junction, street_names=street_names,
                      nearby_to_non_primery_streets=no_primery_nearby_streets,
                      nearby_to_primery_streets=primery_nearby_streets,
                      relation_in_street=relation,
                      neighbourhood=neighbourhood,
                      cardinal_direction_to_city_center=bearing,
                      distance_from_city_center=distance,
                      nearby_landmarks=nearby_landmarks)

        print(doc)
        insert_document(doc)

    def process_batch(self, batch):
        with multiprocessing.Pool(multiprocessing.cpu_count() - 1) as pool:
            results = pool.map(self.run_extractors, batch.to_dict(orient='records'))
        return results

    @staticmethod
    def _process_map_nodes(map: Map):
        map_without_osmid_col = map.nodes.drop('osmid', axis=1)
        return map_without_osmid_col.reset_index()

    def run(self):
        manager = multiprocessing.Manager()
        sema = multiprocessing.Semaphore(settings.N_CPU)
        # if macos or windows - need to use 'fork'
        multiprocessing.set_start_method('fork', force=True)

        # 2. Extract geo features from POI-s
        for i in range(0, 500, settings.BATCH_SIZE):
            batch = self.map_nodes.iloc[i:i + settings.BATCH_SIZE]
            return_dict = manager.dict()
            jobs = []
            for j in batch.iterrows():
                p = multiprocessing.Process(
                    target=self.run_extractors,
                    args=(j[1],
                          sema,
                          return_dict))
                jobs.append(p)
                p.start()


def main():
    # 1. Create Map Object
    map: Map = Map(regions.get_region(settings.REGION), settings.S2_LEVEL, settings.MAP_DIR)
    print(map)
    # 2. Create a BaseRun Object and run

    b = BaseRun(map)
    b.run()


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    main()
