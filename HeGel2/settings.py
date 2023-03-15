import multiprocessing

BATCH_SIZE = 50
REGION = "TelAvivSmall"
MAP_DIR = f"/home/nlp/itaimond1/Thesis/HeGEL/HeGel2/HeGel2/geo/map/{REGION}/"
MAP_DATA_DIR = f"{MAP_DIR}/{REGION}_paths.gpkg"

S2_LEVEL = 14
N_CPU = multiprocessing.cpu_count() - 1