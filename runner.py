import subprocess
import os
import pty
import time
import re
import signal
from fastapi import FastAPI

def check_for_errors(output):
    error_pattern = r"Traceback|Error|Exception"

    if re.search(error_pattern, output, re.IGNORECASE):
        return True
    else:
        return False
class TimeoutException(Exception):
    pass

def signal_handler(signum, frame):
    """ Signal handler to raise TimeoutException """
    raise TimeoutException("Command execution exceeded time limit.")

def spawn_python_shell():
    """ Start a Python interactive shell subprocess connected to a pseudo-terminal """
    master, slave = pty.openpty()  # Create a pseudo-terminal pair

    process = subprocess.Popen(
        ['python3', '-i'],  # Ensure interactive mode
        stdin=slave,
        stdout=slave,
        stderr=slave,
        text=True,
        close_fds=True
    )

    os.close(slave)  # Close the slave end in the parent process
    read_output(master)  # Clear initial Python shell output
    return process, master

def read_output(master):
    """ Read output from the pseudo-terminal until the Python prompt appears """
    output = ""

    while True:
        try:
            data = os.read(master, 1024).decode('utf-8')
            output += data
            if re.search(r"\n?>>> $", output):  # Detects `>>>` at the end
                break
        except OSError:
            break

    # Remove trailing Python prompts (`>>>` or `...`)
    output = re.sub(r"\n?>>> $", "", output).strip()
    
    return output

def send_command(process, master, command):
    """ Send a command to the Python subprocess and return the output,
      with a 2-second timeout and 100 MB memory limit """
    command = "import resource;resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024));" + command
    
    # Set up the signal handler for the alarm
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(2)  # Set the alarm for 2 seconds

    try:
        os.write(master, (command + "\n").encode())  # Send command
        time.sleep(0.1)  # Give Python some time to process

        output = read_output(master)  # Read output

        # Cancel the alarm if the command finishes before the timeout
        signal.alarm(0)
        
      
        output_lines = output.splitlines()
        cleaned_output = []
        for line in output_lines:
            if line.strip() == command.strip():
                continue  # Skip the echoed command
            cleaned_output.append(line)
        stdout="\n".join(cleaned_output).strip()
        if (len(cleaned_output) and cleaned_output[-1].startswith("MemoryError")): #check for memory error
            return {"error":"memory limit exceeded"}
        if  check_for_errors(stdout): # detect if an execution error occured
            return {"stderr":stdout}
        return {"stdout":stdout}
    except TimeoutException:
        return {"error": "time limit exceeded"}

# Spawn Python shell
process, master = spawn_python_shell()

# tests
'''
print(send_command(process, master, 'print("hi")'))  # Should print "hi"
print(send_command(process, master, 'x=5'))  # Should be empty (variable assignment)
print(send_command(process, master, 'print(x * 2)'))  
print(send_command(process, master, '1/0'))  
print(send_command(process,master,'x="c"*100*2**20'))
print(send_command(process, master, 'import time;time.sleep(4)'))
'''