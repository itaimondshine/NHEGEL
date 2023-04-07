from typing import Optional, List, Tuple

import pandas as pd
import pyproj
from shapely.geometry import Point
import geopandas as gpd
from ..map_processor.map import Map
import osmnx as ox
from .utils import polygonizer, get_bearing
from shapely.ops import unary_union

from ... import settings


def create_neighborhood_json(city: str):
    city_graph_option1 = ox.geometries_from_place(f'{city}', {'place': 'suburb'})[['name', 'geometry']]
    city_graph_option2 = ox.geometries_from_place(f'{city}', {'boundary': 'administrative'})[['name', 'geometry']]

    concatenated_gpd = pd.concat([city_graph_option2, city_graph_option1], axis=0)
    concatenated_gpd = concatenated_gpd.dropna(subset=['name']).reset_index()
    concatenated_gpd['area'] = concatenated_gpd['geometry'].area
    concatenated_gpd = concatenated_gpd.loc[concatenated_gpd['area'] < 0.000310]

    concatenated_points = concatenated_gpd.loc[concatenated_gpd.geom_type == 'Point']
    concatenated_polygons = concatenated_gpd.loc[concatenated_gpd.geom_type == 'Polygon']

    concatenated_gdf_has_no_polygons = concatenated_points[
        ~ concatenated_points['name'].isin(concatenated_polygons['name'])]
    concatenated_gdf_has_no_polygons_to_polygons = concatenated_gdf_has_no_polygons.buffer(0.006)
    concatenated_gdf_has_no_polygons['geometry'] = concatenated_gdf_has_no_polygons_to_polygons
    neighborhood_gdf = pd.concat([concatenated_polygons, concatenated_gdf_has_no_polygons], axis=0)
    return neighborhood_gdf


def distance_to_point(poi: Point, point: Point) -> int:
    """
    Calculates the distance between two points
    """
    _, _, distance = pyproj.Geod(ellps='WGS84').inv(poi.x, poi.y, point.x, point.y)
    return distance


class GeoFeatures:

    def __init__(self, city, map: Map):
        # Create Map
        self.city = city
        self.map = map
        self.edges = map.edges.reset_index()
        self.city_polygons = map.city_polygons
        self.city_center = unary_union(map.nodes.geometry).centroid
        self.streets = map.streets
        self.polygons_is_no_primery, self.polygons_is_primery = self.get_polygons()

    def get_streets(self, osm_id: str) -> List[str]:
        """
        Retrieves the streets of the osm id
        """
        osm_id = int(osm_id)
        projection_osmid = self.edges[self.edges['u'] == osm_id]['v']
        try:
            optional_streets = [self.edges[self.edges['u'] == proj_osmid]['name'] for proj_osmid in
                                list(projection_osmid)]
            streets = [s.values[0] for s in optional_streets if len(s.values) != 0]
            print(f"optional_streets: {streets}")
            streets = list(set(streets))
            streets = [street for street in streets if street is not None]
            return streets
        except:
            return None

    def is_poi_in_junction(self, osmid: str) -> bool:
        """
        Checks whether a point of interest (POI) with the given OSM ID (osmid)
        is located within a road junction.
        """
        valid_osmid = int(osmid)
        return dict(self.map.nx_graph.degree())[valid_osmid] >= 2

    def _to_polygons(self, streets: pd.DataFrame):
        """
        Converts a Pandas DataFrame of street geometries to a GeoDataFrame of polygons.
        """
        polygons = polygonizer(streets['geometry'].to_list())
        sjoin_polygons = gpd.sjoin(polygons, streets, predicate='covers')
        polygons['names'] = sjoin_polygons.groupby('index').agg(set)['name']
        return polygons

    def get_polygons(self):
        """
        Retrieves the polygons corresponding to non-primary and primary streets
        from the Map's streets DataFrame.
        """
        self.streets.dropna(subset='name', inplace=True)
        self.streets.reset_index(inplace=True)
        self.streets['type'] = self.streets['name'].apply(lambda x: type(x))
        streets_no_primery = self.streets[self.streets['type'] != list]
        streets_no_primery = streets_no_primery[streets_no_primery['geometry'].geom_type == 'LineString']
        streets_primery = streets_no_primery[
            streets_no_primery['highway'].isin(['trunk', 'primary', 'motorway', 'tertiary', 'secondary',
                                                'footway', 'service'])]
        polygons_no_primery, polygons_primery = self._to_polygons(streets_no_primery), self._to_polygons(
            streets_primery)
        return polygons_no_primery, polygons_primery

    def get_nearby_streets(self, lon, lat, is_primery) -> Optional[List[str]]:
        """
        Returns the nearby streets to the POI, if True - returns primery streets, False, for non primery streets
        """

        point = Point(float('{:.4f}'.format(lon)), float('{:.4f}'.format(lat)))
        print(self.polygons_is_no_primery[self.polygons_is_no_primery.contains(point)]['names'])
        try:
            return (
                list(self.polygons_is_primery[self.polygons_is_primery.contains(point)]['names'].iloc[0]) if is_primery
                else list(self.polygons_is_no_primery[self.polygons_is_no_primery.contains(point)]['names'].iloc[0]))
        except:
            return None

    def get_neighborhood(self, poi: Point) -> Optional[str]:
        """
        Returns the neighborhood of the poi
        """
        neighborhoods_series = self.city_polygons[self.city_polygons.contains(poi)]
        if neighborhoods_series['name'].any():
            return neighborhoods_series['name'].iloc[0]

    def get_relation_in_street(self, osmid: str, point: Point) -> Optional[str]:
        """
        Returns None if no street recognized
        """
        street_name = self.get_streets(osmid)
        if street_name:
            street_name = self.get_streets(osmid)[0]
            total_bounds: List[int] = self.map.streets[self.map.streets.name == street_name].total_bounds
            x_first, y_first = total_bounds[:2]
            x_second, y_second = total_bounds[2:]
            distance_to_first_bound: int = Point(x_first, y_first).distance(point)
            distance_to_second_bound: int = Point(x_second, y_second).distance(point)
            if distance_to_second_bound == distance_to_first_bound == 0:
                relation = 0
            else:
                relation = distance_to_first_bound / (distance_to_first_bound + distance_to_second_bound)
            return 'Start' if relation < 0.4 else 'Middle' if relation < 0.6 else 'End'

    def get_distance_from_city_center(self, point: Point) -> Tuple[int, str]:
        """
        Calculates the cardinal direction from the city center
        """

        distance = ox.distance.great_circle_vec(self.city_center.x, self.city_center.y, point.x, point.y)
        bearing = ox.bearing.calculate_bearing(self.city_center.x, self.city_center.y, point.x, point.y)
        bearing_relation = get_bearing(bearing)
        return distance, bearing_relation

    def get_top_k_nearest_landmarks(self, point: Point, k: int = 5) -> List[Tuple[str, str, str]]:
        """
        Returns k nearest landmarks which are in radios of LANDMARKS_DISTANCE from the selected poi
        """
        gdf = self.map.poi.to_crs('EPSG:4326')
        gdf['distance_to_point'] = gdf.apply(lambda row: distance_to_point(point, row['centroid']), axis=1)
        in_distance_from_poi_gdf = gdf.loc[gdf['distance_to_point'] < settings.LANDMARKS_DISTANCE]
        in_distance_from_poi_gdf = in_distance_from_poi_gdf.dropna(subset=['amenity', 'name']).sample(k)
        bearing_angle_list = list(
            map(lambda poi: ox.bearing.calculate_bearing(point.x, point.y, poi.x, poi.y),
                in_distance_from_poi_gdf.centroid))
        bearing_list = list(map(lambda bearing: get_bearing(bearing), bearing_angle_list))
        return list(zip(in_distance_from_poi_gdf.name, in_distance_from_poi_gdf.amenity, bearing_list))
