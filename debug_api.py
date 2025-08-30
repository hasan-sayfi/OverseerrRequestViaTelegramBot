#!/usr/bin/env python3
"""
Debug script to test different Overseerr API endpoints for media details.
"""
import sys
import os
import logging
import json
import requests

# Add the project directory to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.INFO)

try:
    from config.constants import OVERSEERR_API_URL, OVERSEERR_API_KEY
    
    print("="*60)
    print("TESTING OVERSEERR MEDIA DETAILS ENDPOINTS")
    print("="*60)
    
    base_url = OVERSEERR_API_URL.rstrip('/')
    if base_url.endswith('/api/v1'):
        api_base = base_url
    else:
        api_base = f"{base_url}/api/v1"
    
    headers = {"X-Api-Key": OVERSEERR_API_KEY}
    
    # Test 1: Get a specific media item by ID
    print("\n1. Testing media endpoint...")
    media_id = 375  # From our debug output
    media_url = f"{api_base}/media/{media_id}"
    
    response = requests.get(media_url, headers=headers)
    print(f"Media endpoint status: {response.status_code}")
    
    if response.status_code == 200:
        media_data = response.json()
        print(f"Media data keys: {list(media_data.keys())}")
        if 'title' in media_data or 'name' in media_data:
            title = media_data.get('title') or media_data.get('name')
            print(f"Media title: {title}")
        print(f"Full media data:")
        print(json.dumps(media_data, indent=2)[:1000] + "..." if len(str(media_data)) > 1000 else json.dumps(media_data, indent=2))
    
    # Test 2: Get TV show details using TMDB ID
    print(f"\n2. Testing TV show TMDB endpoint...")
    tmdb_id = 274671  # From our debug output
    tv_url = f"{api_base}/tv/{tmdb_id}"
    
    response = requests.get(tv_url, headers=headers)
    print(f"TV endpoint status: {response.status_code}")
    
    if response.status_code == 200:
        tv_data = response.json()
        print(f"TV data keys: {list(tv_data.keys())}")
        if 'name' in tv_data:
            print(f"TV show name: {tv_data['name']}")
        if 'overview' in tv_data:
            print(f"Overview: {tv_data['overview'][:100]}...")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
