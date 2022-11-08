# Databricks notebook source
import sys, os
import laspy
import numpy as np
import pandas as pd
import logging
import random
import time
from functools import partial, reduce
# import faulthandler
from pyspark.sql.types import StructType,StructField, FloatType, StringType, IntegerType
from pyspark.sql.functions import udf
from pyspark.sql import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
logger = spark._jvm.org.apache.log4j
logging.getLogger("py4j.java_gateway").setLevel(logging.ERROR)
sys.path.append('dbfs/mnt/lsde/datasets/ahn3/')

# COMMAND ----------

# combine files in to one df
dfs = []
for file in os.listdir('/dbfs/mnt/lsde/group02/ahn3_avg_grids'):
    path = '/dbfs/mnt/lsde/group02/ahn3_avg_grids/'+file
    df = pd.read_parquet(path)
    dfs.append(df)
df = pd.concat(dfs, ignore_index=True, copy=False)

# COMMAND ----------

# save df
df.to_parquet('/dbfs/mnt/lsde/group02/ahn3_grids.gzip', compression='gzip')

# COMMAND ----------

# read df
df_ahn2 = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn2_grids.gzip')

# COMMAND ----------

df_ahn3 = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn3_grids.gzip')

# COMMAND ----------

print(len(df_ahn3))
print(len(df_ahn2))

# COMMAND ----------

# get the difference between two heightmaps.
def get_diff(df1, df2):
    df1=spark.createDataFrame(df1)
    df2=spark.createDataFrame(df2)
    #df1 = df1.rename(columns = {"z":"ahn2_height"})
    #df2 = df2.rename(columns = {"z":"ahn3_height"})
    df1 = df1.withColumnRenamed("Z","ahn2_height")
    df2 = df2.withColumnRenamed("Z","ahn3_height")
    heights = df1.join(df2, ["x_grid", "y_grid"])
    display(heights)
    result = heights.withColumn("diff", heights.ahn3_height - heights.ahn2_height).select("x_grid", "y_grid", "diff")
    return result

# COMMAND ----------

result = get_diff(df_ahn2, df_ahn3).toPandas()
result.to_parquet('/dbfs/mnt/lsde/group02/diff.gzip', compression='gzip')

# COMMAND ----------

result.describe().show()

# COMMAND ----------

df1 = df_ahn2.sort_values(by=['x_grid', 'y_grid'])

# COMMAND ----------

# get height with coordinates
def get_height(df, x, y):
    m1 = df['x_grid'] == x
    m2 = df['y_grid'] == y
    if df[m1&m2]['z'].empty:
        return None
    return df[m1&m2]['z'].values[0]

# COMMAND ----------

get_height(df1, 3000, 9000)

# COMMAND ----------

df_ahn3 = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn3_grids.gzip')
df_ahn3.max(axis=0)
#   271,
#         6136,
#         5560,
#         12308

# COMMAND ----------

df_ahn3.min(axis=0)

# COMMAND ----------

import json
import os

def store_positions_as_json(positions, path):
    positions_dict = {
        "positions": positions
    }
    with open(path, 'w') as fp:
        json.dump(positions_dict, fp)


def read_json(path):
    with open(path, 'r') as fp:
        json_str = fp.read()
        d = json.loads(json_str)
    return d


def delete_all_json(path):
    for item in os.listdir(path):
        if item.endswith(".json"):
            os.remove(os.path.join(path, item))


def normalize_bbox(bbox):
    x_norm = (bbox[0] + bbox[2]) / 2
    z_norm = (bbox[1] + bbox[3]) / 2
    bbox_normalized = [
        (bbox[0] - x_norm),
        (bbox[1] - z_norm),
        (bbox[2] - x_norm),
        (bbox[3] - z_norm),
    ]
    return bbox_normalized


def normalize_point(point, bbox):
    x_norm = (bbox[0] + bbox[2]) / 2
    z_norm = (bbox[1] + bbox[3]) / 2

    px, pz = point[0], point[2]
    px = (px - x_norm) * -1
    pz = (pz - z_norm)
    return px, point[1], pz


def create_cube(point, column_delta, row_delta):
    half_column_delta = column_delta / 2
    half_row_delta = row_delta / 2
    x_start = point[0] - half_column_delta
    y_start = 0
    z_start = point[2] - half_row_delta
    x_end = point[0] + half_column_delta
    y_end = point[1]
    z_end = point[2] + half_row_delta

    p1 = [
        x_start, y_start, z_start
    ]
    p2 = [
        x_start, y_start, z_end
    ]
    p3 = [
        x_start, y_end, z_start
    ]
    p4 = [
        x_end, y_start, z_start
    ]
    p5 = [
        x_start, y_end, z_end
    ]
    p6 = [
        x_end, y_end, z_start
    ]
    p7 = [
        x_end, y_start, z_end
    ]
    p8 = [
        x_end, y_end, z_end
    ]

    t1 = [
        p1, p4, p6
    ]
    t2 = [
        p1, p3, p6
    ]

    t3 = [
        p1, p2, p5
    ]
    t4 = [
        p1, p3, p5
    ]

    t5 = [  # these are the bottom triangles most likely
        p1, p4, p7
    ]
    t6 = [  # these are the bottom triangles most likely
        p1, p2, p7
    ]

    t7 = [
        p8, p2, p7
    ]

    t8 = [
        p8, p5, p2
    ]

    t9 = [
        p8, p6, p3
    ]

    t10 = [
        p8, p5, p3
    ]

    t11 = [
        p8, p7, p4
    ]

    t12 = [
        p8, p6, p4
    ]
    positions = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12]
    positions = [item for sublist in positions for item in sublist]
    positions = [item for sublist in positions for item in sublist]
    return positions


# COMMAND ----------

df = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn3_grids.gzip')


# COMMAND ----------

df

# COMMAND ----------

for i in range(1024, 0, -1): 
    if (12308 - 6137) % i == 0:
        print(i)
        break

# COMMAND ----------

561/3

# COMMAND ----------

for i in range(1024, 0, -1): 
    if (5560 - 271) % i == 0:
        print(i)
        break

# COMMAND ----------

import json
import random
import math
import statistics
import pandas as pd
 ### THIS CELL !!! ###

def run(maxColumns, maxRows, ahn):
    levels = [0, 3]  # I think these need to be of the form (2^x)-1 to not have weird gaps in certain levels we need a
    # lot of columns and rows for level 15 tho
    if ahn == 3:
        bbox = [271, 6136, 5560, 12308]
    else:
        bbox = [268, 6134, 5569, 12308]
        
#     bbox = [271, 6137, 5560, 12308]

    magic_value = -0.0891273
#     base_path = "../frontend"
    base_path = "/dbfs/mnt/lsde/group02"
    create_heightmap_cubes(maxColumns, maxRows, levels, bbox, ahn, base_path, magic_value)


def get_height(p, df, magic_value=-0.0891273):
    m1 = df['x_grid'] == (int(p[0]))
    m2 = df['y_grid'] == (int(p[1]))
    z = df[m1 & m2]['z']
    if not z.empty:
        return [p[0], z.values[0], p[1]]
    m1 = df['x_grid'] == (int(p[0]) + 1)
    m2 = df['y_grid'] == (int(p[1]))
    z = df[m1 & m2]['z']
    if not z.empty:
        return [p[0], z.values[0], p[1]]
    m1 = df['x_grid'] == (int(p[0]))
    m2 = df['y_grid'] == (int(p[1]) + 1)
    z = df[m1 & m2]['z']
    if not z.empty:
        return [p[0], z.values[0], p[1]]
    m1 = df['x_grid'] == (int(p[0]) + 1)
    m2 = df['y_grid'] == (int(p[1]) + 1)
    z = df[m1 & m2]['z']
    if not z.empty:
        return [p[0], z.values[0], p[1]]  
    return [p[0], magic_value, p[1]]



def get_batch(points, df):
    res = []
    for p in points:
        res.append(get_height(p, df))
    return res

def create_heightmap_cubes(columns, rows, levels, bbox, ahn, base_path, magic_value):
    max_to_group = 4 ** levels[-1]
    assert (columns * rows) / max_to_group >= 1

    bbox_normalized = normalize_bbox(bbox)
    column_delta_unnormalized = (bbox[2] - bbox[0]) / columns
    row_delta_unnormalized = (bbox[3] - bbox[1]) / rows
    
    if ahn == 3:
        df = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn3_grids.gzip')
    else:
        df = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn2_grids.gzip')

    grid_points_0 = [
        (
            bbox[0] + (x * column_delta_unnormalized),
            bbox[1] + (z * row_delta_unnormalized),
        )
        for x in range(columns) for z in range(rows)
    ]

    chunck_size = 2048
    rdd = sc.parallelize([grid_points_0[i:i + chunck_size] for i in range(0, len(grid_points_0), chunck_size)])
    grid_points_0 = rdd.flatMap((partial(get_batch, df=df))).collect()
    
    
#     noise = PerlinNoise(octaves=1, seed=random.randint(0, 9999))

    #     rdd = sc.parallelize(grid_points_0)
    #     grid_points_0 = rdd.map((partial(get_height, df=df))).collect()

#     grid_points_0 = [
#         (
#             p[0],
#             abs(noise(p)),  # TODO this line would need to be replaced by the heightmap from the gridding/tiling
#             p[1],
#             # i // columns,
#             # i % rows
#         )
#         for i, p in enumerate(grid_points_0)
#     ]

    cubes = []
    ids = {}
    for level in levels:
        ids[level] = []
    vertices_lengths = []
    column_delta = (bbox_normalized[2] - bbox_normalized[0]) / columns
    row_delta = (bbox_normalized[3] - bbox_normalized[1]) / rows

    delete_all_json(f'{base_path}/public/chunks/ahn{ahn}/')

    xs = []
    ys = []
    zs = []
    n_chunks = int(len(grid_points_0) / max_to_group)

    positions = []
    start = 0
    side_length = int(math.pow(max_to_group, 0.5))
    end = columns - side_length
    for i in range(n_chunks):
        print(f"processing {i + 1} out of {n_chunks} chunks")
        point_group = []
        chunk_id = f"{start}"

        for r in range(side_length):
            for c in range(side_length):
                c_idx = start + (r * columns) + c
                point_group.append(grid_points_0[c_idx])
        if start == end:
            start += side_length
            end += side_length * columns
            start += (side_length - 1) * columns
        else:
            start += side_length
        for level in levels:
            step = int(math.pow(4, level))
            points_level = []
#             point_group = [p if is_contained((p[0], p[2])) else (0, magic_value, 0) for p in
#                            point_group]
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
            points_level = [normalize_point(p, bbox) for p in points_level]
            if len(points_level) == 0:
                # print(f"Did not find points for chunk: {chunk_id}")
                continue

            cubes_level = []
            delta_factor = math.pow(step, 0.5)
            for point in points_level:
                cubes_level.extend(create_cube(point, column_delta * delta_factor, row_delta * delta_factor))
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
#             utils.store_positions_as_json(cubes_level, path)

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
    df_positions = pd.DataFrame.from_records(positions)
    df_positions.to_parquet(f"{base_path}/public/chunks/ahn{ahn}/positions.gzip", compression='gzip')

    with open(f'{base_path}/src/chunks/ahn{ahn}/_metadata.json', 'w') as fp:
        print(f"dumped to {base_path}/src/chunks/ahn{ahn}/_metadata.json")
        json.dump(metadata, fp)

column_size = 1024
row_size = 1024
run(column_size, row_size, 2)
run(column_size, row_size, 3)

# COMMAND ----------

dbutils.fs.mkdirs('/mnt/lsde/group02/src/chunks/ahn2/')

# COMMAND ----------

#dbutils.fs.mkdirs('/mnt/lsde/group02/public/chunks/ahn3/')

# COMMAND ----------

df = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn3_avg_grids/avg_grid_C_65AZ2.LAZ.gzip')
square_df = df.set_index(['y_grid', 'x_grid'])['z'].unstack()
print(square_df)
plt.pcolor(square_df)
plt.colorbar()
plt.show()

# COMMAND ----------

df = pd.read_parquet('/dbfs/mnt/lsde/group02/diff.gzip')
std, mean = df['diff'].agg(['std','mean'])

df['diff'] = df['diff'].where(df['diff'].between(mean-3*std, mean+3*std)).ffill()
df.hist(column='diff')


# COMMAND ----------

plt.pcolor(square_df)
plt.colorbar()
plt.show()

# COMMAND ----------

df = pd.read_parquet('/dbfs/mnt/lsde/group02/diff.gzip')
std, mean = df['diff'].agg(['std','mean'])

df['diff'] = df['diff'].where(df['diff'].between(mean-3*std, mean+3*std)).ffill()
diff_df = df.sort_values('diff').drop_duplicates(subset=['y_grid', 'x_grid'], keep='last')
square_df = diff_df.set_index(['y_grid', 'x_grid'])['diff'].unstack()

from matplotlib import colors
#discrete_colors = [(33, 33, 245), (69, 76, 215), (102, 107, 216), (124, 128, 217), (255, 181, 165), (255, 128, 110), (255, 70, 65), (255, 0, 20)]
discrete_colors = [(33, 33, 245), (240, 240, 240), (255, 0, 20)]
discrete_colors = [(r/255., g/255., b/255.) for r, g, b in discrete_colors]         

my_colormap = colors.ListedColormap(discrete_colors)
sub_df = square_df.iloc[1739:1864, 229:329]
plt.pcolor(sub_df, cmap=my_colormap, vmin=-0.15, vmax=0.15)
plt.colorbar()
plt.axis('equal')
plt.show()

# COMMAND ----------

print(square_df)

# COMMAND ----------

df_ahn3 = pd.read_parquet('/dbfs/mnt/lsde/group02/ahn3_grids.gzip')
z_maxes = df_ahn3.groupby(['y_grid', 'x_grid']).z.transform(max)
df_ahn3 = df_ahn3.loc[df_ahn3.z == z_maxes]
square_df = df_ahn3.set_index(['y_grid', 'x_grid'])['z'].unstack()
sub_df = square_df.iloc[1739:1864, 229:329]
plt.pcolor(sub_df)
plt.show()

# COMMAND ----------

sub_df = square_df.iloc[0:4096, 1739:1864]
print(sub_df)

# COMMAND ----------

df_ahn2 = df_ahn2.sort_values('z').drop_duplicates(subset=['y_grid', 'x_grid'], keep='last')
square_df = df_ahn2.set_index(['y_grid', 'x_grid'])['z'].unstack()
plt.pcolor(square_df)
plt.show()

# COMMAND ----------

diff_df = pd.read_parquet('/dbfs/mnt/lsde/group02/diff.gzip')
diff_df = diff_df.sort_values('diff').drop_duplicates(subset=['y_grid', 'x_grid'], keep='last')
square_df = diff_df.set_index(['y_grid', 'x_grid'])['diff'].unstack()
sub_df = square_df.iloc[1739:1864, 229:329]
plt.pcolor(sub_df)
plt.show()