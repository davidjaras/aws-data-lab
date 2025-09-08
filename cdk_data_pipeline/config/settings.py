"""
Centralized configuration settings for the Data Pipeline CDK application.

This module defines all configurable parameters using dataclasses to provide
type safety, autocompletion, and centralized management of deployment settings.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DatabaseConfig:
    """Configuration for AWS Glue Database."""

    name: str
    description: str


@dataclass
class TableConfig:
    """Configuration for Glue Table and Crawler."""

    name: str
    crawler_name: str


@dataclass
class BucketConfig:
    """Configuration for S3 buckets and prefixes."""

    data_prefix: str
    data_bucket_prefix: str
    athena_results_prefix: str


@dataclass
class WorkgroupConfig:
    """Configuration for Athena workgroup."""

    name: str
    description: str


@dataclass
class LambdaConfig:
    """Configuration for Lambda function parameters."""

    timeout_seconds: int
    api_results_count: int
    api_timeout_seconds: int
    max_retry_attempts: int


@dataclass
class LayerConfig:
    """Configuration for Lambda layers."""

    pandas_layer_name: str
    pandas_layer_version: str
    pandas_layer_account: str


@dataclass
class LakeFormationConfig:
    """Configuration for Lake Formation permissions."""

    location_columns: List[str]


@dataclass
class DataPipelineConfig:
    """
    Main configuration container for the entire data pipeline.

    This class aggregates all component configurations and provides
    a factory method for creating default configurations.
    """

    database: DatabaseConfig
    table: TableConfig
    buckets: BucketConfig
    workgroup: WorkgroupConfig
    lambda_config: LambdaConfig
    layers: LayerConfig
    lake_formation: LakeFormationConfig

    @classmethod
    def get_default_config(cls) -> "DataPipelineConfig":
        """
        Create a DataPipelineConfig instance with default values.

        Returns:
            DataPipelineConfig: Configuration with production-ready defaults
        """
        return cls(
            database=DatabaseConfig(
                name="randomuser_database",
                description="Data lake database for RandomUser API data",
            ),
            table=TableConfig(
                name="randomuser_api", crawler_name="randomuser-data-crawler"
            ),
            buckets=BucketConfig(
                data_prefix="randomuser_api",
                data_bucket_prefix="randomuser-api-data",
                athena_results_prefix="athena-results",
            ),
            workgroup=WorkgroupConfig(
                name="randomuser-workgroup",
                description="Workgroup for querying RandomUser data",
            ),
            lambda_config=LambdaConfig(
                timeout_seconds=10,
                api_results_count=100,
                api_timeout_seconds=30,
                max_retry_attempts=3,
            ),
            layers=LayerConfig(
                pandas_layer_name="AWSSDKPandas-Python310",
                pandas_layer_version="25",
                pandas_layer_account="336392948345",
            ),
            lake_formation=LakeFormationConfig(
                location_columns=[
                    "street_number",
                    "street_name",
                    "city",
                    "state",
                    "country",
                    "postcode",
                    "latitude",
                    "longitude",
                ]
            ),
        )


CONFIG = DataPipelineConfig.get_default_config()
