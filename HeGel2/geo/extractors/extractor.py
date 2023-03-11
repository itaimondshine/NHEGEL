from typing import Optional, Dict, List, Tuple, Set

import shapely.geometry
from shapely.geometry import Point
import geopandas as gpd
from ..map_processor.map_structure import Map
import osmnx as ox
from .utils import flatten_list, polygonizer, azimuth_to_street
from pathlib import Path


MINIMAL_DIST = 50
NEIGHBORHOODS_LIBRARY = 'HeGel2/geo/extractors/city_polygons/'


def create_neighborhood_json(city: str):
    city_graph = ox.geometries_from_place(f'{city}, Israel', {'place': 'suburb'})[['name', 'geometry']]
    city_graph.to_file(f'city_polygons/{city}.geojson', driver='GeoJSON')

    # Alternative way, again not working for all the places
    city_graph = ox.geometries_from_place(f'{city}', {'boundary': 'administrative'})[['name', 'geometry']]
    city_graph.to_file(f'city_polygons/{city}', driver='GeoJSON')


class GeoFeatures:

    def __init__(self, city, map: Map):
        # Create Map
        self.city = city
        self.map = map
        self.edges = map.edges.reset_index()
        self.polygons = self.get_polygons()
        self.city_polygons = gpd.read_file(f'{Path(NEIGHBORHOODS_LIBRARY).joinpath(city)}_neighborhoods.geojson')


    def get_streets(self, osm_id: int) -> List[str]:
        streets = self.edges.loc[self.edges['v'] == osm_id, 'name'].tolist()
        valid_streets = flatten_list(streets)
        return valid_streets

    def is_poi_in_junction(self, osmid: int):
        return dict(self.map.nx_graph.degree())[osmid] >= 4

    def get_polygons(self):
        """
        Creates Polygons Initially
        """
        streets = self.map.streets[self.map.streets.geometry.type == 'LineString'].reset_index()
        # streets = streets.set_crs("EPSG:4326", allow_override=True)

        streets.dropna(subset='name', inplace=True)
        streets['type'] = streets['name'].apply(lambda x: type(x))
        streets = streets[streets['type'] != list]
        # if is_primery:
        #     streets = streets[
        #         streets['highway'].isin(
        #             ['trunk', 'primary', 'motorway', 'tertiary', 'secondary', 'footway', 'service'])]
        # streets['azimuth'] = streets['geometry'].apply(lambda x: azimuth_to_street(point, x))
        polygons = polygonizer(streets['geometry'].to_list())
        sjoin_polygons = gpd.sjoin(polygons, streets, predicate='covers')
        polygons['names'] = sjoin_polygons.groupby('index').agg(set)['name']
        return polygons

    def get_nearby_streets(self, lon, lat) -> Optional[List[str]]:
        """
        Returns the nearby streets to the POI
        """
        point = Point(lat, lon)
        try:
            return list(self.polygons[self.polygons.contains(point)]['names'].iloc[0])
        except:
            return None

    def get_neighborhood(self, geometry: shapely.geometry.Point) -> Optional[str]:
        print(self.city_polygons[self.city_polygons.contains(geometry)])
        neighborhoods_series = self.city_polygons[self.city_polygons.contains(geometry)]
        print(type(neighborhoods_series))
        if neighborhoods_series:
            return neighborhoods_series.values[0]





    # def relative_location_to_city_center(city_gdf: GeoDataFrame, end_point: pandas.Series) -> str:
    #     city_center = city_gdf.centroid.iloc[0]
    #     bearing = ox.bearing.calculate_bearing(city_center.y, city_center.x,
    #                                            end_point.centroid[0], end_point.centroid[1])
    #     return _get_bearing(bearing)

# poly, polygons = get_nearby_streets(32.073599, 34.781754, 500, False)
# poly
