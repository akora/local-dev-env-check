#!/usr/bin/env python3
"""
Setup script to copy example configuration files to their proper locations.
Run this script to set up basic configurations for Ansible and DigitalOcean.
"""

import os
import shutil
from pathlib import Path

def setup_ansible_config():
    """Set up Ansible configuration files"""
    print("Setting up Ansible configuration...")
    
    # Source files
    ansible_cfg_src = Path("examples/ansible/ansible.cfg")
    inventory_src = Path("examples/ansible/inventory")
    
    # Destination paths
    ansible_cfg_dst = Path.home() / ".ansible.cfg"
    ansible_dir = Path.home() / "ansible"
    inventory_dst = ansible_dir / "inventory"
    control_dir = Path.home() / ".ansible" / "cp"
    
    # Create directories
    ansible_dir.mkdir(exist_ok=True)
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy files
    if ansible_cfg_src.exists():
        if ansible_cfg_dst.exists():
            backup = ansible_cfg_dst.with_suffix('.cfg.backup')
            print(f"  Backing up existing config to {backup}")
            shutil.copy2(ansible_cfg_dst, backup)
        
        shutil.copy2(ansible_cfg_src, ansible_cfg_dst)
        print(f"  ✅ Copied {ansible_cfg_src} -> {ansible_cfg_dst}")
    
    if inventory_src.exists():
        if inventory_dst.exists():
            backup = inventory_dst.with_suffix('.backup')
            print(f"  Backing up existing inventory to {backup}")
            shutil.copy2(inventory_dst, backup)
        
        shutil.copy2(inventory_src, inventory_dst)
        print(f"  ✅ Copied {inventory_src} -> {inventory_dst}")

def setup_doctl_config():
    """Set up DigitalOcean doctl configuration"""
    print("Setting up DigitalOcean doctl configuration...")
    
    # Source file
    doctl_cfg_src = Path("examples/doctl/config.yaml")
    
    # Destination paths
    doctl_dir = Path.home() / ".config" / "doctl"
    doctl_cfg_dst = doctl_dir / "config.yaml"
    
    # Create directory
    doctl_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    if doctl_cfg_src.exists():
        if doctl_cfg_dst.exists():
            backup = doctl_cfg_dst.with_suffix('.yaml.backup')
            print(f"  Backing up existing config to {backup}")
            shutil.copy2(doctl_cfg_dst, backup)
        
        shutil.copy2(doctl_cfg_src, doctl_cfg_dst)
        print(f"  ✅ Copied {doctl_cfg_src} -> {doctl_cfg_dst}")
        print(f"  ⚠️  Remember to replace YOUR_API_TOKEN with your actual DigitalOcean API token!")

def main():
    """Main setup function"""
    print("🔧 Setting up example configuration files...")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        setup_ansible_config()
        print()
        setup_doctl_config()
        
        print("\n" + "=" * 50)
        print("✅ Setup complete!")
        print("\nNext steps:")
        print("1. For DigitalOcean: Edit ~/.config/doctl/config.yaml and add your API token")
        print("2. Run the environment checker: python3 dev_env_check.py")
        print("3. Test Ansible: ansible localhost -m ping")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
