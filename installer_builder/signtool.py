from __future__ import print_function
import os
import subprocess
import sys

DEFAULT_TIMESTAMP_SERVER = 'http://timestamp.digicert.com'

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
  """
  if not os.path.exists(filename):
    raise FileNotFoundError(f"File to sign not found: {filename}")
    
  if not certificate_file or not os.path.exists(certificate_file):
    raise FileNotFoundError(f"Certificate file not found: {certificate_file}")
    
  command = 'signtool sign /t {timestamp_server}'
  if url:
    command += ' /du {url}'
  if description:
    command += ' /d {description}'
  command += ' /f "{certificate_file}" /p "{certificate_password}"'
  command += ' /v "{filename}"'
  command = command.format(**locals())
  
  # Don't print the command with the password
  safe_command = command.replace(certificate_password, '********') if certificate_password else command
  print(f"Signing: {os.path.basename(filename)}")
  print(safe_command)
  
  try:
    return subprocess.check_call(command, shell=True)
  except subprocess.CalledProcessError as e:
    print(f"Error signing {filename}: {e}")
    print("Make sure signtool.exe is in your PATH and the certificate is valid.")
    raise
