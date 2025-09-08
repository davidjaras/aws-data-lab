from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from constructs import Construct

from config.settings import CONFIG


class IngestionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.data_prefix = CONFIG.buckets.data_prefix
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"{CONFIG.buckets.data_bucket_prefix}-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.lambda_fn = _lambda.Function(
            self,
            "IngestionLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.Code.from_asset("lambda_src/ingestion"),
            handler="handler.lambda_handler",
            timeout=Duration.seconds(CONFIG.lambda_config.timeout_seconds),
            environment={
                "S3_BUCKET": self.data_bucket.bucket_name,
                "S3_PREFIX": self.data_prefix,
                "API_RESULTS_COUNT": str(CONFIG.lambda_config.api_results_count),
                "API_TIMEOUT": str(CONFIG.lambda_config.api_timeout_seconds),
                "MAX_RETRIES": str(CONFIG.lambda_config.max_retry_attempts),
            },
        )

        _pandas_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "ExternalPandasLayer",
            f"arn:aws:lambda:{self.region}:{CONFIG.layers.pandas_layer_account}:layer:{CONFIG.layers.pandas_layer_name}:{CONFIG.layers.pandas_layer_version}",
        )
        self.lambda_fn.add_layers(_pandas_layer)

        self.data_bucket.grant_write(self.lambda_fn)
