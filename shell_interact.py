import subprocess
from config import *


def run_command(cmd):
    process = subprocess.Popen(cmd.split(), stdout = subprocess.PIPE)
    output, error = process.communicate()
    if error:
        print("Error occurred while getting files list. Check CLIENT_FILES_LOC in config.py")
        exit()
    else:
        return output.decode()
