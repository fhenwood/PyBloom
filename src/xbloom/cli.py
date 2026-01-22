import asyncio
import logging
import typer
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.logging import RichHandler
from typing import Optional

from .scanner import discover_devices
from xbloom import XBloomClient

app = typer.Typer(
    name="xbloom",
    help="CLI for XBloom Studio coffee maker",
    add_completion=False,
)
console = Console()

@app.command()
def scan(timeout: int = 5):
    """Scan for XBloom devices."""
    console.print(f"[bold blue]Scanning for XBloom devices ({timeout}s)...[/bold blue]")
    
    devices = asyncio.run(discover_devices(timeout=timeout))
    
    if not devices:
        console.print("[red]No devices found.[/red]")
        return

    table = Table(title="Discovered Devices")
    table.add_column("Name", style="cyan")
    table.add_column("Address", style="green")
    table.add_column("RSSI", style="magenta")

    for d in devices:
        table.add_row(
            d.name or "Unknown", 
            d.address, 
            str(getattr(d, "rssi", "N/A"))
        )
    
    console.print(table)

@app.command()
def monitor(address: str):
    """Connect to a device and monitor status."""
    async def _run():
        console.print(f"[bold green]Connecting to {address}...[/bold green]")
        client = XBloomClient(address)
        
        try:
            connected = await client.connect()
            if not connected:
                console.print("[red]Failed to connect.[/red]")
                return
            
            console.print("[green]Connected! Press Ctrl+C to exit.[/green]")
            
            # Create a live status table
            def generate_table():
                status = client.status
                table = Table(title=f"XBloom Status - {status.model}")
                
                table.add_column("Component", style="cyan")
                table.add_column("State", style="green")
                table.add_column("Value", style="yellow")
                
                table.add_row("Connection", "Online" if status.connected else "Offline", "")
                table.add_row("Brewer", "Running" if status.brewer.is_running else "Idle", f"{status.brewer.temperature:.1f} °C")
                table.add_row("Grinder", "Running" if status.grinder.is_running else "Idle", f"Pos: {status.grinder.position}")
                table.add_row("Scale", "-", f"{status.scale.weight:.2f} g")
                table.add_row("Water Lvl", "OK" if status.water_level_ok else "Low", "")
                
                return table
            
            with Live(generate_table(), refresh_per_second=4) as live:
                while True:
                    live.update(generate_table())
                    await asyncio.sleep(0.25)
                    
        except asyncio.CancelledError:
            pass
        finally:
            console.print("[bold red]Disconnecting...[/bold red]")
            await client.disconnect()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass

@app.command()
def bridge(
    broker: str = typer.Option("localhost", help="MQTT broker hostname"),
    port: int = typer.Option(1883, help="MQTT broker port"),
    username: Optional[str] = typer.Option(None, help="MQTT username"),
    password: Optional[str] = typer.Option(None, help="MQTT password"),
    device_name: str = typer.Option("xbloom", help="Device name for MQTT topics"),
    device_address: Optional[str] = typer.Option(None, help="XBloom device address (auto-discover if not specified)"),
    session_timeout: int = typer.Option(60, help="BLE session timeout in seconds"),
    telemetry_interval: int = typer.Option(5, help="Telemetry publishing interval in seconds"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Start MQTT bridge for Home Assistant integration."""

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
    )
    # Also set level for our modules
    logging.getLogger("xbloom").setLevel(log_level)

    try:
        from .bridge import XBloomMQTTBridge, BridgeConfig
    except ImportError:
        console.print("[red]MQTT bridge requires aiomqtt. Install with: pip install aiomqtt[/red]")
        raise typer.Exit(1)

    console.print("[bold blue]Starting XBloom MQTT Bridge...[/bold blue]")
    
    # Create configuration
    config = BridgeConfig(
        broker_host=broker,
        broker_port=port,
        username=username,
        password=password,
        device_name=device_name,
        device_address=device_address,
        session_timeout=session_timeout,
        telemetry_interval=telemetry_interval,
    )
    
    # Display configuration
    config_table = Table(title="Bridge Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("MQTT Broker", f"{broker}:{port}")
    config_table.add_row("Device Name", device_name)
    config_table.add_row("Device Address", device_address or "Auto-discover")
    config_table.add_row("Session Timeout", f"{session_timeout}s")
    config_table.add_row("Base Topic", f"xbloom/{device_name}")
    
    console.print(config_table)
    console.print("\n[yellow]Available MQTT Commands:[/yellow]")
    
    # Show available topics
    commands_table = Table()
    commands_table.add_column("Topic", style="cyan")
    commands_table.add_column("Payload Example", style="green")
    commands_table.add_column("Description", style="yellow")
    
    commands = [
        ("command/connect", "{}", "Connect to device"),
        ("command/disconnect", "{}", "Disconnect from device"),
        ("command/grind", '{"size": 50, "speed": 80}', "Start grinder"),
        ("command/brew", "{}", "Start brewing"),
        ("command/pour", '{"temperature": 93, "pattern": "spiral"}', "Manual pour"),
        ("command/scale/vibrate", "{}", "Vibrate scale"),
        ("command/scale/move", '{"direction": "left"}', "Move scale tray"),
        ("command/temperature", '{"celsius": 93.5}', "Set temperature"),
        ("command/recipe/execute", '{"recipe_object"}', "Execute recipe"),
        ("command/stop_all", "{}", "Emergency stop"),
    ]
    
    for topic, payload, description in commands:
        commands_table.add_row(f"xbloom/{device_name}/{topic}", payload, description)
    
    console.print(commands_table)
    console.print("\n[green]Press Ctrl+C to stop the bridge[/green]")
    
    # Start bridge
    async def _run_bridge():
        bridge = XBloomMQTTBridge(config)
        await bridge.start()
    
    try:
        asyncio.run(_run_bridge())
    except KeyboardInterrupt:
        console.print("\n[bold red]Bridge stopped by user[/bold red]")

if __name__ == "__main__":
    app()
