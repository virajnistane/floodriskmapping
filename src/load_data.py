# This file contains functions to load the DEM and save intermediate results.
from pathlib import Path
from typing import Optional

import boto3
import geopandas as gpd
import numpy as np
import numpy.typing as npt
import rasterio
from botocore.exceptions import ClientError
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
    """Load a DEM raster file.

    Args:
        path: Path to the DEM file

    Returns:
        Opened rasterio DatasetReader

    Note:
        The caller is responsible for closing the dataset when done,
        or use within a context manager: with rasterio.open(path) as ds: ...
    """
    try:
        return rasterio.open(path)
    except rasterio.errors.RasterioIOError as e:
        raise RuntimeError(f"Failed to load DEM from {path}: {e}")
    finally:
        if "ds" in locals():
            ds.close()


def download_from_s3(
    s3_path: str,
    local_path: Path,
    bucket_name: str,
    region_name: Optional[str] = "eu-north-1",
) -> None:
    """Download file from S3 to local path."""
    s3 = (
        boto3.client("s3", region_name=region_name)
        if region_name
        else boto3.client("s3")
    )

    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        s3.download_file(bucket_name, s3_path, str(local_path))
        print(f"Downloaded {s3_path} → {local_path}")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            raise RuntimeError(
                f"Error: The object {s3_path} does not exist in bucket {bucket_name}."
            )
        raise RuntimeError(f"S3 download failed: {e}")


def upload_to_s3(
    local_path: Path,
    s3_path: str,
    bucket_name: str,
    region_name: Optional[str] = "eu-north-1",
) -> None:
    """Upload local file to S3."""
    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    s3 = (
        boto3.client("s3", region_name=region_name)
        if region_name
        else boto3.client("s3")
    )

    try:
        s3.upload_file(str(local_path), bucket_name, s3_path)
        print(f"Uploaded {local_path} → {s3_path}")
    except ClientError as e:
        raise RuntimeError(f"S3 upload failed: {e}")


# Path for example usage
if __name__ == "__main__":
    dem_path = RAW_DIR / "dem_delft.tif"
    with load_dem(dem_path) as ds:
        print(f"Loaded DEM with shape {ds.read(1).shape} and CRS {ds.crs}")
