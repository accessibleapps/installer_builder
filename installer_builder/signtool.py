from __future__ import print_function
import os
import subprocess
import sys
import platform
import logging
from pathlib import Path
import winreg

# Set up module logger
logger = logging.getLogger(__name__)

DEFAULT_TIMESTAMP_SERVER = 'http://timestamp.digicert.com'

class SignToolNotFoundError(Exception):
    """Exception raised when signtool.exe cannot be found."""
    def __init__(self, message="Could not find signtool.exe. You may need to install the Windows SDK or Visual Studio."):
        self.message = message
        super().__init__(self.message)

def find_signtool(prefer_matching_arch=True, prefer_newest_version=True):
    """
    Find signtool.exe on the system, preferring architecture match and newest version.
    
    Args:
        prefer_matching_arch: If True, prefer signtool matching system architecture
        prefer_newest_version: If True, prefer newest SDK version
    
    Returns:
        str: Path to the most appropriate signtool.exe
        
    Raises:
        SignToolNotFoundError: If signtool.exe cannot be found
    """
    def get_system_architecture():
        """Determine the system's processor architecture"""
        arch = platform.machine().lower()
        
        if arch in ("amd64", "x86_64", "em64t"):
            return "x64"
        elif arch in ("x86", "i386", "i486", "i586", "i686"):
            return "x86"
        elif arch in ("arm64", "aarch64"):
            return "arm64"
        else:
            # Default to x64 if unknown
            return "x64"
    
    def find_signtool_in_registry():
        """Find signtool.exe by checking Windows SDK registry entries"""
        possible_locations = []
        
        # Common registry paths for Windows SDK
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Kits\Installed Roots"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Microsoft SDKs\Windows")
        ]
        
        for hkey, reg_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, reg_path) as key:
                    # For Windows Kits\Installed Roots
                    if "Installed Roots" in reg_path:
                        try:
                            kit_root = winreg.QueryValueEx(key, "KitsRoot10")[0]
                            # Enumerate installed SDK versions
                            i = 0
                            while True:
                                try:
                                    sdk_version = winreg.EnumValue(key, i)[0]
                                    # Only process numeric version entries
                                    if sdk_version.replace(".", "").isdigit():
                                        for arch in ["x86", "x64", "arm64"]:
                                            signtool_path = os.path.join(
                                                kit_root, "bin", sdk_version, arch, "signtool.exe"
                                            )
                                            if os.path.exists(signtool_path):
                                                possible_locations.append((signtool_path, arch, sdk_version))
                                    i += 1
                                except OSError:
                                    break  # No more values
                        except FileNotFoundError:
                            pass
                    
                    # For Microsoft SDKs\Windows
                    else:
                        try:
                            i = 0
                            while True:
                                try:
                                    name, value, _ = winreg.EnumValue(key, i)
                                    if "InstallationFolder" in name:
                                        # Try to extract version info
                                        sdk_version = "unknown"
                                        if "\\" in name:
                                            sdk_version = name.split("\\")[-1]
                                        
                                        for bin_folder, arch in [("bin", "x86"), (r"bin\x64", "x64"), (r"bin\arm64", "arm64")]:
                                            signtool_path = os.path.join(value, bin_folder, "signtool.exe")
                                            if os.path.exists(signtool_path):
                                                possible_locations.append((signtool_path, arch, sdk_version))
                                    i += 1
                                except OSError:
                                    break  # No more values
                        except FileNotFoundError:
                            pass
                        
            except FileNotFoundError:
                continue
        
        return possible_locations
    
    def find_signtool_in_common_paths():
        """Search for signtool.exe in common installation paths"""
        possible_locations = []
        
        # Common paths where signtool might be found
        common_paths = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Windows Kits"),
            os.path.expandvars(r"%ProgramFiles%\Windows Kits"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft SDKs"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft SDKs"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Visual Studio"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft Visual Studio")
        ]
        
        # Walk through directories looking for signtool.exe
        for base_path in common_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    if "signtool.exe" in files:
                        # Try to determine architecture from path
                        path_lower = root.lower()
                        arch = "unknown"
                        sdk_version = "unknown"
                        
                        # Try to detect architecture from path
                        if "\\x64\\" in path_lower or "\\amd64\\" in path_lower:
                            arch = "x64"
                        elif "\\x86\\" in path_lower or "\\i386\\" in path_lower:
                            arch = "x86"
                        elif "\\arm64\\" in path_lower or "\\aarch64\\" in path_lower:
                            arch = "arm64"
                        
                        # Try to extract version info
                        path_parts = path_lower.split(os.sep)
                        for i, part in enumerate(path_parts):
                            if part == "bin" and i > 0 and i+1 < len(path_parts):
                                # Version might be before bin folder
                                potential_version = path_parts[i-1]
                                if potential_version.replace(".", "").isdigit():
                                    sdk_version = potential_version
                        
                        possible_locations.append((os.path.join(root, "signtool.exe"), arch, sdk_version))
        
        return possible_locations
    
    def find_signtool_in_path():
        """Check if signtool is available in the system PATH"""
        try:
            result = subprocess.run(
                ["where", "signtool.exe"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if result.returncode == 0:
                locations = []
                for path in result.stdout.strip().split('\n'):
                    # Try to determine architecture from path
                    path_lower = path.lower()
                    arch = "unknown"
                    sdk_version = "unknown"
                    
                    if "\\x64\\" in path_lower:
                        arch = "x64"
                    elif "\\x86\\" in path_lower:
                        arch = "x86"
                    elif "\\arm64\\" in path_lower:
                        arch = "arm64"
                    
                    # Try to extract version info
                    path_parts = path_lower.split(os.sep)
                    for i, part in enumerate(path_parts):
                        if part == "bin" and i > 0 and i+1 < len(path_parts):
                            potential_version = path_parts[i-1]
                            if potential_version.replace(".", "").isdigit():
                                sdk_version = potential_version
                    
                    locations.append((path, arch, sdk_version))
                return locations
            return []
        except FileNotFoundError:
            return []
    
    # Main logic starts here
    logger.info("Searching for signtool.exe...")
    system_arch = get_system_architecture()
    logger.info(f"System architecture: {system_arch}")
    
    locations = []
    
    # Try registry first
    logger.info("Searching in registry...")
    registry_locations = find_signtool_in_registry()
    if registry_locations:
        locations.extend(registry_locations)
        logger.debug(f"Found {len(registry_locations)} locations in registry.")
    
    # Check system PATH
    logger.info("Checking system PATH...")
    path_locations = find_signtool_in_path()
    if path_locations:
        locations.extend(path_locations)
        logger.debug(f"Found {len(path_locations)} locations in PATH.")
    
    # If not found, do a more extensive search
    if not locations:
        logger.info("Searching in common installation paths (this may take a while)...")
        common_locations = find_signtool_in_common_paths()
        if common_locations:
            locations.extend(common_locations)
            logger.debug(f"Found {len(common_locations)} locations in common paths.")
    
    # Return unique paths
    unique_locations = []
    seen_paths = set()
    
    for path, arch, version in locations:
        if path not in seen_paths:
            seen_paths.add(path)
            unique_locations.append((path, arch, version))
    
    if not unique_locations:
        logger.error("SignTool not found on the system.")
        raise SignToolNotFoundError()
    
    logger.info(f"Found {len(unique_locations)} unique signtool.exe locations.")
    
    # Find best match based on preferences
    if prefer_matching_arch:
        matching_arch = [loc for loc in unique_locations if loc[1] == system_arch]
        if matching_arch:
            logger.info(f"Found {len(matching_arch)} signtool versions matching system architecture ({system_arch}).")
            if prefer_newest_version:
                # Sort by version, with newest first
                def version_key(location):
                    ver = location[2]
                    if ver == "unknown":
                        return (-1,)  # Place unknown versions at the end
                    
                    # Try to convert version to tuple of integers
                    try:
                        return tuple(int(part) for part in ver.split('.'))
                    except ValueError:
                        return (0,)  # Non-numeric versions sort after unknown
                
                best_match = sorted(matching_arch, key=version_key, reverse=True)[0]
                logger.info(f"Selected best match: {best_match[0]} (arch: {best_match[1]}, version: {best_match[2]})")
                return best_match[0]
            else:
                logger.info(f"Selected first match: {matching_arch[0][0]}")
                return matching_arch[0][0]
    
    # If we don't prefer matching arch or no matching arch found,
    # return first available or sorted by version if preferred
    if prefer_newest_version:
        def version_key(location):
            ver = location[2]
            if ver == "unknown":
                return (-1,)
            try:
                return tuple(int(part) for part in ver.split('.'))
            except ValueError:
                return (0,)
        
        best_match = sorted(unique_locations, key=version_key, reverse=True)[0]
        logger.info(f"Selected best available match: {best_match[0]} (arch: {best_match[1]}, version: {best_match[2]})")
        return best_match[0]
    else:
        logger.info(f"Selected first available match: {unique_locations[0][0]}")
        return unique_locations[0][0]

def sign(filename, url='', description='', timestamp_server=DEFAULT_TIMESTAMP_SERVER, certificate_file='', certificate_password=''):
    """
    Sign a Windows executable or DLL using signtool.
    
    Args:
        filename: Path to the file to sign
        url: URL to include in the signature
        description: Description to include in the signature
        timestamp_server: URL of the timestamp server
        certificate_file: Path to the certificate file (.pfx)
        certificate_password: Password for the certificate file
        
    Returns:
        The return code from signtool
        
    Raises:
        subprocess.CalledProcessError: If signtool fails
        FileNotFoundError: If the file to sign or certificate file doesn't exist
        SignToolNotFoundError: If signtool.exe cannot be found
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File to sign not found: {filename}")
        
    if not certificate_file or not os.path.exists(certificate_file):
        raise FileNotFoundError(f"Certificate file not found: {certificate_file}")
    
    # Find signtool.exe
    try:
        signtool_path = find_signtool()
        logger.info(f"Using signtool: {signtool_path}")
    except SignToolNotFoundError as e:
        logger.error(f"Error finding signtool: {e}")
        print(f"Error finding signtool: {e}")
        print("You can download the Windows SDK from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
        raise
    
    # Build the command
    command = f'"{signtool_path}" sign /t {timestamp_server}'
    if url:
        command += f' /du {url}'
    if description:
        command += f' /d "{description}"'
    command += f' /f "{certificate_file}" /p "{certificate_password}"'
    command += f' /v "{filename}"'
    
    # Don't print the command with the password
    safe_command = command.replace(certificate_password, '********') if certificate_password else command
    print(f"Signing: {os.path.basename(filename)}")
    print(safe_command)
    
    try:
        return subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error signing {filename}: {e}")
        print("Make sure the certificate is valid and you have permission to sign.")
        raise

# Configure basic logging if this module is run directly
if __name__ == "__main__":
    # Set up basic logging configuration for command line usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    try:
        signtool_path = find_signtool()
        print(f"Best signtool.exe found: {signtool_path}")
    except SignToolNotFoundError as e:
        print(f"Error: {e}")
        print("You can download the Windows SDK from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
