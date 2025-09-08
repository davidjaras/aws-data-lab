
# AWS Data Pipeline CDK Project

A complete serverless data pipeline built with AWS CDK and Python that extracts data from the RandomUser API, stores it in S3 as Parquet files, catalogs it with AWS Glue, and enables secure querying through Amazon Athena with Lake Formation permissions.

## Architecture Overview

This project implements a modern data lake architecture with the following components:
- **Data Ingestion**: Lambda function extracts data from public APIs and stores in S3
- **Data Cataloging**: AWS Glue Crawler discovers schema and creates table definitions
- **Data Querying**: Amazon Athena provides SQL query interface
- **Data Governance**: Lake Formation manages fine-grained access control

## Project Structure
```
cdk_data_pipeline/
├── app.py                           # CDK application entry point
├── config/                          # Centralized configuration
│   ├── __init__.py                 # Configuration module exports
│   └── settings.py                 # All configurable parameters
├── stacks/                          # Modular CDK stack definitions
│   ├── ingestion_stack.py          # S3 bucket + Lambda for data extraction
│   ├── catalog_stack.py            # Glue database + crawler
│   ├── query_stack.py              # Athena workgroup + IAM roles
│   └── data_governance_stack.py    # Lake Formation permissions
├── lambda_src/                      # Lambda function source code
│   └── ingestion/
│       └── handler.py              # Data extraction and processing logic
├── custom_constructs/               # Reusable CDK constructs
├── tests/                          # Unit and integration tests
└── cdk.json                        # CDK configuration and context
```


## Prerequisites

- AWS CLI configured with appropriate permissions
- AWS CDK v2 installed
- Python 3.10+ with pip
- Node.js (for CDK)

## Setup Instructions

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development/testing
```

### 2. Configuration (Required)
**Important**: You must specify a Lake Formation administrator before deployment:

#### Option A: Command Line Parameter (Recommended)
```bash
# Deploy with specific user
cdk deploy -c lakeFormationAdmin="arn:aws:iam::ACCOUNT-ID:user/USERNAME"

# Deploy with administrative role
cdk deploy -c lakeFormationAdmin="arn:aws:iam::ACCOUNT-ID:role/AdminRole"
```

#### Option B: Add to cdk.json (Permanent)
```json
{
  "context": {
    "lakeFormationAdmin": "arn:aws:iam::123456789012:user/your-username"
  }
}
```

## Deployment Guide

**Important**: Deploy in the correct order to respect stack dependencies.

### Phase 1: Infrastructure (Base Resources)
Deploy all stacks without table-level permissions:
```bash
# Deploy core infrastructure (replace ACCOUNT-ID and USERNAME)
cdk deploy IngestionStack CatalogStack QueryStack DataGovernanceStack \
  -c postCrawlerPermissions=false \
  -c lakeFormationAdmin="arn:aws:iam::ACCOUNT-ID:user/USERNAME"

# Verify deployment
aws glue get-database --name randomuser_database
aws glue get-crawler --name randomuser-data-crawler
```

### Phase 2: Data Generation & Cataloging
Generate sample data and create Glue table:
```bash
# Execute Lambda to generate sample data
aws lambda invoke --function-name IngestionStack-IngestionLambda* response.json

# Run crawler to create table
aws glue start-crawler --name randomuser-data-crawler

# Wait for crawler completion (check status)
aws glue get-crawler --name randomuser-data-crawler --query 'Crawler.State'

# Verify table creation
aws glue get-table --database-name randomuser_database --name randomuser_api
```

### Phase 3: Data Governance (Table Permissions)
Deploy table-level permissions after table exists:
```bash
# Deploy table permissions (replace ACCOUNT-ID and USERNAME)
cdk deploy DataGovernanceStack \
  -c postCrawlerPermissions=true \
  -c lakeFormationAdmin="arn:aws:iam::ACCOUNT-ID:user/USERNAME"

# Verify Lake Formation setup
aws lakeformation get-data-lake-settings
aws lakeformation list-permissions
```

## Testing & Validation

### Test Data Pipeline
```bash
# Generate more data
aws lambda invoke --function-name IngestionStack-IngestionLambda* response.json

# Run crawler to update schema
aws glue start-crawler --name randomuser-data-crawler

# Query data in Athena
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM randomuser_database.randomuser_api" \
  --work-group randomuser-workgroup
```

### Test Lake Formation Permissions
```bash
# Test table reader role (full access)
aws sts assume-role --role-arn "arn:aws:iam::ACCOUNT:role/QueryStack-AthenaTableReaderRole*" --role-session-name test

# Test column reader role (restricted access)
aws sts assume-role --role-arn "arn:aws:iam::ACCOUNT:role/QueryStack-AthenaColumnReaderRole*" --role-session-name test
```

## Development Commands

### CDK Operations
```bash
# List all stacks
cdk list

# Synthesize CloudFormation templates
cdk synth [StackName]

# Show differences from deployed version
cdk diff [StackName]

# Deploy specific stack
cdk deploy [StackName]

# Watch for changes (auto-synthesize)
cdk watch [StackName]
```

### Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest tests/ --cov=stacks --cov-report=html
```

## Configuration Management

The project uses a centralized configuration system in `config/settings.py`:

- **Parameterized**: All hardcoded values eliminated
- **Easily Testable**: Mock configurations for testing
