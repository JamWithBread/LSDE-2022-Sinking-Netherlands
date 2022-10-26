#!/usr/bin/env python3
import json
import argparse
import random
import math
import statistics
import pandas as pd

import shapefile
import shapely
import shapely.geometry
from perlin_noise import PerlinNoise

import utils

parser = argparse.ArgumentParser(description='Create mesh data data dump')
parser.add_argument('-a', '--ahn', type=int, choices=[2, 3])
parser.add_argument('-c', '--maxColumns', type=int, help="number of columns of grid on highest granularity",
                    default=1024)
parser.add_argument('-r', '--maxRows', type=int, help="number of rows of grid on highest granularity", default=1024)
# parser.add_argument('-l', '--levels', type=int, help="number of granularity levels (these might need to be even powers of 4 but this might also just be a bug in the code:)", default=4)
args = parser.parse_args()


def run(maxColumns, maxRows, ahn):
    levels = [0, 3]  # I think these need to be of the form (2^x)-1 to not have weird gaps in certain levels we need a
    # lot of columns and rows for level 15 tho
    sf = shapefile.Reader("./WB_countries_Admin0_10m/WB_countries_Admin0_10m.shp")
    shapeRecordNL = [sr for sr in sf.shapeRecords() if 'Netherlands' in sr.record[4]][-1]

    points = shapeRecordNL.shape.points
    parts = shapeRecordNL.shape.parts
    bbox = shapeRecordNL.shape.bbox
    # bbox = [
    #     268,
    #     6134,
    #     5569,
    #     12308
    # ]

    polygons = utils.create_polygons(points, parts)
    magic_value = -0.0891273
    base_path = "../frontend"
    # base_path = "/dbfs/mnt/lsde/group02"
    create_heightmap_cubes(polygons, args.maxColumns, args.maxRows, levels, bbox, args.ahn, base_path, magic_value)


def get_height(p, df, magic_value=-0.0891273):
    m1 = df['x_grid'] == p[0]
    m2 = df['y_grid'] == p[1]
    if df[m1 & m2]['z'].empty:
        return [p[0], magic_value, p[1]]

    return [p[0], df[m1 & m2]['z'].values[0], p[1]]


# def get_batch(points, df):
#     res = []
#     for p in points:
#         res.append(get_height(p, df))
#     return res
def create_heightmap_cubes(polygons, columns, rows, levels, bbox, ahn, base_path, magic_value):
    max_to_group = 4 ** levels[-1]
    assert (columns * rows) / max_to_group >= 1

    bbox_normalized = utils.normalize_bbox(bbox)
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

    # chunck_size = 2048
    # rdd = sc.parallelize([grid_points_0[i:i + chunck_size] for i in range(0, len(grid_points_0), chunck_size)])
    # grid_points_0 = rdd.flatMap((partial(get_batch, df=df))).collect()
    #
    #
    noise = PerlinNoise(octaves=1, seed=random.randint(0, 9999))

    #     rdd = sc.parallelize(grid_points_0)
    #     grid_points_0 = rdd.map((partial(get_height, df=df))).collect()

    grid_points_0 = [
        (
            p[0],
            abs(noise(p)),  # TODO this line would need to be replaced by the heightmap from the gridding/tiling
            p[1],
            # i // columns,
            # i % rows
        )
        for i, p in enumerate(grid_points_0)
    ]

    cubes = []
    ids = {}
    for level in levels:
        ids[level] = []
    vertices_lengths = []
    column_delta = (bbox_normalized[2] - bbox_normalized[0]) / columns
    row_delta = (bbox_normalized[3] - bbox_normalized[1]) / rows
    # for i, point in enumerate(grid_points_0):
    #     cubes_flat = utils.create_cube(point, column_delta, row_delta)
    #     xs.extend(cubes_flat[0::3])
    #     ys.extend(cubes_flat[1::3])
    #     zs.extend(cubes_flat[2::3])
    #     vertices_lengths.append(len(cubes_flat))
    #     cubes.append(cubes_flat)

    utils.delete_all_json(f'{base_path}/public/chunks/ahn{ahn}/')

    xs = []
    ys = []
    zs = []
    n_chunks = int(len(grid_points_0) / max_to_group)

    positions = []
    start = 0
    side_length = int(math.pow(max_to_group, 0.5))
    # side_length = max_to_group
    end = columns - side_length
    for i in range(n_chunks):
        print(f"processing {i + 1} out of {n_chunks} chunks")
        point_group = []
        chunk_id = f"{start}"

        for r in range(side_length):
            for c in range(side_length):
                c_idx = start + (r * columns) + c
                # print(f"{grid_points_0[0] =}")
                point_group.append(grid_points_0[c_idx])
        if start == end:
            start += side_length
            end += side_length * columns
            start += (side_length - 1) * columns
        else:
            start += side_length
        # for level in levels:
        #     step = int(math.pow(4, level))
        #     # print(f"{step =}")
        #     points_level = []
        #     for foo in range(0, len(point_group), step):
        #         current_points = point_group[foo:foo + step]
        #         points_level.append((
        #             statistics.mean(
        #                 [p[0] for p in current_points]
        #             ),
        #             statistics.mean(
        #                 [p[1] for p in current_points]
        #             ),
        #             statistics.mean(
        #                 [p[2] for p in current_points]
        #             ),
        #         ))
        #     points_level = [p for p in points_level if is_contained((p[0], p[2]))]
        #     points_level = [utils.normalize_point(p, bbox) for p in points_level]
        #     if len(points_level) == 0:
        for level in levels:
            step = int(math.pow(4, level))
            # print(f"{step =}")
            points_level = []
            point_group = [p if is_contained((p[0], p[2])) else (0, magic_value, 0) for p in
                           point_group]
            for foo in range(0, len(point_group), step):
                current_points = point_group[foo:foo + step]
                if all([p[1] == magic_value for p in current_points]):
                    continue
                points_level.append((
                    statistics.mean(
                        [p[0] for p in current_points if p[1] != magic_value]
                    ),
                    statistics.mean(
                        [p[1] for p in current_points if p[1] != magic_value]
                    ),
                    statistics.mean(
                        [p[2] for p in current_points if p[1] != magic_value]
                    ),
                ))
            points_level = [utils.normalize_point(p, bbox) for p in points_level]
            if len(points_level) == 0:
                # print(f"Did not find points for chunk: {chunk_id}")
                continue

            cubes_level = []
            delta_factor = math.pow(step, 0.5)
            for point in points_level:
                cubes_level.extend(utils.create_cube(point, column_delta * delta_factor, row_delta * delta_factor))
            if level == 0:
                xs.extend(cubes_level[0::3])
                ys.extend(cubes_level[1::3])
                zs.extend(cubes_level[2::3])
                vertices_lengths.append(len(cubes_level))
                cubes.append(cubes_level)
            ids[level].append(chunk_id)
            path = f'{base_path}/public/chunks/ahn{ahn}/{chunk_id}_{level}.json'
            positions.append({
                "path": f"ahn{ahn}/{chunk_id}_{level}.json",
                "positions": cubes_level,
            })
            utils.store_positions_as_json(cubes_level, path)
    # for i in range(stop=len(grid_points_0), step=4):

    if any([length % 9 != 0 for length in vertices_lengths]):
        raise ValueError("should be divisible")

    max_vertices = max(vertices_lengths)
    min_x = min(xs)
    min_y = min(ys)
    min_z = min(zs)
    max_x = max(xs)
    max_y = max(ys)
    max_z = max(zs)
    ids_combined = set()
    ids_combined.update(ids[0])
    # for level in levels:
    #     ids_combined.update(ids[level])
    ids['combined'] = sorted(list(ids_combined), key=int)
    if len(ids['combined']) != len(vertices_lengths):
        raise AssertionError(
            f"Number of Chunk IDs [{len(ids_combined)}] and number of vertexLengths [{len(vertices_lengths)}] should be equal"
        )
    metadata = {
        "chunkIds": ids,
        "levels": sorted(levels),
        "maxTriangles": int(max_vertices / 9),
        "vertexLengths": vertices_lengths,
        "minX": min_x,
        "minY": min_y,
        "minZ": min_z,
        "maxX": max_x,
        "maxY": max_y,
        "maxZ": max_z,
        "columns": columns,
        "rows": rows,
    }
    # df_positions = pd.DataFrame.from_records(positions)
    # df_positions.to_parquet(f"{base_path}/public/chunks/ahn{ahn}/positions.gzip", compression='gzip')

    with open(f'{base_path}/src/chunks/ahn{ahn}/_metadata.json', 'w') as fp:
        print(f"dumped to {base_path}/src/chunks/ahn{ahn}/_metadata.json")
        json.dump(metadata, fp)


run(args.maxColumns, args.maxRows, args.ahn)
