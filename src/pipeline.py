from pathlib import Path

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import rasterio
from rasterio import features
from rasterio.io import DatasetReader
from shapely.geometry import shape

from src.load_data import RAW_DIR, PROC_DIR, load_dem

class FloodRiskPipeline:
    def __init__(self, dem_path: Path, water_level: float):
        self.dem_path = dem_path
        self.water_level = water_level

    def compute_flood_mask(self, dem_ds: DatasetReader) -> npt.NDArray[np.bool_]:
        dem = dem_ds.read(1)
        nodata = dem_ds.nodata
        mask = dem != nodata
        flooded: npt.NDArray[np.bool_] = (dem <= self.water_level) & mask
        return flooded

    def save_flood_raster(self, dem_ds: DatasetReader, flooded_mask: npt.NDArray[np.bool_], out_path: Path) -> None:
        meta = dem_ds.meta.copy()
        meta.update(dtype=rasterio.uint8, count=1)
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(flooded_mask.astype(rasterio.uint8), 1)

    def flooded_polygons_from_mask(self, dem_ds: DatasetReader, flooded_mask: npt.NDArray[np.bool_]) -> gpd.GeoDataFrame:
        transform = dem_ds.transform
        shapes = features.shapes(
            flooded_mask.astype(np.uint8),
            mask=flooded_mask,
            transform=transform
        )
        geoms = []
        for geom, value in shapes:
            if value == 1:
                geoms.append(shape(geom))
        gdf = gpd.GeoDataFrame(geometry=geoms, crs=dem_ds.crs)
        return gdf
    
    def summarize_flood_area(self, flood_gdf: gpd.GeoDataFrame) -> float:
        flood_gdf = flood_gdf.to_crs(epsg=3857)  # metric CRS
        area_m2: float = flood_gdf.area.sum()
        area_km2: float = area_m2 / 1e6
        return area_km2
    
    def write_summary_report(self, area_km2: float, out_path: Path) -> None:
        with open(out_path, "w") as f:
            f.write(f"Total flooded area: {area_km2:.2f} km²\n")
    
def main() -> None:
    dem_path = RAW_DIR / "dem_delft.tif"
    water_level: float = 2.0  # meters above reference

    pipeline = FloodRiskPipeline(dem_path, water_level)
    dem_ds = load_dem(dem_path)
    flooded_mask = pipeline.compute_flood_mask(dem_ds)

    flood_raster_path: Path = PROC_DIR / "flood_mask_delft.tif"
    pipeline.save_flood_raster(dem_ds, flooded_mask, flood_raster_path)

    flood_gdf: gpd.GeoDataFrame = pipeline.flooded_polygons_from_mask(dem_ds, flooded_mask)
    flood_vec_path: Path = PROC_DIR / "flood_polygons_delft.gpkg"
    flood_gdf.to_file(flood_vec_path, driver="GPKG")

    area_km2: float = pipeline.summarize_flood_area(flood_gdf)
    print(f"Total flooded area: {area_km2:.2f} km²")

    summary_path: Path = PROC_DIR / "flood_summary_delft.txt"
    pipeline.write_summary_report(area_km2, summary_path)

if __name__ == "__main__":
    main()
