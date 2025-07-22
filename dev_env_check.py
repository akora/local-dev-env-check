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
    
    def run_all_checks(self):
        """Run all environment checks"""
        print(f"{Colors.BOLD}🔍 Local Development Environment Check{Colors.END}\n")
        
        # File checks
        print("Checking system files...")
        self.check_file_exists("/etc/hosts", "System", "/etc/hosts")
        self.check_file_exists("~/.ssh/config", "SSH", "SSH config")
        self.check_file_exists("~/.ssh/known_hosts", "SSH", "Known hosts")
        
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
        print("=" * 80)
        
        # Group results by category
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        # Print each category
        for category, items in categories.items():
            print(f"\n{Colors.BOLD}{category}{Colors.END}")
            print("-" * len(category))
            
            for item in items:
                status_str = self.print_status(item['status'])
                details = f" ({item['details']})" if item['details'] else ""
                print(f"  {item['item']:<30} {status_str}{details}")
        
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
