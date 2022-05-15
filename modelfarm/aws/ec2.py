
import boto3
import logging
from pathlib import Path
from .iam import get_or_create_key_pair, get_or_create_security_group

logger = logging.getLogger(__name__)
    
class EC2SpotInstance:

    @classmethod
    def get_or_create_spot_instance(self,
        region_name: str,
        instance_name: str,
        keypair_directory: str = '.keys',
        instance_type: str = 't2.micro'):
        image_id: str = "ami-0a30c0b8286217815"
        max_price: float = 0.0116
        """
        Interact with AWS EC2 Spot Instances.  
        """
        #Create a boto3 client to connect to ec2
        client = boto3.client('ec2', region_name=region_name)

        # create an IAM key pair
        # TODO what if exists
        key_path = Path(keypair_directory, instance_name + '.pem')
        logger.info(f'KeyPair will be saved to {key_path}')
        get_or_create_key_pair(client, key_path)

        # get security group
        security_group = get_or_create_security_group(client, instance_name)
        logger.info(security_group)

        # find existing instances
        ec2_reservations = client.describe_instances()["Reservations"]
        existing_ec2_instances = []
        for reservation in ec2_reservations:
            for instance in reservation["Instances"]:
                if instance["KeyName"] == instance_name + '.pem':
                    existing_ec2_instances.append(instance)

        if existing_ec2_instances:
            logger.info('Existing spot request found')
            instance_id = existing_ec2_instances[0]['InstanceId']
        else:
            logger.info('Creating new spot request')
            response = client.run_instances(
                ImageId=image_id,
                InstanceType=instance_type,
                MinCount=1, 
                MaxCount=1,
                KeyName=instance_name + '.pem',
                DryRun=False,
                SecurityGroupIds= [
                    security_group["GroupId"],
                ],
                InstanceMarketOptions={
                    'MarketType': 'spot',
                    'SpotOptions': {
                        'MaxPrice': str(max_price),
                        'SpotInstanceType': 'one-time',
                        'InstanceInterruptionBehavior': 'terminate'
                    }
                }
            )
            instance_id = response['Instances'][0]['InstanceId']

        logger.info(f'Spot instance ID: {instance_id}')