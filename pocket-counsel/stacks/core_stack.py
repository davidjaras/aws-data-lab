from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class CoreStack(Stack):
    
    BEDROCK_MODEL_ID = "openai.gpt-oss-120b-1:0"
    BEDROCK_REGION = "us-east-1"

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        region = Stack.of(self).region

        lambda_role = iam.Role(
            self,
            "CoreLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{region}::foundation-model/{self.BEDROCK_MODEL_ID}"
                ]
            )
        )

        self.core_lambda = _lambda.Function(
            self,
            "CoreLambdaFunction",
            function_name="pocket-counsel-core",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda/core"),
            timeout=Duration.seconds(60),
            memory_size=256,
            role=lambda_role,
            environment={
                "BEDROCK_MODEL_ID": self.BEDROCK_MODEL_ID,
                "BEDROCK_REGION": self.BEDROCK_REGION
            },
            log_retention=logs.RetentionDays.THREE_DAYS
        )

        CfnOutput(
            self,
            "CoreLambdaArn",
            value=self.core_lambda.function_arn,
            description="ARN of the Core Lambda function",
            export_name=f"{construct_id}-CoreLambdaArn"
        )

        CfnOutput(
            self,
            "CoreLambdaName",
            value=self.core_lambda.function_name,
            description="Name of the Core Lambda function"
        )
