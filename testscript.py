import logging
import boto3
import time
import uuid
from pathlib import Path
from modelfarm.aws.ec2 import EC2SpotInstance, EC2Instance, InstanceStatus
from modelfarm.aws.iam import get_or_create_key_pair, get_or_create_security_group
logging.basicConfig(level="INFO")

logger = logging.getLogger(__name__)

region_name = 'eu-central-1'

client = boto3.client('ec2', region_name=region_name)

key_name = f'{str(uuid.uuid1())}.pem'
key_pair = get_or_create_key_pair(client, Path(f"./.keys/{key_name}"))
security_group = get_or_create_security_group(client, "ec2-spot-sg4")

instance = EC2Instance.create_instance(client, key_name=key_name, security_group=security_group, instance_type="p3.2xlarge")
logger.info(f"Instance: {instance}")

try:
    while True:
        instance_status = instance.status()
        logger.info(f"Instance status: {instance_status}")
        if instance_status == InstanceStatus.RUNNING:
            logger.info("Instance running")
            break
        time.sleep(10)
    
    start = time.time()
    instance.run_script(key_file=Path(f"./.keys/{key_name}"), script_path="./test.sh")
    end = time.time()
    logger.info(f"Total runtime: {(end-start)/60} minutes")
    instance.download_file(key_file=Path(f"./.keys/{key_name}"), source_path='./pytorch-image-models/model_best.pth.tar', 
                target_path = './model_best.pth.tar')
    instance.download_file(key_file=Path(f"./.keys/{key_name}"), source_path='./pytorch-image-models/summary.csv', 
                target_path = './summary.csv')
    instance.download_file(key_file=Path(f"./.keys/{key_name}"), source_path='./pytorch-image-models/results-all.csv', 
                target_path = './results-all.csv')

finally:
    instance.terminate()
    logger.info("Spot instance terminated")