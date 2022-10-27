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
- Run the `### THIS CELL !!! ###` in Combining grid files notebook, afterwards:
- Go to the cubes folder and:
```shell
chmod +x yank.py
./yank.py
```
This will generate chunks based on the heightmap for ahn2 and ahn3
- Go to the frontend folder and:
```shell
npm i
npm run start
```
- You should now have a server that you can access on `localhost:3000`
