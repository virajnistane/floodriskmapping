"""Tests for visualization module."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
import rasterio

from src.viz import plot_flood, plot_flood_with_coastbuffer


@pytest.fixture
def tmp_dem_path(tmp_path):
    """Create a simple test DEM file."""
    dem_path = tmp_path / "test_dem.tif"

    # Create simple elevation data
    data = np.arange(100).reshape(10, 10).astype(np.float32)

    # Create a simple GeoTIFF
    from rasterio.transform import from_bounds

    transform = from_bounds(0, 0, 10, 10, 10, 10)

    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    return dem_path


@pytest.fixture
def tmp_flood_mask_path(tmp_path):
    """Create a simple test flood mask file."""
    mask_path = tmp_path / "test_flood_mask.tif"

    # Create simple flood mask (half flooded)
    data = np.zeros((10, 10), dtype=np.uint8)
    data[:5, :] = 1  # Top half is flooded

    from rasterio.transform import from_bounds

    transform = from_bounds(0, 0, 10, 10, 10, 10)

    with rasterio.open(
        mask_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    return mask_path


def test_plot_flood_creates_file(tmp_dem_path, tmp_flood_mask_path, tmp_path):
    """Test that plot_flood creates an output file."""
    output_path = tmp_path / "test_plot.png"

    plot_flood(
        dem_path=tmp_dem_path,
        flood_path=tmp_flood_mask_path,
        output_path=output_path,
    )

    # Check that output file was created
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_flood_with_custom_settings(tmp_dem_path, tmp_flood_mask_path, tmp_path):
    """Test plot_flood with custom visualization settings."""
    output_path = tmp_path / "test_plot_custom.png"

    plot_flood(
        dem_path=tmp_dem_path,
        flood_path=tmp_flood_mask_path,
        output_path=output_path,
        figsize=(10, 8),
        terrain_cmap="viridis",
        flood_cmap="Reds",
        alpha=0.7,
        dpi=150,
    )

    assert output_path.exists()


def test_plot_flood_with_real_data(tmp_path):
    """Test plot_flood with real DEM and flood mask data."""
    dem_path = Path("data/raw/dem_delft.tif")
    flood_path = Path("data/processed/flood_mask_delft.tif")

    if not dem_path.exists():
        pytest.skip(f"DEM file not found: {dem_path}")
    if not flood_path.exists():
        pytest.skip(f"Flood mask file not found: {flood_path}")

    output_path = tmp_path / "test_real_plot.png"

    plot_flood(
        dem_path=dem_path,
        flood_path=flood_path,
        output_path=output_path,
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 10000  # Should be a reasonable size


def test_plot_flood_default_parameters(tmp_dem_path, tmp_flood_mask_path, tmp_path):
    """Test that default parameters work correctly."""
    output_path = tmp_path / "test_defaults.png"

    # Call with only required parameters
    plot_flood(
        dem_path=tmp_dem_path,
        flood_path=tmp_flood_mask_path,
        output_path=output_path,
    )

    assert output_path.exists()


def test_plot_flood_closes_figure(tmp_dem_path, tmp_flood_mask_path, tmp_path):
    """Test that plot_flood properly closes matplotlib figure."""
    output_path = tmp_path / "test_close.png"

    # Record number of open figures before
    n_figs_before = len(plt.get_fignums())

    plot_flood(
        dem_path=tmp_dem_path,
        flood_path=tmp_flood_mask_path,
        output_path=output_path,
    )

    # Should not leave extra figures open
    n_figs_after = len(plt.get_fignums())
    assert n_figs_after == n_figs_before


def test_plot_flood_with_coastbuffer_creates_file(
    tmp_dem_path, tmp_flood_mask_path, tmp_path
):
    """Test that plot_flood_with_coastbuffer creates output file."""
    coast_mask_path = tmp_path / "test_coast_mask.tif"

    # Create simple coast mask
    data = np.zeros((10, 10), dtype=np.uint8)
    data[3:7, :] = 1  # Middle section is coastal buffer

    from rasterio.transform import from_bounds

    transform = from_bounds(0, 0, 10, 10, 10, 10)

    with rasterio.open(
        coast_mask_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    output_path = tmp_path / "test_coast_plot.png"

    plot_flood_with_coastbuffer(
        dem_path=tmp_dem_path,
        coast_mask_path=coast_mask_path,
        flood_path=tmp_flood_mask_path,
        output_path=output_path,
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_flood_with_coastbuffer_custom_settings(
    tmp_dem_path, tmp_flood_mask_path, tmp_path
):
    """Test plot_flood_with_coastbuffer with custom settings."""
    coast_mask_path = tmp_path / "test_coast_mask.tif"

    # Create coast mask
    data = np.ones((10, 10), dtype=np.uint8)

    from rasterio.transform import from_bounds

    transform = from_bounds(0, 0, 10, 10, 10, 10)

    with rasterio.open(
        coast_mask_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    output_path = tmp_path / "test_coast_custom.png"

    plot_flood_with_coastbuffer(
        dem_path=tmp_dem_path,
        coast_mask_path=coast_mask_path,
        flood_path=tmp_flood_mask_path,
        output_path=output_path,
        figsize=(12, 10),
        dpi=150,
    )

    assert output_path.exists()


def test_plot_flood_with_coastbuffer_closes_figure(
    tmp_dem_path, tmp_flood_mask_path, tmp_path
):
    """Test that plot_flood_with_coastbuffer closes figure properly."""
    coast_mask_path = tmp_path / "test_coast_mask.tif"

    # Create coast mask
    data = np.ones((10, 10), dtype=np.uint8)

    from rasterio.transform import from_bounds

    transform = from_bounds(0, 0, 10, 10, 10, 10)

    with rasterio.open(
        coast_mask_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    output_path = tmp_path / "test_coast_close.png"

    n_figs_before = len(plt.get_fignums())

    plot_flood_with_coastbuffer(
        dem_path=tmp_dem_path,
        coast_mask_path=coast_mask_path,
        flood_path=tmp_flood_mask_path,
        output_path=output_path,
    )

    n_figs_after = len(plt.get_fignums())
    assert n_figs_after == n_figs_before


def test_plot_flood_invalid_paths():
    """Test that plot_flood handles invalid paths appropriately."""
    with pytest.raises(rasterio.errors.RasterioIOError):
        plot_flood(
            dem_path=Path("nonexistent_dem.tif"),
            flood_path=Path("nonexistent_flood.tif"),
            output_path=Path("/tmp/output.png"),
        )


def test_plot_flood_with_different_formats(tmp_dem_path, tmp_flood_mask_path, tmp_path):
    """Test that plot_flood works with different image formats."""
    formats = ["png", "jpg", "pdf"]

    for fmt in formats:
        output_path = tmp_path / f"test_plot.{fmt}"

        plot_flood(
            dem_path=tmp_dem_path,
            flood_path=tmp_flood_mask_path,
            output_path=output_path,
        )

        assert output_path.exists()


def test_plot_flood_with_real_data_and_config(tmp_path):
    """Test plot_flood using configuration settings."""
    from src.config import load_config

    try:
        config = load_config("configs/config_delft.yaml")
    except FileNotFoundError:
        pytest.skip("Config file not found")

    if not config.dem_path.exists():
        pytest.skip(f"DEM file not found: {config.dem_path}")
    if not config.flood_mask_path.exists():
        pytest.skip(f"Flood mask file not found: {config.flood_mask_path}")

    output_path = tmp_path / "test_config_plot.png"

    plot_flood(
        dem_path=config.dem_path,
        flood_path=config.flood_mask_path,
        output_path=output_path,
        figsize=config.viz_figsize,
        terrain_cmap=config.terrain_colormap,
        flood_cmap=config.flood_colormap,
        alpha=config.flood_alpha,
        dpi=config.viz_dpi,
    )

    assert output_path.exists()
