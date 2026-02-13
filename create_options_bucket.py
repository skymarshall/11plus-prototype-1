import boto3
import os
import dotenv
import sys

# Load env
dotenv.load_dotenv('question-gen/.env')

endpoint = os.getenv('SUPABASE_STORAGE_S3_URL') or 'http://127.0.0.1:54321/storage/v1/s3'
access = os.getenv('SUPABASE_STORAGE_ACCESS_KEY')
secret = os.getenv('SUPABASE_STORAGE_SECRET_KEY')
region = os.getenv('SUPABASE_STORAGE_REGION', 'us-east-1')

if not access or not secret:
    print("Error: Access/Secret keys missing in .env")
    sys.exit(1)

print(f"Connecting to {endpoint}...")
s3 = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    region_name=region
)

bucket_name = 'options'
try:
    s3.create_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' created successfully.")
except Exception as e:
    print(f"Error creating bucket: {e}")
    # Check if exists
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except Exception as e2:
        print(f"Bucket does not exist and creation failed: {e2}")
        sys.exit(1)
