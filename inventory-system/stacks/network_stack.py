from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    Tags
)
from constructs import Construct


class NetworkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env_name = config["environment"]
        vpc_config = config["vpc"]

        self.vpc = ec2.Vpc(
            self, "InventoryVPC",
            vpc_name=f"{env_name}-inventory-vpc",
            ip_addresses=ec2.IpAddresses.cidr(vpc_config["cidr"]),
            max_azs=vpc_config["max_azs"],
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ]
        )

        self.lambda_sg = ec2.SecurityGroup(
            self, "LambdaSecurityGroup",
            vpc=self.vpc,
            security_group_name=f"{env_name}-lambda-sg",
            description="Security group for Lambda functions",
            allow_all_outbound=True
        )

        self.rds_sg = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=self.vpc,
            security_group_name=f"{env_name}-rds-sg",
            description="Security group for RDS instances",
            allow_all_outbound=False
        )

        self.rds_sg.add_ingress_rule(
            peer=self.lambda_sg,
            connection=ec2.Port.tcp(5432),
            description="Allow Lambda to access RDS"
        )

        self.vpc_endpoint_sg = ec2.SecurityGroup(
            self, "VPCEndpointSecurityGroup",
            vpc=self.vpc,
            security_group_name=f"{env_name}-vpc-endpoint-sg",
            description="Security group for VPC Endpoints",
            allow_all_outbound=False
        )

        self.vpc_endpoint_sg.add_ingress_rule(
            peer=self.lambda_sg,
            connection=ec2.Port.tcp(443),
            description="Allow Lambda to access VPC Endpoints"
        )

        self.secrets_manager_endpoint = self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            private_dns_enabled=True,
            security_groups=[self.vpc_endpoint_sg],
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        for key, value in config["tags"].items():
            Tags.of(self).add(key, value)
