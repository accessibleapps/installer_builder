from __future__ import print_function
import subprocess

DEFAULT_TIMESTAMP_SERVER = 'http://timestamp.digicert.com'

def sign(filename, url='', description='', timestamp_server=DEFAULT_TIMESTAMP_SERVER, certificate_file='', certificate_password=''):
  command = 'signtool sign /t {timestamp_server}'
  if url:
    command += ' /du {url}'
  if description:
    command += ' /d {description}'
  command += ' /f "{certificate_file}" /p "{certificate_password}"'
  command += ' /v "{filename}"'
  command = command.format(**locals())
  print(command)
  return subprocess.check_call(command)
