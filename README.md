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

All pipeline parameters are managed through YAML configuration files in the `configs/` directory. Edit or create config files to customize:

- **Config metadata** (name, description)
- **Input data paths** (DEM file, coastline shapefile)
- **Water level threshold** (meters)
- **Coastline buffer distance** (meters, or null to disable)
- **Output file names** and formats
- **Visualization settings** (DPI, colormaps, figure size, output filenames)

Example configuration:
```yaml
# Config identification
info:
  name: "delft"
  description: "Flood risk mapping for Delft"

# Data directories
data:
  raw_dir: "data/raw"
  inter_dir: "data/inter"        # Intermediate files (e.g., coastline buffers)
  processed_dir: "data/processed"
  dem_file: "dem_delft.tif"
  coastline_file: "ne_10m_coastline/ne_10m_coastline.shp"

# Pipeline parameters
pipeline:
  water_level: 2.0  # meters above reference
  coast_buffer_dist_m: 5000.0  # buffer distance in meters
  metric_crs: 3857  # EPSG code for area calculations

# Output files
output:
  flood_mask_raster: "flood_mask_delft.tif"
  flood_polygons_vector: "flood_polygons_delft.gpkg"
  summary_report: "flood_summary_delft.txt"

# Visualization
visualization:
  flood_map_output: "flood_map_delft.png"
  debug_layers_output: "debug_layers_delft.png"
  dpi: 200
  figsize: [8, 6]
```

### Run the flood mapping pipeline:
```bash
# Run with specific config
python -m src.pipeline -c configs/config_delft.yaml

# Run and track/push outputs to DVC S3 (default behavior)
python -m src.pipeline -c configs/config_delft.yaml

# Skip DVC tracking/pushing
python -m src.pipeline -c configs/config_delft.yaml --no-push-data
```

This will:
- Load the DEM from the path specified in config
- Generate flood mask at the configured water level
- Apply coastline buffer (if enabled) and save to `data/inter/`
- Save results to `data/processed/`:
  - Flood mask raster (`.tif`)
  - Flood polygons vector (`.gpkg`)
  - Summary repor -c configs/config_delft.yaml
```

With a custom configuration file:
```bash
python -m src.viz --config configs/my_config.yaml
```

Generates flood visualization maps using settings from the config file. Output filenames are specified in the config's `visualization` section
```bash
python -m src.viz --config configs/my_config.yaml
```

Generates flood visualization maps using settings from the config file.

### Run tests:
```bash
pytest tests/
```

### CLI Options

Both scripts support command-line arguments:

```bash
# Show help
python -m src.pipeline --help
python -m src.viz --help

# Use custom config
python -m src.pipeline -c configs/config_delft.yaml
python -m src.viz -c configs/config_nice.yaml
```

**Managing Multiple Configurations:**
- Store different configs in the `configs/` directory
- Each config can have unique settings for different regions or scenarios
- Output files are automatically named based on the `info.name` field
- This prevents output conflicts when running multiple configurations

## Cloud Data Storage

Large data files (DEMs, flood outputs) are managed with **DVC (Data Version Control)** and stored on **AWS S3**. This keeps the Git repository lightweight while enabling version control and team collaboration for datasets.

### Quick Start with DVC

```bash
# Pull data from S3 (first time or to sync)
dvc pull

# Run pipeline (automatically tracks and pushes results to S3)
python -m src.pipeline -c configs/config_delft.yaml

# Run without DVC tracking/pushing
python -m src.pipeline -c configs/config_delft.yaml --no-push-data

# Manually track and push new files
dvc add data/processed/new_output.tif
dvc push
git add data/processed/new_output.tif.dvc
git commit -m "Add new output"
```

### Setup (One-Time)

1. **Install DVC with S3 support**:
   ```bash
   uv sync --extra s3
   ```

2. **Configure AWS credentials**:
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=eu-north-1
   ```
   
   Or use AWS CLI:
   ```bash
   aws configure
   ```

3. **Pull data from S3**:
   ```bash
   dvc pull
   ```

**For detailed setup, costs, troubleshooting, and best practices**, see [docs/cloud.md](docs/cloud.md).

## Docker Deployment

Run the pipeline in a container without installing dependencies locally:

```bash
# Build image
docker compose build floodmap

# Run with default config
docker compose up floodmap

# Run with different config
docker compose run --rm floodmap python -m src.pipeline -c /app/configs/config_nice.yaml

# Skip DVC tracking/pushing
docker compose run --rm floodmap python -m src.pipeline -c /app/configs/config_delft.yaml --no-push-data
```

**Prerequisites for DVC/S3 support**:
1. Create `.env` file with AWS credentials (see Cloud Data Storage section)
2. DVC and Git directories are automatically mounted

**For detailed Docker setup, deployment options, and troubleshooting**, see [docs/docker.md](docs/docker.md).

## Project Structure

```
.
├── configs/              # Configuration files for different regions
│   ├── config_delft.yaml
│   └── config_nice.yaml
├── data/
│   ├── raw/              # Input DEM files and coastline shapefiles
│   ├── inter/            # Intermediate files (coastline buffer masks)
│   └── processed/        # Output flood masks, polygons, and visualizations
├── notebooks/            # Jupyter notebooks for exploration
├── src/
│   ├── config.py         # Configuration loader
│   ├── pipeline.py       # Main flood mapping pipeline
│   ├── load_data.py      # Data loading utilities
│   ├── coastline_buffer.py  # Coastline processing
│   └── viz.py            # Visualization scripts
├── tests/                # Unit tests
└── pyproject.toml        # Project dependencies
```

## License

This is a toy project for educational purposes.
