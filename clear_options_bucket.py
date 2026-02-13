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
s3 = boto3.resource(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    region_name=region
)

bucket_name = 'options'
bucket = s3.Bucket(bucket_name)

try:
    # Check if bucket exists
    if not bucket.creation_date:
        print(f"Bucket '{bucket_name}' does not exist.")
        sys.exit(0)

    print(f"Clearing bucket '{bucket_name}'...")
    # Delete all objects Iterate because batch delete might fail on some S3 impls or empty body issue
    # bucket.objects.all().delete() 
    
    # Manual deletion loop to be safe with Supabase S3
    paginator = s3.meta.client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name)

    count = 0
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                # delete one by one
                s3.meta.client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                count += 1
                if count % 10 == 0:
                    print(f"Deleted {count} objects...", end='\r')

    print(f"\nBucket cleared. Total objects deleted: {count}")

except Exception as e:
    print(f"Error clearing bucket: {e}")
    sys.exit(1)
