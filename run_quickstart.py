#!/usr/bin/env python3
"""
Quickstart script for the Cybersecurity Framework
"""
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from agents.network_scanner.network_scanner_agent import NetworkScannerAgent
    except ImportError as e:
        print(f"❌ Error importing agent: {e}")
        print("Make sure you're running from the project root directory")
        sys.exit(1)
    
    # Load environment
    load_dotenv('.env.quickstart')
    
    console = Console()
    
    # Welcome message
    console.print(Panel.fit(
        "🚀 Cybersecurity Framework - Quickstart Demo\n"
        "Your first security agent is ready!",
        style="bold green"
    ))
    
    # Create the agent
    try:
        agent = NetworkScannerAgent()
        console.print("✅ Network Scanner Agent initialized successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Error creating agent: {e}", style="red")
        return
    
    # Interactive menu
    while True:
        console.print("\n" + "="*50)
        console.print("Choose an action:", style="bold cyan")
        console.print("1. Ping a host")
        console.print("2. Scan ports on a host")
        console.print("3. Full network summary")
        console.print("4. View scan history")
        console.print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            host = input("Enter hostname or IP address: ").strip()
            if host:
                console.print(f"\n🔍 Pinging {host}...")
                try:
                    result = agent.tool_registry.get_tool("ping_host")(host)
                    display_result(console, result)
                except Exception as e:
                    console.print(f"❌ Error: {e}", style="red")
        
        elif choice == '2':
            host = input("Enter hostname or IP address: ").strip()
            if host:
                console.print(f"\n🔍 Scanning ports on {host}...")
                try:
                    result = agent.tool_registry.get_tool("scan_ports")(host)
                    display_port_scan(console, result)
                except Exception as e:
                    console.print(f"❌ Error: {e}", style="red")
        
        elif choice == '3':
            host = input("Enter hostname or IP address: ").strip()
            if host:
                console.print(f"\n🔍 Performing network summary for {host}...")
                try:
                    result = agent.tool_registry.get_tool("network_summary")(host)
                    display_network_summary(console, result)
                except Exception as e:
                    console.print(f"❌ Error: {e}", style="red")
        
        elif choice == '4':
            console.print("\n📊 Scan History:")
            try:
                history = agent.tool_registry.get_tool("get_scan_history")()
                display_scan_history(console, history)
            except Exception as e:
                console.print(f"❌ Error: {e}", style="red")
        
        elif choice == '5':
            console.print("\n👋 Thanks for trying the Cybersecurity Framework!", style="bold green")
            break
        
        else:
            console.print("❌ Invalid choice. Please try again.", style="bold red")

def display_result(console, result):
    """Display a simple result"""
    console.print(json.dumps(result, indent=2))

def display_port_scan(console, result):
    """Display port scan results in a table"""
    table = Table(title=f"Port Scan Results for {result['host']}")
    table.add_column("Status", style="cyan")
    table.add_column("Ports", style="magenta")
    table.add_column("Count", style="green")
    
    open_ports_str = ", ".join(map(str, result['open_ports'])) if result['open_ports'] else "None"
    table.add_row("Open", open_ports_str, str(len(result['open_ports'])))
    table.add_row("Closed", f"{len(result['closed_ports'])} ports", str(len(result['closed_ports'])))
    
    console.print(table)

def display_network_summary(console, result):
    """Display network summary"""
    summary = result['summary']
    
    # Status panel
    status_color = "green" if summary['reachable'] else "red"
    status_text = "✅ Reachable" if summary['reachable'] else "❌ Not Reachable"
    
    console.print(Panel(
        f"Host: {result['host']}\n"
        f"Status: {status_text}\n"
        f"Open Ports: {summary['open_ports_count']}\n"
        f"Risk Level: {summary['risk_level'].upper()}",
        title="Network Summary",
        border_style=status_color
    ))

def display_scan_history(console, history):
    """Display scan history"""
    if not history:
        console.print("No scan history available.", style="yellow")
        return
    
    table = Table(title="Scan History")
    table.add_column("Host", style="cyan")
    table.add_column("Open Ports", style="green")
    table.add_column("Timestamp", style="blue")
    
    for scan in history:
        table.add_row(
            scan['host'],
            str(len(scan['open_ports'])),
            scan['timestamp'][:19]  # Truncate timestamp
        )
    
    console.print(table)

if __name__ == "__main__":
    main()
