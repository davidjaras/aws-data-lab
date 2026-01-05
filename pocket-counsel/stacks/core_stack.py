import yaml
from pathlib import Path
from typing import Dict, Any
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

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        telegram_bot_token: str = "",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.config = self._load_config()
        
        lambda_role = self._create_lambda_role()
        
        environment = self._build_environment_variables(telegram_bot_token)
        
        self.core_lambda = self._create_lambda_function(lambda_role, environment, construct_id)

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "core_stack_config.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)


    def _create_lambda_role(self) -> iam.Role:
        iam_config = self.config["iam"]
        bedrock_config = self.config["bedrock"]
        region = Stack.of(self).region

        managed_policies = [
            iam.ManagedPolicy.from_aws_managed_policy_name(policy)
            for policy in iam_config["managed_policies"]
        ]

        role = iam.Role(
            self,
            iam_config["role_name"],
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=managed_policies
        )

        bedrock_actions = [f"bedrock:{action}" for action in bedrock_config["permissions"]]
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=bedrock_actions,
                resources=[
                    f"arn:aws:bedrock:{region}::foundation-model/{bedrock_config['model_id']}"
                ]
            )
        )

        return role

    def _build_environment_variables(self, telegram_bot_token: str) -> Dict[str, str]:
        bedrock_config = self.config["bedrock"]
        
        return {
            "BEDROCK_MODEL_ID": bedrock_config["model_id"],
            "BEDROCK_REGION": bedrock_config["region"],
            "TELEGRAM_BOT_TOKEN": telegram_bot_token
        }

    def _create_lambda_function(
        self,
        role: iam.Role,
        environment: Dict[str, str],
        construct_id: str
    ) -> _lambda.Function:
        lambda_config = self.config["lambda"]
        runtime = getattr(_lambda.Runtime, lambda_config["runtime"])

        lambda_function = _lambda.Function(
            self,
            lambda_config["id"],
            function_name=lambda_config["function_name"],
            runtime=runtime,
            handler=lambda_config["handler"],
            code=_lambda.Code.from_asset(
                lambda_config["code_path"],
                bundling={
                    "image": runtime.bundling_image,
                    "command": [
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                }
            ),
            timeout=Duration.seconds(lambda_config["timeout_seconds"]),
            memory_size=lambda_config["memory_size_mb"],
            role=role,
            environment=environment,
            log_retention=getattr(logs.RetentionDays, lambda_config["log_retention_days"])
        )

        CfnOutput(
            self,
            "CoreLambdaArn",
            value=lambda_function.function_arn,
            description="ARN of the Core Lambda function",
            export_name=f"{construct_id}-CoreLambdaArn"
        )

        CfnOutput(
            self,
            "CoreLambdaName",
            value=lambda_function.function_name,
            description="Name of the Core Lambda function"
        )

        return lambda_function
