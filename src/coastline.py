from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, box

from src.load_data import PROC_DIR, RAW_DIR, load_dem

class CoastlineProcessor:
    def __init__(self, dem_path: Path):
        self.dem_path = dem_path

    def load_coastline(self) -> gpd.GeoDataFrame:
        coast_shp = RAW_DIR / "ne_10m_coastline.shp"
        coast = gpd.read_file(coast_shp)
        print(coast.crs)
        return coast

    def clip_to_dem(self, coast: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        dem = load_dem(self.dem_path)
        dem_bounds = dem.bounds  # (left, bottom, right, top)
        minx, miny, maxx, maxy = dem_bounds
        aoi = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs=coast.crs)
        coast_clipped = gpd.overlay(coast, aoi, how="intersection")
        return coast_clipped

    def match_dem_crs(self, coast_clipped: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        dem = load_dem(self.dem_path)
        dem_crs = dem.crs  
        coast_matched = coast_clipped.to_crs(dem_crs)
        return coast_matched
    
    def save_coastline(self, coast_clipped: gpd.GeoDataFrame, out_path: Path) -> None:
        coast_clipped.to_file(out_path, driver="GPKG")

if __name__ == "__main__":
    dem_path = RAW_DIR / "dem_delft.tif"
    processor = CoastlineProcessor(dem_path)
    coast = processor.load_coastline()
    coast_clipped = processor.clip_to_dem(coast)
    coast_matched = processor.match_dem_crs(coast_clipped)
    out_path = PROC_DIR / "coastline_matched_delft.gpkg"
    processor.save_coastline(coast_matched, out_path)
