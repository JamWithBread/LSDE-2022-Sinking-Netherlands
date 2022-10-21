#!/usr/bin/env python3
import sys

import numpy as np
import json
import argparse

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

buffer_geometry = {
    "metadata": {
        "version": 4,
        "type": "BufferGeometry"
    },
    "uuid": "AF2ADB07-FBC5-4BAE-AD60-123456789ABC",
    "type": "BufferGeometry",
    "data": {
        "attributes": {
            "position": {
                "itemSize": 3,
                "type": "Float32Array",
                "array": positions
 }}}}

filename = f'../frontend/public/mesh_data/random_triangles_{args.number}.json' \


with open(filename, 'w') as fp:
    json.dump(buffer_geometry, fp)
