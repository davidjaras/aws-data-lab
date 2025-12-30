#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.core_stack import CoreStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
)

core_stack = CoreStack(
    app,
    "CoreStack",
    env=env,
    description="Core resources for Pocket Counsel: Lambda and Bedrock permissions"
)

cdk.Tags.of(app).add("Project", "PocketCounsel")
cdk.Tags.of(app).add("Environment", "Development")
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
