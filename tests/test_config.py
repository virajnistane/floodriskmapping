"""Tests for configuration management module."""

import tempfile
from pathlib import Path

import pytest

from src.config import Config, load_config


def test_config_file_not_found():
    """Test that FileNotFoundError is raised when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        Config("nonexistent_config.yaml")


def test_config_loads_existing_file():
    """Test that config successfully loads an existing file."""
    config = load_config("configs/config_delft.yaml")
    assert isinstance(config, Config)
    assert config.config_name == "delft"


def test_config_basic_properties():
    """Test basic config properties."""
    config = load_config("configs/config_delft.yaml")
    
    # Test data directories
    assert isinstance(config.raw_dir, Path)
    assert isinstance(config.processed_dir, Path)
    assert isinstance(config.inter_dir, Path)
    
    # Test pipeline parameters
    assert isinstance(config.water_level, float)
    assert config.water_level > 0
    assert isinstance(config.metric_crs, int)
    
    # Test output paths
    assert isinstance(config.flood_mask_path, Path)
    assert isinstance(config.flood_polygons_path, Path)
    assert isinstance(config.summary_report_path, Path)


def test_config_visualization_properties():
    """Test visualization configuration properties."""
    config = load_config("configs/config_delft.yaml")
    
    assert isinstance(config.viz_dpi, int)
    assert config.viz_dpi > 0
    
    assert isinstance(config.viz_figsize, tuple)
    assert len(config.viz_figsize) == 2
    
    assert isinstance(config.flood_colormap, str)
    assert isinstance(config.terrain_colormap, str)
    
    assert isinstance(config.flood_alpha, float)
    assert 0 <= config.flood_alpha <= 1


def test_config_optional_coast_buffer():
    """Test that coast_buffer_dist_m can be None or float."""
    config = load_config("configs/config_delft.yaml")
    
    # Should be either None or a positive float
    if config.coast_buffer_dist_m is not None:
        assert isinstance(config.coast_buffer_dist_m, float)
        assert config.coast_buffer_dist_m > 0


def test_config_paths_exist():
    """Test that configured paths point to existing resources."""
    config = load_config("configs/config_delft.yaml")
    
    # DEM file should exist
    assert config.dem_path.exists(), f"DEM file not found: {config.dem_path}"
    
    # Coastline path should exist
    assert config.coastline_path.exists(), f"Coastline file not found: {config.coastline_path}"


def test_config_creates_output_directories():
    """Test that output directories are created automatically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_content = f"""
info:
  name: "test"

data:
  raw_dir: "data/raw"
  inter_dir: "{tmpdir}/inter"
  processed_dir: "{tmpdir}/processed"
  dem_file: "dem_delft.tif"
  coastline_file: "ne_10m_coastline/ne_10m_coastline.shp"

pipeline:
  water_level: 2.0
  coast_buffer_dist_m: 5000.0
  metric_crs: 3857

output:
  flood_mask_raster: "flood_mask.tif"
  flood_polygons_vector: "flood_polygons.gpkg"
  summary_report: "summary.txt"
  vector_driver: "GPKG"

visualization:
  dpi: 200
  figsize: [8, 6]
  flood_colormap: "Blues"
  terrain_colormap: "terrain"
  flood_alpha: 0.5
  flood_map_output: "flood_map.png"
  debug_layers_output: "debug_layers.png"
"""
        config_path = Path(tmpdir) / "test_config.yaml"
        config_path.write_text(config_content)
        
        config = Config(config_path)
        
        # Accessing these properties should create the directories
        _ = config.inter_dir
        _ = config.processed_dir
        
        assert Path(tmpdir, "inter").exists()
        assert Path(tmpdir, "processed").exists()


def test_config_name_from_info():
    """Test that config name is extracted from info section."""
    config = load_config("configs/config_delft.yaml")
    assert config.config_name == "delft"
    
    config_nice = load_config("configs/config_nice.yaml")
    assert config_nice.config_name == "nice"


def test_config_output_filenames():
    """Test that output filenames match config settings."""
    config = load_config("configs/config_delft.yaml")
    
    # Check that filenames contain the config name
    assert "delft" in str(config.flood_mask_path)
    assert "delft" in str(config.flood_polygons_path)
    assert "delft" in str(config.summary_report_path)


def test_config_visualization_output_paths():
    """Test that visualization output paths are configurable."""
    config = load_config("configs/config_delft.yaml")
    
    assert isinstance(config.flood_map_output_path, Path)
    assert isinstance(config.debug_layers_output_path, Path)
    
    # Should contain the config name
    assert "delft" in str(config.flood_map_output_path)
    assert "delft" in str(config.debug_layers_output_path)


def test_config_vector_driver():
    """Test vector driver configuration."""
    config = load_config("configs/config_delft.yaml")
    
    assert isinstance(config.vector_driver, str)
    assert config.vector_driver in ["GPKG", "GeoJSON", "ESRI Shapefile"]


def test_config_defaults_for_visualization():
    """Test that visualization settings have sensible defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Minimal config without visualization section
        config_content = f"""
info:
  name: "minimal"

data:
  raw_dir: "data/raw"
  inter_dir: "{tmpdir}/inter"
  processed_dir: "{tmpdir}/processed"
  dem_file: "dem_delft.tif"
  coastline_file: "ne_10m_coastline/ne_10m_coastline.shp"

pipeline:
  water_level: 2.0
  coast_buffer_dist_m: null
  metric_crs: 3857

output:
  flood_mask_raster: "flood_mask.tif"
  flood_polygons_vector: "flood_polygons.gpkg"
  summary_report: "summary.txt"
  vector_driver: "GPKG"
"""
        config_path = Path(tmpdir) / "minimal_config.yaml"
        config_path.write_text(config_content)
        
        config = Config(config_path)
        
        # Should have defaults even without visualization section
        assert config.viz_dpi == 200
        assert config.viz_figsize == (8, 6)
        assert config.flood_colormap == "Blues"
        assert config.terrain_colormap == "terrain"
        assert config.flood_alpha == 0.5
