"""Tests for coastline buffer module."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio

from src.coastline_buffer import (CoastlineBuffer, create_coast_buffer,
                                  rasterize_coast_buffer)
from src.load_data import load_dem


@pytest.fixture
def dem_dataset():
    """Fixture to load DEM dataset for testing."""
    dem_path = Path("data/raw/dem_delft.tif")
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    return load_dem(dem_path)


@pytest.fixture
def coastline_path():
    """Fixture for coastline shapefile path."""
    path = Path("data/raw/ne_10m_coastline/ne_10m_coastline.shp")
    if not path.exists():
        pytest.skip(f"Coastline file not found: {path}")
    return path


def test_coastline_buffer_initialization(dem_dataset, coastline_path):
    """Test that CoastlineBuffer initializes correctly."""
    buffer = CoastlineBuffer(
        dem_path=Path("data/raw/dem_delft.tif"),
        coastline_path=coastline_path,
        buffer_dist_m=5000.0,
    )

    assert buffer.dem_ds is not None
    assert buffer.coast_gdf is not None
    assert isinstance(buffer.coast_gdf, gpd.GeoDataFrame)
    assert buffer.buffer_dist_m == 5000.0


def test_create_coast_buffer_returns_geodataframe(dem_dataset):
    """Test that create_coast_buffer returns a GeoDataFrame."""
    # Create a simple coastline GeoDataFrame
    from shapely.geometry import LineString

    coast_gdf = gpd.GeoDataFrame(
        geometry=[LineString([(0, 0), (1, 0), (1, 1)])], crs="EPSG:4326"
    )

    buffered = create_coast_buffer(
        coast_gdf, buffer_dist_m=1000.0, dem_crs=dem_dataset.crs
    )

    assert isinstance(buffered, gpd.GeoDataFrame)
    assert len(buffered) == len(coast_gdf)
    assert buffered.crs == dem_dataset.crs


def test_create_coast_buffer_increases_area(dem_dataset):
    """Test that buffering increases the geometry area."""
    from shapely.geometry import LineString

    # Create a simple coastline
    coast_gdf = gpd.GeoDataFrame(
        geometry=[LineString([(0, 0), (1, 0)])], crs="EPSG:4326"
    )

    buffered = create_coast_buffer(
        coast_gdf, buffer_dist_m=1000.0, dem_crs=dem_dataset.crs
    )

    # Buffered geometry should have area (lines have 0 area before buffering)
    assert buffered.geometry.area.sum() > 0


def test_rasterize_coast_buffer_returns_boolean_array(dem_dataset):
    """Test that rasterize_coast_buffer returns a boolean array."""
    from shapely.geometry import box

    # Create a simple buffered coastline
    geom = box(
        dem_dataset.bounds.left,
        dem_dataset.bounds.bottom,
        dem_dataset.bounds.left + 100,
        dem_dataset.bounds.bottom + 100,
    )
    buffered_gdf = gpd.GeoDataFrame(geometry=[geom], crs=dem_dataset.crs)

    mask = rasterize_coast_buffer(buffered_gdf, dem_dataset)

    assert isinstance(mask, np.ndarray)
    assert mask.dtype == np.bool_
    assert mask.shape == (dem_dataset.height, dem_dataset.width)


def test_rasterize_coast_buffer_has_true_values(dem_dataset):
    """Test that rasterize produces some True values for geometries."""
    from shapely.geometry import box

    # Create a geometry that covers part of the DEM
    bounds = dem_dataset.bounds
    center_lon = (bounds.left + bounds.right) / 2
    center_lat = (bounds.bottom + bounds.top) / 2
    size = min(bounds.right - bounds.left, bounds.top - bounds.bottom) / 4

    geom = box(
        center_lon - size / 2,
        center_lat - size / 2,
        center_lon + size / 2,
        center_lat + size / 2,
    )
    buffered_gdf = gpd.GeoDataFrame(geometry=[geom], crs=dem_dataset.crs)

    mask = rasterize_coast_buffer(buffered_gdf, dem_dataset)

    # Should have some True values where the geometry is
    assert mask.any(), "Rasterized mask should have some True values"
    assert not mask.all(), "Rasterized mask should not be all True"


def test_coastline_buffer_create_buffer_mask(coastline_path):
    """Test that create_buffer_mask produces valid mask."""
    buffer = CoastlineBuffer(
        dem_path=Path("data/raw/dem_delft.tif"),
        coastline_path=coastline_path,
        buffer_dist_m=5000.0,
    )

    mask = buffer.create_buffer_mask()

    assert isinstance(mask, np.ndarray)
    assert mask.dtype == np.bool_
    assert mask.shape == (buffer.dem_ds.height, buffer.dem_ds.width)

    # Should have some buffered area (True values)
    assert mask.any(), "Buffer mask should have some True values"


def test_coastline_buffer_save_buffer_mask(coastline_path, tmp_path):
    """Test that save_buffer_mask creates a valid GeoTIFF."""
    buffer = CoastlineBuffer(
        dem_path=Path("data/raw/dem_delft.tif"),
        coastline_path=coastline_path,
        buffer_dist_m=5000.0,
    )

    mask = buffer.create_buffer_mask()
    out_path = tmp_path / "test_buffer_mask.tif"

    buffer.save_buffer_mask(mask, out_path)

    # Check that file was created
    assert out_path.exists()

    # Verify it's a valid GeoTIFF
    with rasterio.open(out_path) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == "uint8"
        assert ds.width == buffer.dem_ds.width
        assert ds.height == buffer.dem_ds.height
        assert ds.crs == buffer.dem_ds.crs

        # Read and verify data
        saved_mask = ds.read(1)
        assert saved_mask.shape == mask.shape
        np.testing.assert_array_equal(saved_mask, mask.astype(np.uint8))


def test_coastline_buffer_different_buffer_distances(coastline_path):
    """Test that different buffer distances produce different results."""
    buffer_5km = CoastlineBuffer(
        dem_path=Path("data/raw/dem_delft.tif"),
        coastline_path=coastline_path,
        buffer_dist_m=5000.0,
    )

    buffer_10km = CoastlineBuffer(
        dem_path=Path("data/raw/dem_delft.tif"),
        coastline_path=coastline_path,
        buffer_dist_m=10000.0,
    )

    mask_5km = buffer_5km.create_buffer_mask()
    mask_10km = buffer_10km.create_buffer_mask()

    # 10km buffer should have more True pixels than 5km buffer
    assert (
        mask_10km.sum() >= mask_5km.sum()
    ), "Larger buffer should have at least as many pixels"


def test_create_coast_buffer_with_zero_distance(dem_dataset):
    """Test that zero buffer distance still works."""
    from shapely.geometry import LineString

    coast_gdf = gpd.GeoDataFrame(
        geometry=[LineString([(0, 0), (1, 0)])], crs="EPSG:4326"
    )

    # Zero buffer should still work (though may have negligible area)
    buffered = create_coast_buffer(
        coast_gdf, buffer_dist_m=0.0, dem_crs=dem_dataset.crs
    )

    assert isinstance(buffered, gpd.GeoDataFrame)
    assert buffered.crs == dem_dataset.crs


def test_coastline_buffer_crs_handling(coastline_path):
    """Test that CRS mismatch is handled correctly."""
    buffer = CoastlineBuffer(
        dem_path=Path("data/raw/dem_delft.tif"),
        coastline_path=coastline_path,
        buffer_dist_m=5000.0,
    )

    # After initialization, coastline CRS should match DEM CRS
    assert buffer.coast_gdf.crs == buffer.dem_ds.crs


def test_rasterize_coast_buffer_empty_geodataframe(dem_dataset):
    """Test behavior with empty GeoDataFrame."""
    empty_gdf = gpd.GeoDataFrame(geometry=[], crs=dem_dataset.crs)

    mask = rasterize_coast_buffer(empty_gdf, dem_dataset)

    # With no geometries, mask should be all False
    assert isinstance(mask, np.ndarray)
    assert not mask.any(), "Empty GeoDataFrame should produce all-False mask"


def test_coastline_buffer_with_nice_dem():
    """Test CoastlineBuffer with Nice DEM."""
    coastline_path = Path("data/raw/ne_10m_coastline/ne_10m_coastline.shp")
    dem_path = Path("data/raw/dem_nice.tif")

    if not coastline_path.exists():
        pytest.skip(f"Coastline file not found: {coastline_path}")
    if not dem_path.exists():
        pytest.skip(f"Nice DEM file not found: {dem_path}")

    buffer = CoastlineBuffer(
        dem_path=dem_path,
        coastline_path=coastline_path,
        buffer_dist_m=5000.0,
    )

    mask = buffer.create_buffer_mask()

    assert isinstance(mask, np.ndarray)
    assert mask.dtype == np.bool_
    # Nice is coastal, so there should be some buffered area
    assert mask.any(), "Nice coastal area should have buffered regions"
