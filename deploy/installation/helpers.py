import os
import time
from distutils import util

import requests
from fabric.context_managers import settings, hide, quiet
from fabric.operations import sudo

project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

runtime_vars = ''


# Check URL availability (Status code 200)
def check_is_up(url, timeout=10, username='admin', password='password', delay_seconds=1):
    print_title(f"Check for availability: {url}")
    status_code = ""
    start_time = time.time()
    while not status_code == 200:
        duration = int(time.time() - start_time)
        if timeout is not None and duration > timeout:
            break
        try:
            status_code = requests.get(url, auth=(username, password)).status_code
        except:
            print(f"Checking for availability: {url}")
            time.sleep(delay_seconds)
        time.sleep(delay_seconds)
        print(f"Checking for availability: {url}")
    try:
        assert status_code == 200, f"URL {url} is not reachable."
    except:
        print(f"URL {url} is NOT reachable.")
        exit(1)
    print(f"URL: {url} is AVAILABLE")


# Remove trailing '/' from URLs
def normalize_url(url):
    if url.endswith('/'):
        url = url[:-1]
    return url


# Detect target machine's OS
def detect_os():
    with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
        release_info = sudo("cat /etc/*release*")
        if 'ubuntu' in release_info:
            return "ubuntu"
        elif 'debian' in release_info:
            return "debian"
        elif 'centos' in release_info:
            return "centos"
        elif 'redhat' in release_info:
            return "redhat"
        else:
            raise Exception(f"Operational System could not be detected. Content: {release_info}")


def is_debug_mode():
    return bool(util.strtobool(os.getenv("DEBUG_MODE", "False")))


def print_debug(message):
    if is_debug_mode():
        print(message)


# Just a better way to print titles
def print_title(title):
    formatted_title = f"***** {title} *****"
    print("")
    print("*" * len(formatted_title))
    print(formatted_title)
    print("*" * len(formatted_title))


# Parse boolean command line arguments properly
def parse_bool_param(param):
    result = False
    if type(param) is str:
        result = True if param.lower() == 'true' else False
    elif type(param) is bool:
        result = param
    return result


# Stop and remove containers for a specific service
def clean_containers(service):
    print_title(f"Clean containers for service {service}")
    with quiet():
        try:
            sudo(f"docker rm -vf $(docker ps -a -q --filter='name={service}*')")
        except:
            print(f"Service '{service}' is not running")
