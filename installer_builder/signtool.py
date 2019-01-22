import subprocess

def sign(filename, url='', description='', certificate_file='', certificate_password=''):
  command = 'signtool sign /v {filename}'
  if url:
    command += ' /du {url}'
  if description:
    command += ' /d {description}'
  command += ' /f {certificate_file} /p {certificate_password}'
  command = command.format(**locals())
  print command
  return subprocess.check_call(command)
