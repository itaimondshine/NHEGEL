from typing import Optional, Dict, List, Tuple, Set

import pandas as pd
import pyproj
import shapely.geometry
from shapely.geometry import Point
import geopandas as gpd
from ..map_processor.map_structure import Map
import osmnx as ox
from .utils import flatten_list, polygonizer, azimuth_to_street, get_bearing
from pathlib import Path
from shapely.ops import unary_union

from ... import settings

MINIMAL_DIST = 50
NEIGHBORHOODS_LIBRARY = 'HeGel2/geo/extractors/city_polygons/'


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


def distance_to_point(poi, row):
    geod = pyproj.Geod(ellps='WGS84')
    _, _, distance = geod.inv(poi.x, poi.y, row.centroid.x, row.centroid.y)
    return distance


class GeoFeatures:

    def __init__(self, city, map: Map):
        # Create Map
        self.city = city
        self.map = map
        self.edges = map.edges.reset_index()
        self.city_polygons = gpd.read_file(f'{Path(NEIGHBORHOODS_LIBRARY).joinpath(city)}_neighborhoods.geojson')
        self.city_center = unary_union(map.nodes.geometry).centroid
        self.streets = ox.graph_to_gdfs(ox.graph_from_place('Tel Aviv, Israel', network_type='all'), nodes=False,
                                        edges=True)
        self.polygons_is_no_primery, self.polygons_is_primery = self.get_polygons()

    def get_streets(self, osm_id: str) -> List[str]:
        osm_id = osm_id if osm_id.startswith('#') else int(osm_id)
        osmid = self.edges[self.edges['u'] == osm_id].iloc[0]['osmid']
        optional_streets = self.edges[self.edges['osmid'] == osmid]['name'].to_list()
        streets = [edge for edge in optional_streets if edge != 'poi']
        return flatten_list(streets)
        # streets = self.edges.loc[self.edges['v'] == osm_id, 'name'].tolist()
        # valid_streets = flatten_list(streets)
        # return valid_streets

    def is_poi_in_junction(self, osmid: str) -> bool:
        valid_osmid = osmid if osmid.startswith('#') else int(osmid)
        return dict(self.map.nx_graph.degree())[valid_osmid] >= 4

    def _to_polygons(self, streets: pd.DataFrame):
        polygons = polygonizer(streets['geometry'].to_list())
        sjoin_polygons = gpd.sjoin(polygons, streets, predicate='covers')
        polygons['names'] = sjoin_polygons.groupby('index').agg(set)['name']
        return polygons

    def get_polygons(self):
        """
        Creates Polygons Initially
        """
        self.streets.dropna(subset='name', inplace=True)
        self.streets.reset_index(inplace=True)
        self.streets['type'] = self.streets['name'].apply(lambda x: type(x))
        streets_no_primery = self.streets[self.streets['type'] != list]
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

    def get_neighborhood(self, geometry: shapely.geometry.Point) -> Optional[str]:
        neighborhoods_series = self.city_polygons[self.city_polygons.contains(geometry)]
        if neighborhoods_series['name'].any():
            return neighborhoods_series['name'].iloc[0]

    def get_relation_in_street(self, osmid: int, point: Point) -> Optional[str]:
        """
        Returns None if no street recognized
        """
        street_name = self.get_streets(osmid)
        if len(street_name) > 0:
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

    def get_top_k_nearest_landmarks(self, point, k=5) -> List[Tuple[str, str, str]]:
        gdf = self.map.poi.to_crs('EPSG:4326')
        gdf['distance_to_point'] = gdf.apply(lambda row: distance_to_point(point, row), axis=1)
        in_distance_from_poi_gdf = gdf.loc[gdf['distance_to_point'] < settings.LANDMARKS_DISTANCE]
        in_distance_from_poi_gdf = in_distance_from_poi_gdf.dropna(subset=['amenity', 'name']).sample(k)
        bearing_angle_list = list(
            map(lambda poi: ox.bearing.calculate_bearing(point.x, point.y, poi.x, poi.y),
                in_distance_from_poi_gdf.centroid))
        bearing_list = list(map(lambda bearing: get_bearing(bearing), bearing_angle_list))
        return list(zip(in_distance_from_poi_gdf.name, in_distance_from_poi_gdf.amenity, bearing_list))

    # def relative_location_to_city_center(city_gdf: GeoDataFrame, end_point: pandas.Series) -> str:
    #     city_center = city_gdf.centroid.iloc[0]
    #     bearing = ox.bearing.calculate_bearing(city_center.y, city_center.x,
    #                                            end_point.centroid[0], end_point.centroid[1])
    #     return _get_bearing(bearing)

# poly, polygons = get_nearby_streets(32.073599, 34.781754, 500, False)
# poly
