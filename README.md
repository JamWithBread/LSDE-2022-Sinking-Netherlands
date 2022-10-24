# LSDE-2022-Sinking-Netherlands
LSDE Assignment 2, Group02

## TODO
- Reinier & Jeren
  - Line 56 in cubes.py is what functionally needs to be replaced by the result of our gridding/tiling
- Kailhan
    - Update cubes.py to create different granularities, this is a bit dependent on the gridding/tiling but I can use the perlin noise as is for testing
    - Fetch different granularity level chunks based on distance
- Other stuff
  - Make the UI look better and update on resize
  - Tweak scaling
  - Tweak rendering performance parameters e.g. how many chunks to fetch/distance

## To Run
- Go to the cubes folder and:
```shell
chmod +x cubes.py
./cubes.py -a 2
./cubes.py -a 3
```
This will generate simple chunks for ahn2 and ahn3
- Go to the frontend folder and:
```shell
npm i
npm run start
```
- You should now have a server that you can access on `localhost:3000`