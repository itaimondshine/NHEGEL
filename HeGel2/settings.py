import multiprocessing

BATCH_SIZE = 50
REGION = "Tel Aviv"
MAP_DIR = "HeGel2/geo/map_processor/resources"
NEIGHBORHOODS_LIBRARY = 'HeGel2/geo/extractors/city_polygons/'
MAP_DATA_DIR = f"{MAP_DIR}/{REGION}_paths.gpkg"

S2_LEVEL = 14
N_CPU = multiprocessing.cpu_count() - 1
LANDMARKS_DISTANCE = 500
NUMBER_OF_DOCUMENTS = 50
