import logging
import boto3
import time
from pathlib import Path
from modelfarm.aws.ec2 import EC2Instance, InstanceStatus
from modelfarm.aws.iam import get_or_create_key_pair, get_or_create_security_group
logging.basicConfig(level="INFO")

logger = logging.getLogger(__name__)

region_name = 'eu-central-1'

client = boto3.client('ec2', region_name=region_name)

key_name = 'ec2-spot.pem'
key_pair = get_or_create_key_pair(client, Path(f"./.keys/{key_name}"))
security_group = get_or_create_security_group(client, "ec2-spot-sg4")

instance = EC2Instance.create_instance(client, key_name=key_name, security_group=security_group, instance_type="p2.xlarge")
logger.info(f"Spot instance: {instance}")

try:
    time.sleep(5)

    instance = EC2Instance.get_instance(client, instance_id=instance.instance_id)
    logger.info("Spot instance retrieved")

    while True:
        instance_status = instance.status()
        logger.info(f"Instance status: {instance_status}")
        if instance_status == InstanceStatus.RUNNING:
            logger.info("Instance running")
            break
        time.sleep(10)
    
    instance.run_script(key_file=Path(f"./.keys/{key_name}"), script_path="./test.sh")
finally:
    pass
    instance.terminate()
    logger.info("Spot instance terminated")