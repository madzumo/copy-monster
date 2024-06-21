from AWS_base import AWSbase
import boto3


class AWSs3(AWSbase):
    def __init__(self, bucket_name, key_id='', secret_id='', region="us-east-1"):
        super().__init__(key_id, secret_id, region)

        session = boto3.Session(
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.secret_id,
            region_name=self.region)
        self.s3_client = session.client('s3')
        self.s3_resource = session.resource('s3')
        # self.s3_client = boto3.client('s3', region_name=self.region)
        self.bucket_name = bucket_name

    def list_s3_buckets(self):
        for bucket in self.s3_resource.buckets.all():
            print(bucket.name)

    def create_bucket(self):
        try:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
        except Exception as ex:
            print(f"Error:{ex}")
            return False
        return True

    def upload_file_to_bucket(self, file_name, full_file_path):
        """
        File_Name should be the name of the file only. Full_file_Path should be the full path including
        the file name
        """
        try:
            self.s3_client.upload_file(full_file_path, self.bucket_name, file_name)
        except Exception as ex:
            print(f"Error:{ex}")
            return False
        return True

    def delete_bucket(self):
        try:
            self.s3_client.delete_bucket(Bucket=self.bucket_name)
            # print(response)
        except Exception as ex:
            print(f"Error:{ex}")
            return False
        return True

    def download_file_from_bucket(self, file_name, full_save_location):
        """
        File_name is the file in the bucket to download. Full_save_location is the full path where
        you want to save the file on the host including the file name.
        """
        try:
            self.s3_resource.meta.client.download_file(self.bucket_name, file_name, full_save_location)
        except Exception as ex:
            print(f"Error:{ex}")
            return False
        return True

    def delete_bucket_contents(self):
        bucket = self.s3_resource.Bucket(self.bucket_name)
        try:
            bucket.objects.delete()
        except Exception as ex:
            print(f"Error:{ex}")
            return False
        return True

    def check_if_bucket_exists(self):
        try:
            # Try to get metadata about the bucket (this will not incur data transfer costs)
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True  # Bucket exists
        except Exception as ex:
            return False
