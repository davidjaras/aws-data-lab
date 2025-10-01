#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk
from stacks import (
    NetworkStack,
    DatabaseStack,
    LambdaLayersStack,
    CRUDStack,
    ApiStack
)


def load_config(env: str) -> dict:
    config_path = f"config/{env}.json"
    with open(config_path, 'r') as f:
        return json.load(f)


app = cdk.App()

env_name = app.node.try_get_context("env") or "dev"
config = load_config(env_name)

aws_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
)

network_stack = NetworkStack(
    app,
    f"{env_name}-NetworkStack",
    config=config,
    env=aws_env,
    description=f"Network infrastructure for inventory system - {env_name}"
)

layers_stack = LambdaLayersStack(
    app,
    f"{env_name}-LambdaLayersStack",
    config=config,
    env=aws_env,
    description=f"Lambda layers for inventory system - {env_name}"
)

database_stack = DatabaseStack(
    app,
    f"{env_name}-DatabaseStack",
    config=config,
    vpc=network_stack.vpc,
    rds_sg=network_stack.rds_sg,
    lambda_sg=network_stack.lambda_sg,
    psycopg2_layer=layers_stack.psycopg2_layer,
    env=aws_env,
    description=f"Database infrastructure for inventory system - {env_name}"
)
database_stack.add_dependency(network_stack)
database_stack.add_dependency(layers_stack)

crud_stack = CRUDStack(
    app,
    f"{env_name}-CRUDStack",
    config=config,
    vpc=network_stack.vpc,
    lambda_sg=network_stack.lambda_sg,
    psycopg2_layer=layers_stack.psycopg2_layer,
    db_secret=database_stack.db_secret,
    db_endpoint=database_stack.db_instance.db_instance_endpoint_address,
    env=aws_env,
    description=f"Lambda functions for CRUD operations - {env_name}"
)
crud_stack.add_dependency(network_stack)
crud_stack.add_dependency(database_stack)
crud_stack.add_dependency(layers_stack)

api_stack = ApiStack(
    app,
    f"{env_name}-ApiStack",
    config=config,
    create_product_function=crud_stack.create_product_function,
    get_product_function=crud_stack.get_product_function,
    update_product_function=crud_stack.update_product_function,
    delete_product_function=crud_stack.delete_product_function,
    env=aws_env,
    description=f"API Gateway for inventory system - {env_name}"
)
api_stack.add_dependency(crud_stack)

app.synth()
