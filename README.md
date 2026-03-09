# Flood Risk Mapping

A simple flood-exposure toy project using open Digital Elevation Model (DEM) data to identify areas at risk of flooding.

## Goal

Demonstrate a basic flood modeling workflow: load elevation data, apply water-level thresholds, extract flooded regions as polygons, and compute summary statistics.

## Data Sources

- **DEM Provider**: [Copernicus DEM GLO-30](https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model) (30m resolution global elevation data)
- Raw DEM files are stored in `data/raw/`

## Pipeline

The flood mapping pipeline consists of the following steps:

1. **Load DEM** – Read elevation raster data
2. **Thresholding** – Identify cells where elevation ≤ water level
3. **Flood Mask** – Generate binary mask of flooded areas
4. **Polygonization** – Convert raster mask to vector polygons
5. **Summary Stats** – Calculate total flooded area (km²)

## Technology Stack

- **Python 3.12+**
- **rasterio** – Raster data I/O and processing
- **GeoPandas** – Vector geometry operations
- **NumPy** – Array manipulation
- **PyYAML** – Configuration management
- **DVC** (optional) – Data version control
- **pytest** – Testing framework

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd deltares_floodriskmapping

# Install dependencies with uv
uv sync --extra dev

# Activate virtual environment
source .venv/bin/activate
```

## How to Run

### Configuration

All pip-m src.pipeline
```

This will:
- Load the DEM from the path specified in `config.yaml`
- Generate flood mask at the configured water level
- Apply coastline buffer (if enabled)
- Save results to `data/processed/`:
  - Flood mask raster (`.tif`)
  - Flood polygons vector (`.gpkg`)
  - Summary report (`.txt`
```yaml
pipeline:
  water_level: 2.0  # meters above reference
  coast_buffer_dist_m: 5000.0  # buffer distance in meters
  metric_crs: 3857  # EPSG code for area calculations
```

### Run the flood mapping pipeline:
```bash
python src/pipeline.py
```

This will:
- Load the DEM from `data/raw/output_hh.tif`
- Generate flood mask at 2.0m water level
- Save results to `data/processed/`:
  - `flood_mask.tif` (raster)
  - `flood_polygons.gpkg` (vector)
- Print total flooded area in km²

### Run-m src.viz
```

Generates flood visualization maps using settings from `config.yaml`.bash
python src/viz.py
```

### Run tests:
```bash
pytest tests/
```

## Pconfig.yaml           # Pipeline configuration (EDIT THIS!)
├── data/
│   ├── raw/              # Input DEM files
│   └── processed/        # Output flood masks and polygons
├── notebooks/            # Jupyter notebooks for exploration
├── src/
│   ├── config.py         # Configuration loader
│   ├── pipeline.py       # Main flood mapping pipeline
│   ├── load_data.py      # Data loading utilities
│   ├── coastline_buffer.py  # Coastline processing
│   └── viz.py sed/        # Output flood masks and polygons
├── notebooks/            # Jupyter notebooks for exploration
├── src/
│   ├── pipeline.py       # Main flood mapping pipeline
│   └── viz.py           # Visualization scripts
├── tests/                # Unit tests
└── pyproject.toml        # Project dependencies
```

## License

This is a toy project for educational purposes.
