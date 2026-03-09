import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio

from src.config import load_config


def plot_flood(
    dem_path: Path,
    flood_path: Path,
    output_path: Path,
    figsize: tuple[int, int] = (8, 6),
    terrain_cmap: str = "terrain",
    flood_cmap: str = "Blues",
    alpha: float = 0.5,
    dpi: int = 200,
) -> None:
    """Plot DEM with flood mask overlay.

    Args:
        dem_path: Path to DEM raster
        flood_path: Path to flood mask raster
        output_path: Path to save the figure
        figsize: Figure size (width, height)
        terrain_cmap: Colormap for terrain
        flood_cmap: Colormap for flood areas
        alpha: Transparency of flood overlay
        dpi: Output resolution
    """
    with rasterio.open(dem_path) as dem_ds:
        dem = dem_ds.read(1)
    with rasterio.open(flood_path) as f_ds:
        flooded = f_ds.read(1).astype(bool)

    plt.figure(figsize=figsize)
    plt.imshow(dem, cmap=terrain_cmap)
    plt.imshow(np.ma.masked_where(~flooded, flooded), cmap=flood_cmap, alpha=alpha)
    plt.colorbar(label="Elevation (m)")
    plt.title("DEM with simple flood mask")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()


def plot_flood_with_coastbuffer(
    dem_path: Path,
    coast_mask_path: Path,
    flood_path: Path,
    output_path: Path,
    figsize: tuple[int, int] = (10, 8),
    dpi: int = 200,
) -> None:
    """Plot DEM with coastline buffer and flood mask overlays.

    Args:
        dem_path: Path to DEM raster
        coast_mask_path: Path to coastline buffer mask raster
        flood_path: Path to flood mask raster
        output_path: Path to save the figure
        figsize: Figure size (width, height)
        dpi: Output resolution
    """
    with rasterio.open(dem_path) as dem_ds:
        dem = dem_ds.read(1)
    with rasterio.open(coast_mask_path) as coast_ds:
        coast_mask = coast_ds.read(1).astype(bool)
    with rasterio.open(flood_path) as flood_ds:
        flood_mask = flood_ds.read(1).astype(bool)

    plt.figure(figsize=figsize)
    plt.imshow(dem, cmap="terrain")

    # Overlay coast buffer
    plt.imshow(coast_mask, cmap="Greys", alpha=0.3)

    # Overlay flood
    plt.imshow(flood_mask, cmap="Blues", alpha=0.6)

    plt.title("DEM + Coastal Buffer (grey) + Flood (blue)")
    plt.colorbar(label="Elevation (m)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()


def main(config_path: str = "config.yaml") -> None:
    """Generate flood visualizations.

    Args:
        config_path: Path to YAML configuration file
    """
    # Load configuration
    config = load_config(config_path)

    # Create flood visualization
    plot_flood(
        dem_path=config.dem_path,
        flood_path=config.flood_mask_path,
        output_path=config.flood_map_output_path,
        figsize=config.viz_figsize,
        terrain_cmap=config.terrain_colormap,
        flood_cmap=config.flood_colormap,
        alpha=config.flood_alpha,
        dpi=config.viz_dpi,
    )
    print(f"Visualization saved to {config.flood_map_output_path}")

    # Optional: plot with coastline buffer if available
    coastline_buffer_path = (
        config.processed_dir
        / f"coastline_buffer_mask_{config.config_name}_{config.coast_buffer_dist_m}m.tif"
    )
    if coastline_buffer_path.exists():
        plot_flood_with_coastbuffer(
            dem_path=config.dem_path,
            coast_mask_path=coastline_buffer_path,
            flood_path=config.flood_mask_path,
            output_path=config.debug_layers_output_path,
            figsize=(10, 8),
            dpi=config.viz_dpi,
        )
        print(f"Debug visualization saved to {config.debug_layers_output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate flood visualization maps",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to YAML configuration file"
    )
    args = parser.parse_args()
    main(config_path=args.config)
