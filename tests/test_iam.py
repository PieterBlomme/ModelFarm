import uuid
import boto3
import logging
import tempfile
from modelfarm.aws.iam import get_or_create_key_pair, get_or_create_security_group
from pathlib import Path

logger = logging.getLogger(__name__)

REGION = 'eu-central-1'

def test_create_key():
    client = boto3.client('ec2', region_name=REGION)

    with tempfile.TemporaryDirectory() as tmpdir:
        key_name = f'{str(uuid.uuid1())}.pem'
        key_path = Path(f"{tmpdir}/{key_name}")

        # try to create a key
        get_or_create_key_pair(client, key_path)

        key_content = open(key_path).read()
        logger.info(f"Key: {key_content}")
        
        # if asking for a key with the same path, the key should not be overwritten
        get_or_create_key_pair(client, key_path)
        assert key_content == open(key_path).read()

def test_security_group():
    client = boto3.client('ec2', region_name=REGION)

    sgroup_name = str(uuid.uuid1())

    # try to create security group
    security_group = get_or_create_security_group(client, sgroup_name)
    logger.info(security_group)
    # if asking for a sgroup with the same name, the sgroup should be returned
    security_group2 = get_or_create_security_group(client, sgroup_name)
    logger.info(security_group2)
    assert security_group2 == security_group
