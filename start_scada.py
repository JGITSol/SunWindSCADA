#!/usr/bin/env python
"""
SunWindSCADA Startup Script
---------------------------
This script starts all components of the SCADA system:
1. Django backend server
2. Reflex frontend
3. Simulation engine

Usage:
    python start_scada.py [--init-db]

Options:
    --init-db: Initialize the database with sample data
"""
import os
import sys
import subprocess
import time
import argparse
import signal
import threading
import webbrowser

# Parse command line arguments
parser = argparse.ArgumentParser(description='Start the SunWindSCADA system')
parser.add_argument('--init-db', action='store_true', help='Initialize the database with sample data')
args = parser.parse_args()

# Global variables
processes = []
stop_event = threading.Event()

def run_command(command, cwd=None, env=None):
    """Run a command and return the process"""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    processes.append(process)
    
    # Start a thread to read and print the output
    def read_output():
        for line in process.stdout:
            print(f"[{command}] {line.strip()}")
    
    thread = threading.Thread(target=read_output)
    thread.daemon = True
    thread.start()
    
    return process

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    print("\nShutting down...")
    stop_event.set()
    
    # Terminate all processes
    for process in processes:
        process.terminate()
    
    # Wait for processes to terminate
    for process in processes:
        process.wait()
    
    print("All processes terminated")
    sys.exit(0)

def main():
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Set environment variables
    env = os.environ.copy()
    
    # Project paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    django_dir = os.path.join(project_dir, 'django_backend')
    reflex_dir = os.path.join(project_dir, 'reflex_frontend')
    
    print("Starting SunWindSCADA system...")
    
    # Initialize database if requested
    if args.init_db:
        print("Initializing database...")
        init_db_process = run_command(
            'python manage.py migrate && python manage.py initialize_data',
            cwd=django_dir,
            env=env
        )
        init_db_process.wait()
        print("Database initialized")
    
    # Start Django backend
    print("Starting Django backend...")
    django_process = run_command(
        'python -m uvicorn django_backend.config.asgi:application --reload --host 0.0.0.0 --port 8000',
        cwd=project_dir,
        env=env
    )
    
    # Wait for Django to start
    time.sleep(5)
    
    # Start simulation engine
    print("Starting simulation engine...")
    simulation_process = run_command(
        'python manage.py shell -c "from django_backend.apps.core.tasks import start_simulation; start_simulation()"',
        cwd=django_dir,
        env=env
    )
    
    # Start Reflex frontend
    print("Starting Reflex frontend...")
    reflex_process = run_command(
        'reflex run',
        cwd=reflex_dir,
        env=env
    )
    
    # Wait for Reflex to start
    time.sleep(5)
    
    # Open browser
    print("Opening browser...")
    webbrowser.open('http://localhost:3000')
    
    print("\nSunWindSCADA system is running!")
    print("Django API: http://localhost:8000/api/")
    print("Reflex Dashboard: http://localhost:3000")
    print("\nPress Ctrl+C to stop")
    
    # Wait for stop event
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == '__main__':
    main()
