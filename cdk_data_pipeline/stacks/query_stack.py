from aws_cdk import Aws, RemovalPolicy, Stack
from aws_cdk import aws_athena as athena
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct

from config.settings import CONFIG


class QueryStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database: glue.CfnDatabase,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.results_bucket = s3.Bucket(
            self,
            "AthenaResultsBucket",
            bucket_name=f"{CONFIG.buckets.athena_results_prefix}-{Aws.ACCOUNT_ID}-{Aws.REGION}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.athena_execution_role = iam.Role(
            self,
            "AthenaExecutionRole",
            assumed_by=iam.ServicePrincipal("athena.amazonaws.com"),
            description="Role assumed by Athena workgroup to execute queries",
        )

        self.results_bucket.grant_read_write(self.athena_execution_role)

        self.workgroup = athena.CfnWorkGroup(
            self,
            "AthenaWorkGroup",
            name=CONFIG.workgroup.name,
            description=CONFIG.workgroup.description,
            state="ENABLED",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                enforce_work_group_configuration=True,
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.results_bucket.bucket_name}/",
                ),
                execution_role=self.athena_execution_role.role_arn,
            ),
        )
        self.workgroup.node.add_dependency(database)

        self.athena_table_reader_role = iam.Role(
            self,
            "AthenaTableReaderRole",
            assumed_by=iam.AccountPrincipal(Aws.ACCOUNT_ID),
            description="Reader (table-level via Lake Formation)",
        )
        self._attach_min_athena_permissions(self.athena_table_reader_role)

        self.athena_column_reader_role = iam.Role(
            self,
            "AthenaColumnReaderRole",
            assumed_by=iam.AccountPrincipal(Aws.ACCOUNT_ID),
            description="Restricted (column-level via Lake Formation)",
        )
        self._attach_min_athena_permissions(self.athena_column_reader_role)

        for athena_role in [
            self.athena_table_reader_role,
            self.athena_column_reader_role,
        ]:
            athena_role.add_to_policy(
                iam.PolicyStatement(
                    actions=["athena:StartQueryExecution"],
                    resources=["*"],
                    conditions={
                        "StringEquals": {"athena:WorkGroup": CONFIG.workgroup.name}
                    },
                )
            )

    def _attach_min_athena_permissions(self, role: iam.Role) -> None:
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "athena:StartQueryExecution",
                    "athena:GetQueryExecution",
                    "athena:GetQueryResults",
                    "athena:ListQueryExecutions",
                    "athena:ListWorkGroups",
                    "athena:GetWorkGroup",
                    "athena:StopQueryExecution",
                    "glue:GetDatabase",
                    "glue:GetTable",
                    "glue:GetPartitions",
                    "lakeformation:GetDataAccess",
                    "lakeformation:GetResourceLFTags",
                    "lakeformation:ListLFTags",
                ],
                resources=["*"],
            )
        )
        self.results_bucket.grant_read_write(role)
