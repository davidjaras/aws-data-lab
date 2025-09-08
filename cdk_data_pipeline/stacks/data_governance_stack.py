from aws_cdk import Stack
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lakeformation as lakeformation
from aws_cdk import aws_s3 as s3
from aws_cdk import custom_resources as cr
from constructs import Construct

from config.settings import CONFIG


class DataGovernanceStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        data_bucket: s3.Bucket,
        database: glue.CfnDatabase,
        crawler_role: iam.Role,
        athena_table_reader_role: iam.Role,
        athena_column_reader_role: iam.Role,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cfn_exec_role_arn = (
            f"arn:aws:iam::{self.account}:role/"
            f"cdk-hnb659fds-cfn-exec-role-{self.account}-{self.region}"
        )

        lake_formation_admin = self.node.try_get_context("lakeFormationAdmin")
        if not lake_formation_admin:
            raise ValueError(
                "lakeFormationAdmin context variable is required. "
                "Set it using: cdk deploy -c lakeFormationAdmin='arn:aws:iam::ACCOUNT:user/USERNAME' "
                "or add it to cdk.json context section."
            )

        self.data_lake_settings = lakeformation.CfnDataLakeSettings(
            self,
            "RandomUserDataLakeSettings",
            admins=[
                lakeformation.CfnDataLakeSettings.DataLakePrincipalProperty(
                    data_lake_principal_identifier=lake_formation_admin
                ),
                lakeformation.CfnDataLakeSettings.DataLakePrincipalProperty(
                    data_lake_principal_identifier=cfn_exec_role_arn
                ),
            ],
            create_database_default_permissions=[],
            create_table_default_permissions=[],
        )

        put_settings = cr.AwsCustomResource(
            self,
            "ForceLakeFormationSettings",
            on_create=cr.AwsSdkCall(
                service="LakeFormation",
                action="putDataLakeSettings",
                parameters={
                    "DataLakeSettings": {
                        "DataLakeAdmins": [
                            {"DataLakePrincipalIdentifier": lake_formation_admin},
                            {"DataLakePrincipalIdentifier": cfn_exec_role_arn},
                        ],
                        "CreateDatabaseDefaultPermissions": [],
                        "CreateTableDefaultPermissions": [],
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of("LF-Settings-Once"),
            ),
            on_update=cr.AwsSdkCall(
                service="LakeFormation",
                action="putDataLakeSettings",
                parameters={
                    "DataLakeSettings": {
                        "DataLakeAdmins": [
                            {"DataLakePrincipalIdentifier": lake_formation_admin},
                            {"DataLakePrincipalIdentifier": cfn_exec_role_arn},
                        ],
                        "CreateDatabaseDefaultPermissions": [],
                        "CreateTableDefaultPermissions": [],
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of("LF-Settings-Once"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=[
                            "lakeformation:PutDataLakeSettings",
                            "lakeformation:GetDataLakeSettings",
                        ],
                        resources=["*"],
                    )
                ]
            ),
        )

        self.s3_resource = lakeformation.CfnResource(
            self,
            "DataLakeResource",
            resource_arn=data_bucket.bucket_arn,
            use_service_linked_role=True,
        )

        self.crawler_data_location_permissions = lakeformation.CfnPermissions(
            self,
            "CrawlerDataLocationPermissions",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                data_lake_principal_identifier=crawler_role.role_arn
            ),
            resource=lakeformation.CfnPermissions.ResourceProperty(
                data_location_resource=lakeformation.CfnPermissions.DataLocationResourceProperty(
                    s3_resource=data_bucket.bucket_arn
                )
            ),
            permissions=["DATA_LOCATION_ACCESS"],
        )

        self.crawler_database_permissions = lakeformation.CfnPermissions(
            self,
            "CrawlerDatabasePermissions",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                data_lake_principal_identifier=crawler_role.role_arn
            ),
            resource=lakeformation.CfnPermissions.ResourceProperty(
                database_resource=lakeformation.CfnPermissions.DatabaseResourceProperty(
                    catalog_id=self.account, name=database.ref
                )
            ),
            permissions=["CREATE_TABLE", "ALTER", "DESCRIBE"],
        )

        self.table_reader_database_permissions = lakeformation.CfnPermissions(
            self,
            "TableReaderDatabasePermissions",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                data_lake_principal_identifier=athena_table_reader_role.role_arn
            ),
            resource=lakeformation.CfnPermissions.ResourceProperty(
                database_resource=lakeformation.CfnPermissions.DatabaseResourceProperty(
                    catalog_id=self.account, name=database.ref
                )
            ),
            permissions=["DESCRIBE"],
        )

        self.column_reader_database_permissions = lakeformation.CfnPermissions(
            self,
            "ColumnReaderDatabasePermissions",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                data_lake_principal_identifier=athena_column_reader_role.role_arn
            ),
            resource=lakeformation.CfnPermissions.ResourceProperty(
                database_resource=lakeformation.CfnPermissions.DatabaseResourceProperty(
                    catalog_id=self.account, name=database.ref
                )
            ),
            permissions=["DESCRIBE"],
        )

        post_crawler_permissions = self.node.try_get_context("postCrawlerPermissions")
        if post_crawler_permissions == "true":
            self.table_reader_permissions = lakeformation.CfnPermissions(
                self,
                "TableReaderPermissions",
                data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                    data_lake_principal_identifier=athena_table_reader_role.role_arn
                ),
                resource=lakeformation.CfnPermissions.ResourceProperty(
                    table_resource=lakeformation.CfnPermissions.TableResourceProperty(
                        catalog_id=self.account,
                        database_name=database.ref,
                        name=CONFIG.table.name,
                    )
                ),
                permissions=["SELECT"],
            )

            self.column_reader_permissions = lakeformation.CfnPermissions(
                self,
                "ColumnReaderPermissions",
                data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                    data_lake_principal_identifier=athena_column_reader_role.role_arn
                ),
                resource=lakeformation.CfnPermissions.ResourceProperty(
                    table_with_columns_resource=lakeformation.CfnPermissions.TableWithColumnsResourceProperty(
                        catalog_id=self.account,
                        database_name=database.ref,
                        name=CONFIG.table.name,
                        column_names=CONFIG.lake_formation.location_columns,
                    )
                ),
                permissions=["SELECT"],
            )

        self.s3_resource.node.add_dependency(self.data_lake_settings)
        put_settings.node.add_dependency(self.data_lake_settings)
        self.crawler_data_location_permissions.node.add_dependency(self.s3_resource)
        self.crawler_database_permissions.node.add_dependency(database)
        self.table_reader_database_permissions.node.add_dependency(database)
        self.column_reader_database_permissions.node.add_dependency(database)
