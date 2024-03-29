# coding=utf-8
# Copyright 2020 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Defines supported regions and their corresponding polygons."""


import attr
from shapely import wkt
from shapely.geometry import box
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon


@attr.s
class Region:
    """A polygon defining a region on the earth's surface and a name for it.

    `name`: An identifier used to select this region.
    `polygon`: A shapely Polygon defining the bounds of the region.
    `corner_sw`: A shapely Point corresponding to the south-west corner of the
      region's bounding box. This is computed from the given polygon.
    `corner_ne`: A shapely Point corresponding to the north-east corner of the
      region's bounding box. This is computed from the given polygon.
    """

    name: str = attr.ib()
    polygon: Polygon = attr.ib()
    corner_sw: Point = attr.ib(init=False)
    corner_ne: Point = attr.ib(init=False)

    def __attrs_post_init__(self):
        (minx, miny, maxx, maxy) = self.polygon.bounds
        self.corner_sw = Point(minx, miny)
        self.corner_ne = Point(maxx, maxy)


SUPPORTED_REGIONS = [
    Region(
        name="JerusalemSmall",
        polygon=box(minx=35.2220, miny=31.7726, maxx=35.2381, maxy=31.7837),
    ),
    Region(
        name="Haifa",
        polygon=box(minx=34.9499666, miny=32.7579523, maxx=35.0797443, maxy=32.8427003, ccw=True),
    ),
    Region(
        name="DC",
        polygon=box(minx=-77.02767, miny=38.96608, maxx=-77.02704, maxy=38.9686),
    ),
    Region(
        name="Manhattan",
        polygon=wkt.loads(
            "POLYGON ((-73.9455846946375 40.7711351085905,-73.9841893202025 40.7873649535321,-73.9976322499213 40.7733311258037,-74.0035177432988 40.7642404854275,-74.0097394992375 40.7563218869601,-74.01237903206 40.741427380319,-74.0159612551762 40.7237048027967,-74.0199205544099 40.7110727528606,-74.0203570671504 40.7073623945662,-74.0188292725586 40.7010329598287,-74.0087894795267 40.7003781907179,-73.9976584046436 40.707144138196,-73.9767057930988 40.7104179837498,-73.9695033328803 40.730061057073,-73.9736502039152 40.7366087481808,-73.968412051029 40.7433746956588,-73.968412051029 40.7433746956588,-73.9455846946375 40.7711351085905))"
        ),
    ),
    Region(
        name="Pittsburgh",
        polygon=box(minx=-80.035, miny=40.425, maxx=-79.930, maxy=40.460, ccw=True),
    ),
    Region(
        name="Tel Aviv",
        polygon=box(minx=34.7672, miny=32.0620, maxx=34.7802, maxy=32.0700),
    ),
    Region(
        name="Jerusalem",
        polygon=box(minx=35.0852011, miny=31.7096214, maxx=-35.2650457, maxy=31.8826655),
    ),
    Region(
        name="TelAvivSmall",
        polygon=box(minx=34.7726, miny=32.0600, maxx=34.7946, maxy=32.0758),
    ),
    Region(
        name="Pittsburgh_small",
        polygon=Point(-79.9837, 40.4273).buffer(0.0015),
    ),
    Region(
        name="UTAustin",
        polygon=box(minx=-97.74, miny=30.28, maxx=-97.73, maxy=30.29),
    ),
    Region(
        name="RUN-map1",
        polygon=box(minx=-73.99944, miny=40.7484699999999, maxx=-73.98874, maxy=40.7535699999999),
    ),
    Region(
        name="RUN-map2",
        polygon=box(minx=-73.98732, miny=40.723, maxx=-73.97682, maxy=40.7277),
    ),
    Region(
        name="RUN-map3",
        polygon=box(minx=-74.00518, miny=40.74154, maxx=-73.99358, maxy=40.74624),
    ),
]

REGION_LOOKUP = dict(map(lambda r: (r.name, r), SUPPORTED_REGIONS))

SUPPORTED_REGION_NAMES = sorted(list(REGION_LOOKUP.keys()))

REGION_SUPPORT_MESSAGE = "Supported regions: " + ", ".join(SUPPORTED_REGION_NAMES)


def get_region(region_name: str) -> Region:
    try:
        return REGION_LOOKUP[region_name]
    except BaseException:
        raise ValueError(
            f"Unsupported region {region_name}. " "Please choose one of ",
            SUPPORTED_REGION_NAMES,
        )
