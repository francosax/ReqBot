import sys
import subprocess
import os

# Define the path to your PySide6 application script
# Make sure this path is correct relative to run_app.py
APP_SCRIPT_PATH = "main_app.py"

def run_gui_app():
    """
    Launches the PySide6 GUI application.
    """
    print(f"Attempting to launch {APP_SCRIPT_PATH}...")
    try:
        # Use sys.executable to ensure the correct Python from the venv is used
        subprocess.run([sys.executable, APP_SCRIPT_PATH], check=True)
    except FileNotFoundError:
        print(f"Error: Python executable not found at {sys.executable}.")
        print("Please ensure your virtual environment is activated or Python is in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error launching the application: {e}")
        print(f"Stderr: {e.stderr.decode()}") if e.stderr else ""
        print(f"Stdout: {e.stdout.decode()}") if e.stdout else ""
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def run_tests():
    """
    Runs your pytest tests.
    """
    print("Running pytest tests...")
    try:
        # Ensure pytest is installed in your venv: pip install pytest pytest-qt
        # Use sys.executable to run pytest from the venv
        subprocess.run([sys.executable, "-m", "pytest"], check=True)
    except FileNotFoundError:
        print(f"Error: Python executable not found at {sys.executable}.")
        print("Please ensure your virtual environment is activated or Python is in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        print(f"Stderr: {e.stderr.decode()}") if e.stderr else ""
        print(f"Stdout: {e.stdout.decode()}") if e.stdout else ""
    except Exception as e:
        print(f"An unexpected error occurred while running tests: {e}")


if __name__ == "__main__":
    print("Welcome to RequirementBot Launcher!")
    print("1. Launch GUI Application")
    print("2. Run Tests")
    print("3. Exit")

    while True:
        choice = input("Enter your choice (1, 2, or 3): ")
        if choice == '1':
            run_gui_app()
            break # Exit after launching GUI
        elif choice == '2':
            run_tests()
            # Don't break here if you want to allow running GUI after tests
            # break
        elif choice == '3':
            print("Exiting launcher.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")