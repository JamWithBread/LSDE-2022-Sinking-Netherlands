#!/usr/bin/env python3

import alphashape as aps
import numpy as np
import json
import random
import time
import argparse
import trimesh
import tripy
import shapely

parser = argparse.ArgumentParser(description='Create mesh data data dump')
parser.add_argument('-p', '--path', type=str, help='path of np array')
parser.add_argument('-a', '--alpha', type=float, default=1.1)
parser.add_argument('-n', '--number', type=int, default=10)
parser.add_argument('-f', '--filename', type=str)
args = parser.parse_args()

dims = 2 if args.path else 3
coordinates = np.load(args.path) if args.path else np.random.random_sample((args.number, dims))

r = lambda: random.randint(0, 255)

scale_factor = 1
geometry_type = 'random_sample'
color = f'#{r():02X}{r():02X}{r():02X}'
shape = aps.alphashape(coordinates, args.alpha)


def extract_positions(shape):
    if isinstance(shape, shapely.geometry.polygon.Polygon):
        triangles_3d = [
            (triangle[0] * scale_factor, 0, triangle[1] * scale_factor)
            for triangle
            in [
                item
                for sublist
                in tripy.earclip(shape.exterior.coords)
                for item
                in sublist
            ]
        ]
        positions_flat = [item for sublist in triangles_3d for item in sublist]
    elif isinstance(shape, trimesh.base.Trimesh):
        positions_nested = [
            shape.vertices[edge[0]] * scale_factor
            for edge in
            shape.edges
        ]
        positions_flat = [item.tolist() for sublist in positions_nested for item in sublist]
    else:
        raise ValueError(f"Received {shape} as shape; type {type(shape)} is not supported")
    return positions_flat


positions = extract_positions(shape)
name = int(time.time())
geometry_data = {
    'type': geometry_type,
    'color': color,
    'name': name,
    'positions': positions,
}

filename = f'../frontend/src/mesh_data/{args.filename}.json' \
    if args.filename \
    else f'../frontend/src/mesh_data/{geometry_type}_{name}.json'

with open(filename, 'w') as fp:
    json.dump(geometry_data, fp)
