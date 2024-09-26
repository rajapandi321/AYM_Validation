import boto3
from azure.storage.blob import BlobServiceClient
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
import io

# AWS S3 setup
s3 = boto3.client('s3')
bucket_name = 'data-storage-repo'
folder_prefix = 'DEBUG/processed/OrderHistory'  # Folder to download from the S3 bucket

# Azure Blob Storage setup
azure_connection_string = "DefaultEndpointsProtocol=https;AccountName=azuredp;AccountKey=YOUR_AZURE_ACCOUNT_KEY;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
container_name = "image-migration"

try:
    # Ensure the Azure Blob container exists
    container_client = blob_service_client.get_container_client(container_name)
    try:
        container_client.create_container()
    except Exception as e:
        print(f"Container {container_name} already exists or couldn't be created: {str(e)}")

    # List all objects under the given folder prefix in S3
    objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)

    if 'Contents' not in objects:
        print(f"No objects found in folder {folder_prefix} in bucket {bucket_name}.")
    else:
        for obj in objects['Contents']:
            file_key = obj['Key']

            # Skip if the key is just the folder itself (it won't have any content)
            if file_key.endswith('/'):
                continue

            # Download the file from S3 into memory
            file_obj = s3.get_object(Bucket=bucket_name, Key=file_key)
            file_stream = file_obj['Body'].read()

            # Set the same folder structure in Azure Blob Storage
            blob_client = container_client.get_blob_client(blob=file_key)

            try:
                # Upload the file to Azure Blob Storage
                blob_client.upload_blob(io.BytesIO(file_stream), overwrite=True)
                print(f"Uploaded {file_key} to Azure Blob Storage.")
            except Exception as e:
                print(f"Error uploading {file_key} to Azure Blob Storage: {str(e)}")

except (NoCredentialsError, PartialCredentialsError):
    print("AWS credentials not available.")
except Exception as e:
    print(f"Error occurred: {str(e)}")