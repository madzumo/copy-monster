import boto3

from AWS_base import AWSbase


class AWSeks(AWSbase):
    def __init__(self, key_id='', secret_id='', region="us-east-1"):
        super().__init__(key_id, secret_id, region)
        self.cluster_name = 'madzumo-cluster'
        self.cluster_version = '1.29'
        self.endpoint = ''

    def create_eks_cluster(self):
        # Create an EKS client
        eks = boto3.client('eks')

        # Create the EKS cluster
        response = eks.create_cluster(
            name=self.cluster_name,
            version=self.cluster_version,
            # roleArn=self._get_ARN_info,
            resourcesVpcConfig={
                'subnetIds': [
                    'string',
                ],
                'securityGroupIds': [
                    'string',
                ],
                'endpointPublicAccess': True
            },
            tags={
                'madzumo': 'demo'
            }
        )
        self.eks_endpoint = response['cluster']['endpoint']
        print(f"EKS Cluster created:\n{self.eks_endpoint}")

    def delete_eks_cluster(self):
        print('yes')

    def create_node_group(self):
        ec2 = boto3.client('eks')
        ec2.create_nodegroup(
            clusterName=self.cluster_name,
            nodegroupName=f"{self.cluster_name}-nodegroup",
            scalingConfig={
                'minSize': 2,
                'maxSize': 4,
                'desiredSize': 3
            },
            diskSize=123,
            subnets=[
                'string',
            ],
            instanceTypes=[
                self.instance_type,
            ],
            amiType='AL2023_x86_64_STANDARD',
            tags={
                self.tag_identity_key: self.tag_identity_value
            },
            capacityType='SPOT'
        )
        print("Node Group created")

    def create_eks_role(self):
        iam_client = boto3.client('iam')

        # Define the trust relationship policy as a string
        trust_policy = """{
        "Version": "2012-10-17",
        "Statement": [
            {
            "Effect": "Allow",
            "Principal": {
                "Service": "eks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
            }
        ]
        }"""

        # Create the IAM role for EKS
        try:
            role = iam_client.create_role(
                RoleName='eksClusterRole-madzumo',
                AssumeRolePolicyDocument=trust_policy,
                Description='Amazon EKS - Cluster role'
            )
            print("Role created successfully.")
            return role['Role']['RoleId']
        except Exception as e:
            print(f"Error creating role: {e}")
            return ''
