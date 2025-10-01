import json
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    Tags
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        vpc: ec2.Vpc,
        rds_sg: ec2.SecurityGroup,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env_name = config["environment"]
        db_config = config["database"]

        self.db_secret = secretsmanager.Secret(
            self, "DBSecret",
            secret_name=f"/{env_name}/inventory/db-credentials",
            description=f"Database credentials for {env_name} environment",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({"username": "postgres"}),
                generate_string_key="password",
                exclude_characters="/@\"' \\",
                password_length=32,
                exclude_punctuation=True
            )
        )

        db_subnet_group = rds.SubnetGroup(
            self, "DBSubnetGroup",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            description=f"Subnet group for {env_name} RDS instance",
            subnet_group_name=f"{env_name}-inventory-db-subnet-group"
        )

        self.db_instance = rds.DatabaseInstance(
            self, "InventoryDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.of("16.4", "16")
            ),
            instance_type=ec2.InstanceType(db_config["instance_type"]),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[rds_sg],
            subnet_group=db_subnet_group,
            database_name=db_config["database_name"],
            credentials=rds.Credentials.from_secret(self.db_secret),
            allocated_storage=db_config["allocated_storage"],
            multi_az=db_config["multi_az"],
            backup_retention=Duration.days(db_config["backup_retention_days"]),
            deletion_protection=db_config["deletion_protection"],
            removal_policy=RemovalPolicy.DESTROY if not db_config["deletion_protection"] else RemovalPolicy.RETAIN,
            instance_identifier=f"{env_name}-inventory-db",
            publicly_accessible=False,
            storage_encrypted=True
        )

        CfnOutput(
            self, "DBSecretArn",
            value=self.db_secret.secret_arn,
            description="ARN of the database credentials secret",
            export_name=f"{env_name}-inventory-db-secret-arn"
        )

        CfnOutput(
            self, "DBInstanceEndpoint",
            value=self.db_instance.db_instance_endpoint_address,
            description="RDS instance endpoint",
            export_name=f"{env_name}-inventory-db-endpoint"
        )

        for key, value in config["tags"].items():
            Tags.of(self).add(key, value)
