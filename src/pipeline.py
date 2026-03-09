from pathlib import Path

import geopandas as gpd
import numpy as np
import numpy.typing as npt
from typing import Any, Optional
import rasterio
from rasterio import features
from rasterio.io import DatasetReader
from shapely.geometry import shape

from src.load_data import load_dem
from src.coastline_buffer import CoastlineBuffer
from src.config import load_config

class FloodRiskPipeline:
    """ Class to compute flood risk based on DEM and a specified water level, including mask generation, vectorization, area summarization, and report writing. """
    def __init__(self, dem_path: Path, water_level: float, coastline_path: Optional[Path] = None, 
                 coast_buffer_dist_m: Optional[float] = 5000.0, metric_crs: int = 3857):
        self.dem_path = dem_path
        self.water_level = water_level
        self.metric_crs = metric_crs
        self.load_dem = load_dem

        if coast_buffer_dist_m is not None and coastline_path is not None:
            self.coastlinebuffer: Any = CoastlineBuffer(dem_path, coastline_path, 
                                                   buffer_dist_m = coast_buffer_dist_m)
            self.coast_mask: npt.NDArray[np.bool_] | None = self.coastlinebuffer.create_buffer_mask()
        else:
            self.coastlinebuffer = None
            self.coast_mask = None

        self.ratio_flooded: float = 0.0

    def compute_flood_mask(self, dem_ds: DatasetReader, water_level: float | None = None) -> npt.NDArray[np.bool_]:
        """ Compute a boolean mask of flooded areas based on the DEM and water level, while respecting nodata values. """
        dem = dem_ds.read(1)
        # Create a mask to ignore nodata values in the DEM when computing flooded areas
        nodata = dem_ds.nodata
        # Only consider valid DEM pixels for flooding, and mark as flooded where elevation is below or equal to the water level
        mask = dem != nodata

        if water_level is None:
            water_level = self.water_level
        flooded: npt.NDArray[np.bool_] = (dem <= water_level) & mask
        
        if self.coast_mask is not None:
            flooded = flooded & self.coast_mask

        self.ratio_flooded = flooded.sum() / mask.sum() if mask.sum() > 0 else 0
        print(f"Flooded area ratio: {self.ratio_flooded:.2%}")
        return flooded

    def save_flood_raster(self, dem_ds: DatasetReader, flooded_mask: npt.NDArray[np.bool_], out_path: Path) -> None:
        """ Save the flooded area mask as a GeoTIFF, using the DEM's metadata for georeferencing and setting nodata values appropriately. """
        meta = dem_ds.meta.copy()
        # Update metadata to reflect the new data type and single band for the flood mask
        meta.update(dtype=rasterio.uint8, count=1)
        # Write the flooded mask to a new GeoTIFF file, converting boolean to uint8 (1 for flooded, 0 for non-flooded) and ensuring nodata values are handled correctly
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(flooded_mask.astype(rasterio.uint8), 1)

    def flooded_polygons_from_mask(self, dem_ds: DatasetReader, flooded_mask: npt.NDArray[np.bool_]) -> gpd.GeoDataFrame:
        """ Convert the flooded area mask into vector polygons using rasterio's features module, and return as a GeoDataFrame. """
        # Use rasterio's features.shapes to extract polygons from the flooded mask, ensuring that only flooded areas (value of 1) are included, 
        # and convert these geometries into a GeoDataFrame with the same CRS as the DEM for spatial consistency.
        transform = dem_ds.transform
        # Generate shapes from the flooded mask, where the value of 1 indicates flooded areas. The mask parameter ensures that only valid flooded areas are considered.
        shapes = features.shapes(
            flooded_mask.astype(np.uint8),
            mask=flooded_mask,
            transform=transform
        )
        # Convert the shapes into a list of geometries, filtering for those that represent flooded areas (value of 1), and create a GeoDataFrame with the appropriate CRS.
        geoms = []
        for geom, value in shapes:
            if value == 1:
                geoms.append(shape(geom))
        gdf = gpd.GeoDataFrame(geometry=geoms, crs=dem_ds.crs)
        return gdf
    
    def summarize_flood_area(self, flood_gdf: gpd.GeoDataFrame) -> float:
        """ Calculate the total flooded area in square kilometers by summing the areas of the polygons, after reprojecting to a metric CRS. """
        # Reproject the flooded polygons tself.metric_crsmetric CRS (e.g., EPSG:3857) to ensure that area calculations are accurate, 
        # then sum the areas of all flooded polygons and convert from square meters to square kilometers for reporting.
        flood_gdf = flood_gdf.to_crs(epsg=3857)  # metric CRS for accurate area calculation
        area_m2: float = flood_gdf.area.sum()
        area_km2: float = area_m2 / 1e6
        return area_km2
    
    def write_summary_report(self, area_km2: float, out_path: Path) -> None:
        """ Write a simple text report summarizing the total flooded area, which can be extended with additional metrics in the future. """
        with open(out_path, "w") as f:
            f.write("Flood Risk Mapping Summary Report\n")
            f.write("===============================\n")
            f.write(f"Water level threshold: {self.water_level} m\n")
            f.write(f"Flooded ratio: {self.ratio_flooded:.2%}\n")
            f.write(f"Total flooded area: {area_km2:.2f} km²\n")
    
def main() -> None:
    # Load configuration
    config = load_config(config_path="configs/config_nice.yaml")
    
    # Initialize pipeline with config parameters
    pipeline = FloodRiskPipeline(
        dem_path=config.dem_path,
        water_level=config.water_level,
        coastline_path=config.coastline_path,
        coast_buffer_dist_m=config.coast_buffer_dist_m,
        metric_crs=config.metric_crs
    )
    
    # Load DEM
    dem_ds = pipeline.load_dem(config.dem_path)
    
    # Compute flood mask
    flooded_mask = pipeline.compute_flood_mask(dem_ds)

    # Save flood raster
    pipeline.save_flood_raster(dem_ds, flooded_mask, config.flood_mask_path)

    # Generate flood polygons
    flood_gdf: gpd.GeoDataFrame = pipeline.flooded_polygons_from_mask(dem_ds, flooded_mask)
    flood_gdf.to_file(config.flood_polygons_path, driver=config.vector_driver)

    # Compute and report area
    area_km2: float = pipeline.summarize_flood_area(flood_gdf)
    print(f"Total flooded area: {area_km2:.2f} km²")

    # Write summary report
    pipeline.write_summary_report(area_km2, config.summary_report_path)

if __name__ == "__main__":
    main()
