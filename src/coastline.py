import argparse
from ast import arg
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, box

from src.config import load_config
from src.load_data import PROC_DIR, RAW_DIR, load_dem


class CoastlineProcessor:
    """
    Class to handle coastline data processing, including loading, clipping to DEM extent, and saving.
    """

    def __init__(self, dem_path: Path):
        self.dem_path = dem_path
        self.dem_ds = load_dem(dem_path)

    def load_coastline(self, coastline_path: Path) -> gpd.GeoDataFrame:
        """
        Load coastline data from Natural Earth shapefile.
        """
        coast = gpd.read_file(coastline_path)
        print(coast.crs)
        return coast

    def clip_to_dem(self, coast: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Clip the coastline to the extent of the DEM to focus on the area of interest."""
        dem_bounds = self.dem_ds.bounds  # (left, bottom, right, top)
        minx, miny, maxx, maxy = dem_bounds
        aoi = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs=coast.crs)
        coast_clipped = gpd.overlay(coast, aoi, how="intersection")
        return coast_clipped

    def match_dem_crs(self, coast_clipped: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Reproject the coastline to match the DEM's CRS for accurate spatial analysis."""
        dem_crs = self.dem_ds.crs
        coast_matched = coast_clipped.to_crs(dem_crs)
        return coast_matched

    def save_processed_coastline(
        self, coast_clipped_and_matched: gpd.GeoDataFrame, out_path: Path
    ) -> None:
        """Save the processed coastline as a GeoPackage for use in further analysis and visualization."""
        coast_clipped_and_matched.to_file(out_path, driver="GPKG")


def main(config_path: str = "config.yaml") -> None:
    """Process coastline data for flood risk mapping.

    Args:
        config_path: Path to YAML configuration file
    """
    # Load configuration
    config = load_config(config_path)

    # Process coastline data
    processor = CoastlineProcessor(config.dem_path)
    coast = processor.load_coastline(config.coastline_path)
    coast_clipped = processor.clip_to_dem(coast)
    coast_matched = processor.match_dem_crs(coast_clipped)

    # Save processed coastline
    out_path = config.inter_dir / f"coastline_matched_{config.config_name}.gpkg"
    processor.save_processed_coastline(coast_matched, out_path)
    print(f"Processed coastline saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process coastline data for flood risk mapping."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="Path to YAML configuration file",
    )
    args = parser.parse_args()

    main(config_path=args.config)
