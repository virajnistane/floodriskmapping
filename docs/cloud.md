# Cloud Data Storage with AWS S3

## Overview

This project uses **DVC (Data Version Control)** with **AWS S3** for cloud storage of large data files. This approach keeps the Git repository lightweight while enabling version control and sharing of datasets, model outputs, and intermediate results.

## Architecture

```
┌─────────────────────┐
│   Git Repository    │
│  (Code + Metadata)  │
│                     │
│ *.dvc files         │
│ .dvc/config         │
└──────────┬──────────┘
           │
           │ DVC tracks
           │
┌──────────▼──────────┐
│    AWS S3 Bucket    │
│  (Large Data Files) │
│                     │
│ DEMs, Outputs,      │
│ Rasters, Vectors    │
└─────────────────────┘
```

## Benefits

✅ **Version Control for Data**: Track changes to large datasets like Git tracks code  
✅ **Storage Efficiency**: Git repo stays small (<10 MB), S3 stores large files (GBs)  
✅ **Team Collaboration**: Share data without email or file transfer services  
✅ **Reproducibility**: Link specific data versions to code versions  
✅ **Selective Sync**: Download only the data you need  
✅ **Cost-Effective**: Pay only for storage used (~$0.023/GB/month on S3)

## Setup

### 1. Install Dependencies

```bash
uv pip install dvc dvc-s3
# OR if using pyproject.toml extras:
uv sync --extra s3
```

### 2. Configure AWS Credentials

#### Option A: AWS CLI Configuration (Recommended for local development)
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# Enter:
#   AWS Access Key ID: YOUR_ACCESS_KEY
#   AWS Secret Access Key: YOUR_SECRET_KEY
#   Default region: us-east-1  (or your region)
#   Default output format: json
```

#### Option B: .env File (Recommended for Docker)
```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
# .env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=eu-north-1
```

Docker Compose automatically loads this file. DVC will use these environment variables.

**Important**: `.env` is in `.gitignore` to prevent committing credentials.

#### Option C: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

#### Option D: IAM Role (for EC2/Lambda)
If running on AWS infrastructure, attach an IAM role with S3 permissions.

### 3. Configure DVC Remote

```bash
# Add S3 bucket as DVC remote
dvc remote add -d s3remote s3://your-bucket-name/dvc-storage

# Configure region (if needed)
dvc remote modify s3remote region us-east-1

# Make it the default remote
dvc remote default s3remote

# Commit DVC config to Git
git add .dvc/config
git commit -m "Configure S3 remote for DVC"
```

### 4. Set Up S3 Bucket

**AWS Console Steps**:
1. Go to S3 → Create Bucket
2. Name: `vn-floodgis-toy` (must be globally unique)
3. Region: Choose closest to your team
4. Block Public Access: **Enable** (keep data private)
5. Versioning: **Optional** (extra safety)
6. Encryption: **Enable** (recommended)

**Bucket Policy** (optional, for team access):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:user/USERNAME"
      },
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::your-bucket-name/dvc-storage/*"
    }
  ]
}
```

## Usage

### Tracking Files with DVC

```bash
# Track large data files
dvc add data/raw/dem_delft.tif
dvc add data/processed/flood_mask_delft.tif

# This creates .dvc files (metadata, tracked in Git)
# Actual data is stored in .dvc/cache/ locally
```

### Pushing Data to S3

```bash
# Push all tracked files to S3
dvc push

# Push specific file
dvc push data/raw/dem_delft.tif.dvc
```

### Pulling Data from S3

```bash
# Pull all tracked files from S3
dvc pull

# Pull specific file
dvc pull data/raw/dem_delft.tif.dvc

# Force pull (overwrite local changes)
dvc pull --force
```

### Pipeline Integration

The pipeline automatically tracks and pushes outputs to S3 by default:

```bash
# Run pipeline (automatically tracks and pushes results to S3)
python -m src.pipeline -c configs/config_delft.yaml

# Skip DVC tracking/pushing if needed
python -m src.pipeline -c configs/config_delft.yaml --no-push-data

# Manual tracking and push
dvc add data/processed/flood_mask_delft.tif
dvc push
git add data/processed/flood_mask_delft.tif.dvc
git commit -m "Add processed flood mask"
```

## Workflow

### Initial Setup (One-Time)
```bash
# Clone repository
git clone https://github.com/yourusername/floodriskmapping.git
cd floodriskmapping

# Install dependencies
uv sync --extra s3

# Configure AWS credentials (if not already done)
aws configure

# Pull data from S3
dvc pull
```

### Daily Development
```bash
# Pull latest data
dvc pull

# Run pipeline
python -m src.pipeline -c configs/config_delft.yaml

# Track new outputs
dvc add data/processed/new_output.tif

# Push to S3
dvc push

# Commit metadata to Git
git add data/processed/new_output.tif.dvc
git commit -m "Add new flood analysis output"
git push
```

### Team Collaboration
```bash
# Teammate A: Process new data (automatically pushed)
python -m src.pipeline -c configs/config_nice.yaml
git add data/processed/*.dvc
git commit -m "Add Nice flood analysis"
git push

# Teammate B: Get new data
git pull
dvc pull  # Downloads new data from S3
```

## File Organization

### What Goes Where

**Git Repository** (small files, <1 MB):
- Source code (`src/`)
- Configuration files (`configs/*.yaml`)
- Documentation (`docs/`, `README.md`)
- DVC metadata files (`*.dvc`)
- Tests (`tests/`)

**S3 Bucket** (large files, >1 MB):
- Raw DEMs (`data/raw/*.tif`)
- Processed outputs (`data/processed/*.tif`, `*.gpkg`)
- Intermediate results (`data/inter/*.tif`)
- Coastline buffers

**Not Tracked** (temporary/generated):
- Virtual environment (`.venv/`)
- Python cache (`__pycache__/`)
- Jupyter checkpoints (`.ipynb_checkpoints/`)
- Visualization PNGs (`data/processed/flood_maps/*.png`) - tracked in Git

## Cost Estimation

### S3 Storage Costs (us-east-1, as of 2026)

| Data Type | Size | Monthly Cost |
|-----------|------|--------------|
| DEM (high-res) | 500 MB | $0.01 |
| Flood mask | 100 MB | $0.002 |
| Flood polygons | 50 MB | $0.001 |
| **Total per region** | **~650 MB** | **~$0.015/month** |

**For 10 regions**: ~$0.15/month

### Additional Costs
- **Data Transfer OUT** (downloads): $0.09/GB (first 10 GB free per month)
- **API Requests**: Negligible for this use case (~$0.0004 per 1000 requests)

**Typical Monthly Cost**: **< $1** for small team usage

## Security Best Practices

### 1. Never Commit Credentials to Git
```bash
# BAD - Don't do this!
git add .aws/credentials

# GOOD - Use environment variables or AWS CLI config
aws configure
```

### 2. Use IAM Users with Minimal Permissions
Create dedicated IAM user with only S3 access:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

### 3. Enable S3 Bucket Encryption
```bash
# Server-side encryption with S3-managed keys
aws s3api put-bucket-encryption \
  --bucket your-bucket-name \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 4. Use .gitignore
Ensure `.dvc/cache/` and AWS credentials are ignored:
```
# .gitignore
.dvc/cache/
.dvc/tmp/
.aws/
*.pem
```

## Troubleshooting

### DVC Push/Pull Fails

**Problem**: `ERROR: failed to push/pull data from the cloud`

**Solutions**:
1. Check AWS credentials: `aws s3 ls s3://your-bucket-name/`
2. Verify DVC remote: `dvc remote list`
3. Check network connection
4. Ensure IAM permissions are correct

### Slow Uploads/Downloads

**Solutions**:
1. Use `dvc push -j 8` to use 8 parallel threads
2. Enable S3 Transfer Acceleration (costs extra):
   ```bash
   dvc remote modify s3remote use_ssl true
   aws s3api put-bucket-accelerate-configuration \
     --bucket your-bucket-name \
     --accelerate-configuration Status=Enabled
   ```

### Access Denied Errors

**Problem**: `botocore.exceptions.ClientError: An error occurred (403) when calling the PutObject operation: Forbidden`

**Solutions**:
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Check IAM policy includes `s3:PutObject` permission
3. Ensure bucket policy doesn't block your IAM user
4. Verify bucket name is correct

### Cache Disk Full

**Problem**: Local `.dvc/cache/` consuming too much disk space

**Solution**:
```bash
# Remove local cache (data stays in S3)
dvc cache dir -u  # Show cache location
rm -rf .dvc/cache/*

# Pull only what you need
dvc pull data/raw/dem_delft.tif.dvc
```

## Advanced Features

### Named Remotes

Configure multiple remotes for different use cases:
```bash
# Production S3 bucket
dvc remote add production s3://prod-bucket/dvc-storage

# Development S3 bucket  
dvc remote add development s3://dev-bucket/dvc-storage

# Local backup
dvc remote add backup /mnt/external-drive/dvc-cache

# Use specific remote
dvc push -r development
dvc pull -r production
```

### S3 Lifecycle Policies

Automatically archive old data to cheaper storage:
```json
{
  "Rules": [{
    "Id": "Archive old DVC data",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 90,
      "StorageClass": "GLACIER"
    }]
  }]
}
```

### Access Logs

Track who accesses your data:
```bash
aws s3api put-bucket-logging \
  --bucket your-bucket-name \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "your-logs-bucket",
      "TargetPrefix": "dvc-access-logs/"
    }
  }'
```

## Alternatives to S3

DVC supports multiple cloud providers:

| Provider | DVC Remote | Command |
|----------|------------|---------|
| **AWS S3** | `dvc-s3` | `dvc remote add myremote s3://bucket/path` |
| **Google Cloud** | `dvc-gs` | `dvc remote add myremote gs://bucket/path` |
| **Azure Blob** | `dvc-azure` | `dvc remote add myremote azure://container/path` |
| **SSH/SFTP** | `dvc-ssh` | `dvc remote add myremote ssh://server/path` |
| **Local** | built-in | `dvc remote add myremote /mnt/storage` |

**Installation**:
```bash
uv pip install dvc-gs      # Google Cloud Storage
uv pip install dvc-azure   # Azure Blob Storage
uv pip install dvc-ssh     # SSH/SFTP
```

## References

- [DVC Documentation](https://dvc.org/doc)
- [DVC S3 Configuration](https://dvc.org/doc/user-guide/data-management/remote-storage/amazon-s3)
- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)
- [AWS CLI Installation](https://aws.amazon.com/cli/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

**Document Version**: 1.0  
**Last Updated**: March 10, 2026  
**Maintained by**: Flood Risk Mapping Team
