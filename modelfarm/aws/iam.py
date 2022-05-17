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

def get_or_create_security_group(client: boto3.client, group_name: str, enable_nfs:bool=False, enable_ds:bool=False, firewall_ingress_settings=('tcp', 22, 22, '0.0.0.0/0')):
    try:
        security_group = client.create_security_group(GroupName=group_name, Description=group_name)
        logger.info(security_group)
        logger.info(security_group["GroupId"])

        # Add NFS rules (port 2049) in order to connect an EFS instance 
        client.authorize_security_group_ingress(GroupName=group_name,
                                                IpPermissions=[
                                                        {'FromPort': 2049,
                                                            'IpProtocol': 'tcp',
                                                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                                                            'ToPort': 2049,
                                                        }
                                                ])   
        
        # Add ingress & egress rules to enable datasync
        # Add HTTP and HTTPS rules (port 80 & 443) in order to connect to datasync agent
        client.authorize_security_group_ingress(GroupName=group_name,
                                                IpPermissions=[
                                                        {'FromPort': 80,
                                                        'IpProtocol': 'tcp',
                                                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                                                        'ToPort': 80,
                                                        },
                                                        {'FromPort': 443,
                                                        'IpProtocol': 'tcp',
                                                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                                                        'ToPort': 443,
                                                        }                                        
                                                ])

        # Add HTTPS egress rules (port 443) in order to connect datasync agent instance to AWS 
        client.authorize_security_group_egress(GroupId=security_group['GroupId'],  
                                                IpPermissions=[
                                                        {'FromPort': 443,
                                                        'IpProtocol': 'tcp',
                                                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                                                        'ToPort': 443,
                                                        }                                        
                                                ]) 

        # Define ingress rules OTHERWISE YOU WILL NOT BE ABLE TO CONNECT
        client.authorize_security_group_ingress(GroupName=group_name,
                                                IpPermissions=[
                                                        {'FromPort': firewall_ingress_settings[1],
                                                            'IpProtocol': firewall_ingress_settings[0],
                                                            'IpRanges': [
                                                                    {'CidrIp': firewall_ingress_settings[3],
                                                                    'Description': 'ips'
                                                                    },
                                                                    ],
                                                        'ToPort': firewall_ingress_settings[2],
                                                        }
                                                ])
        return security_group
    except botocore.exceptions.ClientError as e:
        if "InvalidGroup.Duplicate" in str((e)):
            return client.describe_security_groups(Filters=[{'Name':'group-name','Values':[group_name]}])['SecurityGroups'][0]
        else:
            raise