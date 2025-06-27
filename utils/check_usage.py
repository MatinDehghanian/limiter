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
    config_data = await read_config()
    show_single_ip_users = config_data.get("SHOW_SINGLE_IP_USERS", True)
    all_users_log = {}
    for email in list(ACTIVE_USERS.keys()):
        data = ACTIVE_USERS[email]
        ip_counts = Counter(data.ip)
        # Filter IPs that appear more than 2 times
        filtered_ips = list({ip for ip in data.ip if ip_counts[ip] > 2})
        # Group IPs by subnet to handle CDN scenarios
        subnet_ips = group_ips_by_subnet(filtered_ips)
        all_users_log[email] = subnet_ips
        logger.info("User data: %s", data)
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
        if not ips:
            continue
        if not show_single_ip_users and len(ips) == 1:
            continue
        if len(ips) == 1:
            user_messages.append(
                (
                    f"<code>{email}</code> with <code>{len(ips)}</code> active ip: "
                    f"<code>{ips[0]}</code>"
                )
            )
        else:
            user_messages.append(
                (
                    f"<code>{email}</code> with <code>{len(ips)}</code> active ips:\n- "
                    + "\n- ".join(ips)
                )
            )
    logger.info("Number of all active ips: %s", str(total_ips))
    # Add total count
    summary_message = f"---------\nCount Of All Active IPs: <b>{total_ips}</b>"
    
    # Split messages into chunks to avoid Telegram's message length limit
    # Telegram has a 4096 character limit, so we'll be conservative with 3000 chars
    MAX_MESSAGE_LENGTH = 3000
    current_message = ""
    message_chunks = []
    
    # First, build the complete message
    complete_message = ""
    for user_msg in user_messages:
        if complete_message:
            complete_message += "\n\n" + user_msg
        else:
            complete_message = user_msg
    
    # Add summary
    complete_message += "\n\n" + summary_message
    
    # Debug logging
    logger.info("Complete message length: %s characters", len(complete_message))
    logger.info("Message length limit: %s characters", MAX_MESSAGE_LENGTH)
    
    # If message is under limit, send as single message
    if len(complete_message) <= MAX_MESSAGE_LENGTH:
        message_chunks = [complete_message]
        logger.info("Message is under limit - sending as single message")
    else:
        logger.info("Message exceeds limit - splitting into multiple parts")
        # Split into 2 or 3 parts
        total_length = len(complete_message)
        if total_length <= MAX_MESSAGE_LENGTH * 2:
            # Split into 2 parts
            split_point = total_length // 2
            # Find a good split point (end of a user entry)
            for i in range(split_point, min(split_point + 200, total_length)):
                if complete_message[i] == '\n' and i + 1 < total_length and complete_message[i + 1] == '\n':
                    split_point = i + 2
                    break
            
            message_chunks = [
                complete_message[:split_point].strip(),
                complete_message[split_point:].strip()
            ]
            logger.info("Split into 2 parts: %s and %s chars", len(message_chunks[0]), len(message_chunks[1]))
        else:
            # Split into 3 parts
            part_length = total_length // 3
            split_point1 = part_length
            split_point2 = part_length * 2
            
            # Find good split points (end of user entries)
            for i in range(split_point1, min(split_point1 + 200, total_length)):
                if complete_message[i] == '\n' and i + 1 < total_length and complete_message[i + 1] == '\n':
                    split_point1 = i + 2
                    break
            
            for i in range(split_point2, min(split_point2 + 200, total_length)):
                if complete_message[i] == '\n' and i + 1 < total_length and complete_message[i + 1] == '\n':
                    split_point2 = i + 2
                    break
            
            message_chunks = [
                complete_message[:split_point1].strip(),
                complete_message[split_point1:split_point2].strip(),
                complete_message[split_point2:].strip()
            ]
            logger.info("Split into 3 parts: %s, %s, and %s chars", len(message_chunks[0]), len(message_chunks[1]), len(message_chunks[2]))
    
    # Send all chunks
    for i, message in enumerate(message_chunks):
        if len(message_chunks) > 1:
            # Add part number to the top of each message when split
            message = f"<b>📋 Part {i+1} of {len(message_chunks)}</b>\n\n" + message
        else:
            message = "<b>Active Users:</b>\n\n" + message
        
        logger.info("Sending message part %d/%d (%d chars)", i + 1, len(message_chunks), len(message))
        try:
            await send_logs(message)
            # Add delay between messages to avoid rate limits
            if i < len(message_chunks) - 1:  # Don't delay after the last message
                await asyncio.sleep(2)  # Increased delay to 2 seconds
        except Exception as e:
            logger.error(f"Failed to send message part {i+1}: {e}")
    
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
