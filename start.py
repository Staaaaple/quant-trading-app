#!/usr/bin/env python3
"""一键启动前后端开发环境."""

import os
import signal
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# 启动后端 (conda quant 环境 + uvicorn)
backend_cmd = [
    "conda", "run", "-n", "quant", "--live-stream",
    "python", "-m", "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", "8000", "--reload",
]

# 启动前端 (npm run dev)
frontend_cmd = ["npm", "run", "dev"]

processes = []


def cleanup(signum, frame):
    print("\n[shutdown] 正在关闭服务...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            p.kill()
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def main():
    print("[start] 启动后端服务: http://127.0.0.1:8000")
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    processes.append(backend_proc)

    # 等待后端启动
    time.sleep(2)

    print("[start] 启动前端服务...")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    processes.append(frontend_proc)

    print("[start] 服务已启动。按 Ctrl+C 停止。\n")

    # 合并输出
    try:
        while True:
            for p in processes:
                line = p.stdout.readline()
                if line:
                    prefix = "[backend]" if p == backend_proc else "[frontend]"
                    print(f"{prefix} {line}", end="")
            time.sleep(0.05)
    except KeyboardInterrupt:
        cleanup(None, None)


if __name__ == "__main__":
    main()
