#!/usr/bin/env python3
"""
Script to install the MaterialX addon to the latest Blender version on macOS.
This script will:
1. Find the latest Blender installation
2. Remove any existing MaterialX addon
3. Copy the current addon to Blender's addon directory
4. Handle errors appropriately
"""

import os
import sys
import shutil
import glob
import subprocess
from pathlib import Path
import platform

def find_latest_blender():
    """Find the latest Blender installation on macOS."""
    if platform.system() != 'Darwin':
        raise RuntimeError("This script is designed for macOS only")
    
    # Common Blender installation paths on macOS
    blender_paths = [
        "/Applications/Blender.app",
        "/Applications/Blender 4.5.app",
        "/Applications/Blender 4.4.app",
        "/Applications/Blender 4.3.app",
        "/Applications/Blender 4.2.app",
        "/Applications/Blender 4.1.app",
        "/Applications/Blender 4.0.app",
    ]
    
    # Also check for any Blender*.app in Applications
    applications_dir = "/Applications"
    if os.path.exists(applications_dir):
        blender_apps = glob.glob(os.path.join(applications_dir, "Blender*.app"))
        blender_paths.extend(blender_apps)
    
    # Find the latest version
    latest_blender = None
    latest_version = (0, 0, 0)
    
    for blender_path in blender_paths:
        if os.path.exists(blender_path):
            # Extract version from path or get it from the app
            version_str = os.path.basename(blender_path).replace("Blender", "").replace(".app", "").strip()
            
            if version_str:
                # Parse version like "4.5" or "4.5.0"
                try:
                    version_parts = [int(x) for x in version_str.split('.')]
                    # Pad to 3 parts
                    while len(version_parts) < 3:
                        version_parts.append(0)
                    version_tuple = tuple(version_parts[:3])
                    
                    if version_tuple > latest_version:
                        latest_version = version_tuple
                        latest_blender = blender_path
                except ValueError:
                    # If we can't parse the version, try to get it from the app
                    try:
                        result = subprocess.run([
                            os.path.join(blender_path, "Contents/MacOS/Blender"),
                            "--version"
                        ], capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0:
                            # Parse version from output like "Blender 4.5.0"
                            output = result.stdout.strip()
                            if "Blender" in output:
                                version_match = output.split("Blender")[1].strip().split()[0]
                                version_parts = [int(x) for x in version_match.split('.')]
                                while len(version_parts) < 3:
                                    version_parts.append(0)
                                version_tuple = tuple(version_parts[:3])
                                
                                if version_tuple > latest_version:
                                    latest_version = version_tuple
                                    latest_blender = blender_path
                    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                        continue
            else:
                # No version in name, try to get it from the app
                try:
                    result = subprocess.run([
                        os.path.join(blender_path, "Contents/MacOS/Blender"),
                        "--version"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        output = result.stdout.strip()
                        if "Blender" in output:
                            version_match = output.split("Blender")[1].strip().split()[0]
                            version_parts = [int(x) for x in version_match.split('.')]
                            while len(version_parts) < 3:
                                version_parts.append(0)
                            version_tuple = tuple(version_parts[:3])
                            
                            if version_tuple > latest_version:
                                latest_version = version_tuple
                                latest_blender = blender_path
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    continue
    
    if not latest_blender:
        raise RuntimeError("Could not find any Blender installation on this system")
    
    print(f"Found Blender {latest_version[0]}.{latest_version[1]}.{latest_version[2]} at: {latest_blender}")
    return latest_blender

def get_blender_addon_directory(blender_path):
    """Get the addon directory for the given Blender installation."""
    # On macOS, Blender addons are typically in:
    # ~/Library/Application Support/Blender/[version]/scripts/addons/
    
    home_dir = os.path.expanduser("~")
    support_dir = os.path.join(home_dir, "Library", "Application Support", "Blender")
    
    if not os.path.exists(support_dir):
        raise RuntimeError(f"Blender support directory not found: {support_dir}")
    
    # Find the version directory
    version_dirs = []
    for item in os.listdir(support_dir):
        item_path = os.path.join(support_dir, item)
        if os.path.isdir(item_path) and item.replace('.', '').isdigit():
            version_dirs.append(item)
    
    if not version_dirs:
        raise RuntimeError(f"No Blender version directories found in: {support_dir}")
    
    # Sort by version and get the latest
    version_dirs.sort(key=lambda x: [int(i) for i in x.split('.')], reverse=True)
    latest_version_dir = version_dirs[0]
    
    addon_dir = os.path.join(support_dir, latest_version_dir, "scripts", "addons")
    
    if not os.path.exists(addon_dir):
        # Try to create the directory
        try:
            os.makedirs(addon_dir, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Could not create addon directory {addon_dir}: {e}")
    
    print(f"Using addon directory: {addon_dir}")
    return addon_dir

def remove_existing_addon(addon_dir, addon_name="materialx_addon"):
    """Remove existing MaterialX addon if it exists."""
    existing_addon_path = os.path.join(addon_dir, addon_name)
    
    if os.path.exists(existing_addon_path):
        print(f"Removing existing addon: {existing_addon_path}")
        try:
            shutil.rmtree(existing_addon_path)
            print("Existing addon removed successfully")
        except OSError as e:
            raise RuntimeError(f"Could not remove existing addon {existing_addon_path}: {e}")
    else:
        print("No existing addon found")

def copy_addon_to_blender(addon_dir, source_dir):
    """Copy the current addon to Blender's addon directory."""
    addon_name = "materialx_addon"
    target_path = os.path.join(addon_dir, addon_name)
    
    print(f"Copying addon from {source_dir} to {target_path}")
    
    try:
        shutil.copytree(source_dir, target_path)
        print("Addon copied successfully")
    except OSError as e:
        raise RuntimeError(f"Could not copy addon to {target_path}: {e}")

def main():
    """Main installation function."""
    print("=" * 60)
    print("MaterialX Addon Installer")
    print("=" * 60)
    
    try:
        # Get the current script directory (project root)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        addon_source_dir = os.path.join(script_dir, "materialx_addon")
        
        # Verify the addon source exists
        if not os.path.exists(addon_source_dir):
            raise RuntimeError(f"Addon source directory not found: {addon_source_dir}")
        
        print(f"Addon source directory: {addon_source_dir}")
        
        # Find the latest Blender installation
        blender_path = find_latest_blender()
        
        # Get the addon directory
        addon_dir = get_blender_addon_directory(blender_path)
        
        # Remove existing addon
        remove_existing_addon(addon_dir)
        
        # Copy the new addon
        copy_addon_to_blender(addon_dir, addon_source_dir)
        
        print("=" * 60)
        print("Installation completed successfully!")
        print("=" * 60)
        print("To enable the addon in Blender:")
        print("1. Open Blender")
        print("2. Go to Edit > Preferences > Add-ons")
        print("3. Search for 'MaterialX'")
        print("4. Enable the 'Material: MaterialX Export' addon")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 