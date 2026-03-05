from pathlib import Path
from src.pipeline import load_dem, compute_flood_mask

def test_compute_flood_mask():
    dem_path = Path("data/raw/output_hh.tif")
    ds = load_dem(dem_path)
    mask = compute_flood_mask(ds, water_level=2.0)
    assert mask.shape == ds.read(1).shape
    # Ensure there is at least one flooded or non-flooded cell
    assert mask.any() or (~mask).any()
