from opensearchpy import OpenSearch
import os 
import boto3
from botocore.exceptions import ClientError

host = 'localhost'
port = 9200
auth = ('admin', 'admin') # For testing only. Don't store credentials in code.
ca_certs_path = '/full/path/to/root-ca.pem' # Provide a CA bundle if you use intermediate CAs with your root CA.

# Optional client certificates if you don't want to use HTTP basic authentication.
# client_cert_path = '/full/path/to/client.pem'
# client_key_path = '/full/path/to/client-key.pem'

hosts = [{"host":os.environ["OS_DOMAIN"], "port":int(os.environ["OS_PORT"])}]
auth = (os.environ["OS_ADMIN_USERNAME"], os.environ["OS_ADMIN_PASSWORD_LOCATION"])

secret_name = "OpenSearchPassword9643DC3D-uVH94BjrbF9u"
region_name = "us-west-2"

# Create a Secrets Manager client
session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name
)
try:
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
except ClientError as e:
    # For a list of exceptions thrown, see
    # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    raise e

# Decrypts secret using the associated KMS key.
secret = get_secret_value_response['SecretString']

auth = ("master-user", secret)

print(secret)
# Create the client with SSL/TLS enabled, but hostname verification disabled.
client = OpenSearch(
    hosts = hosts,
    http_auth = auth,
    # client_cert = client_cert_path,
    # client_key = client_key_path,
    use_ssl = True,
    verify_certs = True
)

# Create an index with non-default settings.
index_name = 'metadata'
index_body = {'mission': 'imap', 'level': 'l0', 'instrument': 'instrument', 'date': 'date', 'version': 'version', 'extension': 'fits'}

document_true = {"_index":"test_data","_type":"_doc","_id":"imap_l0_instrument_date_version.fits","_version":1,"_seq_no":0,"_primary_term":1,"found":True,"_source":{"mission": "imap", "level": "l0", "instrument": "instrument", "date": "date", "version": "version", "extension": "fits"}}

response = client.indices.create(index_name, body=index_body)
print('\nCreating index:')
print(response)

# # Add a document to the index.
# document = {
#   'title': 'Moneyball',
#   'director': 'Bennett Miller',
#   'year': '2011'
# }
# id = '1'

# response = client.index(
#     index = index_name,
#     body = document,
#     id = id,
#     refresh = True
# )

# print('\nAdding document:')
# print(response)

# # Search for the document.
# q = 'miller'
# query = {
#   'size': 5,
#   'query': {
#     'multi_match': {
#       'query': q,
#       'fields': ['title^2', 'director']
#     }
#   }
# }

# response = client.search(
#     body = query,
#     index = index_name
# )
# print('\nSearch results:')
# print(response)

# # Delete the document.
# response = client.delete(
#     index = index_name,
#     id = id
# )

# print('\nDeleting document:')
# print(response)

# # Delete the index.
# response = client.indices.delete(
#     index = index_name
# )

# print('\nDeleting index:')
# print(response)