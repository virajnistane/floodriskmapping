"""Tests for data loading module."""

from pathlib import Path

import numpy as np
import pytest
import rasterio

from src.load_data import load_dem


def test_load_dem_success():
    """Test that DEM loads successfully from valid file."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    
    # Check that we got a rasterio dataset
    assert isinstance(ds, rasterio.io.DatasetReader)
    
    # Check basic properties
    assert ds.count >= 1  # At least one band
    assert ds.width > 0
    assert ds.height > 0
    assert ds.crs is not None  # Has a coordinate reference system
    
    # Clean up
    ds.close()


def test_load_dem_reads_data():
    """Test that DEM data can be read and is valid."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    
    # Read the first band
    data = ds.read(1)
    
    # Check data properties
    assert isinstance(data, np.ndarray)
    assert data.shape == (ds.height, ds.width)
    assert data.dtype in [np.float32, np.float64, np.int16, np.int32]
    
    # Check that we have some valid data (not all nodata)
    if ds.nodata is not None:
        valid_data = data[data != ds.nodata]
        assert len(valid_data) > 0, "DEM contains only nodata values"
    
    ds.close()


def test_load_dem_file_not_found():
    """Test that appropriate error is raised for nonexistent file."""
    nonexistent_path = Path("data/raw/nonexistent_dem.tif")
    
    with pytest.raises(rasterio.errors.RasterioIOError):
        load_dem(nonexistent_path)


def test_load_dem_has_transform():
    """Test that loaded DEM has a valid geotransform."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    
    # Check transform exists and has reasonable values
    assert ds.transform is not None
    
    # Transform should have 6 elements (a, b, c, d, e, f)
    # where a and e are pixel sizes, c and f are upper-left coordinates
    transform = ds.transform
    assert transform.a != 0  # Pixel width
    assert transform.e != 0  # Pixel height (usually negative)
    
    ds.close()


def test_load_dem_metadata():
    """Test that DEM metadata is accessible and valid."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    
    # Check metadata dictionary
    meta = ds.meta
    assert isinstance(meta, dict)
    assert 'driver' in meta
    assert 'dtype' in meta
    assert 'width' in meta
    assert 'height' in meta
    assert 'count' in meta
    assert 'crs' in meta
    assert 'transform' in meta
    
    ds.close()


def test_load_dem_bounds():
    """Test that DEM has valid geographic bounds."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    
    # Check bounds
    bounds = ds.bounds
    assert len(bounds) == 4  # left, bottom, right, top
    
    left, bottom, right, top = bounds
    assert left < right  # Western edge is less than eastern edge
    assert bottom < top  # Southern edge is less than northern edge
    
    ds.close()


def test_load_dem_returns_dataset_reader():
    """Test that load_dem returns correct type."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    
    # Verify it's a DatasetReader, not just any rasterio dataset
    from rasterio.io import DatasetReader
    assert isinstance(ds, DatasetReader)
    
    ds.close()


def test_load_dem_elevation_values_reasonable():
    """Test that elevation values are within reasonable range."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    data = ds.read(1)
    
    # Filter out nodata values
    if ds.nodata is not None:
        valid_data = data[data != ds.nodata]
    else:
        valid_data = data
    
    # For Delft (Netherlands), elevations should be reasonable
    # Typically between -10m and +50m for Netherlands
    assert valid_data.min() > -100, "Elevation too low (likely error)"
    assert valid_data.max() < 10000, "Elevation too high (likely error)"
    
    ds.close()


def test_load_dem_with_path_object():
    """Test that load_dem works with Path objects."""
    dem_path = Path("data/raw/dem_delft.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Test DEM file not found: {dem_path}")
    
    # Should work with Path object
    ds = load_dem(dem_path)
    assert ds is not None
    ds.close()


def test_load_dem_nice():
    """Test loading the Nice DEM file."""
    dem_path = Path("data/raw/dem_nice.tif")
    
    if not dem_path.exists():
        pytest.skip(f"Nice DEM file not found: {dem_path}")
    
    ds = load_dem(dem_path)
    
    assert isinstance(ds, rasterio.io.DatasetReader)
    assert ds.crs is not None
    assert ds.width > 0
    assert ds.height > 0
    
    ds.close()
