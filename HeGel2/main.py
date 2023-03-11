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


def create_osm_graph(region: str, map_data_dir: Optional[str], s2_level: int = 14) -> Map:
    return Map(regions.get_region(region), s2_level, map_data_dir) if map_data_dir is not None else (
        Map(regions.get_region(region), s2_level))


class BaseRun:

    def _process_map_nodes(self, map):
        map_without_osmid_col = map.nodes.drop('osmid', axis=1)
        return map_without_osmid_col.reset_index()

    def __init__(self, map: Map):
        self.map = map
        self.map_nodes = self._process_map_nodes(map)
        self.geo_features = GeoFeatures('Tel_Aviv', map)

    def run_extractors(self, row, sema, return_dict):
        # sema.acquire()
        geometry = row['geometry']
        osmid = row['osmid']
        # print(osmid)
        # street_names = self.geo_features.get_streets(osmid)
        # is_junction = self.geo_features.is_poi_in_junction(osmid)
        # lat, lon = geometry.x, geometry.y
        # nearby_streets = self.geo_features.get_nearby_streets(lon, lat)
        # relation = self.geo_features.get_relation_in_street(osmid, geometry)
        distance, bearing = self.geo_features.get_distance_from_city_center(geometry)
        print(f"{distance}, {bearing}")
        # neighborhood = self.geo_features.get_neighborhood(geometry)

        # print(nearby_streets)
        # doc = PoiData(osmid=osmid, location= Point(coordinates=[geometry.x, geometry.y]),
        #               is_junctfion=is_junction, street_names=street_names, nearby_streets=nearby_streets)
        # doc_dict = doc.dict(by_alias=True, exclude_unset=True)

        # poi_doc = {'osmid': osmid,
        #            'geometry': geometry,
        #            'streets_names': street_name,
        #            "is_junction": is_junction,
        #            "nearby_streets": nearby_streets}
        # insert_document(doc)
        # return_dict[10] = 'i'
        # sema.release()

    def process_batch(self, batch):
        with multiprocessing.Pool(multiprocessing.cpu_count() - 1) as pool:
            results = pool.map(self.run_extractors, batch.to_dict(orient='records'))
        return results

    def run(self):
        # map: Map = Map(regions.get_region(REGION), S2_LEVEL)

        manager = multiprocessing.Manager()
        sema = multiprocessing.Semaphore(n_cpu)
        # if macos or windows - need to use 'fork'
        multiprocessing.set_start_method('fork', force=True)

        # 2. Extract geo features from POI-s

        for i in range(0, 2000, settings.BATCH_SIZE):
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
    map: Map = Map(regions.get_region(REGION), S2_LEVEL)
    #
    b = BaseRun(map)
    b.run()
    # manager = multiprocessing.Manager()
    # sema = multiprocessing.Semaphore(n_cpu)
    # # if macos or windows - need to use 'fork'
    # multiprocessing.set_start_method('fork', force=True)
    #
    # # 2. Extract geo features from POI-s
    # geo_feature = GeoFeatures(map)
    # for i in range(0, 50, settings.BATCH_SIZE):
    #     batch = map.nodes.iloc[i:i + settings.BATCH_SIZE]
    #     results = base_run.process_batch(batch)

    # Save results to MongoDB


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    main()
