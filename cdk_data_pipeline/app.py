import os

import aws_cdk as cdk

from stacks.catalog_stack import CatalogStack
from stacks.data_governance_stack import DataGovernanceStack
from stacks.ingestion_stack import IngestionStack
from stacks.query_stack import QueryStack

DEFAULT_ENV = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
)

app = cdk.App()

ingestion_stack = IngestionStack(
    app,
    "IngestionStack",
    env=DEFAULT_ENV,
)

catalog_stack = CatalogStack(
    app,
    "CatalogStack",
    data_bucket=ingestion_stack.data_bucket,
    data_prefix=ingestion_stack.data_prefix,
    env=DEFAULT_ENV,
)

query_stack = QueryStack(
    app,
    "QueryStack",
    database=catalog_stack.database,
    env=DEFAULT_ENV,
)

data_governance_stack = DataGovernanceStack(
    app,
    "DataGovernanceStack",
    data_bucket=ingestion_stack.data_bucket,
    database=catalog_stack.database,
    crawler_role=catalog_stack.crawler_role,
    athena_table_reader_role=query_stack.athena_table_reader_role,
    athena_column_reader_role=query_stack.athena_column_reader_role,
    env=DEFAULT_ENV,
)

catalog_stack.add_dependency(ingestion_stack)
query_stack.add_dependency(catalog_stack)
data_governance_stack.add_dependency(query_stack)

app.synth()
