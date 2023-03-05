import osmnx as ox
from typing import Optional, Dict, List, Tuple
from geopandas import GeoDataFrame
# from networkx import Mipython ultiDiGraph
import pandas

MINIMAL_DIST = 50


# get street name
def get_street_name(end_point: pandas.Series) -> Optional[str]:
    """
    :param end_point: POI
    :return: Street Name which closet to the POI, otherwise None
    """
    geometry = end_point.centroid
    graph = ox.graph_from_point(geometry, dist=500, network_type='all')
    nearest_node: int = ox.distance.nearest_nodes(graph, geometry.x, geometry.y)
    if nearest_node:
        incident_edges: List[Tuple[int, int]] = [(u, v) for u, v, data in graph.edges(nearest_node, data=True)]
        street_names: List[str] = [data['name'] for u, v, data in graph.edges(data=True) if
                                   (u, v) in incident_edges or (v, u) in incident_edges]
        nearest_street_name = street_names[0] if street_names else None
        return nearest_street_name


def get_close_intersection(end_point: pandas.Series) -> Optional[List[str]]:
    """
    :param end_point: POI
    :return: List of strings if there is an intersection close to the point, otherwise None
    """
    px, py = end_point.centroid
    graph: MultiDiGraph = ox.graph.graph_from_point((py, px), dist=MINIMAL_DIST)
    if graph:
        intersection = [node for node, degree in dict(graph.degree()).items() if degree >= 2][0]
        incident_edges = graph.edges(intersection, data=True)
        street_names: List[str] = [data['name'] for _, _, data in incident_edges]
        return street_names


def _get_bearing(bearing: int) -> str:
    """
    Returns the cardinal direction of a given bearing angle in degrees.
    """
    if 0 <= bearing <= 90:
        location = "northeast"
    elif 90 < bearing <= 180:
        location = "southeast"
    elif 180 < bearing <= 270:
        location = "southwest"
    else:
        location = "northwest"
    return location


def relative_location_to_city_center(city_gdf: GeoDataFrame, end_point: pandas.Series) -> str:
    city_center = city_gdf.centroid.iloc[0]
    bearing = ox.bearing.calculate_bearing(city_center.y, city_center.x,
                                           end_point.centroid[0], end_point.centroid[1])
    return _get_bearing(bearing)


