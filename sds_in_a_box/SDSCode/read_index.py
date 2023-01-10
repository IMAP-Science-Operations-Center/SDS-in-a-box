import json
import urllib.parse
import boto3
import logging 
import os 
import sys
from sds_in_a_box.SDSCode.opensearch_utils.document import Document
from sds_in_a_box.SDSCode.opensearch_utils.index import Index
from sds_in_a_box.SDSCode.opensearch_utils.payload import Payload
from sds_in_a_box.SDSCode.opensearch_utils.action import Action
from sds_in_a_box.SDSCode.opensearch_utils.client import Client
from opensearchpy import OpenSearch, RequestsHttpConnection

logger=logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

s3 = boto3.client('s3')

def _create_open_search_client():
    hosts = [{"host":os.environ["OS_DOMAIN"], "port":int(os.environ["OS_PORT"])}]
    auth = (os.environ["OS_ADMIN_USERNAME"], os.environ["OS_ADMIN_PASSWORD_LOCATION"])
    return Client(hosts=hosts, http_auth=auth, use_ssl=True, verify_certs=True, connnection_class=RequestsHttpConnection)

def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))

    # create opensearch client
    hosts = [{"host":os.environ["OS_DOMAIN"], "port":int(os.environ["OS_PORT"])}]
    auth = (os.environ["OS_ADMIN_USERNAME"], os.environ["OS_ADMIN_PASSWORD_LOCATION"])
    client = Client(hosts=hosts, http_auth=auth, use_ssl=True, verify_certs=True, connnection_class=RequestsHttpConnection)

    index_name = os.environ["OS_INDEX"]
    # Create an index with non-default settings.
    index_name = 'python-test-index'
    index_body = {
    'settings': {
        'index': {
        'number_of_shards': 4
        }
    }
    }

    response = client.indices.create(index_name, body=index_body)
    print('\nCreating index:')
    print(response)

    # Add a document to the index.
    document = {
    'title': 'Moneyball',
    'director': 'Bennett Miller',
    'year': '2011'
    }
    id = '1'

    response = client.index(
        index = index_name,
        body = document,
        id = id,
        refresh = True
    )

    print('\nAdding document:')
    print(response)

    # Search for the document.
    q = 'miller'
    query = {
    'size': 5,
    'query': {
        'multi_match': {
        'query': q,
        'fields': ['title^2', 'director']
        }
    }
    }

    response = client.search(
        body = query,
        index = index_name
    )
    print('\nSearch results:')
    print(response)

    # Delete the document.
    response = client.delete(
        index = index_name,
        id = id
    )

    print('\nDeleting document:')
    print(response)

    # Delete the index.
    response = client.indices.delete(
        index = index_name
    )

    print('\nDeleting index:')
    print(response)
    client.close()