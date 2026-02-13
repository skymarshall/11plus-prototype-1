import boto3
import os
import dotenv
import sys

# Load env
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / '.env'
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
    
    # Efficient batch deletion
    # boto3 generic batch delete:
    # bucket.objects.all().delete()
    
    # Manual batching for better control/compatibility if needed:
    count = 0
    while True:
        objects = list(bucket.objects.limit(1000))
        if not objects:
            break
            
        keys = [{'Key': obj.key} for obj in objects]
        if not keys:
            break
            
        # Delete in batch
        response = bucket.delete_objects(
            Delete={
                'Objects': keys,
                'Quiet': True
            }
        )
        
        deleted = len(response.get('Deleted', []))
        count += deleted
        errors = response.get('Errors', [])
        
        print(f"Deleted {count} objects...", end='\r')
        
        if errors:
            print(f"\nErrors encountered: {errors}")
        
        if len(objects) < 1000:
            break

    print(f"\nBucket cleared. Total objects deleted: {count}")

except Exception as e:
    print(f"Error clearing bucket: {e}")
    sys.exit(1)
