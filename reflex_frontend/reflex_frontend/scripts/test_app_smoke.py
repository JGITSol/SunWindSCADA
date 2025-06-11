import subprocess
import time
import pytest
import os
import sys
import requests
from playwright.sync_api import sync_playwright, expect

APP_URL = "http://localhost:3000"
# Ensure paths in the command are correctly escaped for Popen
VENV_PATH = os.path.abspath("c:\\REPOS\\SunWindSCADA\\venv\\Scripts\\python.exe")
APP_START_COMMAND = [VENV_PATH, "-m", "reflex", "run", "--frontend-only"]
APP_CWD = os.path.abspath("c:\\REPOS\\SunWindSCADA\\reflex_frontend")

@pytest.fixture(scope="module")
def reflex_app():
    """Starts and stops the Reflex application for the test module."""
    print(f"Starting Reflex app with command: {' '.join(APP_START_COMMAND)}")
    print(f"Working directory: {APP_CWD}")
    
    process = subprocess.Popen(
        APP_START_COMMAND, 
        cwd=APP_CWD, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP # For Windows to allow sending CTRL_BREAK_EVENT
    )
    
    # Wait for the app to start with a timeout
    max_wait = 60  # Maximum wait time in seconds
    wait_interval = 5  # Check interval in seconds
    elapsed = 0
    
    print(f"Waiting for {APP_URL} to start (timeout: {max_wait}s)...")
    
    while elapsed < max_wait:
        try:
            # Check if the server is responding
            response = requests.get(APP_URL, timeout=2)
            if response.status_code == 200:
                print(f"Reflex app is up and running after {elapsed}s")
                break
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(wait_interval)
        elapsed += wait_interval
        print(f"Still waiting... ({elapsed}s elapsed)")
    

    if process.poll() is not None:
        stdout, stderr = process.communicate()
        pytest.fail(f"Reflex app failed to start. Exit code: {process.returncode}\\nStdout: {stdout.decode(errors='ignore')}\\nStderr: {stderr.decode(errors='ignore')}", pytrace=False)
    else:
        print(f"Reflex app process started with PID: {process.pid}")

    yield APP_URL

    print(f"\\nTerminating Reflex app process {process.pid}...")
    try:
        process.send_signal(subprocess.CTRL_BREAK_EVENT)
        process.wait(timeout=15) # Wait for graceful shutdown
        print("Reflex app terminated gracefully.")
    except subprocess.TimeoutExpired:
        print("Graceful termination timed out. Killing process.")
        process.kill()
        process.wait()
        print("Reflex app killed.")
    except Exception as e:
        print(f"Error during termination: {e}. Killing process.")
        process.kill()
        process.wait()
        print("Reflex app killed due to error during termination.")

def test_app_loads_and_no_console_errors(reflex_app, page):
    """
    Tests if the Reflex application loads, has the correct title,
    and has no JavaScript console errors.
    """
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    print(f"Navigating to {reflex_app}...")
    try:
        page.goto(reflex_app, timeout=45000)  # Increased timeout for page load
        print(f"Successfully navigated to {reflex_app}.")
    except Exception as e:
        error_texts = [err.text for err in console_errors]
        pytest.fail(f"Failed to navigate to {reflex_app}: {e}\\nConsole errors captured so far: {error_texts}", pytrace=False)

    print("Checking page title...")
    try:
        expect(page).to_have_title("SunWindSCADA Dashboard", timeout=20000) # Increased timeout
        print("Page title is correct.")
    except Exception as e:
        error_texts = [err.text for err in console_errors]
        page_content = page.content()
        pytest.fail(f"Page title incorrect or timed out. Expected 'SunWindSCADA Dashboard'. Error: {e}\\nPage Content (first 500 chars):\\n{page_content[:500]}...\\nConsole errors: {error_texts}", pytrace=False)

    # Assert that there are no console errors after page interaction
    if console_errors:
        error_details = "\\n".join([f"  - Type: {err.type}, Text: {err.text}, Location: {err.location}" for err in console_errors])
        pytest.fail(f"JavaScript console errors found:\\n{error_details}", pytrace=False)
    else:
        print("No JavaScript console errors found.")
