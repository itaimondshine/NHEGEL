from typing import Optional, Dict, List, Tuple
from geopandas import GeoDataFrame
from networkx import Mipython, MultiDiGraph
import pandas
import pandas as pd
import shapely
from shapely.geometry import Point
import geopandas as gpd
import osmnx as ox
import numpy as np
from ..map_processor.map_structure import Map
from .utils import flatten_list, polygonizer, azimuth_to_street

MINIMAL_DIST = 50


class GeoFeatures:

    def __init__(self, map: Map):
        # Create Map
        self.map = map

    def get_streets(self, osm_id: int) -> List[str]:
        streets = self.map.edges.loc[self.map.edges['v'] == osm_id, 'name'].tolist()
        return flatten_list(streets)

    def is_poi_in_junction(self, osmid: int):
        return dict(self.map.nx_graph.degree())[osmid] >= 4

    def get_nearby_streets(self, lat, lng, is_primery=False):
        """
        Returns the nearby streets to the POI
        """
        point = Point(lng, lat)
        streets = self.map.streets[self.map.streets.geometry.type == 'LineString'].reset_index()
        streets.dropna(subset='name', inplace=True)
        streets['type'] = streets['name'].apply(lambda x: type(x))
        streets = streets[streets['type'] != list]
        if is_primery:
            streets = streets[
                streets['highway'].isin(
                    ['trunk', 'primary', 'motorway', 'tertiary', 'secondary', 'footway', 'service'])]
        streets['azimuth'] = streets['geometry'].apply(lambda x: azimuth_to_street(point, x))
        polygons = polygonizer(streets['geometry'].to_list())
        streets = streets.drop('index', axis=1)
        streets = streets.drop('level_0', axis=1)
        sjoin_polygons = gpd.sjoin(polygons, streets, predicate='covers')
        polygons['names'] = sjoin_polygons.groupby('index').agg(set)['name']
        return polygons[polygons.contains(point)], polygons

    # def relative_location_to_city_center(city_gdf: GeoDataFrame, end_point: pandas.Series) -> str:
    #     city_center = city_gdf.centroid.iloc[0]
    #     bearing = ox.bearing.calculate_bearing(city_center.y, city_center.x,
    #                                            end_point.centroid[0], end_point.centroid[1])
    #     return _get_bearing(bearing)

# poly, polygons = get_nearby_streets(32.073599, 34.781754, 500, False)
# poly
