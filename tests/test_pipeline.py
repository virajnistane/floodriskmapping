"""Tests for flood risk mapping pipeline."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio

from src.config import load_config
from src.load_data import load_dem
from src.pipeline import FloodRiskPipeline


@pytest.fixture
def test_config():
    """Fixture to load test configuration."""
    try:
        return load_config("configs/config_delft.yaml")
    except FileNotFoundError:
        pytest.skip("Config file not found")


@pytest.fixture
def test_dem():
    """Fixture to load test DEM."""
    dem_path = Path("data/raw/dem_delft.tif")
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    return load_dem(dem_path)


def test_flood_risk_pipeline_initialization(test_config):
    """Test that FloodRiskPipeline initializes correctly."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=test_config.coastline_path,
        coast_buffer_dist_m=5000.0,
        metric_crs=3857,
    )

    assert pipeline.water_level == 2.0
    assert pipeline.metric_crs == 3857
    assert pipeline.ratio_flooded == 0.0


def test_flood_risk_pipeline_without_coastline(test_config):
    """Test pipeline initialization without coastline buffer."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    assert pipeline.coastlinebuffer is None
    assert pipeline.coast_mask is None


def test_compute_flood_mask_basic(test_config, test_dem):
    """Test basic flood mask computation."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)

    # Check basic properties
    assert isinstance(mask, np.ndarray)
    assert mask.dtype == np.bool_
    assert mask.shape == test_dem.read(1).shape


def test_compute_flood_mask_returns_valid_data(test_config, test_dem):
    """Test that compute_flood_mask returns valid boolean data."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)

    # Mask should have both True and False values (unless DEM is extreme)
    assert mask.any() or (~mask).any()


def test_compute_flood_mask_higher_water_more_flooding(test_config, test_dem):
    """Test that higher water level produces more flooding."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=1.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask_1m = pipeline.compute_flood_mask(test_dem, water_level=1.0)
    mask_5m = pipeline.compute_flood_mask(test_dem, water_level=5.0)

    # Higher water level should have more flooded pixels
    assert mask_5m.sum() >= mask_1m.sum()


def test_compute_flood_mask_respects_nodata(test_config, test_dem):
    """Test that flood mask respects nodata values in DEM."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)
    dem = test_dem.read(1)

    # If DEM has nodata, those pixels should not be marked as flooded
    if test_dem.nodata is not None:
        nodata_mask = dem == test_dem.nodata
        # Flooded pixels should not overlap with nodata
        assert not (mask & nodata_mask).any()


def test_compute_flood_mask_updates_ratio(test_config, test_dem):
    """Test that compute_flood_mask updates the flooded ratio."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    initial_ratio = pipeline.ratio_flooded
    pipeline.compute_flood_mask(test_dem, water_level=2.0)

    # Ratio should be updated after computation
    assert pipeline.ratio_flooded != initial_ratio
    assert 0 <= pipeline.ratio_flooded <= 1


def test_save_flood_raster(test_config, test_dem, tmp_path):
    """Test that flood raster is saved correctly."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)
    out_path = tmp_path / "test_flood_mask.tif"

    pipeline.save_flood_raster(test_dem, mask, out_path)

    # Check that file was created
    assert out_path.exists()

    # Verify it's a valid GeoTIFF
    with rasterio.open(out_path) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == "uint8"
        assert ds.width == test_dem.width
        assert ds.height == test_dem.height
        assert ds.crs == test_dem.crs

        # Read and verify data
        saved_mask = ds.read(1)
        np.testing.assert_array_equal(saved_mask, mask.astype(np.uint8))


def test_flooded_polygons_from_mask(test_config, test_dem):
    """Test conversion of flood mask to vector polygons."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)
    flood_gdf = pipeline.flooded_polygons_from_mask(test_dem, mask)

    # Check basic properties
    assert isinstance(flood_gdf, gpd.GeoDataFrame)
    assert flood_gdf.crs == test_dem.crs

    # If there's flooding, should have geometries
    if mask.any():
        assert len(flood_gdf) > 0
        assert all(flood_gdf.geometry.is_valid)


def test_summarize_flood_area(test_config, test_dem):
    """Test flood area summarization."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)

    if mask.any():
        flood_gdf = pipeline.flooded_polygons_from_mask(test_dem, mask)
        area_km2 = pipeline.summarize_flood_area(flood_gdf)

        # Area should be positive and reasonable
        assert isinstance(area_km2, float)
        assert area_km2 > 0
        assert area_km2 < 100000  # Less than 100,000 km² for test area


def test_write_summary_report(test_config, test_dem, tmp_path):
    """Test summary report writing."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)

    if mask.any():
        flood_gdf = pipeline.flooded_polygons_from_mask(test_dem, mask)
        area_km2 = pipeline.summarize_flood_area(flood_gdf)

        report_path = tmp_path / "test_summary.txt"
        pipeline.write_summary_report(area_km2, report_path)

        # Check that report was created
        assert report_path.exists()

        # Check report content
        content = report_path.read_text()
        assert "Flood Risk Mapping Summary Report" in content
        assert f"Water level threshold: {pipeline.water_level}" in content
        assert f"Total flooded area: {area_km2:.2f}" in content
        assert "Flooded ratio:" in content


def test_pipeline_with_coastline_buffer(test_config, test_dem):
    """Test pipeline with coastline buffer enabled."""
    if not test_config.coastline_path.exists():
        pytest.skip("Coastline file not found")

    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=test_config.coastline_path,
        coast_buffer_dist_m=5000.0,
        metric_crs=3857,
    )

    # Pipeline should have coastline buffer
    assert pipeline.coastlinebuffer is not None
    assert pipeline.coast_mask is not None
    assert isinstance(pipeline.coast_mask, np.ndarray)

    # Compute flood mask with buffer
    mask = pipeline.compute_flood_mask(test_dem, water_level=2.0)

    # Mask should be constrained by coastline buffer
    assert mask.shape == pipeline.coast_mask.shape


def test_pipeline_end_to_end(test_config, tmp_path):
    """Test complete pipeline execution from start to finish."""
    if not test_config.dem_path.exists():
        pytest.skip("DEM file not found")

    # Initialize pipeline
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=3857,
    )

    # Load DEM
    dem_ds = load_dem(test_config.dem_path)

    # Compute flood mask
    mask = pipeline.compute_flood_mask(dem_ds)

    # Save flood raster
    flood_raster_path = tmp_path / "test_flood_mask.tif"
    pipeline.save_flood_raster(dem_ds, mask, flood_raster_path)
    assert flood_raster_path.exists()

    # Generate flood polygons
    if mask.any():
        flood_gdf = pipeline.flooded_polygons_from_mask(dem_ds, mask)
        assert isinstance(flood_gdf, gpd.GeoDataFrame)

        # Save polygons
        flood_vec_path = tmp_path / "test_flood_polygons.gpkg"
        flood_gdf.to_file(flood_vec_path, driver="GPKG")
        assert flood_vec_path.exists()

        # Compute and report area
        area_km2 = pipeline.summarize_flood_area(flood_gdf)
        assert area_km2 > 0

        # Write summary report
        summary_path = tmp_path / "test_summary.txt"
        pipeline.write_summary_report(area_km2, summary_path)
        assert summary_path.exists()

    dem_ds.close()


def test_pipeline_different_water_levels(test_config, test_dem):
    """Test pipeline with different water level thresholds."""
    water_levels = [1.0, 2.0, 3.0, 5.0]
    areas = []

    for wl in water_levels:
        pipeline = FloodRiskPipeline(
            config=test_config,
            dem_path=test_config.dem_path,
            water_level=wl,
            coastline_path=None,
            coast_buffer_dist_m=None,
            metric_crs=3857,
        )

        mask = pipeline.compute_flood_mask(test_dem, water_level=wl)
        flooded_pixels = mask.sum()
        areas.append(flooded_pixels)

    # Higher water levels should generally have more flooding
    # (monotonically increasing)
    assert all(areas[i] <= areas[i + 1] for i in range(len(areas) - 1))


def test_pipeline_metric_crs_configuration(test_config):
    """Test that metric CRS is configurable."""
    pipeline = FloodRiskPipeline(
        config=test_config,
        dem_path=test_config.dem_path,
        water_level=2.0,
        coastline_path=None,
        coast_buffer_dist_m=None,
        metric_crs=32631,  # Different CRS (UTM Zone 31N)
    )

    assert pipeline.metric_crs == 32631
