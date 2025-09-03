from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from constructs import Construct


class IngestionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"aws-data-lab-data-{self.account}-{self.region}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.lambda_fn = _lambda.Function(
            self,
            "IngestionLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda_src/ingestion"),
            handler="handler.lambda_handler",
            environment={
                "S3_BUCKET": self.data_bucket.bucket_name,
                "S3_PREFIX": "randomuser_api",
            },
        )

        self.data_bucket.grant_write(self.lambda_fn)
