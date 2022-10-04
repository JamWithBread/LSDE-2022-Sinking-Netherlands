# Databricks notebook source
# MAGIC %pip install laspy[laszip]
# MAGIC #%pip install open3d
# MAGIC #%pip install pylas

# COMMAND ----------

import sys, os
import laspy#, pylas
#import open3d as o3d
import numpy as np
import pandas as pd
import logging

# COMMAND ----------

# prevents "java_gateway - Received command c on object id p0" from printing all the time
logger = spark._jvm.org.apache.log4j
logging.getLogger("py4j.java_gateway").setLevel(logging.ERROR)

# COMMAND ----------

sys.path.append('dbfs/mnt/lsde/datasets/ahn3/')

# COMMAND ----------

las = laspy.read('/dbfs/mnt/lsde/datasets/ahn3/C_01CZ1.LAZ')

# COMMAND ----------

las

# COMMAND ----------

# MAGIC %md
# MAGIC ###Features available in a lidar file

# COMMAND ----------

list(las.point_format.dimension_names)

# COMMAND ----------

#How the data looks
print(len(las.X),"points in a single file")
print(las.X)
print(las.intensity)
print(las.gps_time)


# COMMAND ----------

# MAGIC %md
# MAGIC ### Create 3D point cloud by stacking together the 3 dimensions using numpy

# COMMAND ----------

point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))
point_data

# COMMAND ----------

# MAGIC %md
# MAGIC ### Point classifications:
# MAGIC https://desktop.arcgis.com/en/arcmap/latest/manage-data/las-dataset/lidar-point-classification.htm

# COMMAND ----------

las_small = las[0:20000]
set(list(las_small.classification))
#{1,2,9} -> 'unasigned', 'ground' or 'water' classifications are given to first 20,000 points

# COMMAND ----------

# MAGIC %md
# MAGIC ### can filter out points of a particular class

# COMMAND ----------

#can filter out points of a particular class
water = laspy.create(point_format=las.header.point_format, file_version=las.header.version)
water.points = las.points[las.classification == 9]

# COMMAND ----------

print(len(water.X)," water points")
print(round(len(las.X)/len(water.X),2),"% of points in the file are labeled as water")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Attempt to visualize the file using Open3D (won't work in virtual env)

# COMMAND ----------

las = las[0:1000]
point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))
point_data



# COMMAND ----------

las = laspy.read('/dbfs/mnt/lsde/datasets/ahn2/tileslaz/tile_0_2/ahn_017000_363000.laz')


# COMMAND ----------

list(las.point_format.dimension_names)

# COMMAND ----------

#How the data looks
print(len(las.X),"points in a single file")

# COMMAND ----------

set(list(las.classification))

# COMMAND ----------

# MAGIC %md
# MAGIC # File sizes

# COMMAND ----------



# COMMAND ----------

# File size of single AHN3 file - Compressed
size = os.path.getsize('/dbfs/mnt/lsde/datasets/ahn3/C_01CZ1.LAZ')
print(size/(10**9), "GB")
# Decompressed object:
las = laspy.read('/dbfs/mnt/lsde/datasets/ahn3/C_01CZ1.LAZ')

# COMMAND ----------

#File size of single AHN2 file
size = os.path.getsize('/dbfs/mnt/lsde/datasets/ahn2/tileslaz/tile_0_2/ahn_017000_363000.laz')
print(size/(10**9), "GB")
# Decompressed object:
'/dbfs/mnt/lsde/datasets/ahn2/tileslaz/tile_0_2/ahn_017000_363000.laz'

# COMMAND ----------

print(type(las))

# COMMAND ----------

print(sys.getsizeof(las.X[0]))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get total file count and overall size for ahn2 LAZ files

# COMMAND ----------

total_size = 0
num_files = 0
directory = '/dbfs/mnt/lsde/datasets/ahn2/tileslaz'
for folder in os.listdir(directory):
    #print(directoryfolder)
    if os.path.isdir(directory+"/"+folder):
        for filename in os.listdir(directory+"/"+folder):
            f = os.path.join(directory+"/"+folder, filename)
            # checking if it is a file
            if os.path.isfile(f):
                num_files+=1
                total_size+= os.path.getsize(f)

# COMMAND ----------

print(num_files, "files")
print(total_size/10**9," GB")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get total file count and overall size for ahn3 LAZ files

# COMMAND ----------

import zipfile

# COMMAND ----------

total_size = 0
num_files = 0
skip_zips = -1
directory = '/dbfs/mnt/lsde/datasets/ahn3'
for filename in os.listdir(directory):
    skip_zips +=1
    if skip_zips <= 7:
        continue
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        total_size += os.path.getsize(f)
        num_files +=1


# COMMAND ----------

print(num_files, "files")
print(total_size/10**9," GB")

# COMMAND ----------


