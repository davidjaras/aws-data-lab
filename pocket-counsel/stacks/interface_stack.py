import yaml
from pathlib import Path
from typing import Dict, Any
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

        self.config = self._load_config()
        
        api = self._create_api_gateway()
        
        self._create_webhook_integration(api, core_lambda, construct_id)

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "interface_stack_config.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _create_api_gateway(self) -> apigateway.RestApi:
        api_config = self.config["api_gateway"]
        
        return apigateway.RestApi(
            self,
            api_config["id"],
            rest_api_name=api_config["name"],
            description=api_config["description"],
            deploy=api_config["deploy"],
            deploy_options=apigateway.StageOptions(
                stage_name=api_config["stage_name"]
            ),
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[getattr(apigateway.EndpointType, api_config["endpoint_type"])]
            )
        )

    def _create_webhook_integration(
        self,
        api: apigateway.RestApi,
        core_lambda: _lambda.IFunction,
        construct_id: str
    ) -> None:
        resources_config = self.config["resources"]
        
        for resource_config in resources_config:
            resource = api.root.add_resource(resource_config["path"])
            
            lambda_integration = apigateway.LambdaIntegration(
                core_lambda,
                proxy=resource_config["methods"][0]["proxy_integration"]
            )
            
            for method_config in resource_config["methods"]:
                resource.add_method(
                    method_config["http_method"],
                    lambda_integration,
                    authorization_type=getattr(apigateway.AuthorizationType, method_config["authorization_type"])
                )
            
            core_lambda.grant_invoke(
                iam.ServicePrincipal("apigateway.amazonaws.com")
            )
            
            CfnOutput(
                self,
                "WebhookUrl",
                value=f"{api.url}{resource_config['path']}",
                description="Telegram webhook URL - use this to set your bot webhook",
                export_name=f"{construct_id}-WebhookUrl"
            )
