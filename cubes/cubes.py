#!/usr/bin/env python3
import json
import argparse
import random

import shapefile
import shapely
import shapely.geometry
from perlin_noise import PerlinNoise

import utils

parser = argparse.ArgumentParser(description='Create mesh data data dump')
parser.add_argument('-a', '--ahn', type=int, choices=[2, 3])
parser.add_argument('-c', '--maxColumns', type=int, help="number of columns of grid on highest granularity",
                    default=256)
parser.add_argument('-r', '--maxRows', type=int, help="number of rows of grid on highest granularity", default=256)
parser.add_argument('-l', '--levels', type=int, help="number of granularity levels", default=3)
args = parser.parse_args()

sf = shapefile.Reader("./WB_countries_Admin0_10m/WB_countries_Admin0_10m.shp")
shapeRecordNL = [sr for sr in sf.shapeRecords() if 'Netherlands' in sr.record[4]][-1]

points = shapeRecordNL.shape.points
parts = shapeRecordNL.shape.parts
bbox = shapeRecordNL.shape.bbox
n_parts = len(parts)
n_points = len(points)

bbox_normalized = utils.normalize_bbox(bbox)
polygons = utils.create_polygons(points, parts)


def create_heightmap_cubes(polygons, columns, rows):
    is_contained = lambda point: any([p.contains(shapely.geometry.Point(point)) for p in polygons])
    column_delta_unnormalized = (bbox[2] - bbox[0]) / columns
    row_delta_unnormalized = (bbox[3] - bbox[1]) / rows

    grid_points_0 = [
        (
            bbox[0] + (x * column_delta_unnormalized),
            bbox[1] + (z * row_delta_unnormalized),
        )
        for x in range(columns) for z in range(rows)
    ]

    grid_points_0 = [p for p in grid_points_0 if
                     is_contained(p)]
    grid_points_0 = [utils.normalize_point(p, bbox, is_flipping=True) for p in grid_points_0]

    noise = PerlinNoise(octaves=1, seed=random.randint(0, 9999))

    grid_points_0 = [
        (
            p[0],
            abs(noise(p)),  # TODO this line would need to be replaced by the heightmap from the gridding/tiling
            p[1],
            i // columns,
            i % rows
        )
        for i, p in enumerate(grid_points_0)
    ]

    ids = []
    max_vertices = 0
    xs = []
    ys = []
    zs = []
    column_delta = (bbox_normalized[2] - bbox_normalized[0]) / columns
    row_delta = (bbox_normalized[3] - bbox_normalized[1]) / rows
    utils.delete_all_json(f'../frontend/public/chunks/ahn{args.ahn}/')
    for i, point in enumerate(grid_points_0):
        cubes_flat = utils.create_cube(point, column_delta, row_delta)
        xs.extend(cubes_flat[0::3])
        ys.extend(cubes_flat[1::3])
        zs.extend(cubes_flat[2::3])
        max_vertices = max(max_vertices, len(cubes_flat))
        level = 0
        column = point[3]
        row = point[4]
        id = f"{(column * rows) + row}"
        ids.append(id)
        path = f'../frontend/public/chunks/ahn{args.ahn}/{id}_{level}.json'
        utils.store_positions_as_json(cubes_flat, path)

    # for i in range(stop=len(grid_points_0), step=4):

    if max_vertices % 9 != 0:
        raise ValueError("should be divisible")

    min_x = min(xs)
    min_y = min(ys)
    min_z = min(zs)
    max_x = max(xs)
    max_y = max(ys)
    max_z = max(zs)
    metadata = {
        "chunkIds": ids,
        "levels": [0],
        "maxTriangles": max_vertices / 9,
        "minX": min_x,
        "minY": min_y,
        "minZ": min_z,
        "maxX": max_x,
        "maxY": max_y,
        "maxZ": max_z,
        "columns": columns,
        "rows": rows,
    }

    with open(f'../frontend/src/chunks/ahn{args.ahn}/_metadata.json', 'w') as fp:
        json.dump(metadata, fp)


create_heightmap_cubes(polygons, args.maxColumns, args.maxRows)
