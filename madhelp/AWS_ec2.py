import AWS_base
import helper as hc
import boto3
import os
from time import sleep
import AWS_s3


class AWSec2(aws_madzumo.AWSbase):
    def __init__(self, instance_name, key_id='', secret_id='', region='us-east-1'):
        super().__init__(key_id, secret_id, region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.ec2_instance_name = instance_name
        self.ec2_instance_public_ip = ''
        self.ec2_instance_private_ip = ''
        self.ec2_instance_id = ''
        self.ec2_instance_public_dns_name = ''
        self.ec2_instance_subnet_id = ''
        self.ec2_instance_vpc_id = ''
        self.ssh_key_path = ''
        self.ssh_key_pair_name = f"{instance_name}-keypair"
        self.s3_temp_bucket = ''
        self.ssh_username = 'ec2-user'
        self.ssh_timeout = 60

    def create_ec2_instance(self, backup_key_to_s3=False):
        """Creates Instance in Default VPC. Instance Name required."""
        if self.get_instance():
            hc.console_message(["EC2 instance already present"], hc.ConsoleColors.info)
            self.populate_ec2_instance()
        else:
            self.create_security_group()
            self.create_ec2_key_pair()
            if backup_key_to_s3:
                self.upload_key_pair()
            try:  # Launch a new EC2 instance
                results = self.ec2_resource.create_instances(
                    ImageId=self.instance_ami,
                    MinCount=1,
                    MaxCount=1,
                    InstanceType=self.instance_type,
                    KeyName=f"{self.ec2_instance_name}-keypair",
                    SecurityGroups=[f"{self.ec2_instance_name}-sg"],
                    # SubnetId = self.ec2_subnet_id,
                    TagSpecifications=[
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {
                                    'Key': 'Name',
                                    'Value': self.ec2_instance_name
                                },
                                {
                                    'Key': self.tag_identity_key,
                                    'Value': self.tag_identity_value
                                }
                            ]
                        }
                    ]
                )[0].id
                hc.console_message([f"EC2 Instance Created:{self.ec2_instance_name}"], hc.ConsoleColors.info)
                self.ec2_instance_id = results
            except Exception as ex:
                hc.console_message([f"Error creating Instance:{ex}"], hc.ConsoleColors.error)
                return

            self.wait_for_instance_to_load()
            self.populate_ec2_instance()
            print(f"EC2 Instance Ready. IP: {self.ec2_instance_public_ip}")

    def populate_ec2_instance(self, show_result=True):
        """Populate all variables with Instance Information"""
        try:
            response = self.get_instance()
            if response:
                if response[0]['Instances'][0]['State']['Name'] != 'running':
                    if show_result:
                        hc.console_message(
                            [f"Error: Instance in {response[0]['Instances'][0]['State']['Name']} state"],
                            hc.ConsoleColors.error)
                else:
                    self.ec2_instance_id = response[0]['Instances'][0]['InstanceId']
                    self.ec2_instance_public_ip = response[0]['Instances'][0]['PublicIpAddress']
                    self.ec2_instance_private_ip = response[0]['Instances'][0]['PrivateIpAddress']
                    self.ec2_instance_public_dns_name = response[0]['Instances'][0]['PublicDnsName']
                    self.ec2_instance_subnet_id = response[0]['Instances'][0]['SubnetId']
                    self.ec2_instance_vpc_id = response[0]['Instances'][0]['VpcId']
                    self.ssh_key_path = os.path.join(os.getcwd(), self.ssh_key_pair_name)
                    self.s3_temp_bucket = f"madzumo-ops-{self.aws_account_number}"
                    self.download_key_pair()
                    if show_result:
                        hc.console_message(["ec2 Instance info populated"], hc.ConsoleColors.info, total_chars=0)
                return True
            else:
                if show_result:
                    hc.console_message([f"Unable to locate instance: {self.ec2_instance_name}"],
                                       hc.ConsoleColors.info)
                return False
        except Exception as ex:
            print(f"Error: {ex}")
            return False

    def delete_all_ec2_instances_tag(self):
        response = self.get_all_instances_tag()
        if response:
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    you_are_terminated = self.ec2_resource.Instance(instance['InstanceId'])
                    you_are_terminated.terminate()
                    print(f"EC2 instance {instance['InstanceId']} terminated.\n Waiting for completion...")
                    # time.sleep(10)
        else:
            hc.console_message(
                [f"No Instance found for Tag-> {self.tag_identity_key}:{self.tag_identity_value}"],
                hc.ConsoleColors.info)

    def delete_ec2_instance(self):
        if self.populate_ec2_instance():
            if self.ec2_instance_id == '':
                print("Error: EC2 instance id needed")
            else:
                hc.console_message(["Terminating Operator Node"], hc.ConsoleColors.info)
                you_are_terminated = self.ec2_resource.Instance(self.ec2_instance_id)
                you_are_terminated.terminate()
                print(f"EC2 instance {self.ec2_instance_id} terminating.....")
                self.wait_for_instance_to_terminate()
                self.delete_key_pair()
                self.delete_security_group()

    def get_security_group_id(self):
        response = self.ec2_client.describe_security_groups(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [f"{self.ec2_instance_name}-sg"]
                }
            ]
        )
        if response['SecurityGroups']:
            return response['SecurityGroups'][0]['GroupId']
        else:
            return

    def delete_security_group(self):
        try:
            this_sg_id = self.get_security_group_id()
            you_are_terminated = self.ec2_resource.SecurityGroup(this_sg_id)
            you_are_terminated.delete()
            hc.console_message([f"Security Group {this_sg_id} terminated."], hc.ConsoleColors.info)
        except Exception as ex:
            print(f"{ex}")

    def create_security_group(self):
        if self.get_security_group_id():
            hc.console_message(["Security Group present"], hc.ConsoleColors.info)
        else:
            sg_madzumo = self.ec2_client.create_security_group(
                GroupName=f"{self.ec2_instance_name}-sg",
                Description='ssh http https',
                VpcId=self.get_default_vpc_id(),
                TagSpecifications=[
                    {
                        'ResourceType': 'security-group',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': f"{self.ec2_instance_name}-sg"
                            },
                            {
                                'Key': self.tag_identity_key,
                                'Value': self.tag_identity_value
                            }
                        ]
                    }
                ]
            )

            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_madzumo['GroupId'],
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )

            self.ec2_client.authorize_security_group_egress(
                GroupId=sg_madzumo['GroupId'],
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 0,
                        'ToPort': 0,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            hc.console_message([f"Created Security Group: {self.ec2_instance_name}-sg"],
                               hc.ConsoleColors.info)

    def get_key_pair_id(self):
        response = self.ec2_client.describe_key_pairs(
            Filters=[
                {
                    'Name': 'key-name',
                    'Values': [f"{self.ec2_instance_name}-keypair"]
                }
            ]
        )
        if response['KeyPairs']:
            return response['KeyPairs'][0]['KeyPairId']
        else:
            return

    def delete_key_pair(self):
        key_pair = self.ec2_resource.KeyPair(f"{self.ec2_instance_name}-keypair")
        key_pair.delete()

        # self.ec2_resource.KeyPair.delete(key_pair_id=key_pair_id)

        hc.console_message(["Key Pair terminated"], hc.ConsoleColors.info)

    def create_ec2_key_pair(self):
        if self.get_key_pair_id():
            hc.console_message(["Key Pair Present"], hc.ConsoleColors.info)
        else:
            try:
                response = self.ec2_client.create_key_pair(KeyName=f"{self.ec2_instance_name}-keypair")
                # self.ssh_key_material = response['KeyMaterial']
                key_material = response['KeyMaterial']
                with open(f"{self.ec2_instance_name}-keypair", 'w') as file:
                    file.write(key_material)
                file_path = f"{os.getcwd()}/{self.ec2_instance_name}-keypair"
                os.chmod(file_path, 0o600)
                hc.console_message([f"Created Key Pair: {self.ec2_instance_name}-keypair"],
                                   hc.ConsoleColors.info)
                # self.upload_key_pair()
            except Exception as ex:
                hc.console_message([f"Error creating key pair:", f"{ex}"], hc.ConsoleColors.error)

    def get_instance(self):
        response = self.ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [self.ec2_instance_name]
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )
        return response['Reservations']

    def get_instance_id(self):
        response = self.ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [self.ec2_instance_name]
                }
            ]
        )
        if response['Reservations']:
            return response['Reservations'][0]['Instances'][0]['InstanceId']
        else:
            return

    def get_all_instances_tag(self):
        response = self.ec2_client.describe_instances(
            Filters=[
                {
                    'Name': f'tag:{self.tag_identity_key}',
                    'Values': [self.tag_identity_value]
                }
            ]
        )
        return response

    def get_default_vpc_id(self):
        response = self.ec2_client.describe_vpcs(
            Filters=[
                {
                    'Name': 'is-default',
                    'Values': ['true']
                }
            ]
        )
        return response['Vpcs'][0]['VpcId']

    def wait_for_instance_to_load(self):
        """Waits until Instance State = running and Instance Status = passed. Have Instance ID assigned."""
        while True:
            hc.console_message([f"{hc.get_current_time()} Waiting for instance to initialize....."],
                               hc.ConsoleColors.basic)
            sleep(20)
            new_response = self.ec2_client.describe_instance_status(InstanceIds=[self.ec2_instance_id])
            if new_response['InstanceStatuses']:
                instance_state = new_response['InstanceStatuses'][0]['InstanceState']['Name']
                instance_status = new_response['InstanceStatuses'][0]['InstanceStatus']['Details'][0]['Status']
                if instance_state == 'running' and instance_status == 'passed':
                    break

    def wait_for_instance_to_terminate(self):
        """Waits until Instance State = running and Instance Status = passed. Have Instance ID assigned."""
        while True:
            response = self.ec2_client.describe_instances(InstanceIds=[self.ec2_instance_id])
            state = response['Reservations'][0]['Instances'][0]['State']['Name']
            if state == 'terminated':
                hc.console_message([f"Instance: {self.ec2_instance_id} terminated."],
                                   hc.ConsoleColors.info)
                break
            else:
                hc.console_message(
                    [f"{hc.get_current_time()} Waiting for instance:{self.ec2_instance_id} to Terminate....."],
                    hc.ConsoleColors.basic)
                sleep(20)

    def download_key_pair(self):
        try:
            file_path = os.path.join(os.getcwd(), self.ssh_key_pair_name)

            if os.path.exists(file_path):
                return True

            s3_setup = s3_config.AWSs3(self.s3_temp_bucket)
            s3_setup.download_file_from_bucket(self.ssh_key_pair_name, file_path)

            os.chmod(file_path, 0o600)
            hc.console_message(['Download Key Pair file'], hc.ConsoleColors.info)
            return True
        except Exception as e:
            hc.console_message(['Error downloading key pair', f"{e}"], hc.ConsoleColors.info)
            return False

    def upload_key_pair(self):
        hc.console_message(['Backing up key pair to S3'], hc.ConsoleColors.info)
        try:
            file_path = os.path.join(os.getcwd(), self.ssh_key_pair_name)
            s3_setup = s3_config.AWSs3(self.s3_temp_bucket)
            if os.path.exists(file_path):
                s3_setup.upload_file_to_bucket(self.ssh_key_pair_name, file_path)
            else:
                hc.console_message(['Unable to find key pair file to upload to S3',
                                    'Pipeline can still continue but PLEASE keep Key Pair file in the same directory'
                                    'as this utility',
                                    'Otherwise you will lose connectivity to the pipeline'], hc.ConsoleColors.warning)
        except Exception as ex:
            hc.console_message([f"Error:{ex}", "Pipeline can continue but PLEASE keep the Key Pair file in "
                                "the the same directory with his utility", "Otherwise you will lose "
                                "connectivity to the pipeline"], hc.ConsoleColors.error)

    def remove_local_key_pair(self):
        try:
            file_path = os.path.join(os.getcwd(), self.ssh_key_pair_name)

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:
            hc.console_message(['Error removing key pair', f"{e}"], hc.ConsoleColors.info)

    def reset_ec2_boto3_objects(self):
        # self.ec2_client = boto3.client('ec2', region_name=self.region)
        # self.ec2_resource = boto3.resource('ec2', region_name=self.region)
        session = boto3.Session(
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.secret_id,
            region_name=self.region  # Optional, but often necessary
        )
        self.ec2_client = session.client('ec2')
        self.ec2_resource = session.resource('ec2')
