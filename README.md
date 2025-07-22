# Local Development Environment Checker

A simple script to check the status of various files, tools, and configurations on your local development machine.

## Features

- ✅ **Intelligent file analysis**: `/etc/hosts` with custom entry detection, SSH config parsing
- 🛠️ **Command line tools**: Git, Docker, Ansible, Terraform with version checks
- ☁️ **Cloud provider credentials**: AWS, Google Cloud, DigitalOcean with API connectivity tests
- 🔧 **Configuration validation**: Ansible and Terraform setup verification
- 🎨 **Professional output**: Colored terminal with status indicators and tabular formatting
- 📊 **Detailed analysis**: Summary statistics plus dedicated detail tables
- 🔍 **SSH infrastructure**: Comprehensive SSH config and known hosts analysis
- 🏠 **Custom host detection**: Identifies non-standard entries in `/etc/hosts`

## Usage

Run the comprehensive Python-based environment checker:

```bash
python3 dev_env_check.py
```

The script provides detailed error handling, JSON parsing for API responses, and comprehensive timeout management.

## What It Checks

### System Files

- **`/etc/hosts`** - Intelligent analysis detecting custom entries beyond system defaults
- **`~/.ssh/config`** - SSH client configuration with host parsing and settings analysis
- **`~/.ssh/known_hosts`** - SSH known hosts with key type analysis and host identification

### Command Line Tools

- **Git** - Version control
- **Docker** - Containerization platform
- **Ansible** - Configuration management
- **Terraform** - Infrastructure as code

### Cloud Providers

#### AWS

- Credentials file (`~/.aws/credentials`)
- Config file (`~/.aws/config`)
- AWS CLI installation and connectivity test

#### Google Cloud Platform

- Application credentials (`~/.config/gcloud/application_default_credentials.json`)
- gcloud CLI installation and authentication status

#### DigitalOcean

- Config file (`~/.config/doctl/config.yaml`)
- doctl CLI installation and API connectivity

### Configuration Files

#### Ansible

- User config (`~/.ansible.cfg`)
- Global config (`/etc/ansible/ansible.cfg`)

#### Terraform

- Installation and version check

## Output Format

The script provides comprehensive output in multiple sections:

### Main Results Table

Professional tabular format with colored status indicators:

- ✅ **OK** - Check passed successfully
- ❌ **MISSING** - File or command not found
- ❌ **ERROR** - Command failed or API error
- ⚠️ **WARNING** - Partial success or configuration issue

### Detailed Analysis Tables

When relevant, additional detailed tables are displayed:

- **🏠 /etc/hosts Custom Entries** - Shows non-standard host mappings (when present)
- **🔧 SSH Configuration Details** - Complete SSH config with hosts, IPs, users, and key files
- **🔑 SSH Known Hosts Details** - All known hosts with their key types

### Summary Statistics

Final summary showing:

- Total number of checks performed
- Count of passed, failed, and warning results
- Quick overview of system health

## Requirements

- **Python 3.6+**
- **No external dependencies** (uses only standard library)
- **macOS/Linux** compatible

## Extending the Script

The modular design makes it easy to add new checks:

1. **Add new check methods** to the `DevEnvChecker` class
2. **Call them from `run_all_checks()`** method
3. **Follow the existing patterns** for consistent output formatting

### Example: Adding a new tool check

```python
def check_kubectl(self):
    """Check Kubernetes kubectl tool"""
    self.check_command_version("kubectl", "Kubernetes", "kubectl")
    
    # Add to run_all_checks():
    self.check_kubectl()
```

## Example Output

```text
🔍 Local Development Environment Check

System
------
  /etc/hosts                     ✅ OK (Size: 298 bytes)

SSH
---
  SSH config                     ✅ OK (Size: 1024 bytes)
  Known hosts                    ✅ OK (Size: 2048 bytes)

Tools
-----
  Git (installed)                ✅ OK (Path: /usr/bin/git)
  Git (version)                  ✅ OK (git version 2.39.0)

📊 Results Summary
================================================================================

Summary:
  Total checks: 15
  ✅ Passed: 12
  ❌ Failed: 2
  ⚠️  Warnings: 1
```

## Example Configurations

This project includes example configuration files in the `examples/` directory:

```text
examples/
├── ansible/
│   ├── ansible.cfg     # Example Ansible configuration
│   └── inventory       # Example inventory file
└── doctl/
    └── config.yaml     # Example DigitalOcean configuration
```

### Setting Up Examples

To use the example configurations:

```bash
# Automatically copy examples to proper locations
python3 setup_examples.py

# Or manually copy files:
cp examples/ansible/ansible.cfg ~/.ansible.cfg
mkdir -p ~/ansible && cp examples/ansible/inventory ~/ansible/
mkdir -p ~/.config/doctl && cp examples/doctl/config.yaml ~/.config/doctl/
```

### Example Features

#### Ansible Configuration

- **SSH optimizations**: Control master, pipelining enabled
- **Development-friendly settings**: Host key checking disabled
- **Basic inventory structure** with local, development, staging, and production groups

#### DigitalOcean Configuration

- **Basic doctl setup** with placeholder for API token
- **Default output format** and context settings

### Testing Setup

```bash
# Check Ansible configuration
ansible --version

# List inventory
ansible-inventory --list

# Test local connection
ansible localhost -m ping

# Test DigitalOcean (after adding API token)
doctl account get
```

## License

This project is open source and available under the MIT License.
