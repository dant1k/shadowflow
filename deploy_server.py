#!/usr/bin/env python3
"""
Система развертывания ShadowFlow на сервере
Поддержка Linux/Ubuntu серверов с systemd
"""

import os
import sys
import subprocess
import json
import shutil
from datetime import datetime

class ServerDeployer:
    def __init__(self):
        self.project_name = "shadowflow"
        self.service_name = "shadowflow"
        self.user = os.getenv('USER', 'ubuntu')
        self.project_dir = f"/home/{self.user}/{self.project_name}"
        self.service_file = f"/etc/systemd/system/{self.service_name}.service"
        self.nginx_config = f"/etc/nginx/sites-available/{self.project_name}"
        
    def log(self, message):
        """Логирование"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def check_requirements(self):
        """Проверка требований сервера"""
        self.log("🔍 Проверка требований сервера...")
        
        requirements = {
            'python3': 'python3 --version',
            'pip3': 'pip3 --version',
            'nginx': 'nginx -v',
            'systemctl': 'systemctl --version'
        }
        
        missing = []
        for tool, command in requirements.items():
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    self.log(f"✅ {tool}: {result.stdout.strip()}")
                else:
                    missing.append(tool)
            except:
                missing.append(tool)
        
        if missing:
            self.log(f"❌ Отсутствуют: {', '.join(missing)}")
            return False
        
        self.log("✅ Все требования выполнены")
        return True
    
    def install_dependencies(self):
        """Установка системных зависимостей"""
        self.log("📦 Установка системных зависимостей...")
        
        commands = [
            "sudo apt update",
            "sudo apt install -y python3 python3-pip python3-venv nginx",
            "sudo apt install -y build-essential cmake",
            "sudo apt install -y git curl wget"
        ]
        
        for cmd in commands:
            self.log(f"Выполняем: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"❌ Ошибка: {result.stderr}")
                return False
        
        self.log("✅ Системные зависимости установлены")
        return True
    
    def create_project_structure(self):
        """Создание структуры проекта на сервере"""
        self.log("📁 Создание структуры проекта...")
        
        # Создаем директории
        dirs = [
            self.project_dir,
            f"{self.project_dir}/logs",
            f"{self.project_dir}/data",
            f"{self.project_dir}/static",
            f"{self.project_dir}/templates"
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
            self.log(f"✅ Создана директория: {dir_path}")
        
        return True
    
    def copy_project_files(self):
        """Копирование файлов проекта"""
        self.log("📋 Копирование файлов проекта...")
        
        # Файлы для копирования
        files_to_copy = [
            'app.py',
            'scheduler.py',
            'start_24_7.py',
            'requirements.txt',
            'api/',
            'analyzer/',
            'ai/',
            'templates/',
            'static/'
        ]
        
        current_dir = os.getcwd()
        
        for item in files_to_copy:
            src = os.path.join(current_dir, item)
            dst = os.path.join(self.project_dir, item)
            
            if os.path.exists(src):
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    self.log(f"✅ Скопирована директория: {item}")
                else:
                    shutil.copy2(src, dst)
                    self.log(f"✅ Скопирован файл: {item}")
            else:
                self.log(f"⚠️ Файл не найден: {item}")
        
        return True
    
    def setup_python_environment(self):
        """Настройка Python окружения"""
        self.log("🐍 Настройка Python окружения...")
        
        # Создаем виртуальное окружение
        venv_cmd = f"cd {self.project_dir} && python3 -m venv venv"
        result = subprocess.run(venv_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.log(f"❌ Ошибка создания venv: {result.stderr}")
            return False
        
        # Активируем и устанавливаем зависимости
        pip_cmd = f"cd {self.project_dir} && source venv/bin/activate && pip install --upgrade pip"
        result = subprocess.run(pip_cmd, shell=True, capture_output=True, text=True)
        
        install_cmd = f"cd {self.project_dir} && source venv/bin/activate && pip install -r requirements.txt"
        result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.log(f"❌ Ошибка установки зависимостей: {result.stderr}")
            return False
        
        self.log("✅ Python окружение настроено")
        return True
    
    def create_systemd_service(self):
        """Создание systemd службы"""
        self.log("⚙️ Создание systemd службы...")
        
        service_content = f"""[Unit]
Description=ShadowFlow - Polymarket Analysis System
After=network.target

[Service]
Type=simple
User={self.user}
WorkingDirectory={self.project_dir}
Environment=PATH={self.project_dir}/venv/bin
ExecStart={self.project_dir}/venv/bin/python {self.project_dir}/start_24_7.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        # Записываем конфигурацию службы
        with open(f"/tmp/{self.service_name}.service", "w") as f:
            f.write(service_content)
        
        # Копируем в systemd
        copy_cmd = f"sudo cp /tmp/{self.service_name}.service {self.service_file}"
        result = subprocess.run(copy_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.log(f"❌ Ошибка создания службы: {result.stderr}")
            return False
        
        # Перезагружаем systemd
        subprocess.run("sudo systemctl daemon-reload", shell=True)
        
        self.log("✅ Systemd служба создана")
        return True
    
    def setup_nginx(self):
        """Настройка Nginx"""
        self.log("🌐 Настройка Nginx...")
        
        nginx_config_content = f"""server {{
    listen 80;
    server_name _;
    
    location / {{
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    location /static {{
        alias {self.project_dir}/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}
"""
        
        # Записываем конфигурацию Nginx
        with open(f"/tmp/{self.project_name}_nginx", "w") as f:
            f.write(nginx_config_content)
        
        # Копируем конфигурацию
        copy_cmd = f"sudo cp /tmp/{self.project_name}_nginx {self.nginx_config}"
        result = subprocess.run(copy_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.log(f"❌ Ошибка настройки Nginx: {result.stderr}")
            return False
        
        # Активируем сайт
        link_cmd = f"sudo ln -sf {self.nginx_config} /etc/nginx/sites-enabled/"
        subprocess.run(link_cmd, shell=True)
        
        # Удаляем дефолтный сайт
        subprocess.run("sudo rm -f /etc/nginx/sites-enabled/default", shell=True)
        
        # Тестируем конфигурацию
        test_cmd = "sudo nginx -t"
        result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.log(f"❌ Ошибка конфигурации Nginx: {result.stderr}")
            return False
        
        # Перезапускаем Nginx
        subprocess.run("sudo systemctl restart nginx", shell=True)
        
        self.log("✅ Nginx настроен")
        return True
    
    def setup_firewall(self):
        """Настройка файрвола"""
        self.log("🔥 Настройка файрвола...")
        
        commands = [
            "sudo ufw allow ssh",
            "sudo ufw allow 'Nginx Full'",
            "sudo ufw --force enable"
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"⚠️ Предупреждение: {result.stderr}")
        
        self.log("✅ Файрвол настроен")
        return True
    
    def start_services(self):
        """Запуск служб"""
        self.log("🚀 Запуск служб...")
        
        # Запускаем ShadowFlow
        start_cmd = f"sudo systemctl start {self.service_name}"
        result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.log(f"❌ Ошибка запуска службы: {result.stderr}")
            return False
        
        # Включаем автозапуск
        enable_cmd = f"sudo systemctl enable {self.service_name}"
        subprocess.run(enable_cmd, shell=True)
        
        # Запускаем Nginx
        subprocess.run("sudo systemctl start nginx", shell=True)
        subprocess.run("sudo systemctl enable nginx", shell=True)
        
        self.log("✅ Службы запущены")
        return True
    
    def check_deployment(self):
        """Проверка развертывания"""
        self.log("🔍 Проверка развертывания...")
        
        # Проверяем статус службы
        status_cmd = f"sudo systemctl status {self.service_name}"
        result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True)
        
        if "active (running)" in result.stdout:
            self.log("✅ ShadowFlow служба работает")
        else:
            self.log("❌ ShadowFlow служба не работает")
            return False
        
        # Проверяем Nginx
        nginx_cmd = "sudo systemctl status nginx"
        result = subprocess.run(nginx_cmd, shell=True, capture_output=True, text=True)
        
        if "active (running)" in result.stdout:
            self.log("✅ Nginx работает")
        else:
            self.log("❌ Nginx не работает")
            return False
        
        # Получаем IP сервера
        ip_cmd = "curl -s ifconfig.me"
        result = subprocess.run(ip_cmd, shell=True, capture_output=True, text=True)
        server_ip = result.stdout.strip()
        
        self.log(f"✅ Сервер доступен по IP: {server_ip}")
        
        return True
    
    def deploy(self):
        """Основной метод развертывания"""
        self.log("🚀 Начало развертывания ShadowFlow на сервер...")
        
        steps = [
            ("Проверка требований", self.check_requirements),
            ("Установка зависимостей", self.install_dependencies),
            ("Создание структуры", self.create_project_structure),
            ("Копирование файлов", self.copy_project_files),
            ("Настройка Python", self.setup_python_environment),
            ("Создание службы", self.create_systemd_service),
            ("Настройка Nginx", self.setup_nginx),
            ("Настройка файрвола", self.setup_firewall),
            ("Запуск служб", self.start_services),
            ("Проверка развертывания", self.check_deployment)
        ]
        
        for step_name, step_func in steps:
            self.log(f"📋 {step_name}...")
            if not step_func():
                self.log(f"❌ Ошибка на шаге: {step_name}")
                return False
        
        self.log("🎉 Развертывание завершено успешно!")
        return True

def main():
    """Основная функция"""
    print("🌐 ShadowFlow Server Deployment")
    print("===============================")
    print("")
    
    deployer = ServerDeployer()
    
    if not deployer.deploy():
        print("❌ Развертывание не удалось")
        sys.exit(1)
    
    print("")
    print("🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!")
    print("============================")
    print("")
    print("🌐 Веб-интерфейс доступен по адресу сервера")
    print("📊 Real-time мониторинг работает")
    print("🔄 Система автоматически перезапускается")
    print("")
    print("🎛️ УПРАВЛЕНИЕ:")
    print("===============")
    print(f"sudo systemctl start {deployer.service_name}")
    print(f"sudo systemctl stop {deployer.service_name}")
    print(f"sudo systemctl restart {deployer.service_name}")
    print(f"sudo systemctl status {deployer.service_name}")
    print("")
    print("📝 ЛОГИ:")
    print("========")
    print(f"sudo journalctl -u {deployer.service_name} -f")
    print(f"tail -f {deployer.project_dir}/logs/24_7.log")

if __name__ == "__main__":
    main()
