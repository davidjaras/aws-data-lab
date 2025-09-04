import os

import aws_cdk as cdk

from stacks.catalog_stack import CatalogStack
from stacks.ingestion_stack import IngestionStack
from stacks.query_stack import QueryStack

app = cdk.App()

ingestion_stack = IngestionStack(
    app,
    "IngestionStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

catalog_stack = CatalogStack(
    app,
    "CatalogStack",
    data_bucket=ingestion_stack.data_bucket,
    data_prefix=ingestion_stack.data_prefix,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

catalog_stack.add_dependency(ingestion_stack)

query_stack = QueryStack(
    app,
    "QueryStack",
    database=catalog_stack.database,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

query_stack.add_dependency(catalog_stack)


app.synth()
