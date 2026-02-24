import subprocess
import sys
import time

def main():
    print("Starting Flask backend...")
    # sys.executable ensures it uses your current Python environment
    flask_process = subprocess.Popen([sys.executable, "backend.py"])
    
    # Give Flask a brief moment to boot up before launching the UI
    time.sleep(2)
    
    print("Starting Streamlit frontend...")
    streamlit_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend.py"])
    
    try:
        # Keep this script running to keep the background processes alive
        flask_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        # Catch Ctrl+C to shut down both servers together
        print("\nShutting down both servers...")
        flask_process.terminate()
        streamlit_process.terminate()
        print("Servers stopped cleanly.")

if __name__ == "__main__":
    main()