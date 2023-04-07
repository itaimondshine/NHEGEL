import math
from typing import List, Tuple, Optional

import numpy as np
import shapely
import geopandas as gpd
from math import atan2, degrees


def flatten_list(streets: List[Tuple[Optional[str], List[str]]]) -> List[str]:
    valid_streets = []
    for street in streets:
        if type(street).__name__ == 'list':
            for sub_list in street:
                valid_streets.append(sub_list)
        elif not str(street) == 'nan':
            valid_streets.append(street)
    return list(set(valid_streets))


def polygonizer(lines):
    merged_lines = shapely.ops.linemerge(lines)
    border_lines = shapely.ops.unary_union(merged_lines)
    decomposition = shapely.ops.polygonize(border_lines)
    polygons = gpd.GeoDataFrame(decomposition, columns=['geometry'])
    return polygons.reset_index()


def azimuth_to_street(point, street):
    angles = 0
    for l in street.boundary.geoms:
        angles += degrees(atan2(l.y - point.y, l.x - point.x))

    azimuth = angles / len(street.boundary.geoms) if len(street.boundary.geoms) != 0 else 0
    if azimuth <= 0:
        azimuth += 360
    return int(np.round(azimuth))


def get_bearing(bearing: int) -> str:
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
