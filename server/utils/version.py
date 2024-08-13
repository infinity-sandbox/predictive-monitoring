from datetime import datetime
from logs.loggers.logger import logger_config
logger = logger_config(__name__)
import os

def set_version_and_build(version_file='VERSION') -> tuple:
    x, y, z = 0, 0, 0  # Default starting version if file doesn't exist
    build_time = ""

    # Check if the file exists and read the current version and build time
    if os.path.exists(version_file):
        with open(version_file, 'r') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                x, y, z = map(int, lines[0].strip().split('.'))
                build_time = lines[1].strip()

    # Increment the patch version (z)
    z += 1

    # Check if z needs to reset and y needs to increment
    if z > 200:
        z = 0
        y += 1

    # Check if y needs to reset and x needs to increment
    if y > 200:
        y = 0
        x += 1

    # Update the build time
    build_time = datetime.now().strftime('%Y%m%d%H%M%S')

    # Write the updated version and build time back to the file
    with open(version_file, 'w') as file:
        file.write(f'{x}.{y}.{z}\n')
        file.write(build_time)

    return f'{x}.{y}.{z}', build_time

def get_version_and_build(version_file='VERSION') -> tuple:
    x, y, z = 0, 0, 0  # Default starting version if file doesn't exist
    build_time = ""

    # Check if the file exists and read the current version and build time
    if os.path.exists(version_file):
        with open(version_file, 'r') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                x, y, z = map(int, lines[0].strip().split('.'))
                build_time = lines[1].strip()
                
    return f'{x}.{y}.{z}', build_time

if __name__ == '__main__':
    # Example of how to use the function
    version, build_time = set_version_and_build()
    