# Docker Deployment Guide

## Overview

This project includes Docker support for containerized deployment with full DVC and AWS S3 integration. The container automatically pulls data from S3, runs the pipeline, and pushes outputs back to S3.

## Quick Start

### Prerequisites

1. **Create `.env` file for AWS credentials**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=eu-north-1
   ```

### Build and Run

```bash
# Build the image
docker compose build floodmap

# Run with default config (pulls from S3, pushes outputs)
docker compose up floodmap

# Run with different config
docker compose run --rm floodmap python -m src.pipeline -c /app/configs/config_nice.yaml

# Run without DVC tracking/pushing
docker compose run --rm floodmap python -m src.pipeline -c /app/configs/config_delft.yaml --no-push-data
```

## Using Docker Compose (Recommended)

Docker Compose simplifies multi-container workflows and automatically handles volume mounts and environment variables.

### Basic Commands

```bash
# Build images
docker compose build

# Run pipeline with default config
docker compose up floodmap

# Run visualization
docker compose up viz

# Run both services
docker compose up

# Build without cache
docker compose build --no-cache

# Run in background
docker compose up -d

# View logs
docker compose logs -f floodmap
```

### Running Different Configurations

```bash
# Method 1: Override command (recommended)
docker compose run --rm floodmap python -m src.pipeline -c /app/configs/config_nice.yaml

# Method 2: Environment variable
docker compose run --rm -e DEFAULT_CONFIG=/app/configs/config_nice.yaml floodmap

# Method 3: Edit docker-compose.yml
# Uncomment and modify the command line:
# command: ["python", "-m", "src.pipeline", "-c", "/app/configs/config_nice.yaml"]
```

### DVC Control

```bash
# Default: automatically pulls and pushes with DVC
docker compose up floodmap

# Skip DVC tracking/pushing
docker compose run --rm floodmap python -m src.pipeline -c /app/configs/config_delft.yaml --no-push-data
```

## Direct Docker Run (Without Compose)

If not using Docker Compose, you need to manually specify all mounts and environment variables:

```bash
# Build image
docker build -t floodriskmap:latest .

# Run with DVC support
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/.dvc:/app/.dvc \
  -v $(pwd)/.git:/app/.git:ro \
  --env-file .env \
  floodriskmap:latest

# Run with specific config
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/.dvc:/app/.dvc \
  -v $(pwd)/.git:/app/.git:ro \
  --env-file .env \
  floodriskmap:latest \
  python -m src.pipeline -c /app/configs/config_nice.yaml

# Run without DVC tracking/pushing
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/configs:/app/configs \
  --env-file .env \
  floodriskmap:latest \
  python -m src.pipeline -c /app/configs/config_delft.yaml --no-push-data
```

## Volume Mounts

The container requires these volume mounts:

| Host Path | Container Path | Purpose | Required |
|-----------|----------------|---------|----------|
| `./data` | `/app/data` | Input/output data files | Yes |
| `./configs` | `/app/configs` | Configuration files | Yes |
| `./.dvc` | `/app/.dvc` | DVC config and cache | For DVC |
| `./.git` | `/app/.git` | Git repository | For DVC |

**Note**: `.dvc` and `.git` mounts are required for DVC to function inside the container.

## Environment Variables

### Using .env File (Recommended)

Create a `.env` file in the project root:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=eu-north-1
DEFAULT_CONFIG=/app/configs/config_delft.yaml
```

Docker Compose automatically loads this file. For `docker run`, use `--env-file .env`.

### Manual Environment Variables

Configure the container with environment variables:

```bash
docker run --rm \
  -e DEFAULT_CONFIG=/app/configs/config_nice.yaml \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_DEFAULT_REGION=eu-north-1 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/.dvc:/app/.dvc \
  -v $(pwd)/.git:/app/.git:ro \
  floodriskmap:latest
```

## Interactive Mode

For debugging or exploration:

```bash
# Start interactive shell with docker compose
docker compose run --rm floodmap /bin/bash

# Or with docker run
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/.dvc:/app/.dvc \
  -v $(pwd)/.git:/app/.git:ro \
  --env-file .env \
  floodriskmap:latest \
  /bin/bash

# Inside container
python -m src.pipeline -c /app/configs/config_delft.yaml
python -m src.viz -c /app/configs/config_delft.yaml
dvc status
dvc pull
```

## Advanced Usage

### Custom Python Commands

```bash
# Run Python interactively
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  floodriskmap:latest \
  python

# Run specific script
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/notebooks:/app/notebooks \
  floodriskmap:latest \
  python /app/notebooks/analysis.py
```

### Jupyter Notebook in Container

Add to Dockerfile:
```dockerfile
RUN uv pip install jupyter
EXPOSE 8888
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--allow-root", "--no-browser"]
```

Run:
```bash
docker run -p 8888:8888 \
  -v $(pwd)/notebooks:/app/notebooks \
  -v $(pwd)/data:/app/data \
  floodriskmap:latest
```

### Multi-Stage Build (Smaller Image)

For production, use multi-stage builds to reduce image size:

```dockerfile
# Builder stage
FROM python:3.12-slim AS builder
# ... install dependencies ...

# Runtime stage
FROM python:3.12-slim
COPY --from=builder /app/.venv /app/.venv
# ... minimal runtime files ...
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t floodriskmap:${{ github.sha }} .
      
      - name: Run tests in container
        run: |
          docker run --rm floodriskmap:${{ github.sha }} \
            pytest tests/
      
      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag floodriskmap:${{ github.sha }} yourusername/floodriskmap:latest
          docker push yourusername/floodriskmap:latest
```

## Cloud Deployment

### AWS ECS

```bash
# Build for ARM64 (Graviton)
docker build --platform linux/arm64 -t floodriskmap:arm64 .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag floodriskmap:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/floodriskmap:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/floodriskmap:latest

# Run on ECS Fargate
# Create task definition with S3 permissions, mount EFS for data
```

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/YOUR_PROJECT/floodriskmap

# Deploy
gcloud run deploy floodriskmap \
  --image gcr.io/YOUR_PROJECT/floodriskmap \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --timeout 3600
```

### Kubernetes

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: floodmap-delft
spec:
  template:
    spec:
      containers:
      - name: floodmap
        image: floodriskmap:latest
        env:
        - name: DEFAULT_CONFIG
          value: /app/configs/config_delft.yaml
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: config-volume
          mountPath: /app/configs
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: flood-data-pvc
      - name: config-volume
        configMap:
          name: flood-configs
      restartPolicy: OnFailure
```

## Troubleshooting

### DVC Issues

**Error**: `ERROR: you are not inside of a DVC repository`

**Solution**: Mount `.dvc` and `.git` directories:
```yaml
# In docker-compose.yml
volumes:
  - ./.dvc:/app/.dvc
  - ./.git:/app/.git:ro
```

**Error**: `s3 is supported, but requires 'dvc-s3' to be installed`

**Solution**: Rebuild image with updated dependencies:
```bash
# Update lockfile first
uv lock --upgrade-package dvc --upgrade-package pathspec

# Rebuild without cache
docker compose build --no-cache floodmap
```

**Error**: `cannot import name '_DIR_MARK' from 'pathspec'`

**Solution**: Update pathspec to ≥0.12.1 and dvc to ≥3.66.1:
```bash
uv lock --upgrade-package pathspec --upgrade-package dvc
docker compose build floodmap
```

### GDAL Issues

**Error**: `ERROR 4: Unable to open EPSG support file`

**Solution**: Ensure GDAL environment variables are set:
```dockerfile
ENV GDAL_DATA=/usr/share/gdal
ENV PROJ_LIB=/usr/share/proj
```

### Permission Errors

**Error**: `Permission denied: '/app/data/processed'`

**Solution**: Ensure mounted volumes have correct permissions:
```bash
# On host
chmod -R 755 data/

# Or run as root (not recommended)
docker run --user root ...
```

### Out of Memory

**Error**: Container killed due to OOM

**Solution**: Increase memory limit:
```bash
docker run --memory=4g --memory-swap=4g ...
```

Or in docker-compose.yml:
```yaml
services:
  floodmap:
    mem_limit: 4g
    memswap_limit: 4g
```

### Slow Builds

**Solution**: Use build cache and .dockerignore:
```bash
# Ensure .dockerignore excludes data/ and .venv/
docker build --cache-from floodriskmap:latest -t floodriskmap:latest .
```

## Best Practices

1. **Use .dockerignore** – Exclude unnecessary files (data/, .venv/, tests/)
2. **Layer caching** – Copy dependency files before source code
3. **Non-root user** – Container runs as unprivileged user (flooduser)
4. **Multi-stage builds** – Separate build and runtime stages for smaller images
5. **Health checks** – Add HEALTHCHECK instruction for production deployments
6. **Security scanning** – Use `docker scan` or Trivy to check for vulnerabilities
7. **Pin versions** – Use specific Python/GDAL versions, not `latest`
8. **Secrets management** – Use `.env` file or Docker secrets, never bake credentials into image
9. **DVC integration** – Mount `.dvc` and `.git` for version control inside containers
10. **Use Docker Compose V2** – Use `docker compose` (space) instead of `docker-compose` (dash)

## Docker Compose V2

This project uses **Docker Compose V2** syntax. Use `docker compose` (with space):

```bash
# ✅ Correct (V2)
docker compose up
docker compose build

# ❌ Old (V1, deprecated)
docker-compose up
docker-compose build
```

If you have the old `docker-compose` command and see errors like `ModuleNotFoundError: No module named 'distutils'`, install Docker Compose V2 as a plugin or use the commands above.

## Image Size Optimization

Current image: ~2.3 GB (with GDAL, DVC, and all dependencies)

**Size breakdown**:
- Python 3.12-slim base: ~150 MB
- GDAL and system libraries: ~400 MB
- Python packages (including DVC, rasterio, geopandas): ~1.7 GB

**Optimization strategies**:
- ✅ Using `python:3.12-slim` instead of full Python image
- ✅ Layer caching for dependencies (uv sync)
- ✅ `.dockerignore` to exclude unnecessary files
- Multi-stage build: Can reduce to ~1.8 GB
- Alpine Linux: ~800 MB (but GDAL compatibility issues)
- Remove dev dependencies: Already done (`--no-dev` flag)

## Reference

- [Dockerfile](../Dockerfile)
- [docker-compose.yml](../docker-compose.yml)
- [.dockerignore](../.dockerignore)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Document Version**: 1.0  
**Last Updated**: March 10, 2026  
**Maintained by**: Flood Risk Mapping Team
