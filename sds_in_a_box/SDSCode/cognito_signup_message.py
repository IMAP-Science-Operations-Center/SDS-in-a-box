import os
import boto3 

def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    domain_desc = client.describe_user_pool_domain(Domain=os.environ["COGNITO_DOMAIN_PREFIX"])
    clients = client.list_user_pool_clients(UserPoolId = domain_desc["DomainDescription"]['UserPoolId'])
    command_line_client = clients['UserPoolClients'][0]['ClientId']
    
    if 'triggerSource' in event:
        if event['triggerSource'] == 'CustomMessage_AdminCreateUser':
            event["response"]["emailSubject"]=f"Science Data System {os.environ['SDS_ID']} sign up"
            event["response"]["smsMessage"]="We don't use this, it requires filling out special forms to get AWS to send SMS."
            event["response"]["emailMessage"]="Your Username is {username} and your password is {####}.  Continue signing up at: " + os.environ["COGNITO_DOMAIN"] + "/login?client_id="+ command_line_client + "&redirect_uri=https://example.com&response_type=code"
            print(event)
    return event