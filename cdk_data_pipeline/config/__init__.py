"""
Configuration module for the Data Pipeline CDK application.

This module provides centralized configuration management using dataclasses
to eliminate hardcoded values and enable environment-specific deployments.
"""

from .settings import CONFIG, DataPipelineConfig

__all__ = ["CONFIG", "DataPipelineConfig"]
