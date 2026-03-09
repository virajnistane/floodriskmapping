"""Configuration management for flood risk mapping pipeline."""
from pathlib import Path
from typing import Any, Optional
import yaml


class Config:
    """Load and manage pipeline configuration from YAML file."""

    def __init__(self, config_path: str | Path = "config.yaml"):
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(self.config_path, "r") as f:
            self._config: dict[str, Any] = yaml.safe_load(f)
    
    @property
    def raw_dir(self) -> Path:
        """Directory containing raw input data."""
        return Path(self._config["data"]["raw_dir"])
    
    @property
    def processed_dir(self) -> Path:
        """Directory for processed output data."""
        proc_dir = Path(self._config["data"]["processed_dir"])
        proc_dir.mkdir(parents=True, exist_ok=True)
        return proc_dir
    
    @property
    def dem_path(self) -> Path:
        """Full path to DEM file."""
        return self.raw_dir / self._config["data"]["dem_file"]
    
    @property
    def coastline_path(self) -> Path:
        """Full path to coastline shapefile."""
        return self.raw_dir / self._config["data"]["coastline_file"]
    
    @property
    def water_level(self) -> float:
        """Water level threshold in meters."""
        return float(self._config["pipeline"]["water_level"])
    
    @property
    def coast_buffer_dist_m(self) -> Optional[float]:
        """Coastline buffer distance in meters (None to disable)."""
        value = self._config["pipeline"]["coast_buffer_dist_m"]
        return float(value) if value is not None else None
    
    @property
    def metric_crs(self) -> int:
        """EPSG code for metric CRS used in area calculations."""
        return int(self._config["pipeline"]["metric_crs"])
    
    @property
    def flood_mask_path(self) -> Path:
        """Output path for flood mask raster."""
        return self.processed_dir / self._config["output"]["flood_mask_raster"]
    
    @property
    def flood_polygons_path(self) -> Path:
        """Output path for flood polygons vector."""
        return self.processed_dir / self._config["output"]["flood_polygons_vector"]
    
    @property
    def summary_report_path(self) -> Path:
        """Output path for summary report."""
        return self.processed_dir / self._config["output"]["summary_report"]
    
    @property
    def vector_driver(self) -> str:
        """Vector file format driver (e.g., 'GPKG', 'GeoJSON')."""
        return str(self._config["output"]["vector_driver"])
    
    @property
    def viz_dpi(self) -> int:
        """Visualization output DPI."""
        return int(self._config.get("visualization", {}).get("dpi", 200))
    
    @property
    def viz_figsize(self) -> tuple[int, int]:
        """Visualization figure size (width, height)."""
        size = self._config.get("visualization", {}).get("figsize", [8, 6])
        return tuple(size)
    
    @property
    def flood_colormap(self) -> str:
        """Colormap for flood visualization."""
        return str(self._config.get("visualization", {}).get("flood_colormap", "Blues"))
    
    @property
    def terrain_colormap(self) -> str:
        """Colormap for terrain visualization."""
        return str(self._config.get("visualization", {}).get("terrain_colormap", "terrain"))
    
    @property
    def flood_alpha(self) -> float:
        """Alpha transparency for flood overlay."""
        return float(self._config.get("visualization", {}).get("flood_alpha", 0.5))


def load_config(config_path: str | Path = "configs/config_delft.yaml") -> Config:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration YAML file
    
    Returns:
        Config object with pipeline parameters
    """
    return Config(config_path)
