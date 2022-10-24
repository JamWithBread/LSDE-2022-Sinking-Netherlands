import json

def store_as_json(positions, path):
    buffer_geometry = {
        "positions": positions
    }
    with open(path, 'w') as fp:
        json.dump(buffer_geometry, fp)
