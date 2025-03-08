from __future__ import print_function
import os
import subprocess
import sys
import platform
import logging
import winreg

# Set up module logger
logger = logging.getLogger(__name__)

DEFAULT_TIMESTAMP_SERVER = 'http://timestamp.digicert.com'

class SignToolNotFoundError(Exception):
    """Exception raised when signtool.exe cannot be found."""
    def __init__(self, message="Could not find signtool.exe. You may need to install the Windows SDK or Visual Studio."):
        self.message = message
        super().__init__(self.message)

def find_signtool():
    """
    Find signtool.exe on the system, preferring architecture match and newest version.
    
    Returns:
        str: Path to the most appropriate signtool.exe
        
    Raises:
        SignToolNotFoundError: If signtool.exe cannot be found
    """
    # Get system architecture
    system_arch = platform.machine().lower()
    if system_arch in ("amd64", "x86_64", "em64t"):
        system_arch = "x64"
    elif system_arch in ("x86", "i386", "i486", "i586", "i686"):
        system_arch = "x86"
    elif system_arch in ("arm64", "aarch64"):
        system_arch = "arm64"
    else:
        system_arch = "x64"  # Default to x64 if unknown
    
    logger.info(f"System architecture: {system_arch}")
    
    # Common paths where signtool might be found
    common_paths = [
        # Windows SDK paths
        os.path.expandvars(r"%ProgramFiles(x86)%\Windows Kits\10\bin"),
        os.path.expandvars(r"%ProgramFiles%\Windows Kits\10\bin"),
        # Visual Studio paths
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft SDKs\Windows\v10.0A\bin"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft SDKs\Windows\v10.0A\bin"),
        # ClickOnce path
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft SDKs\ClickOnce\SignTool"),
        # App Certification Kit
        os.path.expandvars(r"%ProgramFiles(x86)%\Windows Kits\10\App Certification Kit"),
    ]
    
    # Find all signtool.exe instances
    signtool_locations = []
    
    # First check registry for Windows SDK installations
    logger.info("Searching in registry...")
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Kits\Installed Roots") as key:
            kit_root = winreg.QueryValueEx(key, "KitsRoot10")[0]
            
            # Enumerate SDK versions
            i = 0
            while True:
                try:
                    sdk_version = winreg.EnumValue(key, i)[0]
                    # Only process numeric version entries
                    if sdk_version.replace(".", "").isdigit():
                        for arch in ["x86", "x64", "arm", "arm64"]:
                            path = os.path.join(kit_root, "bin", sdk_version, arch, "signtool.exe")
                            if os.path.exists(path):
                                signtool_locations.append((path, arch, sdk_version))
                    i += 1
                except OSError:
                    break  # No more values
    except (FileNotFoundError, OSError):
        pass
    
    # Check PATH
    logger.info("Checking system PATH...")
    try:
        result = subprocess.run(["where", "signtool.exe"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            for path in result.stdout.strip().split('\n'):
                # Determine architecture from path
                arch = "unknown"
                version = "unknown"
                
                path_parts = path.lower().split(os.sep)
                for part in path_parts:
                    if part in ["x64", "amd64"]:
                        arch = "x64"
                        break
                    elif part in ["x86", "i386"]:
                        arch = "x86"
                        break
                    elif part == "arm64":
                        arch = "arm64"
                        break
                    elif part == "arm":
                        arch = "arm"
                        break
                
                # Try to extract version
                for i, part in enumerate(path_parts):
                    if part == "bin" and i > 0 and i+1 < len(path_parts):
                        potential_version = path_parts[i-1]
                        if potential_version.replace(".", "").isdigit():
                            version = potential_version
                
                signtool_locations.append((path, arch, version))
    except FileNotFoundError:
        pass
    
    # If not found, search common paths
    if not signtool_locations:
        logger.info("Searching in common installation paths...")
        for base_path in common_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    if "signtool.exe" in files:
                        # Determine architecture from path
                        arch = "unknown"
                        version = "unknown"
                        
                        path_parts = root.lower().split(os.sep)
                        for part in path_parts:
                            if part in ["x64", "amd64"]:
                                arch = "x64"
                                break
                            elif part in ["x86", "i386"]:
                                arch = "x86"
                                break
                            elif part == "arm64":
                                arch = "arm64"
                                break
                            elif part == "arm":
                                arch = "arm"
                                break
                        
                        # Try to extract version
                        for i, part in enumerate(path_parts):
                            if part == "bin" and i > 0 and i+1 < len(path_parts):
                                potential_version = path_parts[i-1]
                                if potential_version.replace(".", "").isdigit():
                                    version = potential_version
                        
                        signtool_locations.append((os.path.join(root, "signtool.exe"), arch, version))
    
    # Remove duplicates
    unique_locations = []
    seen_paths = set()
    for path, arch, version in signtool_locations:
        if path not in seen_paths:
            seen_paths.add(path)
            unique_locations.append((path, arch, version))
    
    if not unique_locations:
        logger.error("SignTool not found on the system.")
        raise SignToolNotFoundError()
    
    logger.info(f"Found {len(unique_locations)} unique signtool.exe locations.")
    
    # Log all found locations
    for i, (path, arch, version) in enumerate(unique_locations):
        logger.debug(f"Found signtool #{i+1}: {path} (arch: {arch}, version: {version})")
    
    # Filter locations by architecture preference
    matching_arch = [loc for loc in unique_locations if loc[1] == system_arch]
    
    # If we have matching architecture tools, use those
    if matching_arch:
        # Sort by version if possible (newer is better)
        matching_arch.sort(key=lambda loc: loc[2], reverse=True)
        best_match = matching_arch[0]
    else:
        # Fallback to x86 on x64 systems
        if system_arch == "x64":
            x86_tools = [loc for loc in unique_locations if loc[1] == "x86"]
            if x86_tools:
                x86_tools.sort(key=lambda loc: loc[2], reverse=True)
                best_match = x86_tools[0]
            else:
                # Last resort: unknown architecture
                unknown_tools = [loc for loc in unique_locations if loc[1] == "unknown"]
                if unknown_tools:
                    best_match = unknown_tools[0]
                else:
                    # Just take the first one if nothing else matches
                    best_match = unique_locations[0]
        else:
            # For non-x64 systems, just take the first one
            best_match = unique_locations[0]
    
    # Log the best match
    logger.info(f"Best match: {best_match[0]} (arch: {best_match[1]}, version: {best_match[2]})")
    
    # Warn if architecture mismatch
    if system_arch == "x64" and best_match[1] in ["arm", "arm64"]:
        logger.warning(f"WARNING: Selected signtool is for {best_match[1]} architecture but system is {system_arch}!")
    
    # Return the best match path
    return best_match[0]

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
        logger.error("You can download the Windows SDK from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
        raise
    
    # Build the command
    command = f'"{signtool_path}" sign /fd SHA256 /t {timestamp_server}'
    if url:
        command += f' /du {url}'
    if description:
        command += f' /d "{description}"'
    command += f' /f "{certificate_file}" /p "{certificate_password}"'
    command += f' /v "{filename}"'
    
    # Don't log the command with the password
    safe_command = command.replace(certificate_password, '********') if certificate_password else command
    logger.info(f"Signing: {os.path.basename(filename)}")
    logger.info(safe_command)
    
    try:
        return subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error signing {filename}: {e}")
        logger.error("Make sure the certificate is valid and you have permission to sign.")
        raise

# Configure basic logging if this module is run directly
if __name__ == "__main__":
    # Set up basic logging configuration for command line usage
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s: %(message)s'
    )
    
    try:
        signtool_path = find_signtool()
        logger.info(f"Best signtool.exe found: {signtool_path}")
        
        # Verify the signtool is usable
        try:
            result = subprocess.run(
                [signtool_path, "/?"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                logger.info("Verified signtool is working correctly.")
            else:
                logger.warning(f"Signtool returned error code {result.returncode}.")
                logger.warning(f"Error output: {result.stderr}")
        except Exception as e:
            logger.warning(f"Could not verify signtool: {e}")
            
    except SignToolNotFoundError as e:
        logger.error(f"Error: {e}")
        logger.error("You can download the Windows SDK from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
