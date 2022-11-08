# Databricks notebook source
# MAGIC %pip install laspy[laszip]

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
from pyspark.sql.functions import udf
from pyspark.sql import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
logger = spark._jvm.org.apache.log4j
logging.getLogger("py4j.java_gateway").setLevel(logging.ERROR)
sys.path.append('dbfs/mnt/lsde/datasets/ahn3/')

# COMMAND ----------

ahn2_metadata_df = spark.read.parquet("/mnt/lsde/group02/metadata_df_ahn2_schema-1.parquet")
ahn3_metadata_df = spark.read.parquet("/mnt/lsde/group02/metadata_df_ahn3_schema-1.parquet")
ahn2_f_paths = ahn2_metadata_df.select("file_path").rdd.flatMap(lambda x: x).collect()
ahn3_f_paths = ahn3_metadata_df.select("file_path").rdd.flatMap(lambda x: x).collect()
ahn2_metadata_df.describe().show(), ahn3_metadata_df.describe().show()
ahn2_ahn3_factor = 41432/1375

# COMMAND ----------

def convert_mount_to_regular_path(mount_path):
    mount_path_prefix = "dbfs:/"
    if(not mount_path.startswith(mount_path_prefix)):
        raise ValueError(f"didn't receive mount path: {mount_path}")
    return "/dbfs/" + mount_path[len(mount_path_prefix):]

# COMMAND ----------

schema_1 = StructType([ \
    StructField("x", FloatType(), True), \
    StructField("y", FloatType(), True), \
    StructField("z", FloatType(), True), \
    StructField("file_path", StringType(), True), \
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
    StructField("file_path", StringType(), True) \
])
        

schema_4 = StructType([ \
    StructField("x_grid", IntegerType(), True), \
    StructField("y_grid", IntegerType(), True), \
    StructField("z", FloatType(), True), \
])

schemas = {
    1: schema_1,
    2: schema_2,
    3: schema_3,
    4: schema_4,
}

# check for outliers in the data
def is_outlier(s):
    lower_limit = s.mean() - (s.std() * 3)
    upper_limit = s.mean() + (s.std() * 3)
    return ~s.between(lower_limit, upper_limit)

# pandas
def create_grid(df, grid_size_meter, f_path):
    # reduce x and y to grid coordinates
    df["x_grid"] = df.apply(lambda row: np.floor(row.x / grid_size_meter), axis = 1)
    df["y_grid"] = df.apply(lambda row: np.floor(row.y / grid_size_meter), axis = 1)
    
    # take the average of z with the same grid coordinates.
    df = df[~df.groupby(['x_grid', 'y_grid'])['z'].apply(is_outlier)]
    average_grid = df.groupby(['x_grid', 'y_grid']).agg({'z':'mean'})
    
    average_grid = average_grid.reset_index().astype({'x_grid': 'int32', 'y_grid': 'int32'})
    
    fname = f_path.rsplit('/', 1)[1]
    if 'ahn2' in f_path:
        average_grid.to_parquet('/dbfs/mnt/lsde/group02/ahn2_avg_grids/avg_grid_{fname}.gzip'.format(fname = fname), compression='gzip')
    else:
        average_grid.to_parquet('/dbfs/mnt/lsde/group02/ahn3_avg_grids/avg_grid_{fname}.gzip'.format(fname = fname), compression='gzip')
    

def load_map(f_path, n_chunk_iterator, names, grid_size_meter):
    dfs = []
    with laspy.open(f_path) as f:
            # take point every 100sqm 
            if 'ahn2' in f_path:
                sample_size = int(np.ceil(f.header.point_count / 10000)) 
            else:
                sample_size = int(np.ceil(f.header.point_count / 312250)) 
                
            for points in f.chunk_iterator(n_chunk_iterator):
                points = np.vstack((points.x, points.y, points.z)).transpose()
                current_points = points[::sample_size]
                df = pd.DataFrame(current_points)
                dfs.append(df)
    
    df = pd.concat(dfs, ignore_index=True, copy=False)
    df['file_path'] = f_path
    df.columns = names
   
    create_grid(df, grid_size_meter, f_path)
    return [f_path]

def create_df(f_paths, schema, n_chunk_iterator, grid_size_meter):   
    files_rdd = sc.parallelize([convert_mount_to_regular_path(f_path) for f_path in f_paths])
    points_rdd = files_rdd.map(partial(load_map, n_chunk_iterator=n_chunk_iterator, names=schema.names, grid_size_meter=grid_size_meter)).toDF() 
    points_rdd.collect()
    return

# COMMAND ----------

files_left = get_files_left()
print(files_left[-3:])
df = create_df(files_left, schemas[1], 1_000_000, 50)

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

len(get_files_left())

# COMMAND ----------

# MAGIC %md 
# MAGIC #Get Remaining Files

# COMMAND ----------

def get_ahn2_file_list(ah2_tile_path = '/dbfs/mnt/lsde/datasets/ahn2/tileslaz'):
    base_path = ah2_tile_path
    all_ahn2_files = []
    for folder in os.listdir(base_path):
        folders = base_path+"/"+folder
        if os.path.isdir(folders):
            #print(folders)
            for file in os.listdir(folders):
                #print(file)
                path = folders+'/'+file
                if os.path.isfile(path):
                    all_ahn2_files.append(path)   
    return all_ahn2_files

def get_all_ahn2s(ahn2_file_list):
    x = ahn2_file_list
    all_ahn2_files = [x.rsplit('/', 1)[1][:-4] for x in ahn2_file_list]
    return all_ahn2_files

def get_ahn2_avg_grids(ahn2_avg_path):
    ahn2_avg_grids = []
    base_path = '/dbfs/mnt/lsde/group02/ahn2_avg_grids'
    for file in os.listdir(base_path):
        if os.path.isfile(path):
            ahn2_avg_grids.append(file)
    x = ahn2_avg_grids
    x = [x.rsplit('/',1)[0][9:-9] for x in x]
    #print(x)
    return x
            
def ahn2_remaining(all_ahn2_files, ahn2_avg_path):
    ahn2_avg_grids = get_ahn2_avg_grids(ahn2_avg_path)
    all_ahn2s = get_all_ahn2s(all_ahn2_files)
    remaining = list(set(all_ahn2s) - set(ahn2_avg_grids))
    return remaining
    

# COMMAND ----------

