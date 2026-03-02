#!/usr/bin/env python3
"""
Force Kill Python Processes & Start System
Находит и убивает все процессы занимающие порты 8000-8010
"""
import os
import signal
import socket
import subprocess
import time
import sys

def find_process_on_port(port):
    """Найти PID процесса на порту через /proc"""
    for pid_dir in os.listdir('/proc'):
        if not pid_dir.isdigit():
            continue
        
        try:
            pid = int(pid_dir)
            # Проверяем fd (file descriptors)
            fd_dir = f'/proc/{pid}/fd'
            if not os.path.exists(fd_dir):
                continue
            
            for fd in os.listdir(fd_dir):
                try:
                    link = os.readlink(f'{fd_dir}/{fd}')
                    if f'socket:' in link or f'port {port}' in link:
                        # Проверяем cmdline
                        try:
                            with open(f'/proc/{pid}/cmdline', 'r') as f:
                                cmdline = f.read()
                                if 'python' in cmdline and ('run.py' in cmdline or 'orchestrator' in cmdline):
                                    return pid
                        except:
                            pass
                except:
                    continue
        except:
            continue
    
    # Альтернатива: ищем по cmdline
    for pid_dir in os.listdir('/proc'):
        if not pid_dir.isdigit():
            continue
        try:
            with open(f'/proc/{pid_dir}/cmdline', 'r') as f:
                cmdline = f.read()
                if 'python' in cmdline and 'run.py' in cmdline:
                    return int(pid_dir)
        except:
            pass
    
    return None

def kill_process(pid):
    """Убить процесс"""
    try:
        os.kill(pid, signal.SIGKILL)
        print(f"✅ Убит процесс {pid}")
        return True
    except:
        return False

def is_port_in_use(port):
    """Проверить порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    print("="*60)
    print("🔥 Force Kill & Start System")
    print("="*60)
    
    # Находим и убиваем процессы на портах 8000-8010
    for port in range(8000, 8011):
        pid = find_process_on_port(port)
        if pid:
            print(f"⚠️  Порт {port} занят процессом {pid}")
            kill_process(pid)
    
    # Ждём освобождения
    print("\n⏳ Ожидание освобождения портов...")
    time.sleep(5)
    
    # Проверяем
    free_port = 8000
    for port in range(8000, 8020):
        if not is_port_in_use(port):
            free_port = port
            break
    
    print(f"✅ Свободный порт: {free_port}")
    
    # Запускаем систему
    print("\n🚀 Запуск системы...")
    os.chdir('/home/hp/recruitment_agents')
    
    env = os.environ.copy()
    env['ORCHESTRATOR_PORT'] = str(free_port)
    
    proc = subprocess.Popen(
        ['python', 'run.py'],
        env=env,
        stdout=open('/tmp/recruitment.log', 'w'),
        stderr=subprocess.STDOUT
    )
    
    print(f"✅ Система запущена (PID: {proc.pid})")
    print(f"📊 Порт: {free_port}")
    
    # Ждём запуска
    time.sleep(15)
    
    # Проверяем
    print("\n📊 Проверка статуса...")
    try:
        import urllib.request
        import json
        url = f'http://localhost:{free_port}/status'
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
            print("\n✅ Статус системы:")
            print(f"   Orchestrator: {data.get('orchestrator', 'unknown')}")
            agents = data.get('agents', {})
            for agent, status in agents.items():
                alive = "✅" if status.get('alive') else "⏳"
                print(f"   {alive} {agent.title()}")
    except Exception as e:
        print(f"⏳ Система запускается... ({e})")
    
    print("\n" + "="*60)
    print(f"📊 Dashboard: http://localhost:{free_port}/dashboard")
    print("="*60)

if __name__ == "__main__":
    main()
