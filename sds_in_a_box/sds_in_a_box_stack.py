import os
import string
import random
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
import aws_cdk.aws_cognito as cognito
from aws_cdk.aws_lambda_event_sources import S3EventSource, SnsEventSource

class SdsInABoxStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, SDS_ID=None, initial_user=None,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
########### INIT
        # Determines the initial configuration
        if not SDS_ID:
            SDS_ID="".join( [random.choice(string.ascii_lowercase) for i in range(8)] )
        
        if not initial_user:
            print("Please set an initial user before calling this stack")
            return

########### DATA STORAGE 
        # This is the S3 bucket where the data will be stored
        data_bucket = s3.Bucket(self, "DATA-BUCKET",
                                bucket_name=f"sds-data-{SDS_ID}",
                                versioned=True,
                                removal_policy=RemovalPolicy.DESTROY,
                                auto_delete_objects=True
                                )

########### DATABASE
        # Need to make a secret username/password for OpenSearch
        os_secret = secretsmanager.Secret(self, "OpenSearchPassword")

        # Create the opensearch cluster
        sds_metadata_domain = opensearch.Domain(
            self,
            "SDSMetadataDomain",
            # Version 1.3 released 07/27/22
            version=opensearch.EngineVersion.OPENSEARCH_1_3,
            # Define the Nodes
            # Supported EC2 instance types:
            # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/supported-instance-types.html
            capacity=opensearch.CapacityConfig(
                # Single node for DEV
                data_nodes=1,
                data_node_instance_type="t3.small.search"
            ),
            # 10GB standard SSD storage, 10GB is the minimum size
            ebs=opensearch.EbsOptions(
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
            removal_policy=RemovalPolicy.DESTROY,
            fine_grained_access_control=opensearch.AdvancedSecurityOptions(
              master_user_name="master-user",
              master_user_password=os_secret.secret_value
            )
        )

########### LAMBDA FUNCTIONS

        # This is where we install dependencies for the lambda functions
        # We take advantage of something called "lambda layers"
        os.system("pip install requests -t ./external/python")
        os.system("pip install python-jose -t ./external/python")
        layer = lambda_.LayerVersion(self, f"SDSDependencies-{SDS_ID}",
                                    code=lambda_.Code.from_asset("./external"),
                                    description="A layer that contains all dependencies needed for the lambda functions"
                                )

        # This is the role that the lambdas will all assume
        # TODO: We'll narrow things down later, right now we're just giving admin access
        lambda_role = iam.Role(self, "Indexer Role", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"))
        
        # The purpose of this lambda function is to trigger off of a new file entering the SDC.
        indexer_lambda = lambda_.Function(self,
                                          id="IndexerLambda",
                                          function_name=f'file-indexer-{SDS_ID}',
                                          code=lambda_.Code.from_asset(os.path.join(os.path.dirname(os.path.realpath(__file__)), "SDSCode")),
                                          handler="indexer.lambda_handler",
                                          role=lambda_role,
                                          runtime=lambda_.Runtime.PYTHON_3_9,
                                          timeout=cdk.Duration.minutes(15),
                                          memory_size=1000,
                                          layers=[layer],
                                          environment={"OS_ADMIN_USERNAME": "master-user", "OS_ADMIN_PASSWORD_LOCATION": os_secret.secret_name}
                                          )
        indexer_lambda.add_event_source(S3EventSource(data_bucket,
                                                      events=[s3.EventType.OBJECT_CREATED]
                                                      )
                                        )
        indexer_lambda.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        
        # Adding a lambda that acts as a template for future APIs
        api_lambda = lambda_.Function(self,
                                      id="APILambda",
                                      function_name=f'api-handler-{SDS_ID}',
                                      code=lambda_.Code.from_asset(os.path.join(os.path.dirname(os.path.realpath(__file__)), "SDSCode")),
                                      handler="api.lambda_handler",
                                      role=lambda_role,
                                      runtime=lambda_.Runtime.PYTHON_3_9,
                                      timeout=cdk.Duration.minutes(15),
                                      memory_size=1000,
                                      layers=[layer],
                                      environment={"OS_ADMIN_USERNAME": "master-user", "OS_ADMIN_PASSWORD_LOCATION": os_secret.secret_name,
                                                   "COGNITO_USERPOOL_ID": userpool.user_pool_id, "COGNITO_APP_ID": command_line_client.user_pool_client_id}
        )
        api_lambda.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        api_url = api_lambda.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE,
                                              cors=lambda_.FunctionUrlCorsOptions(allowed_origins=["*"])
        )

        # Adding a lambda that sends out an email with a link where the user can reset their password
        signup_lambda = lambda_.Function(self,
                                         id="SignupLambda",
                                         function_name=f'cognito_signup_message-{SDS_ID}',
                                         code=lambda_.Code.from_asset(os.path.join(os.path.dirname(os.path.realpath(__file__)), "SDSCode")),
                                         handler="cognito_signup_message.lambda_handler",
                                         role=lambda_role,
                                         runtime=lambda_.Runtime.PYTHON_3_9,
                                         timeout=cdk.Duration.minutes(15),
                                         memory_size=1000,
                                         layers=[layer],
                                         environment={"COGNITO_DOMAIN_PREFIX": f"sds-login-{SDS_ID}", "COGNITO_DOMAIN": f"https://sds-login-{SDS_ID}.auth.us-west-2.amazoncognito.com", "SDS_ID": SDS_ID}
        )
        signup_lambda.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

########### COGNITO
        # Create the Cognito UserPool
        userpool = cognito.UserPool(self,
                                    id='TeamUserPool',
                                    account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
                                    auto_verify=cognito.AutoVerifiedAttrs(email=True),
                                    standard_attributes=cognito.
                                    StandardAttributes(email=cognito.StandardAttribute(required=True)),
                                    sign_in_aliases=cognito.SignInAliases(username=False, email=True),
                                    removal_policy=cdk.RemovalPolicy.DESTROY
                                    )

        # Add a client sign in for the userpool
        command_line_client = cognito.UserPoolClient(user_pool=userpool, scope=self, id='sds-command-line',
                                                     user_pool_client_name= f"sdscommandline-{SDS_ID}",
                                                     id_token_validity=cdk.Duration.minutes(60),
                                                     access_token_validity=cdk.Duration.minutes(60),
                                                     refresh_token_validity=cdk.Duration.minutes(60),
                                                     auth_flows=cognito.AuthFlow(admin_user_password=True,
                                                                                 user_password=True,
                                                                                 user_srp=True,
                                                                                 custom=True),
                                                     prevent_user_existence_errors=True)
        
        # Add a random unique domain name where users can sign up / reset passwords
        # Users will be able to reset their passwords at https://sds-login-{SDS_ID}.auth.us-west-2.amazoncognito.com/login?client_id={}&redirect_uri=https://example.com&response_type=code
        userpooldomain = userpool.add_domain(id="TeamLoginCognitoDomain",
                                             cognito_domain=cognito.CognitoDomainOptions(domain_prefix=f"sds-login-{SDS_ID}"))

        # Add a lambda function that will trigger whenever an email is sent to the user (see the lambda section above)
        userpool.add_trigger(cognito.UserPoolOperation.CUSTOM_MESSAGE, signup_lambda)

        # Create an initial user of the API
        initial_user = cognito.CfnUserPoolUser(self, "MyCfnUserPoolUser",
                                               user_pool_id=userpool.user_pool_id,
                                               desired_delivery_mediums=["EMAIL"],
                                               force_alias_creation=False,
                                               user_attributes=[cognito.CfnUserPoolUser.AttributeTypeProperty(
                                                  name="email",
                                                  value="harter@lasp.colorado.edu"
                                               )],
                                               username="harter@lasp.colorado.edu"
                                              )

########### OUTPUTS
        # This is a list of the major outputs of the stack
        cdk.CfnOutput(self, "API_URL", value=api_url.url)
        cdk.CfnOutput(self, "COGNITO_USERPOOL_ID", value=userpool.user_pool_id)
        cdk.CfnOutput(self, "COGNITO_APP_ID", value=command_line_client.user_pool_client_id)
        cdk.CfnOutput(self, "SIGN_IN_WEBPAGE", value=f"https://sds-login-{SDS_ID}.auth.us-west-2.amazoncognito.com/login?client_id={command_line_client.user_pool_client_id}&redirect_uri=https://example.com&response_type=code")