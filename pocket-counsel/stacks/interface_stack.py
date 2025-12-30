from aws_cdk import (
    Stack,
    CfnOutput,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct


class InterfaceStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        core_lambda: _lambda.IFunction,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigateway.RestApi(
            self,
            "PocketCounselApi",
            rest_api_name="pocket-counsel-api",
            description="Telegram webhook endpoint for Pocket Counsel",
            deploy=True,
            deploy_options=apigateway.StageOptions(
                stage_name="dev"
            ),
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[apigateway.EndpointType.REGIONAL]
            )
        )

        webhook_resource = api.root.add_resource("webhook")

        lambda_integration = apigateway.LambdaIntegration(
            core_lambda,
            proxy=True
        )

        webhook_resource.add_method(
            "POST",
            lambda_integration,
            authorization_type=apigateway.AuthorizationType.NONE
        )

        core_lambda.grant_invoke(
            iam.ServicePrincipal("apigateway.amazonaws.com")
        )

        CfnOutput(
            self,
            "WebhookUrl",
            value=f"{api.url}webhook",
            description="Telegram webhook URL - use this to set your bot webhook",
            export_name=f"{construct_id}-WebhookUrl"
        )
