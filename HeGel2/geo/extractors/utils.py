import shapely
import geopandas as gpd
from math import atan2, degrees


def flatten_list(l):
    flatten_list = []
    for x in l:
            if type(x).__name__ == 'list':
                for j in x:
                    flatten_list.append(j)
            else:
                flatten_list.append(x)
    return list(set(flatten_list))


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