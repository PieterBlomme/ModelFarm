import logging
import boto3
from pathlib import Path
from modelfarm.aws.ec2 import EC2SpotInstance
from modelfarm.aws.iam import get_or_create_key_pair, get_or_create_security_group
logging.basicConfig(level="INFO")

logger = logging.getLogger(__name__)

region_name = 'eu-central-1'

client = boto3.client('ec2', region_name=region_name)

key_name = 'ec2-spot.pem'
key_pair = get_or_create_key_pair(client, Path(f"./.keys/{key_name}"))
security_group = get_or_create_security_group(client, "ec2-spot-sg")

instance = EC2SpotInstance.create_spot_instance(client, key_name=key_name, security_group=security_group)
logger.info(f"Spot instance ID: {instance}")

instance = EC2SpotInstance.get_spot_instance(client, spot_instance_request_id=instance.spot_instance_request_id)
logger.info("Spot instance retrieved")

instance.terminate(client)
logger.info("Spot instance terminated")