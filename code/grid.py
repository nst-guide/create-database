"""
Helpers for dealing with regularly spaced grids

There are multiple sizes of grids that are important.

- 1 degree: USGS elevation files
- .125 degree: USGS and USFS topo maps
- .1 degree: Lightning count data (with .05 degree offset?)

Lightning data has .1 degree _centerpoints_, so the grid lines are at
40.05, 40.15, 40.25 etc.
"""
from math import ceil, floor
from typing import Iterable

import numpy as np
import pint
from shapely.geometry import Polygon, box

ureg = pint.UnitRegistry()


def get_cells(geom, cell_size, offset=0):
    """
    Args:
        - geom: geometry to check intersections with. Can either be a LineString or a Polygon
        - cell_size: size of cell, usually either 1, .125, or .1 (degrees)
        - offset: Non-zero when looking for centerpoints, i.e. for lightning
          strikes data where the labels are by the centerpoints of the
          cells, not the bordering lat/lons

    Returns:
        Iterable[polygon]: generator yielding polygons representing matching
        cells
    """
    bounds = geom.bounds

    # Get whole-degree bounding box of `bounds`
    minx, miny, maxx, maxy = bounds
    minx, miny = floor(minx), floor(miny)
    maxx, maxy = ceil(maxx), ceil(maxy)

    # Get the lower left corner of each box
    ll_points = get_ll_points(minx, maxx, miny, maxy, offset, cell_size)

    # Get grid intersections
    return get_grid_intersections(geom, ll_points, cell_size)


def get_centroids(cells: Iterable[Polygon], round_digits=None):
    """
    Args:
        - cells: iterable of cells to get centroids of
        - round_digits:
    """
    for cell in cells:
        coord = cell.centroid.coords[0]
        if round_digits is None:
            yield coord
        else:
            yield (round(coord[0], round_digits), round(coord[1], round_digits))


def get_ll_points(minx, maxx, miny, maxy, offset, cell_size):
    for x in np.arange(minx - offset, maxx + offset, cell_size):
        for y in np.arange(miny - offset, maxy + offset, cell_size):
            yield (x, y)


def get_grid_intersections(geom, ll_points, cell_size):
    for ll_point in ll_points:
        ur_point = (ll_point[0] + cell_size, ll_point[1] + cell_size)
        bbox = box(*ll_point, *ur_point)
        if bbox.intersects(geom):
            yield bbox


class LightningGrid:
    def __init__(self, geom):
        super(LightningGrid, self).__init__()

        self.cells = list(get_cells(geom, cell_size=.1, offset=.05))
        self.centroids = list(get_centroids(self.cells, round_digits=1))


class TopoQuadGrid:
    def __init__(self, geom):
        super(TopoQuadGrid, self).__init__()

        self.cells = list(get_cells(geom, cell_size=.125))
