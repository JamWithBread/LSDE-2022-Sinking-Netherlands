# Databricks notebook source
#%pip install laspy[laszip]
#%pip install open3d
#%pip install pylas

# COMMAND ----------

import sys, os
import laspy, pylas
import open3d as o3d
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

geom = o3d.geometry.PointCloud()
geom.points = o3d.utility.Vector3dVector(point_data)
o3d.visualization.draw_geometries([geom])

# COMMAND ----------



# COMMAND ----------


