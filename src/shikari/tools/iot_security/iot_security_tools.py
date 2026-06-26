# ShikariMCP — IoT Security Testing Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="binwalk_firmware_scan",
    category="iot_security",
    scope=ToolScope.LOCAL,
    binary="binwalk",
    description="Scan firmware files for embedded filesystems and signatures",
)
async def binwalk_firmware_scan(firmware: str) -> str:
    """
    Scan a firmware image for embedded filesystems and signatures using binwalk.

    Args:
        firmware: Path to firmware file
    """
    cmd = ["binwalk", firmware]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"binwalk error: {result.stderr}"


@shikari_tool(
    name="binwalk_firmware_extract",
    category="iot_security",
    scope=ToolScope.LOCAL,
    binary="binwalk",
    description="Extract filesystems from firmware images (recursive)",
)
async def binwalk_firmware_extract(firmware: str, outdir: str) -> str:
    """
    Extract embedded filesystems from a firmware image using binwalk.

    Args:
        firmware: Path to firmware file
        outdir: Output directory for extracted files
    """
    cmd = ["binwalk", "-e", "--matryoshka", "-C", outdir, firmware]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"binwalk error: {result.stderr}"


@shikari_tool(
    name="mqtt_subscribe",
    category="iot_security",
    scope=ToolScope.BOTH,
    binary="mosquitto_sub",
    description="Subscribe to an MQTT broker and capture messages",
)
async def mqtt_subscribe(broker: str, count: int = 100) -> str:
    """
    Subscribe to all topics on an MQTT broker and capture messages.

    Args:
        broker: MQTT broker hostname or IP address
        count: Maximum number of messages to receive (default 100)
    """
    broker = validate_target(broker)
    cmd = [
        "mosquitto_sub",
        "-h", broker,
        "-t", "#",
        "-v",
        "-C", str(count),
    ]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"mosquitto_sub error: {result.stderr}"


@shikari_tool(
    name="mqtt_publish_probe",
    category="iot_security",
    scope=ToolScope.BOTH,
    binary="mosquitto_pub",
    description="Publish a probe message to an MQTT topic",
)
async def mqtt_publish_probe(broker: str, topic: str, message: str) -> str:
    """
    Publish a message to a specific MQTT topic for probing.

    Args:
        broker: MQTT broker hostname or IP address
        topic: MQTT topic to publish to
        message: Message payload to publish
    """
    broker = validate_target(broker)
    cmd = [
        "mosquitto_pub",
        "-h", broker,
        "-t", topic,
        "-m", message,
        "-q", "2",
    ]
    result = await execute_command(cmd, timeout=30)
    return result.output if result.success else f"mosquitto_pub error: {result.stderr}"


@shikari_tool(
    name="iot_port_scan",
    category="iot_security",
    scope=ToolScope.BOTH,
    binary="nmap",
    description="Port scan targeting common IoT/SCADA protocols",
)
async def iot_port_scan(target: str) -> str:
    """
    Scan for common IoT and SCADA protocol ports on a target.

    Args:
        target: Target IP address or hostname
    """
    target = validate_target(target)
    cmd = [
        "nmap", "-sV",
        "-p", "23,502,1883,5683,47808,102,2404,4840",
        target,
    ]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"nmap error: {result.stderr}"
