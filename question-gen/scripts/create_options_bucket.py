import boto3
import os
import dotenv
import sys
from pathlib import Path

# Load env
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / '.env'
# Assuming question-gen/scripts/create_options_bucket.py
# .env is in question-gen/.env
# wait, my clear_options_bucket used question-gen/.env ?
# clear_options_bucket was moved to question-gen/scripts/
# .env is in question-gen/
# So SCRIPT_DIR = question-gen/scripts
# SCRIPT_DIR.parent = question-gen
# So ENV_PATH = SCRIPT_DIR.parent / '.env' is correct if .env is in question-gen/
# Let's verify .env location.
# ls d:\Dev\Cursor\11plus\question-gen showed .env (Step 9)
# So yes.

if not ENV_PATH.exists():
    print(f"Warning: .env not found at {ENV_PATH}")
dotenv.load_dotenv(ENV_PATH)

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
