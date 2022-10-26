# LSDE-2022-Sinking-Netherlands
LSDE Assignment 2, Group02

## TODO
- Reinier & Jeren
  - Line 56 in cubes.py is what functionally needs to be replaced by the result of our gridding/tiling
- Kailhan
    - Figure out if we can have different granularities than "0" and "3" atm
- Other stuff
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
