import os
from aws_cdk import (
    # Duration,
    Stack,
    RemovalPolicy,
    # aws_sqs as sqs,
)
from constructs import Construct
import aws_cdk as cdk
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_iam as iam
import aws_cdk.aws_opensearchservice as opensearch
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_secretsmanager as secretsmanager
from aws_cdk.aws_lambda_event_sources import S3EventSource, SnsEventSource

class SdsInABoxStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # This is the S3 bucket where the data will be stored
        data_bucket = s3.Bucket(self, "DATA-BUCKET",
                                #bucket_name="DataBucket",
                                versioned=True,
                                removal_policy=RemovalPolicy.DESTROY,
                                auto_delete_objects=True
                                )

        # Need to make a secret username/password for OpenSearch
        os_secret = secretsmanager.Secret(self, "OpenSearchPassword")

        #Create the opensearch 
        domain = opensearch.Domain(
            self,
            "OpenSearchDomain",
            domain_name=f"sds-metadata",
            # Version 1.2 released 04/22, Version 1.3 released 07/27/22
            version=opensearch.EngineVersion.OPENSEARCH_1_2,
            # Define the Nodes
            # Supported EC2 instance types:
            # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/supported-instance-types.html
            capacity=opensearch.CapacityConfig(
                # Single node for DEV
                data_nodes=1,
                #data_node_instance_type="m5.large.search",
                 data_node_instance_type="t3.small.search"
            ),
            # 10GB standard SSD storage, 10GB is the minimum size
            ebs=opensearch.EbsOptions(
                # As of 07/22/22 GP3 not available in us-west-2 Guidence from docs
                volume_size=10,
                volume_type=ec2.EbsDeviceVolumeType.GP2,
            ),
            # Enable logging
            logging=opensearch.LoggingOptions(
                slow_search_log_enabled=True,
                app_log_enabled=True,
                slow_index_log_enabled=True,
            ),
            # Enable encryption
            node_to_node_encryption=True,
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            # Require https connections
            enforce_https=True,
            # Destroy OS with cdk destroy
            removal_policy=RemovalPolicy.DESTROY
            # fine_grained_access_control=opensearch.AdvancedSecurityOptions(
            #   master_user_name="master-user",
            #   master_user_password=os_secret.secret_value
            # )
        )

        # This is the role that the lambdas will assume
        # We'll narrow things down later
        lambda_role = iam.Role(self, "Indexer Role", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"))
        
        # The purpose of this lambda function is to trigger off of a new file entering the SDC.
        # For now, it just prints the event.  
        indexer_lambda = lambda_.Function(self,
                                          id="IndexerLambda",
                                          #function_name='file-indexer',
                                          code=lambda_.Code.from_asset(os.path.join(os.path.dirname(os.path.realpath(__file__)), "SDSCode")),
                                          handler="indexer.lambda_handler",
                                          role=lambda_role,
                                          runtime=lambda_.Runtime.PYTHON_3_9,
                                          timeout=cdk.Duration.minutes(15),
                                          memory_size=1000,
                                          environment={
                                            "OS_ADMIN_USERNAME": "master-user", 
                                            "OS_ADMIN_PASSWORD_LOCATION": os_secret.secret_name,
                                            "OS_DOMAIN": domain.domain_endpoint,
                                            "OS_PORT": "443",
                                            "OS_INDEX": "metadata"
                                            }
                                          )

        indexer_lambda.add_event_source(S3EventSource(data_bucket,
                                                      events=[s3.EventType.OBJECT_CREATED]
                                                      )
                                        )
        indexer_lambda.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
