#!/usr/bin/env python3
"""
Test script to verify CDN scenario handling
"""

import asyncio
import os
import sys

from utils.check_usage import ACTIVE_USERS, check_ip_used
from utils.types import UserType
from test_utils import get_cdn_test_ips, check_user_result

# Add the current directory to the Python path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_cdn_scenario():
    """Test the CDN scenario with multiple IPs from the same subnet"""

    # Clear any existing data
    ACTIVE_USERS.clear()

    # Get CDN test IPs from shared utilities
    cdn_ips = get_cdn_test_ips()

    # Add some duplicate IPs to simulate the "appears more than two times" logic
    cdn_ips_with_duplicates = cdn_ips + cdn_ips[:10]  # Add some duplicates

    # Create a user with all these IPs
    ACTIVE_USERS["MattDev"] = UserType(name="MattDev", ip=cdn_ips_with_duplicates)

    print("=== CDN Scenario Test ===")
    print(f"Original IP count: {len(cdn_ips_with_duplicates)}")
    print(f"Original unique IPs: {len(set(cdn_ips_with_duplicates))}")

    # Test the full check_ip_used function
    print("\n=== Testing check_ip_used function ===")
    try:
        result = await check_ip_used()
        print(f"Result from check_ip_used: {result}")

        # Check if the user has the expected subnet count
        check_user_result(result, "MattDev", "140.248.74.x")

    except Exception as error:  # pylint: disable=broad-exception-caught
        print(f"❌ ERROR: {error}")

    # Clean up
    ACTIVE_USERS.clear()

if __name__ == "__main__":
    asyncio.run(test_cdn_scenario())
