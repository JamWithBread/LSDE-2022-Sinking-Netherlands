# Databricks notebook source
# MAGIC %pip install laspy[laszip]
# MAGIC %pip install pyspark_dist_explore

# COMMAND ----------

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
from pyspark.sql import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
logger = spark._jvm.org.apache.log4j
logging.getLogger("py4j.java_gateway").setLevel(logging.ERROR)
sys.path.append('dbfs/mnt/lsde/datasets/ahn3/')
# sys.stdout.fileno = lambda: False  # idk its necessary if you want to enable faulthandler https://github.com/ray-project/ray/issues/15551
# faulthandler.enable()
# las = laspy.read('/dbfs/mnt/lsde/datasets/ahn3/C_01CZ1.LAZ')

def convert_mount_to_regular_path(mount_path):
    mount_path_prefix = "dbfs:/"
    if(not mount_path.startswith(mount_path_prefix)):
        raise ValueError(f"didn't receive mount path: {mount_path}")
    return "/dbfs/" + mount_path[len(mount_path_prefix):]

def get_all_laz(dir):
    file_infos = dbutils.fs.ls(dir)
    laz_file_infos = []
    while file_infos:
        file_info = file_infos.pop(0)
        if file_info.name[-1] == '/':
            [file_infos.append(to_check) for to_check in dbutils.fs.ls(file_info.path)]
        elif file_info.name[-4:].lower() == '.laz':
            laz_file_infos.append(file_info)
    return laz_file_infos

# ahn3_file_infos = get_all_laz("dbfs:/mnt/lsde/datasets/ahn3/")
# ahn2_file_infos = get_all_laz("dbfs:/mnt/lsde/datasets/ahn2/")

# COMMAND ----------

def get_file_progress():
    files = []
    for file in os.listdir('/dbfs/mnt/lsde/group02/ahn3_avg_grids'):
        files.append(file[9:-5])
    return files  

def get_files_left():
    files_done = get_file_progress()
    files_left = []

    for file_path in ahn3_f_paths:
        if file_path.rsplit('/', 1)[1] not in files_done:
            files_left.append(file_path)
    files_left.sort()
    return files_left

# COMMAND ----------

len(get_file_progress())

# COMMAND ----------

def get_dir_size(path):
    total = 0
    if os.path.isfile(path):
        total = os.stat(path).st_size
    else:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
    return total

# def create(file_info, which):
#     regular_path = convert_mount_to_regular_path(file_info.path)
#     with laspy.open(regular_path) as f:
#         file_size = get_dir_size(regular_path)
#         df = pd.DataFrame({
#             'point_count': f.header.point_count, 'creation_date': f.header.creation_date, 'x_min': f.header.x_min, 'y_min': f.header.y_min, 'z_min': f.header.z_min, 'x_max': f.header.x_max, 'y_max': f.header.y_max, 'z_max': f.header.z_max, 'file_size': file_size, 'set': which, 'file_path': file_info.path
#         }, index=[file_info.path])
#     return df

# def create_metadata_df(which, file_infos):
#     file_info_rdd = sc.parallelize(file_infos)
#     metadata_dfs = file_info_rdd.map(partial(create, which=which)).collect()
#     metadata_df = pd.concat(
#         metadata_dfs,
#         copy=False
#     )
#     metadata_df = spark.createDataFrame(metadata_df)
#     metadata_df_path = f"/mnt/lsde/group02/metadata_df_{which}_schema-1.parquet"
#     metadata_df.write.mode("overwrite").parquet(metadata_df_path)

# def create_metadata_dfs():
#     create_metadata_df("ahn2", ahn2_file_infos)
#     create_metadata_df("ahn3", ahn3_file_infos)

# create_metadata_dfs()

# COMMAND ----------

ahn2_metadata_df = spark.read.parquet("/mnt/lsde/group02/metadata_df_ahn2_schema-1.parquet")
ahn3_metadata_df = spark.read.parquet("/mnt/lsde/group02/metadata_df_ahn3_schema-1.parquet")
ahn2_f_paths = ahn2_metadata_df.select("file_path").rdd.flatMap(lambda x: x).collect()
ahn3_f_paths = ahn3_metadata_df.select("file_path").rdd.flatMap(lambda x: x).collect()
ahn2_metadata_df.describe().show(), ahn3_metadata_df.describe().show()
ahn2_ahn3_factor = 41432/1375

# COMMAND ----------

metadata_df = ahn2_metadata_df.union(ahn3_metadata_df)
metadata_df = metadata_df.withColumn('square_density', metadata_df.point_count / (metadata_df.x_max -  metadata_df.x_min) * (metadata_df.y_max -  metadata_df.y_min))

# COMMAND ----------

metadata_df.show()

# COMMAND ----------

schema_1 = StructType([ \
    StructField("x", FloatType(), True), \
    StructField("y", FloatType(), True), \
    StructField("z", FloatType(), True), \
    StructField("path", StringType(), True), \
])
schema_2 = StructType([ \
    StructField("X", IntegerType(), True), \
    StructField("Y", IntegerType(), True), \
    StructField("Z", IntegerType(), True), \
    StructField("intensity", IntegerType(), True), \
    StructField("bit_fields", IntegerType(), True), \
    StructField("raw_classification", IntegerType(), True), \
    StructField("scan_angle_rank", IntegerType(), True), \
    StructField("user_data", IntegerType(), True), \
    StructField("point_source_id", IntegerType(), True), \
    StructField("gps_time", FloatType(), True), \
    StructField("file_path", StringType(), True) \
])

schema_3 = StructType([ \
    StructField("X", IntegerType(), True), \
    StructField("Y", IntegerType(), True), \
    StructField("Z", IntegerType(), True), \
    StructField("raw_classification", IntegerType(), True), \
    StructField("gps_time", FloatType(), True), \
    StructField("file_path", StringType(), True) \
])

schemas = {
    1: schema_1,
    2: schema_2,
    3: schema_3,
}

def load_map(f_path, n_point_sample, n_chunk_iterator, names):
    dfs = []
    with laspy.open(f_path) as f:
        if n_point_sample > f.header.point_count:
            n_point_sample = f.header.point_count
        n_points_read = 0 
        n_points_added = 0
        sample = np.random.choice(f.header.point_count, n_point_sample, replace=False)
        mask = np.full(f.header.point_count, False)
        mask[sample] = True
        for points in f.chunk_iterator(n_chunk_iterator):
            current_mask = mask[n_points_read:n_points_read+len(points)]
            current_points = points.array[current_mask]
            if(len(current_points) > 0):
                n_points_added += len(current_points)
                df = pd.DataFrame(current_points)
                dfs.append(df)
            n_points_read += len(points)
            if n_points_added == n_point_sample:
                break        
    df = pd.concat(dfs, ignore_index=True, copy=False)
    df['file_path'] = f_path
    if not 'gps_time' in df.columns:
        df['gps_time'] = pd.Series([], dtype='float64')
    df = df[names]
    return df.to_numpy().tolist()

def create_df(f_paths, schema, n_f_paths, n_point_sample, n_chunk_iterator):
    if(n_f_paths):
        f_paths_sampled = random.sample(f_paths, n_f_paths)
    else:
        f_paths_sampled = f_paths
    files_rdd = sc.parallelize([convert_mount_to_regular_path(f_path) for f_path in f_paths_sampled])
    points_rdd = files_rdd.flatMap(partial(load_map, n_point_sample=n_point_sample, n_chunk_iterator=n_chunk_iterator, names=schema.names))
    df_points = spark.createDataFrame(points_rdd)
    return df_points


# def create_and_store_or_load_df(which, f_paths, n_f_paths, n_point_sample, n_chunk_iterator, schema=3):
#     df_points_path = f"/mnt/lsde/group02/df_points_{which}_files-{n_f_paths}_samples-{n_point_sample}_schema-{schema}.parquet"
#     try:
#         dbutils.fs.ls(df_points_path)
#     except Exception as err:
#         df_points = create_df(f_paths, schemas[schema], n_f_paths, n_point_sample, n_chunk_iterator)
#         df_points.write.parquet(df_points_path)
#         return df_points
#     df_points = spark.read.parquet(df_points_path)
#     return df_points

def create_and_store_df(which, f_paths, n_f_paths, n_point_sample, n_chunk_iterator, schema_id=3):
    df_points_path = f"/mnt/lsde/group02/df_points_{which}_files-{n_f_paths}_samples-{n_point_sample}_schema-{schema_id}.parquet"
    df_points = create_df(f_paths, schemas[schema_id], n_f_paths, n_point_sample, n_chunk_iterator)
    df_points.write.mode("overwrite").parquet(df_points_path)
    parquet_size = get_dir_size(f"/dbfs/{df_points_path}")
#     df_points = spark.read.parquet(df_points_path)
    return df_points, parquet_size

def create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, n_f_paths, n_point_sample=10_000_000, n_chunk_iterator=2_000_000):
    start_time = time.time()
#     df_points_ahn2 = create_and_store_or_load_df("ahn2", ahn2_f_paths, n_f_paths, n_point_sample, n_chunk_iterator)
#     df_points_ahn3 = create_and_store_or_load_df("ahn3", ahn3_f_paths, n_f_paths, n_point_sample, n_chunk_iterator)
    df_points_ahn2, ahn2_parquet_size = create_and_store_df("ahn2", ahn2_f_paths, int(n_f_paths * ahn2_ahn3_factor), int(n_point_sample / ahn2_ahn3_factor), n_chunk_iterator)
    df_points_ahn3, ahn3_parquet_size = create_and_store_df("ahn3", ahn3_f_paths, n_f_paths, n_point_sample, n_chunk_iterator)
    end_time = time.time()
#     print(f"took {end_time - start_time:.2f} for n_f_paths={n_f_paths} n_point_sample={n_point_sample}")  # this isn't very accurate/comparable if loading from disk
    return df_points_ahn2, df_points_ahn3, ahn2_parquet_size, ahn3_parquet_size

# COMMAND ----------

def benchmark(ahn2_f_paths, ahn3_f_paths, n_files):
    start_time = time.time()
    df_points_ahn2, df_points_ahn3, ahn2_parquet_size, ahn3_parquet_size = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, n_files)
    end_time = time.time()
    final_time = end_time - start_time
    print(f"Took {final_time} for n_files=[{n_files}], ahn2_parquet_size=[{ahn2_parquet_size}], ahn3_parquet_size=[{ahn3_parquet_size}]")
    return {
        'final_time': final_time,
        'ahn2_parquet_size': ahn2_parquet_size,
        'ahn3_parquet_size': ahn3_parquet_size,
        'n_files': n_files,
    }

# Took 564.3687908649445 for n_files=[1], ahn2_parquet_size=[159637444], ahn3_parquet_size=[102063005]
# Took 507.361186504364 for n_files=[2], ahn2_parquet_size=[238026499], ahn3_parquet_size=[203126111]
# Took 683.0185735225677 for n_files=[3], ahn2_parquet_size=[253973155], ahn3_parquet_size=[306012682]
# Took 1601.80793094635 for n_files=[4], ahn2_parquet_size=[731415992], ahn3_parquet_size=[719810374]
# Took 1664.0523626804352 for n_files=[5], ahn2_parquet_size=[432920641], ahn3_parquet_size=[812771689]
# Took 983.4224154949188 for n_files=[10], ahn2_parquet_size=[933045820], ahn3_parquet_size=[1014900380]
# Took 2105.7942757606506 for n_files=[25], ahn2_parquet_size=[2272695634], ahn3_parquet_size=[2332844914]





# benchmark_results = [benchmark(ahn2_f_paths, ahn3_f_paths, n_files) for n_files in [2,3,4]]
# benchmark_results

# COMMAND ----------

p = np.polyfit(x,y1,1)
p

# COMMAND ----------

fig, ax = plt.subplots(figsize=(6, 6))
x = np.array([1,2,3,4, 5, 10, 25])
y1 = np.array([ 564.3687908649445 , 507.361186504364 , 683.0185735225677,1601.80793094635, 1664.0523626804352, 983.4224154949188, 2105.794275760650])
sns.scatterplot(x=x, y=y1, ax=ax)
ax.set(ylabel='runtime in seconds', xlabel='# files')
ax.legend()
plt.show()

# COMMAND ----------

benchmark_results = [benchmark(ahn2_f_paths, ahn3_f_paths, n_files) for n_files in [2]]

# COMMAND ----------

benchmark_results = [benchmark(ahn2_f_paths, ahn3_f_paths, n_files) for n_files in [3]]

# COMMAND ----------

benchmark_results = [benchmark(ahn2_f_paths, ahn3_f_paths, n_files) for n_files in [4]]

# COMMAND ----------

benchmark_results = [benchmark(ahn2_f_paths, ahn3_f_paths, n_files) for n_files in [5]]

# COMMAND ----------

benchmark_results = [benchmark(ahn2_f_paths, ahn3_f_paths, n_files) for n_files in [10]]

# COMMAND ----------

benchmark_results = [benchmark(ahn2_f_paths, ahn3_f_paths, n_files) for n_files in [25]]

# COMMAND ----------

n_files_ahn2 = 41432
n_files_ahn3 = 1375
time_for_16_files = 9999
estimated_time = 1375 / 16 * time_for_16_files

# COMMAND ----------

x = np.array([1, 1, 2, 3, 4, 4, 5, 6])
y = np.array([1,2,4])
ax = sns.regplot(x=x, y=y, order=2)
plt.ylabel('runtime in ??')
plt.xlabel('# files sampled')
plt.show()

# COMMAND ----------

x = np.array([1, 1, 2, 3, 4, 4, 5, 6])
y = np.array([1,2,4])
ax = sns.regplot(x=x, y=y, order=2)
plt.ylabel('storage in ??')
plt.xlabel('# files sampled')
plt.show()

# COMMAND ----------

df_points_ahn2_1, df_points_ahn3_1 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 1)
df_points_ahn2_1.describe().show(), df_points_ahn3_1.describe().show()

# COMMAND ----------



# COMMAND ----------

df_points_ahn2_10, df_points_ahn3_10 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 10)
df_points_ahn2_10.describe().show(), df_points_ahn3_10.describe().show()

# COMMAND ----------

df_points_ahn2_20, df_points_ahn3_20 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 25)
df_points_ahn2_20.describe().show(), df_points_ahn3_20.describe().show()

# COMMAND ----------

df_points_ahn2_50, df_points_ahn3_50 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 50)
df_points_ahn2_50.describe().show(), df_points_ahn3_50.describe().show()

# COMMAND ----------

df_points_ahn2_75, df_points_ahn3_75 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 75)
df_points_ahn2_75.describe().show(), df_points_ahn3_75.describe().show()

# COMMAND ----------

df_points_ahn2_100, df_points_ahn3_100 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 100)
df_points_ahn2_100.describe().show(), df_points_ahn3_100.describe().show()

# COMMAND ----------

n_files_values = [1, 10, 25, 50]
for value in n_files_values:
    start_time = time.time()
    
    end_ti

# COMMAND ----------

x = np.array([1, 1, 2, 3, 4, 4, 5, 6])
y = np.array([1, 10, 25, 50, 75, 100])
m, b = np.polyfit(x, y, 1)
plt.plot(x, m*x+b)
plt.ylabel('runtime in s')
plt.ylabel('# files sampled')



# COMMAND ----------



# COMMAND ----------

df_points_ahn2_1375_100, df_points_ahn3_1375_100 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 100)
df_points_ahn2_1375_100.describe().show(), df_points_ahn3_1375_100.describe().show()

# COMMAND ----------

# n_point_sample = 1_000_000
# n_f_paths = len(ahn2_f_paths)
# n_chunk_iterator=100_000
# n_point_sample = int(n_point_sample / ahn2_ahn3_factor)
# which = "ahn2"
# schema_id = 3
# schema = schemas[schema_id]
# df_points_path = f"/mnt/lsde/group02/df_points_{which}_files-{n_f_paths}_samples-{n_point_sample}_schema-{schema_id}.parquet"
# df_points_path = f"/mnt/lsde/group02/tmp-kailhan.parquet"

# start_time = time.time()
# files_rdd = sc.parallelize([convert_mount_to_regular_path(f_path) for f_path in ahn2_f_paths[:100]])
# files_rdd.foreach(lambda x: x)
# time_1 = time.time()
# print(f"took {time_1 - start_time} for parallelize")
# points_rdd = files_rdd.flatMap(partial(load_map, n_point_sample=n_point_sample, n_chunk_iterator=n_chunk_iterator, names=schema.names))
# points_rdd.foreach(lambda x: x)
# time_2 = time.time()
# print(f"took {time_2 - time_1} for flatmap")
# df_points = spark.createDataFrame(points_rdd, schema)

# df_points.write.mode("overwrite").parquet(df_points_path)
# time_3 = time.time()

# # df_points_ahn3 = create_and_store_df("ahn3", ahn3_f_paths, n_f_paths, n_point_sample, n_chunk_iterator)
# df_points.show()
# print(f"took {time_3 - time_2} for write")
# # 2.5min 5.9min

# COMMAND ----------

df_points_ahn2_1375_10000, df_points_ahn3_1375_10000 = create_and_store_or_load_dfs(ahn2_f_paths, ahn3_f_paths, 1375, n_point_sample=10_000)
df_points_ahn2_1375_10000.describe().show(), df_points_ahn3_1375_10000.describe().show()

# COMMAND ----------

from pyspark_dist_explore import hist
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
hist(ax, df_points_ahn2_100.select('z'), bins = 20, color=['red'])
display(fig)

# COMMAND ----------

fig, ax = plt.subplots()
hist(ax, df_points_ahn3_100.select('z'), bins = 20, color=['blue'])
display(fig)

# COMMAND ----------

from pyspark.sql.functions import avg, max, min

df_points_ahn3_100_groupby_path = df_points_ahn3_100.groupBy("path") \
    .agg(min("x").alias("x_min"), \
         max("x").alias("x_max"), \
         avg("x").alias("x_avg"), \
         min("y").alias("y_min"), \
         max("y").alias("y_max"), \
         avg("y").alias("y_avg"), \
         min("z").alias("z_min"), \
         max("z").alias("z_max"), \
         avg("z").alias("z_avg"), \
     )
df_points_ahn3_100_groupby_path.show()

# COMMAND ----------

# # maybe useful snippets
# import shutil  # dbfs doesn't like the way las writes so we first write it locally and then use shutil which dbfs does like
# temp_file = '/tmp/sample.laz'
# dbfs_file = '/dbfs/mnt/lsde/datasets/ahn3/group02/sample.laz'
# las_sample.write(temp_file)
# shutil.copyfile(temp_file, final)

# n_sample = 100
# las_sample = laspy.LasData(las.header)
# indices = np.sort(np.random.choice(len(las.points), n_sample))  # sequential access into las seems to be important
# las_sample.points = las.points[indices]

# COMMAND ----------

df_points = spark.read.parquet('/mnt/lsde/group02/df_points_ahn2_files-100_samples-10000000.parquet')
df_points.describe().show()

# COMMAND ----------

dbutils.fs.ls('/mnt/lsde/group02/')

# COMMAND ----------

dbutils.fs.rm('dbfs:/mnt/lsde/group02/df_points_ahn2_files-1_samples-10000000_schema-2.parquet/', True)

# COMMAND ----------

estimated_size = (1375 / 25) * (2272695634 + 2332844914)

# COMMAND ----------

estimated_size / 1000000000

# COMMAND ----------

((1375 / 25) * 2105.7942757606506) / 1000000000

# COMMAND ----------

115818.68516683578 / (3600)

# COMMAND ----------

get_dir_size( '/dbfs/mnt/lsde/group02/df_points_ahn3_files-25_samples-10000000_schema-3.parquet/')

# COMMAND ----------

get_dir_size( '/dbfs/mnt/lsde/group02/df_points_ahn3_files-25_samples-10000000_schema-3.parquet/')

# COMMAND ----------

# Took 2105.7942757606506 for n_files=[25], ahn2_parquet_size=[2272695634], ahn3_parquet_size=[2332844914]


# COMMAND ----------

