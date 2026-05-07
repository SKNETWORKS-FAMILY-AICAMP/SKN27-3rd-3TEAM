import schedule
import time
import subprocess
import sys
from datetime import datetime

def job():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled update...")
    # Run the main pipeline
    try:
        subprocess.run([sys.executable, "main_pipeline.py"], check=True)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled update completed successfully.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled update failed: {e}")

# 매일 오전 9시에 실행
schedule.every().day.at("09:00").do(job)

print("📅 Pokemon Data Scheduler Started.")
print("The pipeline will run every day at 09:00 AM.")
print("Press Ctrl+C to stop.")

# 테스트를 위해 즉시 실행하고 싶다면 아래 주석을 해제하세요
# job()

while True:
    schedule.run_pending()
    time.sleep(60) # 1분마다 체크
