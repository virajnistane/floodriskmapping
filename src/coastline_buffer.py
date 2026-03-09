import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import rasterio
from rasterio import features
from rasterio.io import DatasetReader
from shapely.geometry import shape

from src.coastline import CoastlineProcessor
from src.config import load_config
from src.load_data import PROC_DIR, RAW_DIR, load_dem


class CoastlineBuffer:
    """Class to create a coastal buffer zone and generate a raster mask for flood risk analysis."""

    def __init__(self, dem_path: Path, coastline_path: Path, buffer_dist_m: float):
        self.dem_ds = load_dem(dem_path)
        self.coastline_processor = CoastlineProcessor(dem_path)

        self.coast_gdf = self.coastline_processor.load_coastline(coastline_path)
        if self.coast_gdf.crs != self.dem_ds.crs:
            print(
                f"Warning: Coastline CRS {self.coast_gdf.crs} does not match DEM CRS {self.dem_ds.crs}. Clipping and matching will be performed."
            )
            coast_clipped = self.coastline_processor.clip_to_dem(self.coast_gdf)
            self.coast_gdf = self.coastline_processor.match_dem_crs(coast_clipped)

        self.buffer_dist_m = buffer_dist_m

    def create_buffer_mask(self) -> npt.NDArray[np.bool_]:
        """Create a raster mask of the coastal buffer zone for use in flood risk analysis."""

        buffered_gdf = create_coast_buffer(
            self.coast_gdf, self.buffer_dist_m, self.dem_ds.crs
        )
        coast_mask: npt.NDArray[np.bool_] = rasterize_coast_buffer(
            buffered_gdf, self.dem_ds
        )
        return coast_mask

    def save_buffer_mask(
        self, coast_mask: npt.NDArray[np.bool_], out_path: Path
    ) -> None:
        """Save the coastal buffer mask as a GeoTIFF, using the DEM's metadata for georeferencing and setting nodata values appropriately."""
        meta = self.dem_ds.meta.copy()
        meta.update(dtype=rasterio.uint8, count=1)
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(coast_mask.astype(rasterio.uint8), 1)


def create_coast_buffer(coast_gdf, buffer_dist_m: float, dem_crs):
    """Buffer coastline inland by X meters."""
    buffered = coast_gdf.to_crs("EPSG:3857")  # metric CRS for buffering
    buffered["geometry"] = buffered.geometry.buffer(buffer_dist_m)
    buffered = buffered.to_crs(dem_crs)
    return buffered


def rasterize_coast_buffer(buffered_gdf, dem_ds, out_value=1):
    """Convert buffered coastline to raster mask matching DEM."""
    transform = dem_ds.transform
    height, width = dem_ds.height, dem_ds.width

    # Rasterize: 1 where within buffer, 0 elsewhere
    coast_mask = features.geometry_mask(
        buffered_gdf.geometry,
        out_shape=(height, width),
        transform=transform,
        invert=True,  # True = inside polygon
    ).astype(bool)

    return coast_mask


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate coastal buffer mask for flood risk mapping."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="Path to YAML configuration file",
    )
    args = parser.parse_args()
    config = load_config(config_path=args.config)

    coastline_buffer = CoastlineBuffer(
        dem_path=config.dem_path,
        coastline_path=config.coastline_path,
        buffer_dist_m=5000.0,  # Example buffer distance, can be set in config if desired
    )
    coast_mask = coastline_buffer.create_buffer_mask()
    coastline_buffer.save_buffer_mask(
        coast_mask,
        config.inter_dir
        / f"coastline_buffer_mask_{config.config_name}_{config.coast_buffer_dist_m}.tif",
    )
