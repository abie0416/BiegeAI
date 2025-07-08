#!/usr/bin/env python3
"""
GCP Cloud Storage Setup Script for RAG Index Persistence

This script helps you set up Google Cloud Storage for storing and retrieving
your RAG index data across multiple Railway deployments.
"""

import os
import json
from google.cloud import storage
from google.cloud.exceptions import NotFound

def setup_gcp_storage():
    """Setup GCP Cloud Storage for RAG index persistence"""
    
    print("🚀 GCP Cloud Storage Setup for RAG Index")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if service account JSON is available
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not found in environment variables!")
        print("Please add your service account JSON to the .env file")
        return False
    
    # Create temporary credentials file
    import tempfile
    import json
    
    try:
        # Parse the JSON to validate it
        service_account_data = json.loads(service_account_json)
        
        # Create temporary file with credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(service_account_data, f)
            temp_credentials_path = f.name
        
        # Set environment variable for Google Cloud client
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_credentials_path
        
        print("✅ Service account credentials loaded from environment variable")
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON")
        return False
    except Exception as e:
        print(f"❌ Error setting up credentials: {e}")
        return False
    
    try:
        # Initialize GCP client
        client = storage.Client()
        
        # Get project ID
        project_id = client.project
        print(f"✅ Connected to GCP project: {project_id}")
        
        # Create or verify bucket
        bucket_name = input("Enter bucket name for RAG index storage (e.g., 'my-rag-index'): ").strip()
        
        if not bucket_name:
            print("❌ Bucket name is required")
            return False
        
        # Check if bucket exists
        try:
            bucket = client.get_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' already exists")
        except NotFound:
            # Create new bucket
            print(f"🔄 Creating new bucket: {bucket_name}")
            bucket = client.create_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' created successfully")
        
        # Test upload/download
        print("🧪 Testing upload/download functionality...")
        
        # Create test file
        test_content = "This is a test file for RAG index storage"
        test_blob = bucket.blob("test/rag_test.txt")
        test_blob.upload_from_string(test_content)
        print("✅ Test upload successful")
        
        # Download test file
        downloaded_content = test_blob.download_as_text()
        if downloaded_content == test_content:
            print("✅ Test download successful")
        else:
            print("❌ Test download failed")
            return False
        
        # Clean up test file
        test_blob.delete()
        print("✅ Test cleanup successful")
        
        # Generate environment variables
        env_vars = {
            "GCP_PROJECT_ID": project_id,
            "GCP_BUCKET_NAME": bucket_name
        }
        
        print("\n📋 Environment Variables for Railway:")
        print("=" * 40)
        for key, value in env_vars.items():
            print(f"{key}={value}")
        
        # Save to .env file
        env_file_path = ".env"
        with open(env_file_path, "a") as f:
            f.write(f"\n# GCP Cloud Storage Configuration\n")
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"\n✅ Environment variables saved to {env_file_path}")
        print("\n🎉 GCP Cloud Storage setup completed successfully!")
        print("\nNext steps:")
        print("1. Add the environment variables to your Railway project")
        print("2. Deploy your application")
        print("3. Use the /rebuild-rag endpoint to build and upload your first index")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def test_gcp_connection():
    """Test GCP connection and bucket access"""
    print("🧪 Testing GCP Connection...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if service account JSON is available
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not found in environment variables!")
        return False
    
    # Create temporary credentials file
    import tempfile
    import json
    
    try:
        # Parse the JSON to validate it
        service_account_data = json.loads(service_account_json)
        
        # Create temporary file with credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(service_account_data, f)
            temp_credentials_path = f.name
        
        # Set environment variable for Google Cloud client
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_credentials_path
        
        client = storage.Client()
        project_id = client.project
        print(f"✅ Connected to GCP project: {project_id}")
        
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        if not bucket_name:
            print("❌ GCP_BUCKET_NAME environment variable not set")
            return False
        
        bucket = client.get_bucket(bucket_name)
        print(f"✅ Successfully accessed bucket: {bucket_name}")
        
        # List existing files
        blobs = list(bucket.list_blobs(prefix="rag_index/"))
        print(f"📁 Found {len(blobs)} existing RAG index files")
        
        return True
        
    except Exception as e:
        print(f"❌ GCP connection test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_gcp_connection()
    else:
        setup_gcp_storage() 