# Databricks notebook source
# MAGIC %pip install alphashape

# COMMAND ----------

import numpy as np
import alphashape as aps
import time
import matplotlib.pyplot as plt
import seaborn as sns

# COMMAND ----------

def benchmark(n, alpha):
    start_time = time.time()
    coordinates = np.random.random_sample((n, 3))
    alpha_shape = alphashape.alphashape(coordinates, n)
    end_time = time.time()
    final_time = end_time - start_time
    print(f"Took {final_time} for n=[{n}] and alpha=[{alpha}]")
    return final_time

# times = [benchmark(n, 0) for n in [16**1,16**2,16**3, 16**4, 16**5]]

# COMMAND ----------

times = [benchmark(n, 2) for n in [16**1,16**2,16**3, 16**4, 16**5]]

# COMMAND ----------

times = [benchmark(n, 0) for n in [2097152,4194304]]
times = [benchmark(n, 2) for n in [2097152,4194304]]

# COMMAND ----------

2097152*2

# COMMAND ----------

x = np.array([16,256,4096,65536, 1048576, 2097152])
y1 = np.array([0.012003421783447266, 0.18588471412658691, 2.632500648498535, 37.881858587265015, 614.1783375740051, 1189.2934136390686])
y2 = np.array([0.04332256317138672, 0.12378525733947754, 2.1727211475372314, 36.416183948516846, 597.9597585201263, ])

fig, ax = plt.subplots(figsize=(6, 6))

sns.regplot(x=x, y=y1, fit_reg=True, order=2, ci=None, ax=ax, label='alpha = 0')
sns.regplot(x=x, y=y2,  fit_reg=True, order=2, ci=None, ax=ax, label='alpha = 2')
ax.set(ylabel='runtime in seconds', xlabel='# coordinates')
ax.legend()
plt.show()

# COMMAND ----------

p = np.polyfit(x,y1,1)
p

# COMMAND ----------

coordinates = np.random.random_sample((6, 3))
alpha_shape = alphashape.alphashape(coordinates, 1.1)
alpha_shape.show()

# COMMAND ----------

type(alpha_shape)

# COMMAND ----------

def extract_positions(alpha_shape):
    positions_nested = [
        alpha_shape.vertices[edge[0]]
        for edge in
        alpha_shape.edges
    ]
    positions_flat = [item.tolist() for sublist in positions_nested for item in sublist]
    return positions_flat

def print_positions(l):
    for i in range(0, len(l), 3):
    #     if i % 9==0: print()
        print(f"{l[i]}, {l[i+1]}, {l[i+2]},")
print_positions(extract_positions(alpha_shape))

# COMMAND ----------

# MAGIC %pip install laspy[laszip]

# COMMAND ----------

import laspy
las = laspy.open('/dbfs/mnt/lsde/datasets/ahn2/tileslaz/tile_0_2/ahn_017000_363000.laz')

# COMMAND ----------

las.header.point_format.dimensions

# COMMAND ----------

dbutils.fs.ls('/mnt/lsde/group02/')

# COMMAND ----------

