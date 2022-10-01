#!/usr/bin/env python3

import os
import laspy

las_path = './las'
laz_path = './laz'
get_file_paths = lambda path: [f_path for f_path in os.listdir(path) if os.path.isfile(os.path.join(path, f_path))]
las_file_paths = get_file_paths(las_path)
laz_file_paths = get_file_paths(laz_path)
strip_extension = lambda path: path.split('.')[:-1][-1]
las_file_paths_wo_extension = [strip_extension(f_path) for f_path in las_file_paths]

to_decompress = [f_path for f_path in laz_file_paths if (strip_extension(f_path)) not in las_file_paths_wo_extension]

for f_path in to_decompress:
    las = laspy.read(f"{laz_path}/{f_path}")
    las.write(f"{las_path}/{strip_extension(f_path)}.las")
