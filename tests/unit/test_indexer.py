import unittest
import json
import os
from sds_in_a_box.SDSCode import indexer
from sds_in_a_box.SDSCode.opensearch_utils.action import Action
from sds_in_a_box.SDSCode.opensearch_utils.index import Index
from sds_in_a_box.SDSCode.opensearch_utils.document import Document
from sds_in_a_box.SDSCode.opensearch_utils.payload import Payload
from sds_in_a_box.SDSCode.opensearch_utils.client import Client
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3
from botocore.exceptions import ClientError

class TestIndexer(unittest.TestCase):

    def setUp(self):
        #Opensearch client Params
        os.environ["OS_DOMAIN"] = 'search-sds-metadata-yuc7xogphdyvj6rtoelcg5reqi.us-east-1.es.amazonaws.com'
        os.environ["OS_PORT"] = '443'
        os.environ["OS_INDEX"] = "test_data"

        hosts = [{"host":os.environ["OS_DOMAIN"], "port":os.environ["OS_PORT"]}]
        
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
        self.client = Client(hosts=hosts, http_auth=auth, use_ssl=True, verify_certs=True, connnection_class=RequestsHttpConnection)

        os.environ["OS_ADMIN_USERNAME"] = "master-user"
        os.environ["OS_ADMIN_PASSWORD_LOCATION"] = secret

        # This is a pretend new file payload, like we just received "imap_l0_instrument_date_version.fits" from the bucket "IMAP-Data-Bucket"
        self.sample_payload = {
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

        self.body = {'mission': 'imap', 'level': 'l0', 'instrument': 'instrument', 'date': 'date', 'version': 'version', 'extension': 'fits'}
        self.index = Index(os.environ["OS_INDEX"])
        self.action = Action.CREATE
        identifier = self.sample_payload["Records"][0]["s3"]["object"]["key"]
        self.document = Document(self.index, identifier, self.action, self.body)
        try:
            self.client.delete_index(self.index)
        except:
            pass
        
        self.client.create_index(self.index)

        self.payload = Payload()

    def test_indexer(self):
        ## Arrange
        exists_true = True
        document_true = {"_index":"test_data","_type":"_doc","_id":"imap_l0_instrument_date_version.fits","_version":1,"_seq_no":0,"_primary_term":1,"found":True,"_source":{"mission": "imap", "level": "l0", "instrument": "instrument", "date": "date", "version": "version", "extension": "fits"}}

        ## Act
        indexer.lambda_handler(self.sample_payload, "")

        document_out = self.client.get_document(self.document)

        ## Assert
        assert document_out == document_true

        

    def tearDown(self):
        self.client.send_document(self.document, Action.DELETE)
        self.client.delete_index(self.index)
        self.client.close()

if __name__ == '__main__':
    unittest.main()
