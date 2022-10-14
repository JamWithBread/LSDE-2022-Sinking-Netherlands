#!/usr/bin/env python3

import alphashape as aps
import numpy as np
import json
import random
import time

r = lambda: random.randint(0, 255)

scale_factor = 5
geometry_type = 'random_sample'
color = f'#{r():02X}{r():02X}{r():02X}'
coordinates = np.random.random_sample((11, 3))
shape = aps.alphashape(coordinates, 1.1)

def extract_positions(shape):
    positions_nested = [
        shape.vertices[edge[0]] * scale_factor
        for edge in
        shape.edges
    ]
    print(positions_nested)
    positions_flat = [item.tolist() for sublist in positions_nested for item in sublist]
    return positions_flat


def print_positions(positions):
    for i in range(0, len(positions), 3):
        #     if i % 9==0: print()
        print(f"{positions[i]}, {positions[i + 1]}, {positions[i + 2]},")


positions = extract_positions(shape)
name = int(time.time())
geometry_data = {
    'type': geometry_type,
    'color': color,
    'name': name,
    'positions': positions,
}

with open(f'../frontend/src/mesh_data/{geometry_type}_{name}.json', 'w') as fp:
    json.dump(geometry_data, fp)
