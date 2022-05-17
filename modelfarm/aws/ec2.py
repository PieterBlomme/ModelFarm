
from pickle import NONE
import boto3
import paramiko
import logging
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)

class InstanceStatus(Enum):
    NONE = 1
    INITIALIZING = 2
    RUNNING = 3

class BaseInstance:
    def __init__(self, client: boto3.client, instance_id: str):
        self._client = client
        self.instance_id = instance_id

    def status(self): 
        response = self._client.describe_instance_status(InstanceIds=[self.instance_id])
        if not response['InstanceStatuses']:
            return InstanceStatus.NONE
        
        if response['InstanceStatuses'][0]["InstanceStatus"]["Status"] == "initializing":
            return InstanceStatus.INITIALIZING
        elif response['InstanceStatuses'][0]["InstanceStatus"]["Status"] == "ok":
            return InstanceStatus.RUNNING
        else:
            logger.info(response)
            raise Exception(f"Unexpected instance status: {response}")

    def _connect_to_instance(self, ip, key_file, username='ubuntu', port=22, timeout=10):
        logger.info(f"Paramiko connection with key_file {key_file} and ip {ip}")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        k = paramiko.RSAKey.from_private_key_file(str(key_file))
        logger.info(f"Paramiko RSAKey {k}")

        retries = 0 
        connected = False 
        while not connected: 
            try:
                # use the public IP address to connect to an instance over the internet, default username is ubuntu
                ssh_client.connect(ip, username=username, pkey=k, port=port, timeout=timeout)
                return ssh_client
            except Exception as e:
                retries += 1 
                if retries >= 5: 
                    raise e  

        return ssh_client

    def run_script(self, key_file, script_path):
        response = self._client.describe_instances(InstanceIds=[self.instance_id])['Reservations'][0]['Instances'][0]
        public_ip_address = response["PublicIpAddress"]
        ssh_client = self._connect_to_instance(public_ip_address, key_file)
        session = ssh_client.get_transport().open_session()
        session.set_combine_stderr(True) 
        session.exec_command(open(script_path, 'r').read().replace('\r', ''))
        out = session.makefile()
        for line in out:
            logger.info(line)
        ssh_client.close()

    def terminate(self):
        response = self._client.terminate_instances(InstanceIds=[self.instance_id])
        logger.info(f"Termination response: {response}")
        
class EC2SpotInstance(BaseInstance):

    def __init__(self, client: boto3.client, instance_id: str, spot_instance_request_id: str):
        super().__init__(client=client, instance_id=instance_id)
        self.spot_instance_request_id = spot_instance_request_id

    @classmethod
    def create_spot_instance(self,
        client: boto3.client,
        key_name: str,
        security_group: Any,
        instance_type: str = 't2.micro',
        image_id: str = "ami-0a30c0b8286217815",
        max_price: float = 0.0116):

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
        spot_instance_requests = client.describe_spot_instance_requests(Filters=[{'Name':'spot-instance-request-id', 'Values':[spot_instance_request_id]}])["SpotInstanceRequests"]
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
        super().terminate()

    def __str__(self):
        return f"EC2SpotInstance(instance_id={self.instance_id}, spot_instance_request_id={self.spot_instance_request_id}"

class EC2Instance(BaseInstance):

    @classmethod
    def create_instance(self,
        client: boto3.client,
        key_name: str,
        security_group: Any,
        instance_type: str = 't2.micro',
        image_id: str = "ami-0a30c0b8286217815"):

        logger.info('Creating new request')
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
        )["Instances"]
        logger.info(f"Creation response: {response}")
        instance_id = response[0]['InstanceId']
        return EC2Instance(client=client, instance_id=instance_id)

    @classmethod
    def get_instance(self,
        client: boto3.client,
        instance_id: str):

        # find existing instances
        try:
            response = client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
            logger.info(f"Instances requests: {response}")
            return EC2Instance(client=client, instance_id=response["InstanceId"])
        except Exception as e:
            logger.exception(e)
            raise Exception(f'Instance {instance_id} not found')


    def __str__(self):
        return f"EC2Instance(instance_id={self.instance_id}"
