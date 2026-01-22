"""
Robust Bluetooth connection with automatic retry and process cleanup.
"""
import asyncio
import subprocess
import logging
import psutil
import os
from typing import Optional
from xbloom.connection.bleak_impl import BleakConnection

logger = logging.getLogger(__name__)


def kill_competing_processes(mac_address: str) -> int:
    """
    Find and kill Python processes that might be holding a BLE connection.

    Args:
        mac_address: The MAC address to check for

    Returns:
        Number of processes killed
    """
    killed_count = 0
    current_pid = os.getpid()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue

            # Check if it's a Python process
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(cmdline)

                    # Check if it's related to xbloom or BLE
                    if any(keyword in cmdline_str.lower() for keyword in
                           ['xbloom', 'bleak', mac_address.lower(), 'tea_', 'brew']):
                        logger.warning(f"Killing competing process: PID {proc.info['pid']} - {cmdline_str[:100]}")
                        proc.kill()
                        proc.wait(timeout=3)
                        killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass

    return killed_count


def bluetooth_disconnect(mac_address: str) -> bool:
    """
    Force disconnect a device using bluetoothctl.

    Args:
        mac_address: MAC address to disconnect

    Returns:
        True if disconnect command succeeded
    """
    try:
        result = subprocess.run(
            ['bluetoothctl', 'disconnect', mac_address],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'Successful' in result.stdout or result.returncode == 0:
            logger.info(f"Successfully disconnected {mac_address} via bluetoothctl")
            return True
        else:
            logger.debug(f"bluetoothctl disconnect output: {result.stdout}")
            return False
    except Exception as e:
        logger.debug(f"bluetoothctl disconnect failed: {e}")
        return False


async def robust_connect(
    mac_address: str,
    timeout: float = 15.0,
    max_retries: int = 3,
    cleanup_on_failure: bool = True
) -> Optional[BleakConnection]:
    """
    Robustly connect to a BLE device with automatic retry and process cleanup.

    Strategy:
    1. Try initial connection with timeout
    2. On failure, check for competing processes and kill them
    3. Force disconnect via bluetoothctl
    4. Retry connection
    5. Repeat up to max_retries times

    Args:
        mac_address: BLE MAC address to connect to
        timeout: Connection timeout in seconds (default 15s)
        max_retries: Maximum number of retry attempts (default 3)
        cleanup_on_failure: If True, kill competing processes on failure

    Returns:
        Connected BleakConnection, or None if all retries failed
    """
    connection = BleakConnection()

    for attempt in range(1, max_retries + 1):
        logger.info(f"Connection attempt {attempt}/{max_retries} to {mac_address} (timeout={timeout}s)")

        try:
            # Try to connect
            await connection.connect(mac_address, timeout=timeout)

            if connection.is_connected:
                logger.info(f"✓ Successfully connected on attempt {attempt}")
                return connection

        except Exception as e:
            logger.warning(f"Connection attempt {attempt} failed: {e}")

        # Connection failed - try cleanup before retrying
        if attempt < max_retries and cleanup_on_failure:
            logger.info("Connection failed, performing cleanup...")

            # Step 1: Kill competing Python processes
            killed = kill_competing_processes(mac_address)
            if killed > 0:
                logger.info(f"Killed {killed} competing process(es)")
                await asyncio.sleep(1.0)

            # Step 2: Force disconnect via bluetoothctl
            if bluetooth_disconnect(mac_address):
                await asyncio.sleep(2.0)

            # Step 3: Brief delay before retry
            logger.info(f"Retrying in 2 seconds...")
            await asyncio.sleep(2.0)

    logger.error(f"Failed to connect after {max_retries} attempts")
    return None


class RobustBleakConnection(BleakConnection):
    """
    BleakConnection with built-in robust connection logic.
    """

    async def connect(
        self,
        mac_address: str,
        timeout: float = 15.0,
        max_retries: int = 3,
        cleanup_on_failure: bool = True
    ) -> None:
        """
        Connect with automatic retry and cleanup.

        Args:
            mac_address: BLE MAC address
            timeout: Connection timeout per attempt
            max_retries: Maximum retry attempts
            cleanup_on_failure: Enable process cleanup on failure
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"Connection attempt {attempt}/{max_retries}")

            try:
                # Call parent connect method
                await super().connect(mac_address, timeout=timeout)

                if self.is_connected:
                    logger.info(f"✓ Connected on attempt {attempt}")
                    return

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")

            # Cleanup and retry logic
            if attempt < max_retries and cleanup_on_failure:
                logger.info("Performing cleanup before retry...")

                killed = kill_competing_processes(mac_address)
                if killed > 0:
                    await asyncio.sleep(1.0)

                bluetooth_disconnect(mac_address)
                await asyncio.sleep(2.0)

                logger.info("Retrying...")

        raise ConnectionError(f"Failed to connect to {mac_address} after {max_retries} attempts")
