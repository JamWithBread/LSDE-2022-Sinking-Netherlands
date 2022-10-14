# LSDE-2022-Sinking-Netherlands
LSDE Assignment 2, Group02

# Approach 3

### Step 0: ML Model for AHN2 classes
- Note: Realized the AHN2 dataset is unlabeled, hence this step 0 for this dataset where we first use ML to create labels, such as in this example: https://pure.tudelft.nl/ws/portalfiles/portal/54920903/isprs_annals_IV_2_W5_445_2019.pdf
- Use PointNet Model 1 (Section 3.2 of paper) to make ground / not ground classifications of AHN2 dataset. Only keep ground points from result. 
- Impressively accurate

### Step 1: Reduce data size
  - Use point cloud classification labels to filter dataset, ie only keep data points with Ground (2). Only 5 classifications are available in the AHN3 dataset ( Ground, vegetation, building, bridge, and water). Intuitively, the ground label seems like the only reliable class to compare between the dataset s for the purpose of measuing land elevation.
  
### Step 2: 
Establish sea level reference, ie something we can treat as a reference elevation between the ANH2 and ANH3 datasets

### Step 3: 
 - Adjust this step accordingly later, but for now use some heuristic to partition the data into say 100 regions. Do this for both ANH2 and ANH3 datasets so there is an old(ANH2) and a new (ANH3 version for each region. 
 - TODO: How to get the many smaller ANH2 files synced with the larger ANH3 / what points are from the same region?

### Step 4: 
Sample some reasonable amount of datapoints for each region, measure them relative to the sea level reference, get an average elevation for the region. Now we can compare average evelation between the two time periods. For regions where there is a difference, can now "zoom in" and apply the same pipeline again, but on a smaller area and keep more data points.

### Step 5: 
Create simple map visualization (not directly animated from point cloud data) where the degree of average elevation change is indicated by shading of the 100 regions. Can click on a region and the map zooms in, new sub shadings are shown for the zoomed in region. 

## Pros of this method:
 - Straightforward, hardest part will probably be the partitioning of the regions and lining them up with a graphical map of the netherlands to apply shading to + working with the ML model. 
 - Don't have to worry about rendering point cloud images (although it would be cool) - just compares the data directly in a simple way
## Cons of this method
- average height measure might not be sensitive enough to detect sinking in a region
- Might still end up with a lot of data --> sample less but then the average could be even less reliable - must find a balance

# Approach 2
General idea is create a machine learning model that given a x and y coordinate predicts z (height) (potentially swap y and z). We can then query our model and obtain a height map and make it more accurate by querying for more points in the current FOV (if we query in a "grid" pattern for x and y we can easily generate a 2d map of squares with as height the average of the 4 points of its corner). This approach is nice because we can just train the model on as much data as possible, we don't have to wory about overfitting (the model doesn't need to predict anything but the data) and can naturally increase the detail when zooming in by querying more. The bad part is that we are relying on us being able to create a model that actually reasonably approximates the height. If the error of our model is in the order of the difference in heights between ahn2 and ahn3 then what we render obviously doesn't have a lot of meaning. Hence the things that we need to figure out as soon as possible would be:

- Expected average height and standard deviation of ahn2 and ahn3
- Expected mean absolute error for some models

Additionally this approach approximates the point cloud, so we could still use 3d rendering and really it's just a way to compress the points. I am pretty sure there are quite some papers on "compressing" using machine learning. In the end we would just need to store the model which is (hopefully) a lot smaller than the original data, while trading this storage cost for more runtime calculations and (hopefully) not too much of a loss in accuracy (in height)
