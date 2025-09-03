import os

import aws_cdk as cdk

from stacks.ingestion_stack import IngestionStack


app = cdk.App()

ingestion_stack = IngestionStack(
    app, 
    "IngestionStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()
