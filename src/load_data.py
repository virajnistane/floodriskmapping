# This file contains functions to load the DEM and save intermediate results.
import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import rasterio
from rasterio import features
from rasterio.io import DatasetReader
from shapely.geometry import shape

# Define data directories
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROC_DIR = DATA_DIR / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

# Parser for command-line arguments
parser = argparse.ArgumentParser(description="Flood risk mapping pipeline")
parser.add_argument("--dem", type=Path, default=RAW_DIR / "output_hh.tif", help="Path to the input DEM raster")
parser.add_argument("--water-level", type=float, default=2.0, help="Water level in meters above reference")
parser.add_argument("--output-raster", type=Path, default=PROC_DIR / "flood_mask.tif", help="Path to save the flood mask raster")
parser.add_argument("--output-vector", type=Path, default=PROC_DIR / "flood_polygons.gpkg", help="Path to save the flood polygons vector")

args = parser.parse_args()


# Function definitions
def load_dem(path: Path) -> DatasetReader:
    try:
        ds = rasterio.open(path)
        return ds
    except rasterio.errors.RasterioIOError as e:
        print(f"Error loading DEM from {path}: {e}")
        raise

