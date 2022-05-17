import boto3
import botocore.exceptions
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_or_create_key_pair(client: boto3.client, key_path: Path):
    assert isinstance(key_path, Path), "key_path should be an instance of pathlib.Path"
    key_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a key pair on AWS
    try:
        key_pair = client.create_key_pair(KeyName=key_path.name)

        # Write the key to file
        with open(key_path, 'w') as f:             
            f.write(key_pair['KeyMaterial'])
    except botocore.exceptions.ClientError as e:
        if "InvalidKeyPair.Duplicate" in str((e)):
            assert key_path.exists(), f"Key {key_path.name} already creating in AWS, but not found locally"
        else:
            raise

def get_or_create_security_group(client: boto3.client, group_name: str):
    try:
        return client.create_security_group(GroupName=group_name, Description=group_name)
    except botocore.exceptions.ClientError as e:
        if "InvalidGroup.Duplicate" in str((e)):
            return client.describe_security_groups(Filters=[{'Name':'group-name','Values':[group_name]}])['SecurityGroups'][0]
        else:
            raise