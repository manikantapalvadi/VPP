import subprocess
import time
from prometheus_client import start_http_server, Counter, Gauge

# Prometheus Metrics Definitions
vpp_requests_total = Counter("vpp_app_requests_total", "Total number of requests sent to VPP")
vpp_ping_success_total = Counter("vpp_app_ping_success_total", "Total successful ping responses from VPP")
vpp_ping_failure_total = Counter("vpp_app_ping_failure_total", "Total failed ping responses from VPP")
rx_packets = Gauge("vpp_rx_packets", "Total received packets on VPP interfaces", ["interface"])
tx_packets = Gauge("vpp_tx_packets", "Total transmitted packets on VPP interfaces", ["interface"])
routes_total = Gauge("vpp_routes_total", "Total number of routes in VPP")
tcp_sessions = Gauge("vpp_tcp_sessions", "Number of TCP sessions in VPP")
udp_sessions = Gauge("vpp_udp_sessions", "Number of UDP sessions in VPP")

# Helper Function: Run VPPCLI Commands
def run_command(command):
    try:
        result = subprocess.check_output(command, stderr=subprocess.PIPE)
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return ""

# Function to Ping from Host to VPP
def send_ping():
    vpp_requests_total.inc()
    response = run_command(["ping", "-c", "1", "10.10.1.2"])
    if "1 received" in response:
        vpp_ping_success_total.inc()
    else:
        vpp_ping_failure_total.inc()

# Function to Fetch Interface Stats
def fetch_interface_stats():
    output = run_command(["sudo", "vppctl", "show", "interface"])
    for line in output.splitlines():
        if "host-" in line:  # Filter interfaces starting with "host-"
            parts = line.split()
            interface_name = parts[0]
            rx = int(parts[4])
            tx = int(parts[5])
            rx_packets.labels(interface=interface_name).set(rx)
            tx_packets.labels(interface=interface_name).set(tx)

# Function to Fetch Routes
def fetch_routes():
    output = run_command(["sudo", "vppctl", "show", "ip", "fib"])
    total_routes = len([line for line in output.splitlines() if "/" in line])
    routes_total.set(total_routes)

# Function to Fetch Session Data
def fetch_sessions():
    output = run_command(["sudo", "vppctl", "show", "session"])
    tcp_count = sum(1 for line in output.splitlines() if "TCP" in line)
    udp_count = sum(1 for line in output.splitlines() if "UDP" in line)
    tcp_sessions.set(tcp_count)
    udp_sessions.set(udp_count)

# Main App Loop
if __name__ == "__main__":
    # Start the Prometheus HTTP server
    start_http_server(8000)
    print("Prometheus server started on port 8000")
    
    # Periodic Metric Updates
    while True:
        send_ping()  # Simulate ping requests
        fetch_interface_stats()  # Collect interface metrics
        fetch_routes()  # Collect route metrics
       # fetch_sessions()  # Collect session metrics
        time.sleep(10)  # Scrape every 10 seconds

