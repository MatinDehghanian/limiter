#!/usr/bin/env python3
"""
Simple test script to verify CDN scenario handling without external dependencies
"""

from test_utils import (
    get_cdn_test_ips,
    group_ips_by_subnet,
    simulate_check_ip_used_logic,
    check_user_result
)


def test_cdn_scenario():
    """Test the CDN scenario with multiple IPs from the same subnet"""

    # Get CDN test IPs from shared utilities
    cdn_ips = get_cdn_test_ips()

    # Add duplicates to ensure IPs appear more than 2 times
    cdn_ips_with_duplicates = cdn_ips + cdn_ips + cdn_ips[:20]  # Add many duplicates

    # Create a user with all these IPs
    active_users = {
        "MattDev": {"name": "MattDev", "ip": cdn_ips_with_duplicates}
    }

    print("=== CDN Scenario Test ===")
    print(f"Original IP count: {len(cdn_ips_with_duplicates)}")
    print(f"Original unique IPs: {len(set(cdn_ips_with_duplicates))}")

    # Test the subnet grouping function directly
    subnet_ips = group_ips_by_subnet(cdn_ips_with_duplicates)
    print(f"After subnet grouping: {len(subnet_ips)}")
    print(f"Subnet representations: {subnet_ips}")

    # Test the full logic
    print("\n=== Testing complete logic ===")
    result = simulate_check_ip_used_logic(active_users)
    print(f"Result: {result}")

    # Check if the user has the expected subnet count
    check_user_result(result, "MattDev", "140.248.74.x")

    # Test with mixed IPs from different subnets
    print("\n=== Testing mixed subnets ===")
    mixed_ips = [
        '140.248.74.46', '140.248.74.171', '140.248.74.76',  # Same subnet
        '192.168.1.1', '192.168.1.2', '192.168.1.3',        # Different subnet
        '8.8.8.8', '1.1.1.1'                                # Individual IPs
    ]

    # Add duplicates to ensure they appear more than 2 times
    mixed_ips_with_duplicates = mixed_ips + mixed_ips + mixed_ips[:4]

    mixed_users = {
        "TestUser": {"name": "TestUser", "ip": mixed_ips_with_duplicates}
    }

    mixed_result = simulate_check_ip_used_logic(mixed_users)
    print(f"Mixed result: {mixed_result}")

    if "TestUser" in mixed_result:
        user_subnets = mixed_result["TestUser"]
        print(f"User TestUser has {len(user_subnets)} subnet(s): {user_subnets}")

        # Should have 4 different subnets
        if len(user_subnets) == 4:
            print("✅ SUCCESS: Mixed subnets handled correctly!")
        else:
            print("❌ FAILED: Mixed subnets not handled correctly")

    # Test subnet grouping without filtering (to show the core functionality)
    print("\n=== Testing subnet grouping without filtering ===")
    direct_subnet_result = group_ips_by_subnet(cdn_ips)
    print(f"Direct subnet grouping of {len(cdn_ips)} IPs: {len(direct_subnet_result)} subnets")
    print(f"Subnet representations: {direct_subnet_result}")

    if len(direct_subnet_result) == 1 and "140.248.74.x" in direct_subnet_result:
        print("✅ SUCCESS: Core subnet grouping works correctly!")
    else:
        print("❌ FAILED: Core subnet grouping not working")


if __name__ == "__main__":
    test_cdn_scenario()
