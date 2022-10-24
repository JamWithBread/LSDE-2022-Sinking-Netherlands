#!/usr/bin/env python3
import sys

import numpy as np
import json
import argparse
import utils

parser = argparse.ArgumentParser(description='Create mesh data data dump')
parser.add_argument('-n', '--number', type=int, default=10)
args = parser.parse_args()

if args.number % 3 != 0:
    print(f"number of vertices needs to be divisible by 3 to create triangles, got: {args.number}")
    sys.exit()

dims = 3
coordinates = np.random.random_sample((args.number, dims))

geometry_type = 'random_sample'

positions = [item.tolist() for sublist in coordinates for item in sublist]

path = f'../frontend/public/mesh_data/random_triangles_{args.number}.json'
utils.store_as_json(positions, path)


