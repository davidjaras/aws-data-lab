from aws_cdk import Stack
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lakeformation as lakeformation
from aws_cdk import aws_s3 as s3
from constructs import Construct


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

        self.data_lake_settings = lakeformation.CfnDataLakeSettings(
            self,
            "DataLakeSettings",
            admins=[
                lakeformation.CfnDataLakeSettings.DataLakePrincipalProperty(
                    data_lake_principal_identifier=f"arn:aws:iam::{self.account}:user/davidjaras"
                ),
                lakeformation.CfnDataLakeSettings.DataLakePrincipalProperty(
                    data_lake_principal_identifier=f"arn:aws:iam::{self.account}:root"
                ),
                lakeformation.CfnDataLakeSettings.DataLakePrincipalProperty(
                    data_lake_principal_identifier=cfn_exec_role_arn
                )
            ],
            create_database_default_permissions=[],
            create_table_default_permissions=[],
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

        self.table_reader_data_location_permissions = lakeformation.CfnPermissions(
            self,
            "TableReaderDataLocationPermissions",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                data_lake_principal_identifier=athena_table_reader_role.role_arn
            ),
            resource=lakeformation.CfnPermissions.ResourceProperty(
                data_location_resource=lakeformation.CfnPermissions.DataLocationResourceProperty(
                    s3_resource=data_bucket.bucket_arn
                )
            ),
            permissions=["DATA_LOCATION_ACCESS"],
        )

        self.column_reader_data_location_permissions = lakeformation.CfnPermissions(
            self,
            "ColumnReaderDataLocationPermissions",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                data_lake_principal_identifier=athena_column_reader_role.role_arn
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
            permissions=["CREATE_TABLE", "DESCRIBE"],
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

        self.table_reader_table_permissions = lakeformation.CfnPermissions(
            self,
            "TableReaderTablePermissions",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(
                data_lake_principal_identifier=athena_table_reader_role.role_arn
            ),
            resource=lakeformation.CfnPermissions.ResourceProperty(
                table_resource=lakeformation.CfnPermissions.TableResourceProperty(
                    catalog_id=self.account,
                    database_name=database.ref,
                    table_wildcard=lakeformation.CfnPermissions.TableWildcardProperty(),
                )
            ),
            permissions=["SELECT"],
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
                    name="randomuser_api",
                    column_names=[
                        "street_number",
                        "street_name",
                        "city",
                        "state",
                        "country",
                        "postcode",
                        "latitude",
                        "longitude",
                    ],
                )
            ),
            permissions=["SELECT"],
        )

        self.s3_resource.node.add_dependency(self.data_lake_settings)
        self.crawler_data_location_permissions.node.add_dependency(self.s3_resource)
        self.table_reader_data_location_permissions.node.add_dependency(
            self.s3_resource
        )
        self.column_reader_data_location_permissions.node.add_dependency(
            self.s3_resource
        )
        self.crawler_database_permissions.node.add_dependency(database)
        self.table_reader_database_permissions.node.add_dependency(database)
        self.table_reader_table_permissions.node.add_dependency(
            self.table_reader_data_location_permissions
        )
        self.column_reader_database_permissions.node.add_dependency(database)
        self.column_reader_permissions.node.add_dependency(
            self.column_reader_data_location_permissions
        )
