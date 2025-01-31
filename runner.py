import subprocess
import os
import pty
import time
import re
import signal
from pydantic import BaseModel

class FileDescriptor(BaseModel):
    fd: int

def check_for_errors(output):
    error_pattern = r"Traceback|Error|Exception"
    if re.search(error_pattern, output, re.IGNORECASE):
        return True
    return False

class TimeoutException(Exception):
    pass

def signal_handler(signum, frame):
    """Signal handler to raise TimeoutException."""
    raise TimeoutException("Command execution exceeded time limit.")

def spawn_python_shell():
    """Start a Python interactive shell subprocess connected to a pseudo-terminal."""
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

def read_output(master: FileDescriptor):
    """Read output from the pseudo-terminal until the Python prompt appears."""
    output = ""
   
    while True:
        try:
            data = os.read(master, 1024).decode('utf-8')
            output += data
            if re.search(r"\n?>>> $", output):  # Detects >>> at the end
                break
            
        except OSError:
            break

    # Remove trailing Python prompts (>>> or ...)
    output = re.sub(r"\n?>>> $", "", output).strip()
    return output

def send_command(process: subprocess.Popen, master: FileDescriptor, command: str):
    """Send a command to the Python subprocess and return the output."""
    # Set up the signal handler for the alarm
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(2)  # Set the alarm for 2 seconds

    try:
        setup_command = "import resource;resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024));"
        os.write(master, (setup_command+"\n" ).encode())
        time.sleep(0.1)  # Give Python some time to process\
        os.write(master, (command+"\n" ).encode())
        time.sleep(0.1)  # Give Python some time to process


        # Read the output
        output = read_output(master)

        # Cancel the alarm if the command finishes before the timeout
        signal.alarm(0)

        # Clean up the output
        output_lines = output.splitlines()
        cleaned_output = []
        for line in output_lines:
            if line.strip(">>>").strip() == command.strip() or line.strip(">>>").strip()  == setup_command.strip():
                continue  # Skip the echoed command
            cleaned_output.append(line)
        stdout = "\n".join(cleaned_output).strip()

        # Check for errors
        if check_for_errors(stdout):
            return {"stderr": stdout}
        return {"stdout": stdout}
    except TimeoutException:
        process.terminate()
        return {"error": "time limit exceeded and the interpreter is dead"}
    except Exception as e:
        return {"error": str(e)}