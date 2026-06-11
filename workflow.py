import os
import sys
import csv
import json

from gwf import Workflow

from .models import Config


gwf = Workflow(".")

# Assuming input.csv is in the format:
# sample, /path/to/sample/cram

# Parse config
with open("config.json") as fh:
    config = Config(**json.load(fh))

if not os.path.exists(config.ref_path):
    print(f"Invalid path: {config.ref_path}")
    sys.exit(1)

# Create targets for each CRAM in samplesheet
with open('input.csv', "r") as file:
    for row in csv.reader(file):
        # Skip header/comment lines
        if row[0].startswith("#"):
            continue

        sample = row[0].strip()
