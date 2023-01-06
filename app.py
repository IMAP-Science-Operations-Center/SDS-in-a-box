#!/usr/bin/env python3
import os
import boto3 
import string
import random
import aws_cdk as cdk
import aws_cdk.assertions as assertions
from sds_in_a_box.sds_in_a_box_stack import SdsInABoxStack

### Configuration variables
# A random unqiue ID for this particular instance of the SDS
SDS_ID = "".join( [random.choice(string.ascii_lowercase) for i in range(8)] )

# An initial user of the APIs
initial_user = "harter@lasp.colorado.edu"

### Implement the code found in "sds_in_a_box_stack.py"
app = cdk.App()
SdsInABoxStack(app, "SdsInABoxStack-"+SDS_ID, SDS_ID=SDS_ID, initial_user=initial_user)
app.synth()