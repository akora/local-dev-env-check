# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Python-based local development environment checker that audits system configurations, tools, and cloud provider credentials. The script performs comprehensive security analysis, detects configuration issues, and provides detailed reporting for development environments.

## Architecture

**Core Components:**

- `DevEnvChecker` class: Main checker engine with modular check methods
- Category-based checks: System files, SSH configuration, cloud credentials, command-line tools
- Intelligent parsing: JSON credentials, SSH configs, hosts files with custom entry detection
- Security analysis: SSH key validation, weak key detection, orphaned key identification

**Key Files:**

- `dev_env_check.py`: Main environment checker script (1050+ lines)
- `setup_examples.py`: Configuration setup utility for Ansible and DigitalOcean
- `examples/`: Sample configuration files for development tools

## Common Commands

**Run environment check:**

```bash
python3 dev_env_check.py
```

**Setup example configurations:**

```bash
python3 setup_examples.py
```

**Test Ansible after setup:**

```bash
ansible localhost -m ping
```

## Security Analysis Features

**SSH Key Security:**

- Detects orphaned keys (private without public, public without private)
- Identifies weak key types (DSA deprecated, RSA < 2048 bits)
- Recursive scanning of SSH directory and subdirectories
- Shows WARNING status for security issues

**System File Analysis:**

- `/etc/hosts` custom entry detection with security warnings
- SSH config parsing with host and credential analysis
- Known hosts validation with key type identification

**Cloud Provider Integration:**

- AWS: Credential files, config parsing, API connectivity testing
- GCP: Application credentials analysis, authentication status
- DigitalOcean: Config detection with smart path resolution

## Development Notes

**Adding New Checks:**

1. Create method in `DevEnvChecker` class following naming pattern `check_*`
2. Use `self.add_result(category, item, status, details)` for consistent output
3. Add method call to `run_all_checks()`
4. Follow existing patterns for error handling and timeouts

**Status Types:**

- `OK`: Check passed successfully
- `MISSING`: File or command not found  
- `ERROR`: Command failed or API error
- `WARNING`: Security issues or configuration problems
- `INFO`: Informational status

**Output Format:**

- Main results in tabular format with colored status indicators
- Detailed analysis tables for SSH configuration, keys, and known hosts
- Summary statistics showing total checks and status counts
