from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    BundlingOptions,
    Tags
)
from constructs import Construct


class LambdaLayersStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env_name = config["environment"]

        self.psycopg2_layer = lambda_.LayerVersion(
            self, "Psycopg2Layer",
            code=lambda_.Code.from_asset(
                "lambda_src/layers/psycopg2",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        " && ".join([
                            "pip install -r requirements.txt -t /asset-output/python",
                            "find /asset-output -type d -name '__pycache__' -exec rm -rf {} + || true",
                            "find /asset-output -type f -name '*.pyc' -delete || true"
                        ])
                    ]
                )
            ),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_12
            ],
            description="PostgreSQL adapter (psycopg2)",
            layer_version_name=f"{env_name}-psycopg2-layer"
        )

        for key, value in config["tags"].items():
            Tags.of(self).add(key, value)
