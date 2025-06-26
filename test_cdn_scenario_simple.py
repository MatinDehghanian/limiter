#!/usr/bin/env python3
"""
Simple test script to verify CDN scenario handling without external dependencies
"""

import ipaddress
from collections import Counter


def group_ips_by_subnet(ip_list: list[str]) -> list[str]:
    """
    Group IPs by their /24 subnet and return unique subnets.
    This helps handle CDN scenarios where multiple IPs come from the same subnet.
    
    Args:
        ip_list (list[str]): List of IP addresses
        
    Returns:
        list[str]: List of unique subnet representations (e.g., "140.248.74.x")
    """
    subnet_groups = {}
    
    for ip in ip_list:
        try:
            # Parse the IP address
            ip_obj = ipaddress.ip_address(ip)
            
            # For IPv4, group by /24 subnet (first 3 octets)
            if ip_obj.version == 4:
                # Get the network address for /24 subnet
                network = ipaddress.ip_network(f"{ip}/24", strict=False)
                subnet_key = f"{network.network_address.exploded.rsplit('.', 1)[0]}.x"
            else:
                # For IPv6, use the full IP as is (less common for CDN scenarios)
                subnet_key = str(ip_obj)
            
            if subnet_key not in subnet_groups:
                subnet_groups[subnet_key] = []
            subnet_groups[subnet_key].append(ip)
            
        except ValueError:
            # If IP parsing fails, treat as individual IP
            subnet_key = ip
            if subnet_key not in subnet_groups:
                subnet_groups[subnet_key] = []
            subnet_groups[subnet_key].append(ip)
    
    # Return the subnet representations
    return list(subnet_groups.keys())


def simulate_check_ip_used_logic(active_users: dict) -> dict:
    """
    Simulate the check_ip_used logic without external dependencies
    """
    all_users_log = {}
    for email in list(active_users.keys()):
        data = active_users[email]
        ip_counts = Counter(data["ip"])
        # Filter IPs that appear more than 2 times
        filtered_ips = list({ip for ip in data["ip"] if ip_counts[ip] > 2})
        
        # Group IPs by subnet to handle CDN scenarios
        subnet_ips = group_ips_by_subnet(filtered_ips)
        all_users_log[email] = subnet_ips
    
    return all_users_log


def test_cdn_scenario():
    """Test the CDN scenario with multiple IPs from the same subnet"""
    
    # Simulate the CDN scenario from the user's example
    cdn_ips = [
        '140.248.74.46', '140.248.74.171', '140.248.74.76', '140.248.74.56', '140.248.74.107',
        '140.248.74.126', '140.248.74.36', '140.248.74.28', '140.248.74.169', '140.248.74.129',
        '140.248.74.27', '140.248.74.89', '140.248.74.40', '140.248.74.131', '140.248.74.31',
        '140.248.74.170', '140.248.74.123', '140.248.74.67', '140.248.74.108', '140.248.74.162',
        '140.248.74.33', '140.248.74.20', '140.248.74.60', '140.248.74.84', '140.248.74.68',
        '140.248.74.168', '140.248.74.172', '140.248.74.32', '140.248.74.26', '140.248.74.164',
        '140.248.74.130', '140.248.74.97', '140.248.74.61', '140.248.74.100', '140.248.74.86',
        '140.248.74.166', '140.248.74.176', '140.248.74.69', '140.248.74.151', '140.248.74.174',
        '140.248.74.165', '140.248.74.142', '140.248.74.173', '140.248.74.122', '140.248.74.150',
        '140.248.74.39', '140.248.74.42', '140.248.74.149', '140.248.74.90', '140.248.74.34',
        '140.248.74.29', '140.248.74.74', '140.248.74.155', '140.248.74.37', '140.248.74.83',
        '140.248.74.139', '140.248.74.156', '140.248.74.48', '140.248.74.82', '140.248.74.115',
        '140.248.74.117', '140.248.74.92', '140.248.74.177', '140.248.74.73', '140.248.74.137',
        '140.248.74.54', '140.248.74.80', '140.248.74.24', '140.248.74.163', '140.248.74.104',
        '140.248.74.103', '140.248.74.143', '140.248.74.91', '140.248.74.141', '140.248.74.111',
        '140.248.74.120', '140.248.74.44', '140.248.74.77', '140.248.74.57', '140.248.74.124',
        '140.248.74.102', '140.248.74.79', '140.248.74.114', '140.248.74.119', '140.248.74.43',
        '140.248.74.87', '140.248.74.51', '140.248.74.158', '140.248.74.47', '140.248.74.75',
        '140.248.74.145', '140.248.74.93', '140.248.74.96', '140.248.74.94', '140.248.74.133',
        '140.248.74.134', '140.248.74.161', '140.248.74.30', '140.248.74.38', '140.248.74.85',
        '140.248.74.148', '140.248.74.144', '140.248.74.64', '140.248.74.41', '140.248.74.157',
        '140.248.74.154', '140.248.74.136', '140.248.74.128', '140.248.74.71', '140.248.74.50',
        '140.248.74.118', '140.248.74.49', '140.248.74.140', '140.248.74.62', '140.248.74.72',
        '140.248.74.175', '140.248.74.58', '140.248.74.78', '140.248.74.113', '140.248.74.125',
        '140.248.74.95', '140.248.74.153', '140.248.74.159', '140.248.74.63', '140.248.74.160',
        '140.248.74.25', '140.248.74.106', '140.248.74.88', '140.248.74.98', '140.248.74.135'
    ]
    
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
    if "MattDev" in result:
        user_subnets = result["MattDev"]
        print(f"User MattDev has {len(user_subnets)} subnet(s): {user_subnets}")
        
        # Verify that it's counted as 1 subnet instead of 130+ IPs
        if len(user_subnets) == 1 and "140.248.74.x" in user_subnets:
            print("✅ SUCCESS: CDN scenario handled correctly!")
            print("   - 130+ individual IPs are now counted as 1 subnet")
            print("   - This prevents false warnings about too many active IPs")
        else:
            print("❌ FAILED: CDN scenario not handled correctly")
    else:
        print("❌ FAILED: User not found in results")
    
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