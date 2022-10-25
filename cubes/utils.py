import json
import shapely
import os


def create_polygons(points, parts):
    polygons = []
    for i in range(len(parts)):
        start = parts[i]
        end = parts[i + 1] if i != (len(parts) - 1) else None
        polygon = shapely.geometry.Polygon(shapely.geometry.LinearRing(points[start:end]))
        polygons.append(polygon)
    return polygons


def store_positions_as_json(positions, path):
    positions_dict = {
        "positions": positions
    }
    with open(path, 'w') as fp:
        json.dump(positions_dict, fp)


def read_json(path):
    with open(path, 'r') as fp:
        json_str = fp.read()
        d = json.loads(json_str)
    return d


def delete_all_json(path):
    for item in os.listdir(path):
        if item.endswith(".json"):
            os.remove(os.path.join(path, item))


def normalize_bbox(bbox):
    x_norm = (bbox[0] + bbox[2]) / 2
    z_norm = (bbox[1] + bbox[3]) / 2
    bbox_normalized = [
        (bbox[0] - x_norm),
        (bbox[1] - z_norm),
        (bbox[2] - x_norm),
        (bbox[3] - z_norm),
    ]
    return bbox_normalized


def normalize_point(point, bbox, is_flipping=True):
    x_norm = (bbox[0] + bbox[2]) / 2
    z_norm = (bbox[1] + bbox[3]) / 2

    flip = 1
    if is_flipping:
        flip = -1  # the -1 is to flip the image on the north axis, it's more natural for three js

    px, pz = point[0], point[2]
    px = (px - x_norm) * flip
    pz = (pz - z_norm) * flip
    return px, point[1], pz


def create_cube(point, column_delta, row_delta):
    half_column_delta = column_delta / 2
    half_row_delta = row_delta / 2
    x_start = point[0] - half_column_delta
    y_start = 0
    z_start = point[2] - half_row_delta
    x_end = point[0] + half_column_delta
    y_end = point[1]
    z_end = point[2] + half_row_delta

    p1 = [
        x_start, y_start, z_start
    ]
    p2 = [
        x_start, y_start, z_end
    ]
    p3 = [
        x_start, y_end, z_start
    ]
    p4 = [
        x_end, y_start, z_start
    ]
    p5 = [
        x_start, y_end, z_end
    ]
    p6 = [
        x_end, y_end, z_start
    ]
    p7 = [
        x_end, y_start, z_end
    ]
    p8 = [
        x_end, y_end, z_end
    ]

    t1 = [
        p1, p4, p6
    ]
    t2 = [
        p1, p3, p6
    ]

    t3 = [
        p1, p2, p5
    ]
    t4 = [
        p1, p3, p5
    ]

    t5 = [  # these are the bottom triangles most likely
        p1, p4, p7
    ]
    t6 = [  # these are the bottom triangles most likely
        p1, p2, p7
    ]

    t7 = [
        p8, p2, p7
    ]

    t8 = [
        p8, p5, p2
    ]

    t9 = [
        p8, p6, p3
    ]

    t10 = [
        p8, p5, p3
    ]

    t11 = [
        p8, p7, p4
    ]

    t12 = [
        p8, p6, p4
    ]
    positions = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12]
    positions = [item for sublist in positions for item in sublist]
    positions = [item for sublist in positions for item in sublist]
    return positions
