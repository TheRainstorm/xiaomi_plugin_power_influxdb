from apscheduler.schedulers.background import BackgroundScheduler
import signal  # Linux/macOS
import time    # Windows备用
import os    # Windows备用
from datetime import datetime
import math

from task import task

INTERVAL = int(os.getenv("INTERVAL", "5"))  # 从环境变量读取间隔时间，默认为5秒
print(f"任务执行间隔: {INTERVAL} 秒")

# 计算下一个对齐的时间点
now_ts = time.time()
next_ts = math.ceil(now_ts / INTERVAL) * INTERVAL
start_date = datetime.fromtimestamp(next_ts)
print(f"任务将于 {start_date} 开始执行")

scheduler = BackgroundScheduler()
scheduler.add_job(task, 'interval', seconds=INTERVAL, start_date=start_date)
scheduler.start()

# 平台兼容性处理
if hasattr(signal, 'pause'):  # Linux/macOS
    signal.pause()            # 主线程完全挂起，CPU占用0%
else:                         # Windows
    while True:
        time.sleep(3600)      # 休眠1小时，期间CPU占用≈0%