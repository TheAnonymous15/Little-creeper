import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psutil
import time
import socket
import uuid
import subprocess

# Email configuration
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_user = 'muthikedaniel59@gmail.com'
smtp_password = 'pjnf xrhf myqw gmha'
recipient_email = 'daniel.kinyua@tutamail.com'


def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ':'.join([mac[e:e + 2] for e in range(0, 11, 2)])


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def get_network_info():
    net_if_addrs = psutil.net_if_addrs()
    network_details = []
    for interface_name, interface_addresses in net_if_addrs.items():
        for address in interface_addresses:
            if str(address.family) == 'AddressFamily.AF_INET':
                ip_address = address.address
                net_if_stats = psutil.net_if_stats()
                if interface_name in net_if_stats:
                    is_up = net_if_stats[interface_name].isup
                    if is_up:
                        network_details.append((interface_name, ip_address))
    return network_details


def get_wifi_ssid():
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], capture_output=True, text=True)
        ssid_lines = result.stdout.splitlines()
        for line in ssid_lines:
            if line.startswith('yes:'):
                return line.split(':')[1]
    except Exception as e:
        print(f"Error fetching SSID: {e}")
    return None


def send_email(mac_address, ip_address, network_ssid):
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = 'Initial Network Configuration'

    body = f'Device {mac_address} identified as {ip_address} is connected to a network called {network_ssid}'
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, recipient_email, text)
        server.quit()
        print(f'Initial configuration email sent to {recipient_email}')
    except Exception as e:
        print(f'Failed to send initial configuration email: {str(e)}')


def main():
    last_ip_addresses = {}
    last_ssid = None

    # Send initial email with current configuration
    current_ssid = get_wifi_ssid()
    network_details = get_network_info()
    for interface_name, ip_address in network_details:
        mac_address = get_mac_address()
        send_email(mac_address, ip_address, current_ssid)
        last_ip_addresses[interface_name] = ip_address
        last_ssid = current_ssid

    while True:
        current_ssid = get_wifi_ssid()
        network_details = get_network_info()

        for interface_name, ip_address in network_details:
            mac_address = get_mac_address()
            if interface_name not in last_ip_addresses or ip_address != last_ip_addresses[
                interface_name] or current_ssid != last_ssid:
                print(f"Configuration change detected:")
                print(f"Previous: SSID={last_ssid}, IP={last_ip_addresses.get(interface_name)}")
                print(f"New: SSID={current_ssid}, IP={ip_address}")

                send_email(mac_address, ip_address, current_ssid)

                last_ip_addresses[interface_name] = ip_address
                last_ssid = current_ssid
        time.sleep(10)


if __name__ == "__main__":
    main()
