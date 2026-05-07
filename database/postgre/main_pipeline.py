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
        "database/common/processing/api_collector.py",
        "database/common/processing/data_processor.py",
        "database/postgre/utils/db_loader.py",
        "database/postgre/utils/vectorizer.py"
    ]
    
    for script in scripts:
        if not run_script(script):
            print(f"Pipeline failed at {script}. Aborting.")
            return
            
    print("\n✅ Pokemon Data Pipeline Update Complete!")

if __name__ == "__main__":
    main()
