
from pickle import NONE
import boto3
import logging
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)

class InstanceStatus(Enum):
    NONE = 1
    INITIALIZING = 2
    RUNNING = 3
class EC2SpotInstance:

    def __init__(self, client: boto3.client, instance_id: str, spot_instance_request_id: str):
        self._client = client
        self.instance_id = instance_id
        self.spot_instance_request_id = spot_instance_request_id

    @classmethod
    def create_spot_instance(self,
        client: boto3.client,
        key_name: str,
        security_group: Any,
        instance_type: str = 't2.micro'):
        image_id: str = "ami-0a30c0b8286217815"
        max_price: float = 0.0116

        logger.info('Creating new spot request')
        response = client.run_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            MinCount=1, 
            MaxCount=1,
            KeyName=key_name,
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
        )["Instances"]
        logger.info(f"Creation response: {response}")
        instance_id = response[0]['InstanceId']
        spot_instance_request_id = response[0]["SpotInstanceRequestId"]
        return EC2SpotInstance(client=client, instance_id=instance_id, spot_instance_request_id=spot_instance_request_id)

    @classmethod
    def get_spot_instance(self,
        client: boto3.client,
        spot_instance_request_id: str):

        # find existing instances
        spot_instance_requests = client.describe_spot_instance_requests()["SpotInstanceRequests"]
        logger.info(f"Spot instance requests: {spot_instance_requests}")
        for request in spot_instance_requests:
            if request["SpotInstanceRequestId"] == spot_instance_request_id:
                instance_id = request['InstanceId']
                spot_instance_request_id = request["SpotInstanceRequestId"]
                return EC2SpotInstance(client=client, instance_id=instance_id, spot_instance_request_id=spot_instance_request_id)

        raise Exception(f'Spot request {spot_instance_request_id} not found')

    def terminate(self):
        response = self._client.cancel_spot_instance_requests(SpotInstanceRequestIds=[self.spot_instance_request_id])
        logger.info(f"Cancel response: {response}")
        response = self._client.terminate_instances(InstanceIds=[self.instance_id])
        logger.info(f"Termination response: {response}")

    def status(self): 
        response = self._client.describe_instance_status(InstanceIds=[self.instance_id])
        if not response['InstanceStatuses']:
            return InstanceStatus.NONE
        
        if response['InstanceStatuses'][0]["InstanceStatus"]["Status"] == "initializing":
            return InstanceStatus.INITIALIZING
        else:
            raise Exception(f"Unexpected instance status: {response}")

    def __str__(self):
        return f"EC2SpotInstance(instance_id={self.instance_id}, spot_instance_request_id={self.spot_instance_request_id}"