import subprocess
print(subprocess.run(['tail', '-n', '50', '/tmp/fastapi_error.log'], capture_output=True, text=True).stdout)
