# Databricks notebook source
# from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import GaussianMixture, KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# COMMAND ----------

points_df_path = '/mnt/lsde/group02/df_points_ahn3_files-3_samples-10000000_schema-3.parquet/'
points_df = spark.read.parquet(points_df_path)
assembler = VectorAssembler(
inputCols=["X", "Y", "Z"],
outputCol="features")
points_features_df = assembler.transform(points_df)
# points_features_df.show()
# points_features_df.count()

# COMMAND ----------

n_points_df = points_features_df.count()
print(f"count: {n_points_df}")
sampled_features_df = points_features_df.sample(fraction=(8/n_points_df))

# COMMAND ----------

def benchmark(features_df, n_points, n_clusters):
    # todo fix handling of sampling
    start_time = time.time()
    gmm = KMeans(k=n_clusters)
    model = gmm.fit(features_df.select('features').distinct())  
    # Dont ask me why this distinct is needed even if there are no distinct rows
    # I have the feeling this call creates a new dataframe that doesn't have some data in the old dataframe which causes the fit call to fail due to some unspecified assertion failing, a simple alias doesn't fix it though
    predictions_df = model.transform(features_df)
    evaluator = ClusteringEvaluator()
    silhouette = evaluator.evaluate(predictions_df)
    print("Silhouette with squared euclidean distance = " + str(silhouette))
    end_time = time.time()
    final_time = end_time - start_time
    print(f"Took {final_time} for n_points=[{n_points}] and n_clusters=[{n_clusters}]")
    return final_time


final_time = benchmark(sampled_features_df, 2**8, 2)
# final_time = benchmark(points_features_df, 3**8, 4)
# final_time = benchmark(points_features_df, 4**8, 4)
# final_time = benchmark(points_features_df, 5**8, 4)
# final_time = benchmark(points_features_df, 6**8, 4)
# final_time = benchmark(points_features_df, 7**8, 4)
# final_time = benchmark(points_features_df, 8**8, 4)

# COMMAND ----------

features_df=sampled_features_df
n_points=2**8
n_clusters=2
start_time = time.time()
gmm = KMeans(k=n_clusters)
model = gmm.fit(features_df.select('features').distinct())  
# Dont ask me why this distinct is needed even if there are no distinct rows
# I have the feeling this call creates a new dataframe that doesn't have some data in the old dataframe which causes the fit call to fail due to some unspecified assertion failing, a simple alias doesn't fix it though
predictions_df = model.transform(features_df)
evaluator = ClusteringEvaluator()
silhouette = evaluator.evaluate(predictions_df)
print("Silhouette with squared euclidean distance = " + str(silhouette))
end_time = time.time()
final_time = end_time - start_time
print(f"Took {final_time} for n_points=[{n_points}] and n_clusters=[{n_clusters}]")
model.clusterCenters

# COMMAND ----------

# final_time = benchmark(points_features_df, 2**8, 4)
# final_time = benchmark(points_features_df, 3**8, 4)
# final_time = benchmark(points_features_df, 4**8, 4)
# final_time = benchmark(points_features_df, 5**8, 4)
# final_time = benchmark(points_features_df, 6**8, 4)
# final_time = benchmark(points_features_df, 7**8, 4)
# final_time = benchmark(points_features_df, 8**8, 4)
# print()
# print("yooooo")
# print()
# final_time = benchmark(points_features_df, 2**8, 16)
final_time = benchmark(points_features_df, 3**8, 16)
final_time = benchmark(points_features_df, 4**8, 16)
final_time = benchmark(points_features_df, 5**8, 16)
final_time = benchmark(points_features_df, 6**8, 16)
final_time = benchmark(points_features_df, 7**8, 16)
final_time = benchmark(points_features_df, 8**8, 16)

# COMMAND ----------

8388608 * 2

# COMMAND ----------

# final_time = benchmark(points_features_df, 4194304, 4)
# final_time = benchmark(points_features_df, 8388608, 4)
# final_time = benchmark(points_features_df, 4194304, 16)
final_time = benchmark(points_features_df, 8388608, 16)

# COMMAND ----------



x = np.array([256,6561,65536,390625, 1679616, 5764801, 4194304, 8388608, 16777216])
y1 = np.array([77.4420063495636, 68.51130676269531 , 54.32145285606384,58.30058145523071, 83.19623064994812, 174.74088883399963, 184.59756636619568, 532.3610992431641, 417.3221445083618])
y2 = np.array([80.2148585319519, 167.47473073005676, 170.78217363357544, 74.51310110092163, 98.84519052505493, 283.2104604244232, 229.67225861549377, 229.59729170799255,  925.8220195770264])

fig, ax = plt.subplots(figsize=(6, 6))

sns.scatterplot(x=x, y=y1, ax=ax, label='n_cluster = 4')
sns.scatterplot(x=x, y=y2, ax=ax, label='n_cluster = 16')
ax.set(ylabel='runtime in seconds', xlabel='# points')
ax.legend()
plt.show()

# COMMAND ----------

p = np.polyfit(x,y1,1)
p

# COMMAND ----------

[file_info.path for file_info in dbutils.fs.ls('/mnt/lsde/group02/') if 'schema-3' in file_info.path]

# COMMAND ----------

for cluster_id in range(n_clusters)[:1]:
    cluster_df = predictions.filter(predictions.prediction == cluster_id)
    cluster_df.show()

# COMMAND ----------

g = model.gaussians[0]

# COMMAND ----------

g.__dict__