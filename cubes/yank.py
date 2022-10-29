#!/usr/bin/env python3
import shutil
import os
import sys

import pandas as pd
import utils

public_path = '../frontend/public/chunks'
src_path = '../frontend/src/chunks'

for ahn in ["ahn2", "ahn3"]:
    shutil.rmtree(f'{public_path}/{ahn}')
    shutil.rmtree(f'{src_path}/{ahn}')

try:
    os.system(f'databricks fs cp -r dbfs:/mnt/lsde/group02/public/chunks {public_path}')
    os.system(f'databricks fs cp -r dbfs:/mnt/lsde/group02/src/chunks {src_path}')
except:
    print(
        f"You probably need to install: https://github.com/databricks/databricks-cli. Try running: pip install --upgrade databricks-cli")
    sys.exit()

for ahn in ["ahn2", "ahn3"]:
    df = pd.read_parquet(f'{public_path}/{ahn}/positions.gzip')
    dicts = df.to_dict('records')
    for d in dicts:
        utils.store_positions_as_json(d['positions'], f"{public_path}/{d['path']}")
