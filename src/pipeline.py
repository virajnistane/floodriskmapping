from pathlib import Path
import numpy as np
import rasterio
from rasterio import features
import geopandas as gpd
from shapely.geometry import shape

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROC_DIR = DATA_DIR / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

def load_dem(path: Path):
    return rasterio.open(path)

def compute_flood_mask(dem_ds, water_level: float):
    dem = dem_ds.read(1)  # first band
    nodata = dem_ds.nodata
    mask = dem != nodata
    flooded = (dem <= water_level) & mask
    return flooded

def save_flood_raster(dem_ds, flooded_mask, out_path: Path):
    meta = dem_ds.meta.copy()
    meta.update(dtype=rasterio.uint8, count=1)
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(flooded_mask.astype(rasterio.uint8), 1)

def flooded_polygons_from_mask(dem_ds, flooded_mask):
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

def summarize_flood_area(flood_gdf):
    flood_gdf = flood_gdf.to_crs(epsg=3857)  # metric CRS
    area_m2 = flood_gdf.area.sum()
    area_km2 = area_m2 / 1e6
    return area_km2

def main():
    dem_path = RAW_DIR / "output_hh.tif"
    dem_ds = load_dem(dem_path)
    water_level = 2.0  # meters above reference

    flooded_mask = compute_flood_mask(dem_ds, water_level)
    flood_raster_path = PROC_DIR / "flood_mask.tif"
    save_flood_raster(dem_ds, flooded_mask, flood_raster_path)

    flood_gdf = flooded_polygons_from_mask(dem_ds, flooded_mask)
    flood_vec_path = PROC_DIR / "flood_polygons.gpkg"
    flood_gdf.to_file(flood_vec_path, driver="GPKG")

    area_km2 = summarize_flood_area(flood_gdf)
    print(f"Total flooded area: {area_km2:.2f} km²")

if __name__ == "__main__":
    main()
