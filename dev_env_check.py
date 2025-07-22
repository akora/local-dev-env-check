#!/usr/bin/env python3
"""
Local Development Environment Checker
Checks various files, tools, and configurations on the local dev machine.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class DevEnvChecker:
    def __init__(self):
        self.results = []
        self.custom_hosts_entries = []
        
    def add_result(self, category: str, item: str, status: str, details: str = ""):
        """Add a check result to the results list"""
        self.results.append({
            'category': category,
            'item': item,
            'status': status,
            'details': details
        })
    
    def print_status(self, status: str) -> str:
        """Return colored status indicator"""
        if status == "OK":
            return f"{Colors.GREEN}✅ OK{Colors.END}"
        elif status == "MISSING":
            return f"{Colors.RED}❌ MISSING{Colors.END}"
        elif status == "ERROR":
            return f"{Colors.RED}❌ ERROR{Colors.END}"
        elif status == "WARNING":
            return f"{Colors.YELLOW}⚠️  WARNING{Colors.END}"
        else:
            return f"{Colors.BLUE}ℹ️  {status}{Colors.END}"
    
    def check_file_exists(self, filepath: str, category: str, description: str):
        """Check if a file exists"""
        expanded_path = os.path.expanduser(filepath)
        if os.path.exists(expanded_path):
            # Get file size for additional info
            size = os.path.getsize(expanded_path)
            self.add_result(category, description, "OK", f"Size: {size} bytes")
        else:
            self.add_result(category, description, "MISSING", f"Path: {expanded_path}")
    
    def check_command_exists(self, command: str, category: str, description: str):
        """Check if a command exists and is executable"""
        try:
            result = subprocess.run(['which', command], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                self.add_result(category, description, "OK", f"Path: {path}")
                return True
            else:
                self.add_result(category, description, "MISSING", "Command not found")
                return False
        except Exception as e:
            self.add_result(category, description, "ERROR", str(e))
            return False
    
    def check_command_version(self, command: str, category: str, description: str, version_flag: str = "--version"):
        """Check command version"""
        if not self.check_command_exists(command, category, f"{description} (installed)"):
            return
        
        try:
            result = subprocess.run([command, version_flag], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]  # First line usually contains version
                self.add_result(category, f"{description} (version)", "OK", version)
            else:
                self.add_result(category, f"{description} (version)", "ERROR", result.stderr.strip())
        except subprocess.TimeoutExpired:
            self.add_result(category, f"{description} (version)", "ERROR", "Command timeout")
        except Exception as e:
            self.add_result(category, f"{description} (version)", "ERROR", str(e))
    
    def check_aws_credentials_file(self):
        """Analyze AWS credentials file for profiles"""
        aws_creds_path = os.path.expanduser("~/.aws/credentials")
        
        if not os.path.exists(aws_creds_path):
            self.add_result("AWS", "Credentials file", "MISSING", f"Path: {aws_creds_path}")
            return
        
        try:
            with open(aws_creds_path, 'r') as f:
                content = f.read()
            
            # Parse profiles from credentials file
            profiles = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    profile_name = line[1:-1]  # Remove brackets
                    profiles.append(profile_name)
            
            # Create summary
            if profiles:
                if len(profiles) == 1:
                    summary = f"Profiles: 1 ({profiles[0]})"
                elif len(profiles) <= 5:
                    profile_list = ', '.join(profiles)
                    summary = f"Profiles: {len(profiles)} ({profile_list})"
                else:
                    summary = f"Profiles: {len(profiles)}"
                
                self.add_result("AWS", "Credentials file", "OK", summary)
            else:
                self.add_result("AWS", "Credentials file", "WARNING", "No profiles found")
            
        except PermissionError:
            self.add_result("AWS", "Credentials file", "ERROR", "Permission denied")
        except Exception as e:
            self.add_result("AWS", "Credentials file", "ERROR", f"Failed to parse: {str(e)}")
    
    def check_aws_config_file(self):
        """Analyze AWS config file for regions and settings"""
        aws_config_path = os.path.expanduser("~/.aws/config")
        
        if not os.path.exists(aws_config_path):
            self.add_result("AWS", "Config file", "MISSING", f"Path: {aws_config_path}")
            return
        
        try:
            with open(aws_config_path, 'r') as f:
                content = f.read()
            
            # Parse config settings
            lines = content.split('\n')
            default_region = None
            default_output = None
            regions = set()
            profiles = []
            
            current_profile = None
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    profile_name = line[1:-1]  # Remove brackets
                    if profile_name.startswith('profile '):
                        profile_name = profile_name[8:]  # Remove 'profile ' prefix
                    current_profile = profile_name
                    profiles.append(profile_name)
                elif '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'region':
                        regions.add(value)
                        if current_profile == 'default' or default_region is None:
                            default_region = value
                    elif key == 'output' and current_profile == 'default':
                        default_output = value
            
            # Create summary
            summary_parts = []
            
            if default_region:
                summary_parts.append(f"Region: {default_region}")
            
            if default_output:
                summary_parts.append(f"Output: {default_output}")
            
            if len(regions) > 1:
                summary_parts.append(f"Multiple regions: {len(regions)}")
            
            if len(profiles) > 1:
                summary_parts.append(f"Profiles: {len(profiles)}")
            
            if summary_parts:
                summary = ", ".join(summary_parts)
                self.add_result("AWS", "Config file", "OK", summary)
            else:
                self.add_result("AWS", "Config file", "OK", "Basic configuration")
            
        except PermissionError:
            self.add_result("AWS", "Config file", "ERROR", "Permission denied")
        except Exception as e:
            self.add_result("AWS", "Config file", "ERROR", f"Failed to parse: {str(e)}")
    
    def check_aws_credentials(self):
        """Check AWS credentials and connectivity with intelligent analysis"""
        # Analyze credentials file
        self.check_aws_credentials_file()
        
        # Analyze config file
        self.check_aws_config_file()
        
        # Test AWS CLI connectivity
        if self.check_command_exists("aws", "AWS", "AWS CLI"):
            try:
                result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    identity = json.loads(result.stdout)
                    user_info = identity.get('Arn', 'Unknown user')
                    self.add_result("AWS", "API connectivity", "OK", user_info)
                else:
                    self.add_result("AWS", "API connectivity", "ERROR", result.stderr.strip())
            except subprocess.TimeoutExpired:
                self.add_result("AWS", "API connectivity", "ERROR", "Request timeout")
            except Exception as e:
                self.add_result("AWS", "API connectivity", "ERROR", str(e))
    
    def check_gcp_credentials_file(self):
        """Analyze GCP application credentials file"""
        gcp_creds_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
        
        if not os.path.exists(gcp_creds_path):
            self.add_result("GCP", "Application credentials", "MISSING", f"Path: {gcp_creds_path}")
            return
        
        try:
            with open(gcp_creds_path, 'r') as f:
                creds_data = json.load(f)
            
            # Extract useful information
            summary_parts = []
            
            # Credential type
            cred_type = creds_data.get('type', 'unknown')
            if cred_type == 'authorized_user':
                summary_parts.append("Type: User")
            elif cred_type == 'service_account':
                summary_parts.append("Type: Service Account")
            else:
                summary_parts.append(f"Type: {cred_type}")
            
            # Project ID (quota_project_id is the active project)
            project_id = creds_data.get('quota_project_id') or creds_data.get('project_id')
            if project_id:
                summary_parts.append(f"Project: {project_id}")
            
            # Universe domain (for specialized GCP environments)
            universe = creds_data.get('universe_domain', 'googleapis.com')
            if universe != 'googleapis.com':
                summary_parts.append(f"Domain: {universe}")
            
            # Service account email (if service account)
            if cred_type == 'service_account':
                client_email = creds_data.get('client_email')
                if client_email:
                    summary_parts.append(f"SA: {client_email.split('@')[0]}")
            
            if summary_parts:
                summary = ", ".join(summary_parts)
                self.add_result("GCP", "Application credentials", "OK", summary)
            else:
                self.add_result("GCP", "Application credentials", "OK", "Valid credentials")
            
        except json.JSONDecodeError:
            self.add_result("GCP", "Application credentials", "ERROR", "Invalid JSON format")
        except PermissionError:
            self.add_result("GCP", "Application credentials", "ERROR", "Permission denied")
        except Exception as e:
            self.add_result("GCP", "Application credentials", "ERROR", f"Failed to parse: {str(e)}")
    
    def check_gcp_credentials(self):
        """Check Google Cloud credentials and connectivity with intelligent analysis"""
        # Analyze application credentials
        self.check_gcp_credentials_file()
        
        # Test gcloud connectivity
        if self.check_command_exists("gcloud", "GCP", "gcloud CLI"):
            try:
                result = subprocess.run(['gcloud', 'auth', 'list', '--format=json'], 
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    accounts = json.loads(result.stdout)
                    active_accounts = [acc for acc in accounts if acc.get('status') == 'ACTIVE']
                    if active_accounts:
                        account = active_accounts[0]['account']
                        self.add_result("GCP", "Authentication", "OK", f"Active: {account}")
                    else:
                        self.add_result("GCP", "Authentication", "WARNING", "No active accounts")
                else:
                    self.add_result("GCP", "Authentication", "ERROR", result.stderr.strip())
            except subprocess.TimeoutExpired:
                self.add_result("GCP", "Authentication", "ERROR", "Request timeout")
            except Exception as e:
                self.add_result("GCP", "Authentication", "ERROR", str(e))
    
    def check_digitalocean_credentials(self):
        """Check DigitalOcean credentials with smart detection"""
        # Smart detection for doctl config
        self.check_doctl_config_smart()
        
        # Test doctl connectivity
        if self.check_command_exists("doctl", "DigitalOcean", "doctl CLI"):
            try:
                result = subprocess.run(['doctl', 'account', 'get'], 
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    self.add_result("DigitalOcean", "API connectivity", "OK", "Account accessible")
                else:
                    self.add_result("DigitalOcean", "API connectivity", "ERROR", result.stderr.strip())
            except subprocess.TimeoutExpired:
                self.add_result("DigitalOcean", "API connectivity", "ERROR", "Request timeout")
            except Exception as e:
                self.add_result("DigitalOcean", "API connectivity", "ERROR", str(e))
    
    def check_ansible_config_smart(self):
        """Smart detection for Ansible configuration files"""
        # Check project-local first (highest priority)
        if os.path.exists('./ansible.cfg'):
            self.add_result("Ansible", "Config file", "OK", "Project: ./ansible.cfg")
        # Check user home directory
        elif os.path.exists(os.path.expanduser('~/.ansible.cfg')):
            self.add_result("Ansible", "Config file", "OK", "User: ~/.ansible.cfg")
        else:
            self.add_result("Ansible", "Config file", "MISSING", "No project or user config found")
        
        # Check system-wide config (separate check)
        if os.path.exists('/etc/ansible/ansible.cfg'):
            self.add_result("Ansible", "Global config", "OK", "System: /etc/ansible/ansible.cfg")
        else:
            self.add_result("Ansible", "Global config", "MISSING", "Path: /etc/ansible/ansible.cfg")
    
    def check_doctl_config_smart(self):
        """Smart detection for DigitalOcean doctl configuration files"""
        # Project-specific locations to check
        project_configs = [
            './doctl.yaml',
            './.doctl/config.yaml',
            './config/doctl.yaml'
        ]
        
        # Check for project-specific config first
        project_found = False
        for config_path in project_configs:
            if os.path.exists(config_path):
                self.add_result("DigitalOcean", "Config file", "OK", f"Project: {config_path}")
                project_found = True
                break
        
        # Check global config if no project config found
        if not project_found:
            global_config = os.path.expanduser('~/.config/doctl/config.yaml')
            if os.path.exists(global_config):
                self.add_result("DigitalOcean", "Config file", "OK", "Global: ~/.config/doctl/config.yaml")
            else:
                self.add_result("DigitalOcean", "Config file", "MISSING", "No project or global config found")
    
    def check_ssh_config(self):
        """Check and parse SSH configuration"""
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        
        if not os.path.exists(ssh_config_path):
            self.add_result("SSH", "SSH config", "MISSING", f"Path: {ssh_config_path}")
            return
        
        try:
            with open(ssh_config_path, 'r') as f:
                content = f.read()
            
            # Parse SSH config for key settings
            lines = content.split('\n')
            hosts = []
            global_settings = {}
            current_host = None
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.lower().startswith('host '):
                    host_name = line.split(None, 1)[1]
                    if host_name != '*':  # Skip global host patterns for counting
                        hosts.append(host_name)
                    current_host = host_name
                elif current_host is None:  # Global settings
                    if ' ' in line:
                        key, value = line.split(None, 1)
                        global_settings[key.lower()] = value
            
            # Create simple summary - just host count
            if hosts:
                summary = f"Hosts: {len(hosts)}"
            else:
                summary = "No hosts configured"
            
            self.add_result("SSH", "SSH config", "OK", summary)
            
        except Exception as e:
            self.add_result("SSH", "SSH config", "ERROR", f"Failed to parse: {str(e)}")
    
    def check_ssh_known_hosts(self):
        """Check and parse SSH known hosts"""
        known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
        
        if not os.path.exists(known_hosts_path):
            self.add_result("SSH", "Known hosts", "MISSING", f"Path: {known_hosts_path}")
            return
        
        try:
            with open(known_hosts_path, 'r') as f:
                lines = f.readlines()
            
            # Parse known hosts
            hosts = set()
            key_types = {}
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 3:
                    host_part = parts[0]
                    key_type = parts[1]
                    
                    # Extract hostname (handle hashed hosts)
                    if host_part.startswith('|1|'):
                        hosts.add('[hashed]')
                    else:
                        # Handle comma-separated hosts and ports
                        for host in host_part.split(','):
                            # Remove port numbers and brackets
                            clean_host = host.split(':')[0].strip('[]')
                            if clean_host:
                                hosts.add(clean_host)
                    
                    # Count key types
                    key_types[key_type] = key_types.get(key_type, 0) + 1
            
            # Create simple summary - just entry count
            non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            summary = f"Entries: {len(non_empty_lines)}"
            
            self.add_result("SSH", "Known hosts", "OK", summary)
            
        except Exception as e:
            self.add_result("SSH", "Known hosts", "ERROR", f"Failed to parse: {str(e)}")
    
    def check_ssh_keys(self):
        """Check SSH keys in .ssh directory"""
        ssh_dir = os.path.expanduser("~/.ssh")
        
        if not os.path.exists(ssh_dir):
            self.add_result("SSH Keys", "SSH directory", "MISSING", f"Path: {ssh_dir}")
            return
        
        if not os.access(ssh_dir, os.R_OK):
            self.add_result("SSH Keys", "SSH directory", "WARNING", f"Permission denied: {ssh_dir}")
            return
        
        try:
            # Common SSH key patterns
            key_patterns = [
                'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
                'id_rsa_*', 'id_dsa_*', 'id_ecdsa_*', 'id_ed25519_*'
            ]
            
            found_keys = []
            warnings = []
            
            # Get all files in .ssh directory
            try:
                ssh_files = os.listdir(ssh_dir)
            except PermissionError as e:
                self.add_result("SSH Keys", "SSH directory", "WARNING", f"Permission denied: {str(e)}")
                return
            
            # Find potential private key files (no .pub extension)
            private_key_files = [f for f in ssh_files if not f.endswith('.pub') and not f.startswith('.') 
                               and os.path.isfile(os.path.join(ssh_dir, f))]
            
            for key_file in private_key_files:
                key_path = os.path.join(ssh_dir, key_file)
                pub_path = key_path + '.pub'
                
                # Only include keys that have corresponding .pub files
                if os.path.exists(pub_path):
                    try:
                        # Try to determine key type by reading the public key
                        with open(pub_path, 'r') as f:
                            pub_content = f.read().strip()
                        
                        key_type = "Unknown"
                        if pub_content.startswith('ssh-rsa '):
                            key_type = "RSA"
                        elif pub_content.startswith('ssh-dss '):
                            key_type = "DSA"
                        elif pub_content.startswith('ecdsa-sha2-'):
                            key_type = "ECDSA"
                        elif pub_content.startswith('ssh-ed25519 '):
                            key_type = "ED25519"
                        
                        found_keys.append({
                            'name': key_file,
                            'type': key_type,
                            'has_public': True
                        })
                        
                    except Exception as e:
                        warnings.append(f"Could not read {key_file}: {str(e)}")
            
            # Create summary
            if found_keys:
                key_types = [key['type'] for key in found_keys]
                type_counts = {}
                for kt in key_types:
                    type_counts[kt] = type_counts.get(kt, 0) + 1
                
                summary_parts = [f"{count} {ktype}" for ktype, count in type_counts.items()]
                summary = f"Found {len(found_keys)} keys: {', '.join(summary_parts)}"
                
                if warnings:
                    summary += f" (Warnings: {len(warnings)})"
                
                details = summary
                if warnings:
                    details += f"\nWarnings: {'; '.join(warnings)}"
                
                self.add_result("SSH Keys", "SSH keys", "OK", details)
            else:
                if warnings:
                    self.add_result("SSH Keys", "SSH keys", "WARNING", f"No valid key pairs found. Warnings: {'; '.join(warnings)}")
                else:
                    self.add_result("SSH Keys", "SSH keys", "INFO", "No SSH key pairs found")
        
        except Exception as e:
            self.add_result("SSH Keys", "SSH keys", "ERROR", f"Failed to check SSH keys: {str(e)}")
    
    def check_hosts_file(self):
        """Check /etc/hosts file and identify non-standard entries"""
        hosts_path = "/etc/hosts"
        
        if not os.path.exists(hosts_path):
            self.add_result("System", "/etc/hosts", "MISSING", "File not found")
            return
        
        try:
            with open(hosts_path, 'r') as f:
                lines = f.readlines()
            
            # Standard entries that are typically found in /etc/hosts
            standard_entries = {
                '127.0.0.1': ['localhost'],
                '::1': ['localhost'],
                '255.255.255.255': ['broadcasthost'],
                'fe80::1%lo0': ['localhost']
            }
            
            custom_entries = []
            total_entries = 0
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse the line
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                ip = parts[0]
                hostnames = parts[1:]
                total_entries += 1
                
                # Check if this is a standard entry
                is_standard = False
                if ip in standard_entries:
                    # Check if hostnames match standard ones
                    expected_hostnames = standard_entries[ip]
                    if set(hostnames).issubset(set(expected_hostnames)):
                        is_standard = True
                
                # If not standard, add to custom entries
                if not is_standard:
                    custom_entries.append({
                        'ip': ip,
                        'hostnames': hostnames
                    })
            
            # Create summary
            if custom_entries:
                custom_count = len(custom_entries)
                if custom_count <= 5:  # Show details if reasonable number
                    custom_list = []
                    for entry in custom_entries[:5]:
                        hostnames_str = ', '.join(entry['hostnames'])
                        custom_list.append(f"{entry['ip']} -> {hostnames_str}")
                    summary = f"Total: {total_entries}, Custom: {custom_count} ({'; '.join(custom_list)})"
                else:
                    summary = f"Total: {total_entries}, Custom: {custom_count} entries"
                
                self.add_result("System", "/etc/hosts", "OK", summary)
            else:
                summary = f"Total: {total_entries}, Standard entries only"
                self.add_result("System", "/etc/hosts", "OK", summary)
            
            # Store custom entries for detailed display
            self.custom_hosts_entries = custom_entries
            
        except PermissionError:
            self.add_result("System", "/etc/hosts", "ERROR", "Permission denied")
        except Exception as e:
            self.add_result("System", "/etc/hosts", "ERROR", f"Failed to parse: {str(e)}")
    
    def print_ssh_config_details(self):
        """Print detailed SSH configuration table"""
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        
        if not os.path.exists(ssh_config_path):
            return
        
        try:
            with open(ssh_config_path, 'r') as f:
                content = f.read()
            
            # Parse SSH config for detailed host information
            lines = content.split('\n')
            hosts_config = {}
            current_host = None
            global_settings = {}
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.lower().startswith('host '):
                    current_host = line.split(None, 1)[1]
                    if current_host not in hosts_config:
                        hosts_config[current_host] = {}
                elif current_host and ' ' in line:
                    key, value = line.split(None, 1)
                    hosts_config[current_host][key.lower()] = value
                elif current_host is None and ' ' in line:  # Global settings
                    key, value = line.split(None, 1)
                    global_settings[key.lower()] = value
            
            if hosts_config:
                print(f"\n{Colors.BOLD}🔧 SSH Configuration Details{Colors.END}")
                print("=" * 100)
                print(f"{Colors.BOLD}{'Host':<20} {'Hostname':<25} {'User':<15} {'Port':<8} {'Other Settings':<30}{Colors.END}")
                print("-" * 100)
                
                for host, config in hosts_config.items():
                    if host == '*':  # Skip global patterns
                        continue
                    
                    hostname = config.get('hostname', '')
                    user = config.get('user', '')
                    port = config.get('port', '22')
                    
                    # Collect other interesting settings
                    other_settings = []
                    for key in ['identityfile', 'forwardagent', 'compression']:
                        if key in config:
                            value = config[key]
                            if key == 'identityfile':
                                value = value.split('/')[-1]  # Just filename
                            other_settings.append(f"{key.title()}: {value}")
                    
                    other_str = ', '.join(other_settings[:2])  # Limit to avoid overflow
                    if len(other_settings) > 2:
                        other_str += '...'
                    
                    print(f"{host:<20} {hostname:<25} {user:<15} {port:<8} {other_str:<30}")
            
        except Exception as e:
            print(f"Error parsing SSH config: {e}")
    
    def print_known_hosts_details(self):
        """Print detailed known hosts table"""
        known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
        
        if not os.path.exists(known_hosts_path):
            return
        
        try:
            with open(known_hosts_path, 'r') as f:
                lines = f.readlines()
            
            # Parse known hosts for detailed information
            host_entries = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 3:
                    host_part = parts[0]
                    key_type = parts[1]
                    # Extract hostname (handle hashed hosts)
                    if host_part.startswith('|1|'):
                        display_host = '[hashed]'
                    else:
                        # Handle comma-separated hosts and ports
                        hosts = []
                        for host in host_part.split(','):
                            # Remove port numbers and brackets
                            clean_host = host.split(':')[0].strip('[]')
                            if clean_host:
                                hosts.append(clean_host)
                        display_host = ', '.join(hosts[:2])  # Show max 2 hosts
                        if len(hosts) > 2:
                            display_host += f' (+{len(hosts)-2} more)'
                    
                    host_entries.append({
                        'host': display_host,
                        'key_type': key_type
                    })
            
            if host_entries:
                print(f"\n{Colors.BOLD}🔑 SSH Known Hosts Details{Colors.END}")
                print("=" * 65)
                print(f"{Colors.BOLD}{'Host/IP':<40} {'Key Type':<25}{Colors.END}")
                print("-" * 65)
                
                # Sort by host for better readability
                host_entries.sort(key=lambda x: x['host'])
                
                for entry in host_entries:
                    print(f"{entry['host']:<40} {entry['key_type']:<25}")
            
        except Exception as e:
            print(f"Error parsing known hosts: {e}")
    
    def print_hosts_details(self):
        """Print detailed /etc/hosts custom entries table"""
        if not hasattr(self, 'custom_hosts_entries') or not self.custom_hosts_entries:
            return
        
        print(f"\n{Colors.BOLD}🏠 /etc/hosts Custom Entries{Colors.END}")
        print("=" * 70)
        print(f"{Colors.BOLD}{'IP Address':<20} {'Hostnames':<50}{Colors.END}")
        print("-" * 70)
        
        for entry in self.custom_hosts_entries:
            hostnames_str = ', '.join(entry['hostnames'])
            # Truncate if too long
            if len(hostnames_str) > 48:
                hostnames_str = hostnames_str[:45] + '...'
            print(f"{entry['ip']:<20} {hostnames_str:<50}")
    
    def print_ssh_keys_details(self):
        """Print detailed SSH keys table"""
        ssh_dir = os.path.expanduser("~/.ssh")
        
        if not os.path.exists(ssh_dir) or not os.access(ssh_dir, os.R_OK):
            return
        
        try:
            found_keys = []
            
            # Get all files in .ssh directory
            ssh_files = os.listdir(ssh_dir)
            
            # Find potential private key files (no .pub extension)
            private_key_files = [f for f in ssh_files if not f.endswith('.pub') and not f.startswith('.') 
                               and os.path.isfile(os.path.join(ssh_dir, f))]
            
            for key_file in private_key_files:
                key_path = os.path.join(ssh_dir, key_file)
                pub_path = key_path + '.pub'
                
                # Only include keys that have corresponding .pub files
                if os.path.exists(pub_path):
                    try:
                        # Try to determine key type by reading the public key
                        with open(pub_path, 'r') as f:
                            pub_content = f.read().strip()
                        
                        key_type = "Unknown"
                        key_details = ""
                        
                        if pub_content.startswith('ssh-rsa '):
                            key_type = "RSA"
                            # Extract key size for RSA keys
                            try:
                                import base64
                                key_data = pub_content.split()[1]
                                decoded = base64.b64decode(key_data)
                                # RSA key size extraction is complex, simplified here
                                key_details = "RSA key"
                            except:
                                key_details = "RSA key"
                        elif pub_content.startswith('ssh-dss '):
                            key_type = "DSA"
                            key_details = "DSA key"
                        elif pub_content.startswith('ecdsa-sha2-'):
                            key_type = "ECDSA"
                            if 'nistp256' in pub_content:
                                key_details = "ECDSA 256-bit"
                            elif 'nistp384' in pub_content:
                                key_details = "ECDSA 384-bit"
                            elif 'nistp521' in pub_content:
                                key_details = "ECDSA 521-bit"
                            else:
                                key_details = "ECDSA key"
                        elif pub_content.startswith('ssh-ed25519 '):
                            key_type = "ED25519"
                            key_details = "ED25519 256-bit"
                        
                        # Get file modification time for creation info
                        import time
                        mtime = os.path.getmtime(key_path)
                        created = time.strftime('%Y-%m-%d', time.localtime(mtime))
                        
                        found_keys.append({
                            'name': key_file,
                            'type': key_type,
                            'details': key_details,
                            'created': created,
                            'has_public': True
                        })
                        
                    except Exception:
                        # Skip problematic keys silently in details view
                        continue
            
            if found_keys:
                print(f"\n{Colors.BOLD}🔐 SSH Keys Details{Colors.END}")
                print("=" * 100)
                print(f"{Colors.BOLD}{'Key Name':<25} {'Type':<15} {'Details':<20} {'Created':<15} {'Public Key':<10}{Colors.END}")
                print("-" * 100)
                
                # Sort by key name for better readability
                found_keys.sort(key=lambda x: x['name'])
                
                for key in found_keys:
                    public_status = "✅ Yes" if key['has_public'] else "❌ No"
                    print(f"{key['name']:<25} {key['type']:<15} {key['details']:<20} {key['created']:<15} {public_status:<10}")
            
        except Exception as e:
            print(f"Error displaying SSH keys details: {e}")
    
    def run_all_checks(self):
        """Run all environment checks"""
        print(f"{Colors.BOLD}🔍 Local Development Environment Check{Colors.END}\n")
        
        # File checks
        print("Checking system files...")
        self.check_hosts_file()
        
        # SSH configuration checks
        print("Checking SSH configuration...")
        self.check_ssh_config()
        self.check_ssh_known_hosts()
        self.check_ssh_keys()
        
        # Command line tools
        print("Checking command line tools...")
        self.check_command_version("git", "Tools", "Git")
        self.check_command_version("docker", "Tools", "Docker")
        self.check_command_version("ansible", "Ansible", "Ansible")
        self.check_command_version("terraform", "Terraform", "Terraform")
        
        # Cloud provider checks
        print("Checking cloud providers...")
        self.check_aws_credentials()
        self.check_gcp_credentials()
        self.check_digitalocean_credentials()
        
        # Ansible specific checks
        print("Checking Ansible configuration...")
        self.check_ansible_config_smart()
        
        # Terraform specific checks
        print("Checking Terraform configuration...")
        if self.check_command_exists("terraform", "Terraform", "Terraform CLI"):
            try:
                result = subprocess.run(['terraform', 'version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Take only the first line and clean it up
                    version_info = result.stdout.strip().split('\n')[0]
                    self.add_result("Terraform", "Version check", "OK", version_info)
            except Exception as e:
                self.add_result("Terraform", "Version check", "ERROR", str(e))
    
    def print_results(self):
        """Print results in a tabular format"""
        print(f"\n{Colors.BOLD}📊 Results Summary{Colors.END}")
        print("=" * 120)
        
        # Table headers
        print(f"{Colors.BOLD}{'Category':<15} {'Item':<35} {'Status':<12} {'Details':<50}{Colors.END}")
        print("-" * 120)
        
        # Group results by category
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        # Print each category in table format
        for category, items in categories.items():
            for i, item in enumerate(items):
                # Show category name only for first item in each category
                cat_display = category if i == 0 else ""
                
                status_str = self.print_status(item['status'])
                details = item['details'] if item['details'] else ""
                
                # Truncate long details to fit in column
                if len(details) > 47:
                    details = details[:44] + "..."
                
                print(f"{cat_display:<15} {item['item']:<35} {status_str:<20} {details:<50}")
            
            # Add separator between categories
            if category != list(categories.keys())[-1]:  # Not the last category
                print("-" * 120)
        
        # Summary statistics
        total = len(self.results)
        ok_count = sum(1 for r in self.results if r['status'] == 'OK')
        error_count = sum(1 for r in self.results if r['status'] in ['ERROR', 'MISSING'])
        warning_count = sum(1 for r in self.results if r['status'] == 'WARNING')
        
        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"  Total checks: {total}")
        print(f"  {Colors.GREEN}✅ Passed: {ok_count}{Colors.END}")
        print(f"  {Colors.RED}❌ Failed: {error_count}{Colors.END}")
        print(f"  {Colors.YELLOW}⚠️  Warnings: {warning_count}{Colors.END}")

def main():
    """Main function"""
    checker = DevEnvChecker()
    
    try:
        checker.run_all_checks()
        checker.print_results()
        
        # Print detailed tables
        checker.print_hosts_details()
        checker.print_ssh_config_details()
        checker.print_ssh_keys_details()
        checker.print_known_hosts_details()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Check interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
