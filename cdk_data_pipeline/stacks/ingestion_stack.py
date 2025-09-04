from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from constructs import Construct


class IngestionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.data_prefix = "randomuser_api"
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"randomuser-api-data-{self.account}-{self.region}",
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
            timeout=Duration.seconds(10),
            environment={
                "S3_BUCKET": self.data_bucket.bucket_name,
                "S3_PREFIX": self.data_prefix,
            },
        )

        _pandas_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "ExternalPandasLayer",
            "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python310:25",
        )
        self.lambda_fn.add_layers(_pandas_layer)

        self.data_bucket.grant_write(self.lambda_fn)
