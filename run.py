#!/usr/bin/env python
"""
Quick start script for the Mockup Image Compositing API
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'MONGODB_URI',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'S3_BUCKET_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file")
        print("You can copy .env.example to .env and fill in the values")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import pymongo
        import boto3
        import PIL
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nPlease install dependencies with:")
        print("   pip install -r requirements.txt")
        return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("Mockup Image Compositing API - Quick Start")
    print("=" * 60)
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("Starting the API server...")
    print("=" * 60)
    print()
    
    # Get port from environment
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f"Server will run on port: {port}")
    print(f"Access the API at: http://localhost:{port}")
    print()
    
    # Import and run the app
    from app import app
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()