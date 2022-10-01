# LSDE-2022-Sinking-Netherlands
LSDE Assignment 2, Group02

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