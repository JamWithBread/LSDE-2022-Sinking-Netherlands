# LSDE-2022-Sinking-Netherlands
LSDE Assignment 2, Group02

# Approach 2
General idea is create a machine learning model that given a x and y coordinate predicts z (height) (potentially swap y and z). We can then query our model and obtain a height map and make it more accurate by querying for more points in the current FOV (if we query in a "grid" pattern for x and y we can easily generate a 2d map of squares with as height the average of the 4 points of its corner). This approach is nice because we can just train the model on as much data as possible, we don't have to wory about overfitting (the model doesn't need to predict anything but the data) and can naturally increase the detail when zooming in by querying more. The bad part is that we are relying on us being able to create a model that actually reasonably approximates the height. If the error of our model is in the order of the difference in heights between ahn2 and ahn3 then what we render obviously doesn't have a lot of meaning. Hence the things that we need to figure out as soon as possible would be:

- Expected average height and standard deviation of ahn2 and ahn3
- Expected mean absolute error for some models

Additionally this approach approximates the point cloud, so we could still use 3d rendering and really it's just a way to compress the points. I am pretty sure there are quite some papers on "compressing" using machine learning. In the end we would just need to store the model which is (hopefully) a lot smaller than the original data, while trading this storage cost for more runtime calculations and (hopefully) not too much of a loss in accuracy (in height)

# Approach 1
This method probably won't work as it kinda requires us to convert all points to Potree's format and then render this. While this isn't a problem on it own we are ideally supposed to keep the file size for our final visualisation under 10gb. I haven't verified how big the files are but I am about 99% sure it won't be.
# TODO
- Figure out a way to run Potree on cluster. According to Peter:
> It is possible to execute programs on the cluster (eg using the python os.system function) but indeed the binary program should be present on the driver and workers. The easiest way to do so, certainly if it would be compiled without dynamic libraries that are nonstandard, to simply place it on DBFS. But there is also a possibility to install binary software on Databricks clusters using an install script (if you can provide).
- Get water working see `potree/examples/sample.html` and search for `const plane =`
- Implement slider so we can move plane up and down
- Investigate if the `lidar-data/decompress.py` script is actually necessary. It seems like PotreeConverter might be able to just read the `.laz` files although we might need the decompressed files for mapping as discussed in this doc later as well.
- Size plane to max x/y of points instead of magic value
- Investigate how we want to display the different datasets
  - While Potree seems very easy to use OOTB I doubt that it is easy to implement the interpolation between the two datasets
    - Need to investigate the hierarchy/metadata/octree files and if we can create a mapping between them
      - Mapping could also be created earlier when we still have `.las/laz` files, I don't really know what's easier
    - In principle Potree uses three.js, afaik all "objects" that you render in three.js have a Vector3 position attached to them. Interpolation between this position and a targetPosition is then possible. I (Kailhan) am not a 100% sure if the rendered points are "objects". Creating this mapping so we can have a position and targetPosition is probably not trivial.
  - It is possible to render multiple pointclouds at once though (see `potree/examples/multiple_pointclouds.html` for example) and think it should be relatively straight forward to toggle between which one we are displaying
- Figure out which parts of Potree and PotreeConverter we actually need and throw away the rest
- Clean up the UI
- Automate (more/final) steps

# Installation

These are nowhere near ready or reproducible but as a reference there are roughly the steps I took.

- On Databricks, in workspaces/group-02/the-sinking-netherlands there is a notebook. Executing this in some order should create a sample.laz.
- Download this file to your local computer (e.g using Databricks CLI, might be easier way) to `lidar-data/laz` folder
  - Also mkdir a `lidar-data/las` folder
- Add [potree](https://github.com/potree/potree) as submodule (`git submodule add https://github.com/potree/potree.git`)
- Add [PotreeConverter](https://github.com/potree/PotreeConverter) as submodule (`git submodule add  https://github.com/dddpt/PotreeConverter.git`)
  - This is a fork that has Docker file to build a container that runs PotreeConverter
- Run `lidar-data/decompress.py`
- Run `docker run -it --rm -v /Users/hkstm/IdeaProjects/LSDE-2022-Sinking-Netherlands/lidar-data/las:/lasfiles potreeconverter`
  - The value to `-v` needs an absolute path; replace with whatever you need
- Copy `hierarchy.bin`, `metadata.json`, `octree.bin` to `potree/pointclouds/sample`
- In `potree` directory run `npm start`
- Go to `http://localhost:1234/examples/sample.html`
  - You should get something like this
![](state-of-potree.png)
