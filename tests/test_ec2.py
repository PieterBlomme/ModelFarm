import logging
import time
import tempfile
import uuid
import os
import pytest
from pathlib import Path
from modelfarm.aws.ec2 import EC2SpotInstance, EC2Instance, InstanceStatus

logger = logging.getLogger(__name__)

@pytest.mark.parametrize("Type", (EC2Instance, EC2SpotInstance))
def test_create_instance(client, Type, security_key, security_group):
    instance = Type.create_instance(client, key_name=security_key, security_group=security_group)
    logger.info(f"Spot instance: {instance}")
    instance.terminate()
    logger.info("Spot instance terminated")

@pytest.mark.parametrize("Type", (EC2Instance, EC2SpotInstance))
def test_get_instance(client, Type, security_key, security_group):
    instance = Type.create_instance(client, key_name=security_key, security_group=security_group)
    logger.info(f"Spot instance: {instance}")
    if Type == EC2SpotInstance:
        instance = Type.get_instance(client, spot_instance_request_id=instance.spot_instance_request_id)
    else:
        instance = Type.get_instance(client, instance_id=instance.instance_id)

    logger.info("Spot instance retrieved")
    instance.terminate()
    logger.info("Spot instance terminated")

@pytest.mark.parametrize("Type", (EC2Instance, EC2SpotInstance))
def test_wait_until_instance_running(client, Type, security_key, security_group):
    instance = Type.create_instance(client, key_name=security_key, security_group=security_group)
    logger.info(f"Spot instance: {instance}")

    for i in range(20):
        instance_status = instance.status()
        logger.info(f"Instance status: {instance_status}")
        if instance_status == InstanceStatus.RUNNING:
            logger.info("Instance running")
            break
        time.sleep(10)
    assert instance_status == InstanceStatus.RUNNING

    instance.terminate()
    logger.info("Spot instance terminated")

@pytest.mark.parametrize("Type", (EC2Instance, EC2SpotInstance))
def test_ssh_and_download(client, Type, security_key, security_group):
    instance = Type.create_instance(client, key_name=security_key, security_group=security_group)

    for i in range(20):
        instance_status = instance.status()
        logger.info(f"Instance status: {instance_status}")
        if instance_status == InstanceStatus.RUNNING:
            logger.info("Instance running")
            break
        time.sleep(10)
    assert instance_status == InstanceStatus.RUNNING

    with open("test_ssh.sh", "w") as f:
        identifier = str(uuid.uuid1())
        f.write(f"echo '{identifier}' > file.txt")

    instance.run_script(key_file=Path(f"./.keys/{security_key}"), script_path="test_ssh.sh")
    os.remove("test_ssh.sh")

    instance.download_file(key_file=Path(f"./.keys/{security_key}"), source_path='./file.txt', 
                target_path = "test_ssh.txt")

    assert open("test_ssh.txt").read().strip() == identifier
    os.remove("test_ssh.txt")

    instance.terminate()
    logger.info("Spot instance terminated")