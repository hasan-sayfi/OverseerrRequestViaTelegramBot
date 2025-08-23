#!/usr/bin/env python3
"""
Test script for health check functionality.
This script tests the health checker without running the full bot.
"""
import sys
import os
import time
import signal
import threading
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.health_check import HealthChecker

def test_health_checker():
    """Test the health checker functionality."""
    print("Testing Health Checker...")
    
    # Create a test health checker with a test file
    test_health_file = "data/test_bot_health.txt"
    health_checker = HealthChecker(test_health_file)
    
    try:
        # Test 1: Start health monitoring
        print("1. Starting health monitoring...")
        health_checker.start_health_monitor()
        
        # Wait a moment for the first health file to be created
        time.sleep(2)
        
        # Test 2: Check if health file exists
        print("2. Checking if health file exists...")
        if os.path.exists(test_health_file):
            print("   ✅ Health file created successfully")
            with open(test_health_file, 'r') as f:
                content = f.read()
            print(f"   Content: {content.strip()}")
        else:
            print("   ❌ Health file not found")
            return False
        
        # Test 3: Wait and check if file gets updated
        print("3. Waiting for health file update...")
        initial_mtime = os.path.getmtime(test_health_file)
        
        # Wait for at least one update cycle (30+ seconds)
        print("   Waiting 35 seconds for health file update...")
        time.sleep(35)
        
        new_mtime = os.path.getmtime(test_health_file)
        if new_mtime > initial_mtime:
            print("   ✅ Health file updated successfully")
        else:
            print("   ❌ Health file not updated")
            return False
        
        # Test 4: Test the health check script
        print("4. Testing health check validation...")
        
        # Simulate the Docker health check logic
        try:
            current_time = time.time()
            file_age = current_time - new_mtime
            
            if file_age <= 120:  # Within 2 minutes
                print(f"   ✅ Health file is recent (age: {file_age:.1f}s)")
            else:
                print(f"   ❌ Health file is too old (age: {file_age:.1f}s)")
                return False
        except Exception as e:
            print(f"   ❌ Error checking health file: {e}")
            return False
        
        print("5. All tests passed! ✅")
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return False
        
    finally:
        # Cleanup
        print("6. Cleaning up...")
        health_checker.stop_health_monitor()
        health_checker.cleanup_health_file()
        
        # Remove test file if it exists
        if os.path.exists(test_health_file):
            os.remove(test_health_file)
        print("   Cleanup completed")

def main():
    """Main function."""
    print("🏥 Health Checker Test")
    print("=" * 50)
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    success = test_health_checker()
    
    if success:
        print("\n🎉 All health check tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Health check tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
