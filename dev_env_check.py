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
    
    def check_aws_credentials(self):
        """Check AWS credentials and connectivity"""
        # Check credentials file
        aws_creds = "~/.aws/credentials"
        self.check_file_exists(aws_creds, "AWS", "Credentials file")
        
        # Check config file
        aws_config = "~/.aws/config"
        self.check_file_exists(aws_config, "AWS", "Config file")
        
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
    
    def check_gcp_credentials(self):
        """Check Google Cloud credentials and connectivity"""
        # Check default credentials
        gcp_creds = "~/.config/gcloud/application_default_credentials.json"
        self.check_file_exists(gcp_creds, "GCP", "Application credentials")
        
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
        """Check DigitalOcean credentials"""
        # Check for doctl config
        do_config = "~/.config/doctl/config.yaml"
        self.check_file_exists(do_config, "DigitalOcean", "Config file")
        
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
            
            # Create summary
            size = os.path.getsize(ssh_config_path)
            summary_parts = [f"Size: {size} bytes"]
            
            if hosts:
                if len(hosts) <= 5:  # Show host names if reasonable number
                    host_list = ', '.join(hosts)
                    summary_parts.append(f"Hosts: {len(hosts)} ({host_list})")
                else:
                    summary_parts.append(f"Hosts: {len(hosts)}")
            
            if global_settings:
                key_settings = []
                for key in ['serveraliveinterval', 'compression', 'forwardagent']:
                    if key in global_settings:
                        key_settings.append(f"{key.title()}: {global_settings[key]}")
                if key_settings:
                    summary_parts.append(f"Settings: {', '.join(key_settings)}")
            
            summary = ", ".join(summary_parts)
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
            
            # Create summary
            size = os.path.getsize(known_hosts_path)
            summary_parts = [f"Size: {size} bytes", f"Entries: {len(lines)}"]
            
            if hosts:
                visible_hosts = [h for h in hosts if h != '[hashed]']
                hashed_count = len([h for h in hosts if h == '[hashed]'])
                
                if visible_hosts:
                    if len(visible_hosts) <= 10:  # Show host names if reasonable number
                        host_list = ', '.join(sorted(visible_hosts))
                        summary_parts.append(f"Hosts: {len(visible_hosts)} ({host_list})")
                    else:
                        summary_parts.append(f"Hosts: {len(visible_hosts)}")
                        
                if hashed_count > 0:
                    summary_parts.append(f"Hashed: {hashed_count}")
            
            if key_types:
                key_summary = ', '.join([f"{k}: {v}" for k, v in key_types.items()])
                summary_parts.append(f"Keys: {key_summary}")
            
            summary = ", ".join(summary_parts)
            self.add_result("SSH", "Known hosts", "OK", summary)
            
        except Exception as e:
            self.add_result("SSH", "Known hosts", "ERROR", f"Failed to parse: {str(e)}")
    
    def run_all_checks(self):
        """Run all environment checks"""
        print(f"{Colors.BOLD}🔍 Local Development Environment Check{Colors.END}\n")
        
        # File checks
        print("Checking system files...")
        self.check_file_exists("/etc/hosts", "System", "/etc/hosts")
        
        # SSH configuration checks
        print("Checking SSH configuration...")
        self.check_ssh_config()
        self.check_ssh_known_hosts()
        
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
        self.check_file_exists("~/.ansible.cfg", "Ansible", "Config file")
        self.check_file_exists("/etc/ansible/ansible.cfg", "Ansible", "Global config")
        
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
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Check interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
