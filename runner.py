import subprocess
import os
import pty
import time
import re
import signal
from fastapi import FastAPI

# Global flag to handle timeout exception
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
    """ Send a command to the Python subprocess and return the output, with a 2-second timeout """
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
        
        # Remove echoed command from output
        output_lines = output.splitlines()
        cleaned_output = []
        for line in output_lines:
            if line.strip() == command.strip():
                continue  # Skip the echoed command
            cleaned_output.append(line)

        return "\n".join(cleaned_output).strip()
    except MemoryError:
        "Error: memory limit exceeded."
    except TimeoutException:
        return "Error: Command execution exceeded time limit."

# Spawn Python shell
process, master = spawn_python_shell()

# Example commands
print(send_command(process, master, 'print("hi")'))  # Should print "hi"
print(send_command(process, master, 'x = 5'))  # Should be empty (variable assignment)
print(send_command(process, master, 'print(x * 2)'))  
print(send_command(process,master,'x="c"*100*2**20'))
print(send_command(process, master, 'import time;time.sleep(4)'))
