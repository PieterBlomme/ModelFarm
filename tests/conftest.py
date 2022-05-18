import boto3
import pytest
import uuid
from pathlib import Path
from modelfarm.aws.iam import get_or_create_key_pair, get_or_create_security_group

REGION = 'eu-central-1'

@pytest.fixture
def client():
    return boto3.client('ec2', region_name=REGION)

@pytest.fixture
def security_key(client):
    key_name = f'{str(uuid.uuid1())}.pem'
    key_path = Path(f".keys/{key_name}")
    get_or_create_key_pair(client, key_path)
    return key_name

@pytest.fixture
def security_group(client):
    sgroup_name = str(uuid.uuid1())
    return get_or_create_security_group(client, sgroup_name)