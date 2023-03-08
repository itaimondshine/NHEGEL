import multiprocessing
from typing import Optional

from HeGel2.geo.map_processor import regions
from HeGel2.geo.map_processor.map_structure import Map

REGION = "TelAvivSmall"
MAP_DIR = f"/home/nlp/itaimond1/Thesis/HeGEL/HeGel2/HeGel2/geo/map/{REGION}/"
MAP_DATA_DIR = f"{MAP_DIR}/{REGION}_paths.gpkg"

S2_LEVEL = 14
n_cpu = multiprocessing.cpu_count() - 1


def create_osm_graph(region: str, map_data_dir: Optional[str], s2_level: int = 14) -> Map:
    return Map(regions.get_region(region), s2_level, map_data_dir) if map_data_dir is not None else (
        Map(regions.get_region(region), s2_level))


def main():
    pass



# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    print("here")
    # Creating OSM Graphs For the area
    # map_region = Map(regions.get_region(REGION), S2_LEVEL)
    # current_dir = os.getcwd()
    # if not Path(MAP_DIR).is_dir():
    #     os.mkdir(MAP_DIR)
    # map_region.write_map(MAP_DIR)
    #
    # # Constructing geographic

    # load map from memory
    osm_map_from_memory = Map(regions.get_region(REGION), S2_LEVEL)
    print(osm_map_from_memory)
    # Create a file with multiple layers of data.
    # walker = walk.Walker(osm_map_from_memory)
    # walker.generate_and_save_routes(MAP_DATA_DIR, 100)
