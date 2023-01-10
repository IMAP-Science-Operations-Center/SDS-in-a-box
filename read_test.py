#!/usr/bin/env python3
from sds_in_a_box.SDSCode.read_index import lambda_handler
from sds_in_a_box.SDSCode.indexer import lambda_handler

import boto3
import json
import requests
import os
from requests_aws4auth import AWS4Auth

region = 'us-east-1' # For example, us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
# access_key = os.environ.get('AWS_ACCESS_KEY_ID')
# secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

# create opensearch client
hosts = [{"host":os.environ["OS_DOMAIN"], "port":int(os.environ["OS_PORT"])}]
auth = (os.environ["OS_ADMIN_USERNAME"], os.environ["OS_ADMIN_PASSWORD_LOCATION"])
# client = Client(hosts=hosts, http_auth=auth, use_ssl=True, verify_certs=True, connnection_class=RequestsHttpConnection)
host = 'https://search-sds-metadata-yuc7xogphdyvj6rtoelcg5reqi.us-east-1.es.amazonaws.com' # The OpenSearch domain endpoint with https:// and without a trailing slash
index = 'metadata'
url = host + '/' + index + '/_search'

# Lambda execution starts here
def read_file(event, context):

    # Put the user query into the query DSL for more accurate search results.
    # Note that certain fields are boosted (^).
    query = {
    'size' : 100,
    'query': {
        'match_all' : {}
    }
    }
    # query = {
    #     "size": 25,
    #     "query": {
    #         "multi_match": {
    #             "query": event['queryStringParameters']['q'],
    #             "fields": ["title^4", "plot^2", "actors", "directors"]
    #         }
    #     }
    # }

    # Elasticsearch 6.x requires an explicit Content-Type header
    headers = { "Content-Type": "application/json" }

    # Make the signed HTTP request
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))

    # Create the response and add some extra content to support CORS
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    # Add the search results to the response
    response['body'] = r.text
    print(response)
    return response

sample_payload = {
    "Records": [
        {
        "s3": {
            "bucket": {
            "name": "IMAP-Data-Bucket"
            },
            "object": {
            "key": "imap_l0_instrument_date_version.fits",
            "size": 1305107
            }
        }
        }
    ]
    }

# print(lambda_handler(sample_payload, None))
read_file(None, None)