# This file contains functions to load the DEM and save intermediate results.
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


# Function definitions
def load_dem(path: Path) -> DatasetReader:
    try:
        ds = rasterio.open(path)
        return ds
    except rasterio.errors.RasterioIOError as e:
        print(f"Error loading DEM from {path}: {e}")
        raise


# Path for example usage
if __name__ == "__main__":
    dem_path = RAW_DIR / "dem_delft.tif"
    ds = load_dem(dem_path)
    print(f"Loaded DEM with shape {ds.read(1).shape} and CRS {ds.crs}")
