from dotenv import load_dotenv
load_dotenv()

import os
import subprocess
import sys

def run_streamlit():
    """Run Streamlit with the right settings."""
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set the working directory
    os.chdir(current_dir)
    
    # Run Streamlit with the right settings
    cmd = [
        sys.executable,  # Use the current Python interpreter
        "-m", "streamlit", "run",
        "app/main.py",
        "--server.runOnSave=true",
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down Streamlit...")
    except Exception as e:
        print(f"Error running Streamlit: {str(e)}")

if __name__ == "__main__":
    run_streamlit() 