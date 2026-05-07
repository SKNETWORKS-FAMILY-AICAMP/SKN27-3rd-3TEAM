import subprocess
import sys
import os

def run_script(script_path):
    print(f"\n--- Running {script_path} ---")
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e}")
        return False

def main():
    print("Starting Pokemon Data Pipeline Update...")
    
    scripts = [
        # "data/collectors/api_collector.py",
        "data/processing/data_processor.py",
        "data/database/db_loader.py"
        # "data/database/vectorizer.py"
    ]
    
    for script in scripts:
        if not run_script(script):
            print(f"Pipeline failed at {script}. Aborting.")
            return
            
    print("\n✅ Pokemon Data Pipeline Update Complete!")

if __name__ == "__main__":
    main()
