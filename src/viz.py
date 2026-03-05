import matplotlib.pyplot as plt
import rasterio
from pathlib import Path
import numpy as np

from src.load_data import RAW_DIR, PROC_DIR, load_dem

def plot_flood(dem_path: Path, flood_path: Path) -> None:
    with rasterio.open(dem_path) as dem_ds:
        dem = dem_ds.read(1)
    with rasterio.open(flood_path) as f_ds:
        flooded = f_ds.read(1).astype(bool)

    plt.figure(figsize=(8, 6))
    plt.imshow(dem, cmap="terrain")
    plt.imshow(
        np.ma.masked_where(~flooded, flooded),
        cmap="Blues",
        alpha=0.5
    )
    plt.colorbar(label="Elevation (m)")
    plt.title("DEM with simple flood mask")
    plt.tight_layout()
    plt.savefig(PROC_DIR / "flood_map.png", dpi=200)

if __name__ == "__main__":
    dem_path = RAW_DIR / "dem_delft.tif"
    flood_path = PROC_DIR / "flood_mask_delft.tif"
    plot_flood(dem_path, flood_path)
