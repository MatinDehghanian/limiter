"""
This module checks if a user (name and IP address)
appears more than two times in the ACTIVE_USERS list.
"""

import asyncio
import ipaddress
from collections import Counter

from telegram_bot.send_message import send_logs
from utils.logs import logger
from utils.panel_api import disable_user
from utils.read_config import read_config
from utils.types import PanelType, UserType

ACTIVE_USERS: dict[str, UserType] | dict = {}


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


async def check_ip_used() -> dict:
    """
    This function checks if a user (name and IP address)
    appears more than two times in the ACTIVE_USERS list.
    """
    all_users_log = {}
    for email in list(ACTIVE_USERS.keys()):
        data = ACTIVE_USERS[email]
        ip_counts = Counter(data.ip)
        # Filter IPs that appear more than 2 times
        filtered_ips = list({ip for ip in data.ip if ip_counts[ip] > 2})
        
        # Group IPs by subnet to handle CDN scenarios
        subnet_ips = group_ips_by_subnet(filtered_ips)
        all_users_log[email] = subnet_ips
        logger.info(data)
    total_ips = sum(len(ips) for ips in all_users_log.values())
    all_users_log = dict(
        sorted(
            all_users_log.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )
    )
    
    # Create a more compact message format for better readability
    user_messages = []
    for email, ips in all_users_log.items():
        if ips:
            if len(ips) == 1:
                # Single subnet - show it inline
                user_messages.append(f"<code>{email}</code> with <code>{len(ips)}</code> active ip: <code>{ips[0]}</code>")
            else:
                # Multiple subnets - show them on separate lines
                user_messages.append(f"<code>{email}</code> with <code>{len(ips)}</code> active ips:\n- " + "\n- ".join(ips))
    
    logger.info("Number of all active ips: %s", str(total_ips))
    
    # Add total count
    summary_message = f"---------\nCount Of All Active IPs: <b>{total_ips}</b>"
    
    # Split messages into chunks to avoid Telegram's message length limit
    # Telegram has a 4096 character limit, so we'll be conservative with 3000 chars
    MAX_MESSAGE_LENGTH = 3000
    current_message = ""
    message_chunks = []
    
    for user_msg in user_messages:
        # Check if adding this user would exceed the limit
        if len(current_message) + len(user_msg) + 2 > MAX_MESSAGE_LENGTH:
            # Save current chunk and start a new one
            if current_message:
                message_chunks.append(current_message.strip())
            current_message = user_msg
        else:
            # Add to current chunk
            if current_message:
                current_message += "\n\n" + user_msg
            else:
                current_message = user_msg
    
    # Add the last chunk if it has content
    if current_message:
        message_chunks.append(current_message.strip())
    
    # Add summary to the last chunk
    if message_chunks:
        message_chunks[-1] += "\n\n" + summary_message
    
    # Send all chunks
    for i, message in enumerate(message_chunks):
        if i > 0:
            # Add header for subsequent chunks
            message = f"<b>Active Users (Part {i+1}):</b>\n\n" + message
        else:
            message = "<b>Active Users:</b>\n\n" + message
        await send_logs(message)
    
    return all_users_log


async def check_users_usage(panel_data: PanelType):
    """
    checks the usage of active users
    """
    config_data = await read_config()
    all_users_log = await check_ip_used()
    except_users = config_data.get("EXCEPT_USERS", [])
    special_limit = config_data.get("SPECIAL_LIMIT", {})
    limit_number = config_data["GENERAL_LIMIT"]
    for user_name, user_ip in all_users_log.items():
        if user_name not in except_users:
            user_limit_number = int(special_limit.get(user_name, limit_number))
            if len(set(user_ip)) > user_limit_number:
                message = (
                    f"User {user_name} has {str(len(set(user_ip)))}"
                    + f" active ips. {str(set(user_ip))}"
                )
                logger.warning(message)
                await send_logs(str("<b>Warning: </b>" + message))
                try:
                    await disable_user(panel_data, UserType(name=user_name, ip=[]))
                except ValueError as error:
                    print(error)
    ACTIVE_USERS.clear()
    all_users_log.clear()


async def run_check_users_usage(panel_data: PanelType) -> None:
    """run check_ip_used() function and then run check_users_usage()"""
    while True:
        await check_users_usage(panel_data)
        data = await read_config()
        await asyncio.sleep(int(data["CHECK_INTERVAL"]))
