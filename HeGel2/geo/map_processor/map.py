import logging
from pathlib import Path
from typing import Tuple, Text, Optional
import copy
import osmnx as ox
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point
from geopandas import GeoSeries

from .toolbox import connect_poi
from . import osm, regions, util
import pandas as pd
import os

LARGE_AREAS = 0.0001
NEIGHBORHOODS_LIBRARY = 'HeGel2/geo/extractors/city_polygons/'


class Map:
    def __init__(
            self, region: regions.Region, level: int = 18, load_directory: Text = None):
        self.osmnx_graph = ox.graph_from_polygon(region.polygon, network_type='all')
        self.city_polygons = gpd.read_file(f'{Path(NEIGHBORHOODS_LIBRARY).joinpath("Tel_Aviv")}_neighborhoods.geojson')
        self.polygon_area = region.polygon
        self.map_name = region.name
        self.s2_graph = None
        self.region = region
        self.level = level
        self.polygon_area = region.polygon
        self.num_poi_add = 0
        self.load_directory = load_directory
        self.nx_graph = None
        self.nodes = None
        self.edges = None

        if load_directory and len(os.listdir(self.load_directory)) == 0:
            print("Loading map from directory.")
            self.load_map(self.load_directory)
        else:
            print("Preparing map.")
            print("Extracting POI.")
            self.poi, self.streets = self.get_poi()
            self.build_graph()
            logging.info("Graph Built successfully.")
            # self.write_map(load_directory)
            logging.info("Graph Saved successfully.")

    def get_poi(self) -> Tuple[GeoSeries, GeoSeries]:
        '''Extract point of interests (POI) for the defined region.
        Returns:
          (1) The POI that are not roads; and (2) the roads POI.
        '''

        tags = osm.INTERESTING_TAGS
        osm_poi = ox.geometries_from_polygon(self.polygon_area, tags=tags)

        if ('highway' in osm_poi.columns) and ('railway' in osm_poi.columns):
            condition_streets = osm_poi.apply(
                lambda x: (pd.notnull(x.highway))
                          or (pd.notnull(x.railway))
                          or (isinstance(x.geometry, LineString)), axis=1)
        else:
            condition_streets = osm_poi.apply(
                lambda x: isinstance(x.geometry, LineString), axis=1)
        osm_poi_no_streets = osm_poi[~condition_streets]
        osm_poi_streets = osm_poi[condition_streets]

        # Remove large POI such as Manhattan.
        osm_without_large_areas = osm_poi_no_streets[
            osm_poi_no_streets.geometry.apply(lambda x: x.area < LARGE_AREAS)]

        # Get centroid for POI.
        centroid_list = osm_without_large_areas['geometry'].apply(
            lambda x: x if isinstance(x, Point) else x.centroid).tolist()

        osm_without_large_areas = osm_without_large_areas.assign(centroid=centroid_list)

        streets = ox.graph_to_gdfs(self.osmnx_graph, nodes=False, edges=True)

        return osm_without_large_areas.reset_index(), streets

    def is_graph_available(self):
        if self.load_directory is None:
            print("Preparing map.")
            print("Extracting POI.")
            self.build_graph()
            logging.info("Graph built successfully.")
        else:
            print("Loading map from directory.")
            self.load_map(self.load_directory)

    def build_graph(self):
        processed_poi = self.poi.reset_index()
        processed_poi = processed_poi[processed_poi.element_type == 'node']
        ox.save_graph_shapefile(self.osmnx_graph, filepath='data/sample/', encoding='utf-8')
        # load as GeoDataFrame
        nodes = gpd.read_file('data/sample/nodes.shp')
        edges = gpd.read_file('data/sample/edges.shp')
        # Todo Add support for polygons
        self.nodes, self.edges = connect_poi(processed_poi, nodes, edges, key_col='osmid', path=None)
        self.nx_graph = nx.from_pandas_edgelist(self.edges, 'u', 'v', edge_attr='geometry')
        for index, row in self.nodes.iterrows():
            try:
                self.nx_graph.nodes[row['osmid']]['geometry'] = (row['geometry'].x, row['geometry'].y)
            except:
                print(f"failed: {row['osmid']}")

    def get_valid_path(self, dir_name: Text, name_ending: Text,
                       file_ending: Text) -> Optional[Text]:
        '''Creates the file path and checks validity.
        Arguments:
          dir_name: The directory of the path.
          name_ending: the end of the name  of the file
          (_graph or _node or_poi or_streets).
          file_ending: the type of the file.
        Returns:
          The valid path.
        '''

        base_filename = self.map_name.lower() + name_ending

        # Check if directory is valid.
        assert os.path.exists(dir_name), "Current directory is: {0}. The \
    directory {1} doesn't exist.".format(
            os.getcwd(), dir_name)

        # Create path.
        path = os.path.join(dir_name, base_filename + file_ending)

        return path

    def write_map(self, dir_name: Text):
        '''Save POI to disk.'''
        # Write POI.
        pd_poi = copy.deepcopy(self.poi)
        if 's2cellids' in pd_poi.columns:
            pd_poi['cellids'] = pd_poi['s2cellids'].apply(
                lambda x: util.cellids_from_s2cellids(x))
        # pd_poi.drop(['s2cellids'], 1, inplace=True)

        path = self.get_valid_path(dir_name, '_poi', '.pkl')
        if not os.path.exists(path):
            pd_poi.to_pickle(path)
        else:
            logging.info(f"path {path} already exist.")

        # Write streets.
        pd_streets = copy.deepcopy(self.streets)

        path = self.get_valid_path(dir_name, '_streets', '.pkl')
        if not os.path.exists(path):
            pd_streets.to_pickle(path)
        else:
            logging.info(f"path {path} already exist.")

        # Write graph.
        base_filename = self.map_name.lower() + "_graph"
        path = os.path.join(dir_name, base_filename + ".gpickle")
        if not os.path.exists(path):
            nx.write_gpickle(self.nx_graph, path)
        else:
            logging.info(f"path {path} already exist.")

    def load_poi(self, path: Text):
        '''Load POI from disk.'''
        assert os.path.exists(
            path), f"Path {path} doesn't exist."
        poi_pandas = pd.read_pickle(path)
        if 'cellids' in poi_pandas:
            poi_pandas['s2cellids'] = poi_pandas['cellids'].apply(
                lambda x: util.s2cellids_from_cellids(x))
            poi_pandas.drop(['cellids'], 1, inplace=True)

        return poi_pandas

    def load_map(self, dir_name: Text):
        '''Load POI from disk.'''

        # Load POI.
        path = self.get_valid_path(dir_name, '_poi', '.pkl')
        self.poi = self.load_poi(path)

        # Load streets.
        path = self.get_valid_path(dir_name, '_streets', '.pkl')
        self.streets = self.load_poi(path)

        # Load graph.
        path = self.get_valid_path(dir_name, '_graph', '.gpickle')
        assert os.path.exists(
            path), f"path {path} doesn't exists"
        self.nx_graph = nx.read_gpickle(path)
        self.nodes = gpd.read_file('data/sample/nodes.shp')
        self.edges = gpd.read_file('data/sample/edges.shp')

        # TODO fix it
        # self.nodes, self.edges = ox.graph_to_gdfs(self.nx_graph)

        # self.process_param()

    def process_param(self):
        '''Helper function for processing the class data objects.'''

        # Drop columns with list type.
        self.edges.drop(self.edges.columns.difference(
            ['osmid', 'true_length', 'length', 'geometry', 'u', 'v', 'key', 'name']),
            1, inplace=True)
        self.edges['osmid'] = self.edges['osmid'].apply(lambda x: str(x))

# if __name__ == '__main__':
#     out_map = Map(regions.get_region('TelAvivSmall'), 14)
#     out_map.is_graph_available()
#     out_map.write_map('/Users/itaimondshine/PycharmProjects/NLP/toolbox')
