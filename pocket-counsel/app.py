#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.core_stack import CoreStack
from stacks.interface_stack import InterfaceStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
)

telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")

core_stack = CoreStack(
    app,
    "CoreStack",
    telegram_bot_token=telegram_bot_token,
    env=env,
    description="Core resources for Pocket Counsel: Lambda and Bedrock permissions"
)

interface_stack = InterfaceStack(
    app,
    "InterfaceStack",
    core_lambda=core_stack.core_lambda,
    env=env,
    description="API Gateway webhook endpoint for Pocket Counsel"
)

interface_stack.add_dependency(core_stack)

cdk.Tags.of(app).add("Project", "PocketCounsel")
cdk.Tags.of(app).add("Environment", "Development")
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
