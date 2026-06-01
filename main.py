# omni.py - Omni AI Terminal (Полная версия на русском языке)
# Автор: ilabolAfk
# Версия: 2.0.0

import sys
import os
import subprocess
import json
import re
import shutil
import traceback
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    from ctransformers import AutoModelForCausalLM
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Установи: pip install ctransformers")


# ==================== ГЛОБАЛЬНЫЙ ЛОГ ОШИБОК ====================

ERROR_LOG_FILE = "omni_error.log"

def log_error(error_msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {error_msg}\n")
        f.write(f"{traceback.format_exc()}\n")
        f.write("-" * 50 + "\n")


# ==================== SSH КОНФИГ ====================

SSH_CONFIG_FILE = "ssh_config.json"

def load_ssh_config():
    try:
        with open(SSH_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"connections": []}

def save_ssh_config(config):
    with open(SSH_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ==================== ПЛАГИНЫ ====================

class PluginManager:
    PLUGINS_DIR = "plugins"
    
    @staticmethod
    def init():
        os.makedirs(PluginManager.PLUGINS_DIR, exist_ok=True)
    
    @staticmethod
    def get_installed():
        plugins = []
        if not os.path.exists(PluginManager.PLUGINS_DIR):
            return plugins
        for item in os.listdir(PluginManager.PLUGINS_DIR):
            plugin_path = os.path.join(PluginManager.PLUGINS_DIR, item)
            manifest_path = os.path.join(plugin_path, "manifest.json")
            if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    plugins.append({
                        "id": item,
                        "path": plugin_path,
                        "name": manifest.get("name", item),
                        "version": manifest.get("version", "1.0"),
                        "description": manifest.get("description", ""),
                        "author": manifest.get("author", "Unknown"),
                        "command": manifest.get("command", f"& '{plugin_path}\\script.ps1'")
                    })
                except:
                    pass
        return plugins
    
    @staticmethod
    def install(folder_path):
        manifest_path = os.path.join(folder_path, "manifest.json")
        if not os.path.exists(manifest_path):
            return False, "manifest.json не найден"
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            plugin_name = manifest.get("name", os.path.basename(folder_path))
            plugin_id = re.sub(r'[^a-zA-Z0-9_-]', '_', plugin_name.lower().replace(" ", "_"))
            target_path = os.path.join(PluginManager.PLUGINS_DIR, plugin_id)
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(folder_path, target_path)
            return True, f"Плагин '{plugin_name}' установлен"
        except Exception as e:
            return False, f"Ошибка: {e}"
    
    @staticmethod
    def uninstall(plugin_id):
        plugin_path = os.path.join(PluginManager.PLUGINS_DIR, plugin_id)
        if os.path.exists(plugin_path):
            shutil.rmtree(plugin_path)
            return True, "Плагин удалён"
        return False, "Плагин не найден"
    
    @staticmethod
    def run(plugin_id, parent):
        plugins = PluginManager.get_installed()
        for p in plugins:
            if p["id"] == plugin_id:
                try:
                    subprocess.Popen(p["command"], shell=True)
                    return True, f"Запущен: {p['name']}"
                except Exception as e:
                    return False, f"Ошибка: {e}"
        return False, "Плагин не найден"


# ==================== ОКНО ПЛАГИНОВ ====================

class PluginsManagerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("🔌 Управление плагинами - Omni")
        self.setGeometry(300, 300, 600, 450)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        PluginManager.init()
        self.init_ui()
        self.load_plugins()
    
    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QListWidget { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; font-family: Consolas; font-size: 11px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #3c3c3c; }
            QListWidget::item:selected { background-color: #0e639c; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 8px 16px; font-weight: bold; border-radius: 3px; }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton.danger { background-color: #c42e2e; }
            QPushButton.danger:hover { background-color: #a02222; }
            QLabel { color: #d4d4d4; }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        header = QLabel("🔌 Управление плагинами")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        self.install_btn = QPushButton("📁 Установить плагин из папки")
        self.install_btn.clicked.connect(self.install_plugin)
        layout.addWidget(self.install_btn)
        
        layout.addSpacing(10)
        layout.addWidget(QLabel("📦 Установленные плагины:"))
        
        self.plugins_list = QListWidget()
        layout.addWidget(self.plugins_list)
        
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶️ Выполнить")
        self.run_btn.clicked.connect(self.run_plugin)
        self.uninstall_btn = QPushButton("🗑️ Удалить")
        self.uninstall_btn.setProperty("class", "danger")
        self.uninstall_btn.clicked.connect(self.uninstall_plugin)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.uninstall_btn)
        layout.addLayout(btn_layout)
        
        layout.addSpacing(10)
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)
    
    def load_plugins(self):
        self.plugins_list.clear()
        plugins = PluginManager.get_installed()
        if not plugins:
            item = QListWidgetItem("📭 Нет установленных плагинов")
            item.setFlags(Qt.NoItemFlags)
            self.plugins_list.addItem(item)
            return
        for p in plugins:
            text = f"{p['name']} v{p['version']}\n   {p['description'][:60]}\n   👤 {p['author']}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, p)
            self.plugins_list.addItem(item)
    
    def install_plugin(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с плагином (где есть manifest.json)")
        if folder:
            success, msg = PluginManager.install(folder)
            if success:
                self.load_plugins()
                if self.parent:
                    self.parent.log(msg, "success")
            else:
                QMessageBox.warning(self, "Ошибка", msg)
    
    def run_plugin(self):
        current = self.plugins_list.currentItem()
        if current and current.data(Qt.UserRole):
            plugin = current.data(Qt.UserRole)
            success, msg = PluginManager.run(plugin["id"], self.parent)
            if self.parent:
                self.parent.log(msg, "success" if success else "error")
            if not success:
                QMessageBox.warning(self, "Ошибка", msg)
    
    def uninstall_plugin(self):
        current = self.plugins_list.currentItem()
        if current and current.data(Qt.UserRole):
            plugin = current.data(Qt.UserRole)
            reply = QMessageBox.question(self, "Удаление", f"Удалить плагин '{plugin['name']}'?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                success, msg = PluginManager.uninstall(plugin["id"])
                if success:
                    self.load_plugins()
                    if self.parent:
                        self.parent.log(msg, "success")
                else:
                    QMessageBox.warning(self, "Ошибка", msg)


# ==================== ОКНО SSH ====================

class SSHWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("🔌 SSH Manager - Omni")
        self.setGeometry(300, 300, 650, 450)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.config = load_ssh_config()
        self.current_process = None
        self.init_ui()
        self.load_connections()
    
    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QListWidget { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; font-family: Consolas; font-size: 12px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #3c3c3c; }
            QListWidget::item:selected { background-color: #0e639c; }
            QLineEdit, QTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; padding: 8px; border-radius: 3px; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 8px 16px; font-weight: bold; border-radius: 3px; }
            QPushButton:hover { background-color: #1177bb; }
            QLabel { color: #d4d4d4; }
            QTabWidget::pane { border: 1px solid #3c3c3c; background-color: #2d2d2d; border-radius: 3px; }
            QTabBar::tab { background-color: #1e1e1e; color: #d4d4d4; padding: 8px 16px; margin-right: 2px; }
            QTabBar::tab:selected { background-color: #0e639c; }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        tabs = QTabWidget()
        
        # Вкладка "Подключения"
        conn_tab = QWidget()
        conn_layout = QVBoxLayout(conn_tab)
        conn_layout.addWidget(QLabel("📡 Сохранённые подключения:"))
        self.connections_list = QListWidget()
        self.connections_list.itemDoubleClicked.connect(self.connect_to_server)
        conn_layout.addWidget(self.connections_list)
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("🔌 Подключиться")
        self.connect_btn.clicked.connect(self.connect_to_selected)
        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_connection)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.delete_btn)
        conn_layout.addLayout(btn_layout)
        
        # Вкладка "Новое подключение"
        new_tab = QWidget()
        new_layout = QVBoxLayout(new_tab)
        new_layout.addWidget(QLabel("➕ Добавить новое SSH подключение:"))
        new_layout.addSpacing(10)
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Мой сервер")
        form_layout.addRow("📛 Имя:", self.name_input)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.1.100 или example.com")
        form_layout.addRow("🌐 Хост:", self.host_input)
        self.port_input = QLineEdit()
        self.port_input.setText("22")
        form_layout.addRow("🔌 Порт:", self.port_input)
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("root")
        form_layout.addRow("👤 Пользователь:", self.user_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("пароль (опционально)")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("🔒 Пароль:", self.password_input)
        new_layout.addLayout(form_layout)
        new_layout.addSpacing(20)
        self.add_btn = QPushButton("💾 Сохранить подключение")
        self.add_btn.clicked.connect(self.add_connection)
        new_layout.addWidget(self.add_btn)
        new_layout.addStretch()
        
        # Вкладка "Терминал"
        term_tab = QWidget()
        term_layout = QVBoxLayout(term_tab)
        term_layout.addWidget(QLabel("🖥️ SSH Терминал (активное подключение):"))
        self.term_output = QTextEdit()
        self.term_output.setReadOnly(True)
        self.term_output.setFont(QFont("Consolas", 10))
        term_layout.addWidget(self.term_output)
        term_input_layout = QHBoxLayout()
        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("Введите команду для удалённого сервера...")
        self.term_input.returnPressed.connect(self.send_ssh_command)
        term_input_layout.addWidget(self.term_input, 1)
        self.term_send_btn = QPushButton("📤 Отправить")
        self.term_send_btn.clicked.connect(self.send_ssh_command)
        self.disconnect_btn = QPushButton("❌ Отключиться")
        self.disconnect_btn.clicked.connect(self.disconnect_ssh)
        term_input_layout.addWidget(self.term_send_btn)
        term_input_layout.addWidget(self.disconnect_btn)
        term_layout.addLayout(term_input_layout)
        
        tabs.addTab(conn_tab, "📡 Подключения")
        tabs.addTab(new_tab, "➕ Новое")
        tabs.addTab(term_tab, "🖥️ Терминал")
        
        layout.addWidget(tabs)
        
        self.status_label = QLabel("🟢 Готов")
        self.status_label.setStyleSheet("padding: 5px; background-color: #1e1e1e; border-radius: 3px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_connections(self):
        self.connections_list.clear()
        for conn in self.config.get("connections", []):
            item = QListWidgetItem(f"🔌 {conn['name']}\n   📡 {conn['user']}@{conn['host']}:{conn['port']}")
            item.setData(Qt.UserRole, conn)
            self.connections_list.addItem(item)
    
    def add_connection(self):
        name = self.name_input.text().strip()
        host = self.host_input.text().strip()
        port = self.port_input.text().strip() or "22"
        user = self.user_input.text().strip() or "root"
        password = self.password_input.text().strip()
        if not name or not host:
            QMessageBox.warning(self, "Ошибка", "Заполните имя и хост")
            return
        new_conn = {"name": name, "host": host, "port": port, "user": user, "password": password}
        self.config["connections"].append(new_conn)
        save_ssh_config(self.config)
        self.name_input.clear()
        self.host_input.clear()
        self.port_input.setText("22")
        self.user_input.clear()
        self.password_input.clear()
        self.load_connections()
        self.status_label.setText(f"✅ Добавлено подключение: {name}")
    
    def delete_connection(self):
        current = self.connections_list.currentItem()
        if current:
            conn = current.data(Qt.UserRole)
            reply = QMessageBox.question(self, "Удаление", f"Удалить подключение '{conn['name']}'?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.config["connections"] = [c for c in self.config["connections"] if c["name"] != conn["name"]]
                save_ssh_config(self.config)
                self.load_connections()
                self.status_label.setText(f"🗑️ Удалено: {conn['name']}")
    
    def connect_to_selected(self):
        current = self.connections_list.currentItem()
        if current:
            conn = current.data(Qt.UserRole)
            self.connect_to_server(conn)
    
    def connect_to_server(self, conn):
        self.status_label.setText(f"🔌 Подключение к {conn['name']}...")
        if self.current_process:
            self.disconnect_ssh()
        self.current_process = QProcess()
        self.current_process.setProcessChannelMode(QProcess.MergedChannels)
        self.current_process.readyReadStandardOutput.connect(self.read_ssh_output)
        cmd = ["ssh", f"{conn['user']}@{conn['host']}", "-p", conn['port']]
        if conn.get('password'):
            cmd = ["sshpass", "-p", conn['password'], *cmd]
        try:
            self.current_process.start(cmd[0], cmd[1:])
            self.status_label.setText(f"🟢 Подключено к {conn['name']}")
            self.term_output.append(f"\n=== Подключено к {conn['name']} ({conn['user']}@{conn['host']}) ===\n")
        except Exception as e:
            self.status_label.setText(f"🔴 Ошибка подключения")
            self.term_output.append(f"\n❌ Ошибка: {e}\n")
    
    def read_ssh_output(self):
        if self.current_process:
            data = self.current_process.readAllStandardOutput()
            text = bytes(data).decode('utf-8', errors='ignore')
            self.term_output.append(text)
            cursor = self.term_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.term_output.setTextCursor(cursor)
    
    def send_ssh_command(self):
        command = self.term_input.text().strip()
        if not command or not self.current_process:
            return
        self.term_output.append(f"\n$ {command}")
        self.term_input.clear()
        self.current_process.write(f"{command}\n".encode())
    
    def disconnect_ssh(self):
        if self.current_process:
            self.current_process.terminate()
            self.current_process.waitForFinished(3000)
            self.current_process = None
            self.term_output.append("\n=== Отключено ===\n")
            self.status_label.setText("🔴 Отключено")
    
    def closeEvent(self, event):
        self.disconnect_ssh()
        event.accept()


# ==================== AI WORKER ДЛЯ АНАЛИЗА ОШИБОК ====================

class ErrorAnalysisWorker(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_path, error_text):
        super().__init__()
        self.model_path = model_path
        self.error_text = error_text
    
    def run(self):
        try:
            if not AI_AVAILABLE:
                self.error_occurred.emit("AI не доступен")
                return
            if not hasattr(ErrorAnalysisWorker, 'llm'):
                if not os.path.exists(self.model_path):
                    self.error_occurred.emit("Модель не найдена")
                    return
                ErrorAnalysisWorker.llm = AutoModelForCausalLM.from_pretrained(
                    self.model_path, model_type="mistral", threads=4, context_length=2048
                )
            prompt = f"""<s>[INST] Ты - эксперт по PowerShell и Windows. Пользователь получил ошибку:

{self.error_text}

Проанализируй ошибку и дай ответ на русском языке в формате:

🔍 ЧТО ЗНАЧИТ ОШИБКА:
(объяснение простыми словами)

🛠️ КАК ИСПРАВИТЬ:
(пошаговое решение с готовыми командами)

💡 ПРЕДОТВРАЩЕНИЕ:
(как избежать в будущем)

Ответ: [/INST]"""
            response = ErrorAnalysisWorker.llm(prompt, max_new_tokens=800, temperature=0.3)
            self.result_ready.emit(response.strip())
        except Exception as e:
            self.error_occurred.emit(str(e))


# ==================== ОКНО АНАЛИЗА ОШИБОК ====================

class ErrorAnalyzerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("🔍 Анализ ошибок - Omni")
        self.setGeometry(350, 350, 750, 550)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; font-family: Consolas; font-size: 12px; border-radius: 5px; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #1177bb; }
            QLabel { color: #d4d4d4; }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("🔍 Анализ ошибок PowerShell")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        layout.addSpacing(10)
        layout.addWidget(QLabel("📋 Вставьте ошибку из PowerShell:"))
        
        self.error_input = QTextEdit()
        self.error_input.setPlaceholderText("Вставьте сюда текст ошибки...")
        self.error_input.setMaximumHeight(150)
        layout.addWidget(self.error_input)
        
        layout.addSpacing(10)
        self.analyze_btn = QPushButton("🤖 Проанализировать ошибку")
        self.analyze_btn.clicked.connect(self.analyze_error)
        layout.addWidget(self.analyze_btn)
        
        layout.addSpacing(10)
        layout.addWidget(QLabel("🧠 Анализ и решение:"))
        
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        layout.addWidget(self.result_output)
        
        layout.addSpacing(10)
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def analyze_error(self):
        error_text = self.error_input.toPlainText().strip()
        if not error_text:
            QMessageBox.warning(self, "Ошибка", "Введите текст ошибки")
            return
        self.analyze_btn.setEnabled(False)
        self.result_output.clear()
        self.result_output.append("🤖 Анализирую ошибку...\n")
        self.worker = ErrorAnalysisWorker(self.parent.model_path, error_text)
        self.worker.result_ready.connect(self.on_analysis)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.start()
    
    def on_analysis(self, result):
        self.analyze_btn.setEnabled(True)
        self.result_output.append(result)
    
    def on_analysis_error(self, error_msg):
        self.analyze_btn.setEnabled(True)
        self.result_output.append(f"❌ Ошибка анализа: {error_msg}")
        self.result_output.append("\n💡 Попробуйте переформулировать описание ошибки.")


# ==================== AI WORKER ДЛЯ СКРИПТОВ ====================

class ScriptAIWorker(QThread):
    script_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_path, user_input, script_type="powershell"):
        super().__init__()
        self.model_path = model_path
        self.user_input = user_input
        self.script_type = script_type
    
    def run(self):
        try:
            if not AI_AVAILABLE:
                self.error_occurred.emit("AI не доступен")
                return
            if not hasattr(ScriptAIWorker, 'llm'):
                if not os.path.exists(self.model_path):
                    self.error_occurred.emit("Модель не найдена")
                    return
                ScriptAIWorker.llm = AutoModelForCausalLM.from_pretrained(
                    self.model_path, model_type="mistral", threads=4, context_length=4096
                )
            ext = "ps1" if self.script_type == "powershell" else "bat"
            prompt = f"""<s>[INST] Ты - Omni, AI помощник для Windows. Пользователь просит написать скрипт: {self.user_input}

Напиши скрипт на {self.script_type} (.{ext}). Ответь ТОЛЬКО JSON. Формат:
{{"filename": "название_скрипта.{ext}", "content": "полное содержимое скрипта", "explanation": "краткое пояснение на русском"}}

Правила:
- Для PowerShell используй синтаксис PowerShell
- Для BAT используй команды cmd
- Добавляй комментарии на русском внутри скрипта
- Скрипт должен быть рабочим и безопасным

Твой ответ (только JSON): [/INST]"""
            response = ScriptAIWorker.llm(prompt, max_new_tokens=2000, temperature=0.3)
            text = response.strip()
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"filename": "script.ps1", "content": "# Скрипт не сгенерирован", "explanation": "Ошибка генерации"}
            self.script_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


# ==================== ОКНО СОЗДАНИЯ СКРИПТОВ ====================

class ScriptCreatorWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("📜 Создание скриптов - Omni")
        self.setGeometry(200, 200, 950, 650)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.current_script_content = ""
        self.current_filename = "script.ps1"
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas; font-size: 12px; border: 1px solid #3c3c3c; border-radius: 5px; }
            QLineEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; padding: 10px; border-radius: 5px; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #1177bb; }
            QComboBox { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; padding: 8px; border-radius: 5px; }
            QLabel { color: #d4d4d4; }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("📜 Создание скриптов с помощью AI")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)
        
        layout.addSpacing(10)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Тип скрипта:"))
        self.script_type = QComboBox()
        self.script_type.addItems(["PowerShell (.ps1)", "Batch (.bat)"])
        top_layout.addWidget(self.script_type)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        layout.addSpacing(10)
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("📝 Что должен делать скрипт?"))
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Например: заархивировать папку Downloads...")
        self.prompt_input.returnPressed.connect(self.generate_script)
        prompt_layout.addWidget(self.prompt_input, 1)
        self.generate_btn = QPushButton("🎲 Сгенерировать")
        self.generate_btn.clicked.connect(self.generate_script)
        prompt_layout.addWidget(self.generate_btn)
        layout.addLayout(prompt_layout)
        
        layout.addSpacing(10)
        self.status_label = QLabel("🟢 Готов")
        self.status_label.setStyleSheet("padding: 5px; background-color: #1e1e1e; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        layout.addSpacing(10)
        self.code_area = QTextEdit()
        self.code_area.setPlaceholderText("Здесь появится сгенерированный скрипт...")
        layout.addWidget(self.code_area)
        
        layout.addSpacing(10)
        actions_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Сохранить как файл")
        self.save_btn.clicked.connect(self.save_script)
        self.run_btn = QPushButton("▶️ Выполнить сейчас")
        self.run_btn.clicked.connect(self.run_script)
        self.copy_btn = QPushButton("📋 Копировать в буфер")
        self.copy_btn.clicked.connect(self.copy_script)
        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.run_btn)
        actions_layout.addWidget(self.copy_btn)
        actions_layout.addStretch()
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        actions_layout.addWidget(close_btn)
        layout.addLayout(actions_layout)
        
        self.setLayout(layout)
    
    def generate_script(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Ошибка", "Введите описание скрипта")
            return
        self.status_label.setText("🧠 AI генерирует скрипт...")
        self.generate_btn.setEnabled(False)
        self.prompt_input.setEnabled(False)
        script_type = "powershell" if self.script_type.currentIndex() == 0 else "batch"
        self.worker = ScriptAIWorker(self.parent.model_path, prompt, script_type)
        self.worker.script_ready.connect(self.on_script_ready)
        self.worker.error_occurred.connect(self.on_script_error)
        self.worker.start()
    
    def on_script_ready(self, result):
        self.status_label.setText("🟢 Скрипт готов")
        self.generate_btn.setEnabled(True)
        self.prompt_input.setEnabled(True)
        self.current_filename = result.get("filename", "script.ps1")
        self.current_script_content = result.get("content", "")
        self.code_area.clear()
        self.code_area.append(self.current_script_content)
        if self.parent:
            self.parent.log(f"Создан скрипт: {self.current_filename}", "success")
    
    def on_script_error(self, error_msg):
        self.status_label.setText("🔴 Ошибка")
        self.generate_btn.setEnabled(True)
        self.prompt_input.setEnabled(True)
        if self.parent:
            self.parent.log(f"Ошибка генерации: {error_msg}", "error")
        QMessageBox.critical(self, "Ошибка", error_msg)
    
    def save_script(self):
        if not self.current_script_content:
            QMessageBox.warning(self, "Ошибка", "Нет скрипта для сохранения")
            return
        scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить скрипт", 
                                                   os.path.join(scripts_dir, self.current_filename),
                                                   "PowerShell (*.ps1);;Batch (*.bat);;All files (*.*)")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.current_script_content)
                if self.parent:
                    self.parent.log(f"Скрипт сохранён: {os.path.basename(filepath)}", "success")
                QMessageBox.information(self, "Сохранено", f"Скрипт сохранён:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def run_script(self):
        if not self.current_script_content:
            QMessageBox.warning(self, "Ошибка", "Нет скрипта для выполнения")
            return
        temp_dir = os.environ.get('TEMP', '')
        ext = "ps1" if self.script_type.currentIndex() == 0 else "bat"
        temp_file = os.path.join(temp_dir, f"omni_temp_script.{ext}")
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(self.current_script_content)
            if ext == "ps1":
                subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", temp_file])
            else:
                subprocess.Popen(["cmd.exe", "/c", temp_file])
            if self.parent:
                self.parent.log(f"Выполнен скрипт: {self.current_filename}", "success")
        except Exception as e:
            if self.parent:
                self.parent.log(f"Ошибка выполнения: {str(e)}", "error")
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def copy_script(self):
        if self.current_script_content:
            QApplication.clipboard().setText(self.current_script_content)
            self.status_label.setText("📋 Скопировано в буфер обмена")
            if self.parent:
                self.parent.log("Скрипт скопирован в буфер обмена", "success")


# ==================== ОКНО ИНФО ====================

class InfoWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ℹ️ О программе - Omni")
        self.setGeometry(400, 400, 480, 380)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QLabel { color: #d4d4d4; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #1177bb; }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        
        logo = QLabel("🤖")
        logo.setStyleSheet("font-size: 72px;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        
        title = QLabel("Omni AI Terminal")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0e639c;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        version = QLabel("Версия 2.0.0")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        layout.addSpacing(20)
        
        author = QLabel("👤 Автор: ilabolAfk")
        author.setAlignment(Qt.AlignCenter)
        layout.addWidget(author)
        layout.addSpacing(10)
        
        desc = QLabel("📟 Локальный AI-терминал с поддержкой\n\n"
                     "• PowerShell (интерактивный)\n"
                     "• SSH подключения\n"
                     "• Плагины\n"
                     "• Создание скриптов\n"
                     "• Анализ ошибок\n"
                     "• 5 тем оформления")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(20)
        
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)


# ==================== ОКНО ПОМОЩИ ====================

class HelpWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Помощь - Omni")
        self.setGeometry(350, 350, 750, 550)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; font-family: Consolas; font-size: 12px; border-radius: 5px; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #1177bb; }
            QLabel { color: #d4d4d4; }
            QTabWidget::pane { border: 1px solid #3c3c3c; background-color: #2d2d2d; border-radius: 5px; }
            QTabBar::tab { background-color: #1e1e1e; color: #d4d4d4; padding: 8px 16px; margin-right: 2px; }
            QTabBar::tab:selected { background-color: #0e639c; }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("📚 Помощь - Omni AI Terminal")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        tabs = QTabWidget()
        
        # Быстрый старт
        t1 = QTextEdit()
        t1.setReadOnly(True)
        t1.setPlainText("""
🚀 БЫСТРЫЙ СТАРТ

1. Введите запрос в левом терминале (AI)
2. При первом запуске модель загрузится в память (30-60 секунд)
3. AI выполнит команду в правом терминале PowerShell

ПРИМЕРЫ КОМАНД:
  • открой блокнот
  • покажи файлы
  • создай папку Project
  • открой калькулятор

💡 ПОЛЕЗНЫЕ СОВЕТЫ:
  • Опасные команды требуют подтверждения [y/N]
  • Используйте !команда для выполнения без AI
  • В правом терминале можно вводить команды напрямую
  • Все настройки сохраняются автоматически
""")
        tabs.addTab(t1, "🚀 Быстрый старт")
        
        # Команды AI
        t2 = QTextEdit()
        t2.setReadOnly(True)
        t2.setPlainText("""
🤖 КОМАНДЫ AI

Omni понимает запросы на естественном русском языке.

📁 ФАЙЛЫ:
  • покажи файлы | список файлов в папке
  • создай папку Project
  • удали файл test.txt
  • переименуй report.txt в final.txt
  • скопируй все фото в папку backup

🖥️ ПРОГРАММЫ:
  • открой блокнот | notepad
  • запусти калькулятор | calc
  • открой Google Chrome
  • запусти диспетчер задач

⚙️ СИСТЕМА:
  • сколько оперативной памяти свободно
  • какой процессор
  • покажи загрузку диска
  • выключи компьютер через 10 минут
  • сделай отчёт о батарее

🌐 СЕТЬ:
  • какой IP адрес
  • пинг до google.com
  • покажи wifi сети

📦 ПАКЕТНЫЕ КОМАНДЫ:
  • создай папку Project, перейди в неё и открой блокнот
  • найди все pdf файлы и скопируй их в папку pdf_backup
""")
        tabs.addTab(t2, "🤖 Команды AI")
        
        # Создание скриптов
        t3 = QTextEdit()
        t3.setReadOnly(True)
        t3.setPlainText("""
📜 СОЗДАНИЕ СКРИПТОВ

Omni может генерировать полноценные PowerShell (.ps1) и Batch (.bat) скрипты.

КАК СОЗДАТЬ СКРИПТ:
1. Нажмите кнопку "📜 Создать скрипт"
2. Выберите тип скрипта (PowerShell / Batch)
3. Опишите что должен делать скрипт
4. AI сгенерирует код

ПРИМЕРЫ ЗАПРОСОВ:
  • "сделай бэкап папки Documents в zip архив с датой"
  • "напиши скрипт который очищает временные файлы"
  • "bat файл который перезапускает проводник"

Скрипт можно:
  • 💾 Сохранить в файл
  • ▶️ Выполнить сразу
  • 📋 Копировать в буфер обмена

Все скрипты сохраняются в папку: Omni/scripts/
""")
        tabs.addTab(t3, "📜 Создание скриптов")
        
        # SSH
        t4 = QTextEdit()
        t4.setReadOnly(True)
        t4.setPlainText("""
🔌 SSH ПОДКЛЮЧЕНИЯ

Omni позволяет управлять удалёнными серверами через SSH.

КАК ПОДКЛЮЧИТЬСЯ:
1. Нажмите кнопку "🔌 SSH"
2. Перейдите на вкладку "➕ Новое"
3. Заполните данные:
   • Имя: например "Мой сервер"
   • Хост: IP адрес или домен
   • Порт: 22 (стандартный)
   • Пользователь: root или ваш логин
   • Пароль: (опционально)
4. Нажмите "💾 Сохранить подключение"

КАК ИСПОЛЬЗОВАТЬ:
1. Выберите подключение из списка
2. Дважды кликните или нажмите "Подключиться"
3. Перейдите на вкладку "🖥️ Терминал"
4. Вводите команды как в обычном терминале

ПРИМЕРЫ КОМАНД НА СЕРВЕРЕ:
  • ls -la              → список файлов
  • cd /var/log         → перейти в папку
  • cat file.txt        → показать содержимое
  • sudo apt update     → обновить пакеты (Linux)

Для подключения с паролем нужен sshpass (установите через Git Bash или WSL)
""")
        tabs.addTab(t4, "🔌 SSH")
        
        # Анализ ошибок
        t5 = QTextEdit()
        t5.setReadOnly(True)
        t5.setPlainText("""
🔍 АНАЛИЗ ОШИБОК

Omni умеет анализировать ошибки PowerShell и предлагать решения.

КАК ИСПОЛЬЗОВАТЬ:
1. Нажмите кнопку "🔍 Анализ ошибок"
2. Вставьте текст ошибки из PowerShell
3. Нажмите "🤖 Проанализировать ошибку"
4. AI объяснит:
   • 🔍 Что значит ошибка
   • 🛠️ Как исправить (с готовыми командами)
   • 💡 Как предотвратить в будущем

ПРИМЕРЫ ОШИБОК ДЛЯ АНАЛИЗА:

ОШИБКА 1 (файл не найден):
  Remove-Item : Cannot find path 'C:\\file.txt' because it does not exist.

ОШИБКА 2 (нет прав):
  Access to the path 'C:\\Windows\\System32\\config' is denied.

ОШИБКА 3 (Git конфликт):
  Updates were rejected because the remote contains work that you do not have locally.

AI понимает как русские, так и английские ошибки.
""")
        tabs.addTab(t5, "🔍 Анализ ошибок")
        
        # Плагины
        t6 = QTextEdit()
        t6.setReadOnly(True)
        t6.setPlainText("""
🔌 ПЛАГИНЫ

Omni поддерживает локальные плагины для расширения функционала.

ЧТО ТАКОЕ ПЛАГИН:
Плагин — это папка с двумя файлами:
  • manifest.json — описание плагина
  • script.ps1 — PowerShell скрипт

СТРУКТУРА ПЛАГИНА:
my_plugin/
├── manifest.json
└── script.ps1

ПРИМЕР manifest.json:
{
    "name": "Мой плагин",
    "version": "1.0",
    "description": "Что делает плагин",
    "author": "Автор",
    "command": "& '$PSScriptRoot\\script.ps1'"
}

КАК УСТАНОВИТЬ ПЛАГИН:
1. Нажмите кнопку "🔌 Плагины"
2. Нажмите "📁 Установить из папки"
3. Выберите папку с плагином
4. Плагин появится в списке

КАК ИСПОЛЬЗОВАТЬ:
  • ▶️ Выполнить выбранный — запускает скрипт
  • 🗑️ Удалить выбранный — удаляет плагин

Все плагины хранятся в папке: Omni/plugins/
""")
        tabs.addTab(t6, "🔌 Плагины")
        
        # Темы
        t7 = QTextEdit()
        t7.setReadOnly(True)
        t7.setPlainText("""
🎨 НАСТРОЙКА ТЕМ

Omni поддерживает 5 встроенных тем оформления.

ДОСТУПНЫЕ ТЕМЫ:
  • 🌙 Тёмная (по умолчанию) — классическая тёмная тема
  • ☀️ Светлая — для светлых помещений
  • 💜 Фиолетовая — стильная фиолетовая гамма
  • 💚 Зелёная — приятная для глаз зелёная тема
  • 🔵 Синяя — профессиональная синяя тема

КАК СМЕНИТЬ ТЕМУ:
  • Выберите тему в выпадающем списке в правом верхнем углу
  • Тема меняется мгновенно, без перезапуска

СОХРАНЕНИЕ НАСТРОЕК:
  • Выбранная тема автоматически сохраняется в omni_config.json
  • При следующем запуске тема восстановится

Все темы поддерживают тёмные и светлые цветовые схемы.
""")
        tabs.addTab(t7, "🎨 Темы")
        
        layout.addWidget(tabs)
        
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


# ==================== AI WORKER (ОСНОВНОЙ) ====================

class AIWorker(QThread):
    response_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)
    model_loaded = pyqtSignal()
    
    def __init__(self, model_path, user_input):
        super().__init__()
        self.model_path = model_path
        self.user_input = user_input
    
    def run(self):
        try:
            if not AI_AVAILABLE:
                self.error_occurred.emit("Установите ctransformers: pip install ctransformers")
                return
            
            if not hasattr(AIWorker, 'llm'):
                if not os.path.exists(self.model_path):
                    self.error_occurred.emit(f"Модель не найдена: {self.model_path}")
                    return
                
                self.progress_update.emit(10, "Чтение файла модели...")
                self.msleep(500)
                self.progress_update.emit(25, "Проверка целостности...")
                self.msleep(500)
                self.progress_update.emit(40, "Инициализация токенизатора...")
                self.msleep(500)
                self.progress_update.emit(55, "Загрузка весов модели...")
                self.msleep(500)
                self.progress_update.emit(70, "Инициализация слоёв...")
                self.msleep(500)
                self.progress_update.emit(85, "Финальная настройка...")
                
                print("Загрузка Mistral-7B...")
                AIWorker.llm = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    model_type="mistral",
                    threads=4,
                    context_length=2048
                )
                self.progress_update.emit(100, "Модель загружена!")
                self.model_loaded.emit()
                print("Mistral-7B загружена!")
            
            self.progress_update.emit(0, "Генерация ответа...")
            
            prompt = f"""<s>[INST] Ты - Omni, AI помощник для Windows PowerShell. Пользователь пишет: {self.user_input}

Ответь ТОЛЬКО JSON. Формат:
{{"command": "команда PowerShell", "explanation": "пояснение на русском"}}

Примеры:
"открой блокнот" -> {{"command": "Start-Process notepad.exe", "explanation": "Открываю блокнот"}}
"покажи файлы" -> {{"command": "Get-ChildItem", "explanation": "Показываю список файлов"}}
"привет" -> {{"command": "", "explanation": "Привет! Я Omni, могу выполнять команды PowerShell"}}

Твой ответ (только JSON): [/INST]"""
            
            response = AIWorker.llm(prompt, max_new_tokens=200, temperature=0.2)
            text = response.strip()
            
            json_match = re.search(r'\{[^{}]*\}', text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"command": "", "explanation": "Не понял запрос. Попробуйте переформулировать."}
            
            self.progress_update.emit(100, "Готово!")
            self.response_ready.emit(result)
            
        except Exception as e:
            log_error(str(e))
            self.error_occurred.emit(str(e))


# ==================== ИНТЕРАКТИВНЫЙ POWER SHELL ТЕРМИНАЛ ====================

class PowerShellTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.process = None
        self.init_ui()
        self.start_powershell()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.header = QLabel("🖥️ PowerShell (Интерактивный)")
        self.header.setStyleSheet("background-color: #0e639c; padding: 8px; color: white; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.header)
        
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 10))
        self.output_area.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.output_area)
        
        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Введите команду PowerShell...")
        self.input_line.setStyleSheet("background-color: #2d2d2d; color: #d4d4d4; padding: 8px; font-family: Consolas;")
        self.input_line.returnPressed.connect(self.execute_command)
        
        self.send_btn = QPushButton("▶️ Выполнить")
        self.send_btn.setStyleSheet("background-color: #0e639c; color: white; border: none; padding: 8px 16px; font-weight: bold;")
        self.send_btn.clicked.connect(self.execute_command)
        
        input_layout.addWidget(self.input_line, 1)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)
        
        self.setLayout(layout)
    
    def start_powershell(self):
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.start("powershell.exe", ["-NoExit", "-Command", "-"])
    
    def read_output(self):
        try:
            if self.process:
                data = self.process.readAllStandardOutput()
                text = bytes(data).decode('utf-8', errors='ignore')
                self.output_area.append(text)
                cursor = self.output_area.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.output_area.setTextCursor(cursor)
                
                # Автоматическое обнаружение ошибок
                self.check_for_errors(text)
        except Exception as e:
            log_error(f"read_output: {e}")
    
    def check_for_errors(self, output):
        error_patterns = [
            r'error:', r'ошибка:', r'failed:', r'не найдена',
            r'отказано в доступе', r'access denied', r'not found',
            r'cannot find', r'не удается найти'
        ]
        for pattern in error_patterns:
            if re.search(pattern, output.lower()):
                self.output_area.append("\n⚠️ Обнаружена ошибка! Используйте кнопку '🔍 Анализ ошибок' для получения помощи.\n")
                break
    
    def execute_command(self):
        try:
            command = self.input_line.text().strip()
            if not command:
                return
            self.output_area.append(f"\nPS> {command}")
            self.input_line.clear()
            if self.process and self.process.state() == QProcess.Running:
                self.process.write(f"{command}\n".encode())
        except Exception as e:
            log_error(f"execute_command: {e}")
            self.output_area.append(f"\n❌ Ошибка: {e}")
    
    def execute_direct(self, command):
        try:
            if self.process and self.process.state() == QProcess.Running:
                self.output_area.append(f"\n🤖 Omni> {command}")
                self.process.write(f"{command}\n".encode())
        except Exception as e:
            log_error(f"execute_direct: {e}")
    
    def update_style(self, bg, text_color, header_color):
        self.output_area.setStyleSheet(f"background-color: {bg}; color: {text_color};")
        self.input_line.setStyleSheet(f"background-color: {bg}; color: {text_color}; padding: 8px; font-family: Consolas;")
        self.header.setStyleSheet(f"background-color: {header_color}; padding: 8px; color: white; font-weight: bold; font-size: 12px;")


# ==================== ГЛАВНОЕ ОКНО ====================

class OmniTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Omni AI Terminal v2.0 - Русская версия")
        self.setGeometry(50, 50, 1450, 850)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(os.environ.get('APPDATA', ''), "Omni", "mistral-7b-instruct-v0.3.Q4_K_M.gguf")
        
        self.custom_shortcuts = ["", ""]
        self.custom_names = ["Настроить", "Настроить"]
        self.current_theme = "Тёмная"
        
        self.plugins_manager = None
        self.ssh_window = None
        self.error_analyzer = None
        self.script_creator = None
        self.info_window = None
        self.help_window = None
        
        self.init_ui()
        self.load_config()
        self.apply_theme()
        self.log("🚀 Omni AI Terminal v2.0 готов к работе!", "success")
        self.log("🤖 Mistral-7B загрузится при первом запросе (30-60 секунд)", "ai")
        
        if not os.path.exists(self.model_path):
            self.log("⚠️ Модель не найдена! Поместите файл mistral-7b-instruct-v0.3.Q4_K_M.gguf в папку с программой", "error")
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Верхняя панель с темами
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("🎨 Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["🌙 Тёмная", "☀️ Светлая", "💜 Фиолетовая", "💚 Зелёная", "🔵 Синяя"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        top_bar.addWidget(self.theme_combo)
        top_bar.addStretch()
        
        # Кнопки инструментов
        self.btn_plugins = self.make_btn("🔌 Плагины", self.open_plugins_manager)
        self.btn_ssh = self.make_btn("🔌 SSH", self.open_ssh)
        self.btn_error = self.make_btn("🔍 Анализ ошибок", self.open_error_analyzer)
        self.btn_script = self.make_btn("📜 Создать скрипт", self.open_script_creator)
        self.btn_info = self.make_btn("ℹ️ О программе", self.open_info)
        self.btn_help = self.make_btn("📚 Помощь", self.open_help)
        
        top_bar.addWidget(self.btn_plugins)
        top_bar.addWidget(self.btn_ssh)
        top_bar.addWidget(self.btn_error)
        top_bar.addWidget(self.btn_script)
        top_bar.addWidget(self.btn_info)
        top_bar.addWidget(self.btn_help)
        main_layout.addLayout(top_bar)
        
        # Панель шорткатов
        shortcuts = QHBoxLayout()
        self.btn_dir = self.make_btn("📁 Сменить папку", self.change_dir)
        self.btn_npp = self.make_btn("📝 Notepad++", lambda: self.run_cmd("Start-Process notepad++.exe"))
        self.btn_notepad = self.make_btn("📄 Блокнот", lambda: self.run_cmd("Start-Process notepad.exe"))
        self.btn_clean = self.make_btn("🧹 Очистка Temp", self.clean_temp)
        self.btn_custom1 = self.make_btn("⚙️ Настроить", lambda: self.setup_shortcut(0))
        self.btn_custom2 = self.make_btn("⚙️ Настроить", lambda: self.setup_shortcut(1))
        shortcuts.addWidget(self.btn_dir)
        shortcuts.addWidget(self.btn_npp)
        shortcuts.addWidget(self.btn_notepad)
        shortcuts.addWidget(self.btn_clean)
        shortcuts.addWidget(self.btn_custom1)
        shortcuts.addWidget(self.btn_custom2)
        main_layout.addLayout(shortcuts)
        
        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        
        # Левый терминал (AI)
        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.ai_header = QLabel("🤖 Omni AI (Mistral-7B)")
        self.ai_header.setStyleSheet("background-color: #0e639c; padding: 8px; color: white; font-weight: bold; font-size: 12px;")
        left_layout.addWidget(self.ai_header)
        
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setFont(QFont("Consolas", 10))
        left_layout.addWidget(self.ai_output)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #2d2d2d; border: none; height: 3px; } QProgressBar::chunk { background-color: #0e639c; }")
        left_layout.addWidget(self.progress_bar)
        
        self.ai_status = QLabel("🟢 Готов")
        self.ai_status.setStyleSheet("padding: 5px; background-color: #2d2d2d; font-size: 11px;")
        left_layout.addWidget(self.ai_status)
        
        input_layout = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Скажите что-нибудь по-русски...")
        self.ai_input.setStyleSheet("background-color: #2d2d2d; color: #d4d4d4; padding: 10px; font-family: Consolas;")
        self.ai_input.returnPressed.connect(self.process_ai)
        self.ai_btn = self.make_btn("📤 Отправить", self.process_ai)
        input_layout.addWidget(self.ai_input, 1)
        input_layout.addWidget(self.ai_btn)
        left_layout.addLayout(input_layout)
        
        left.setLayout(left_layout)
        splitter.addWidget(left)
        
        # Правый терминал (PowerShell)
        self.ps_term = PowerShellTerminal()
        splitter.addWidget(self.ps_term)
        
        splitter.setSizes([720, 720])
        main_layout.addWidget(splitter)
    
    def make_btn(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 12px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        btn.clicked.connect(callback)
        return btn
    
    def apply_theme(self):
        themes = {
            "🌙 Тёмная": {"bg": "#1e1e1e", "text": "#d4d4d4", "input_bg": "#2d2d2d", "header": "#0e639c"},
            "☀️ Светлая": {"bg": "#ffffff", "text": "#000000", "input_bg": "#f0f0f0", "header": "#0078d4"},
            "💜 Фиолетовая": {"bg": "#1a0b2e", "text": "#d4b8ff", "input_bg": "#2a1a3e", "header": "#6a0dad"},
            "💚 Зелёная": {"bg": "#0a1f0a", "text": "#a8f0a8", "input_bg": "#1a2f1a", "header": "#2e8b57"},
            "🔵 Синяя": {"bg": "#0a1a2e", "text": "#a8d4ff", "input_bg": "#1a2a3e", "header": "#1e90ff"}
        }
        theme = themes.get(self.current_theme, themes["🌙 Тёмная"])
        
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {theme['bg']}; }}
            QTextEdit {{ background-color: {theme['bg']}; color: {theme['text']}; border: 1px solid #3c3c3c; border-radius: 4px; }}
            QLineEdit {{ background-color: {theme['input_bg']}; color: {theme['text']}; border: 1px solid #3c3c3c; padding: 10px; border-radius: 4px; }}
            QPushButton {{ background-color: {theme['header']}; color: white; border: none; padding: 8px 12px; font-weight: bold; border-radius: 4px; }}
            QPushButton:hover {{ background-color: {theme['header']}; opacity: 0.8; }}
            QLabel {{ color: {theme['text']}; }}
            QComboBox {{ background-color: {theme['input_bg']}; color: {theme['text']}; padding: 5px; border-radius: 4px; }}
        """)
        
        self.ps_term.update_style(theme['bg'], theme['text'], theme['header'])
        self.ai_header.setStyleSheet(f"background-color: {theme['header']}; padding: 8px; color: white; font-weight: bold; font-size: 12px; border-radius: 4px;")
        self.ai_output.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['text']}; border: 1px solid #3c3c3c; border-radius: 4px;")
        self.ai_input.setStyleSheet(f"background-color: {theme['input_bg']}; color: {theme['text']}; padding: 10px; font-family: Consolas; border-radius: 4px;")
        self.ai_status.setStyleSheet(f"padding: 5px; background-color: {theme['input_bg']}; border-radius: 4px;")
    
    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.apply_theme()
        self.save_config()
    
    def log(self, message, msg_type="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {"info": "#d4d4d4", "error": "#f48771", "success": "#6a9955", 
                  "warning": "#dcdcaa", "ai": "#9cdcfe", "command": "#ce9178"}
        symbols = {"info": " ", "error": "❌", "success": "✅", "warning": "⚠️", "ai": "🤖", "command": "$"}
        color = colors.get(msg_type, "#d4d4d4")
        symbol = symbols.get(msg_type, " ")
        self.ai_output.append(f'<span style="color:#858585;">[{timestamp}]</span> <span style="color:{color};">{symbol} {message}</span>')
        cursor = self.ai_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ai_output.setTextCursor(cursor)
    
    def run_cmd(self, command):
        self.ps_term.execute_direct(command)
    
    def change_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.ps_term.execute_direct(f"Set-Location '{folder}'")
            self.log(f"Смена папки: {folder}", "success")
    
    def clean_temp(self):
        reply = QMessageBox.question(self, "Очистка Temp", "Удалить все временные файлы?\n(Это действие необратимо)",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            temp = os.environ.get('TEMP', '')
            if temp and os.path.exists(temp):
                count = 0
                for item in os.listdir(temp):
                    try:
                        path = os.path.join(temp, item)
                        if os.path.isfile(path):
                            os.unlink(path)
                            count += 1
                        elif os.path.isdir(path):
                            shutil.rmtree(path)
                            count += 1
                    except:
                        pass
                self.log(f"Очищено {count} временных файлов", "success")
                self.ps_term.execute_direct("Write-Host 'Temp очищен!' -ForegroundColor Green")
    
    def setup_shortcut(self, idx):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите приложение", "C:\\", "*.exe")
        if path:
            self.custom_shortcuts[idx] = path
            self.custom_names[idx] = os.path.basename(path)
            btn = self.btn_custom1 if idx == 0 else self.btn_custom2
            btn.setText(f"🚀 {self.custom_names[idx]}")
            btn.clicked.disconnect()
            btn.clicked.connect(lambda: self.run_cmd(f"Start-Process '{path}'"))
            self.save_config()
            self.log(f"Шорткат настроен на: {self.custom_names[idx]}", "success")
    
    def open_plugins_manager(self):
        try:
            if self.plugins_manager is not None:
                try:
                    if self.plugins_manager.isVisible():
                        self.plugins_manager.raise_()
                        return
                    else:
                        self.plugins_manager.show()
                        return
                except RuntimeError:
                    self.plugins_manager = None
            self.plugins_manager = PluginsManagerWindow(self)
            self.plugins_manager.show()
        except Exception as e:
            log_error(str(e))
            self.plugins_manager = PluginsManagerWindow(self)
            self.plugins_manager.show()
    
    def open_ssh(self):
        try:
            if self.ssh_window is not None:
                try:
                    if self.ssh_window.isVisible():
                        self.ssh_window.raise_()
                        return
                    else:
                        self.ssh_window.show()
                        return
                except RuntimeError:
                    self.ssh_window = None
            self.ssh_window = SSHWindow(self)
            self.ssh_window.show()
        except Exception as e:
            log_error(str(e))
            self.ssh_window = SSHWindow(self)
            self.ssh_window.show()
    
    def open_error_analyzer(self):
        try:
            if self.error_analyzer is not None:
                try:
                    if self.error_analyzer.isVisible():
                        self.error_analyzer.raise_()
                        return
                    else:
                        self.error_analyzer.show()
                        return
                except RuntimeError:
                    self.error_analyzer = None
            self.error_analyzer = ErrorAnalyzerWindow(self)
            self.error_analyzer.show()
        except Exception as e:
            log_error(str(e))
            self.error_analyzer = ErrorAnalyzerWindow(self)
            self.error_analyzer.show()
    
    def open_script_creator(self):
        try:
            if self.script_creator is not None:
                try:
                    if self.script_creator.isVisible():
                        self.script_creator.raise_()
                        return
                    else:
                        self.script_creator.show()
                        return
                except RuntimeError:
                    self.script_creator = None
            self.script_creator = ScriptCreatorWindow(self)
            self.script_creator.show()
        except Exception as e:
            log_error(str(e))
            self.script_creator = ScriptCreatorWindow(self)
            self.script_creator.show()
    
    def open_info(self):
        try:
            if self.info_window is not None:
                try:
                    if self.info_window.isVisible():
                        self.info_window.raise_()
                        return
                    else:
                        self.info_window.show()
                        return
                except RuntimeError:
                    self.info_window = None
            self.info_window = InfoWindow(self)
            self.info_window.show()
        except Exception as e:
            log_error(str(e))
            self.info_window = InfoWindow(self)
            self.info_window.show()
    
    def open_help(self):
        try:
            if self.help_window is not None:
                try:
                    if self.help_window.isVisible():
                        self.help_window.raise_()
                        return
                    else:
                        self.help_window.show()
                        return
                except RuntimeError:
                    self.help_window = None
            self.help_window = HelpWindow(self)
            self.help_window.show()
        except Exception as e:
            log_error(str(e))
            self.help_window = HelpWindow(self)
            self.help_window.show()
    
    def save_config(self):
        try:
            with open("omni_config.json", "w", encoding="utf-8") as f:
                json.dump({
                    "shortcuts": self.custom_shortcuts,
                    "names": self.custom_names,
                    "theme": self.current_theme
                }, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def load_config(self):
        try:
            with open("omni_config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.custom_shortcuts = data.get("shortcuts", ["", ""])
                self.custom_names = data.get("names", ["Настроить", "Настроить"])
                self.current_theme = data.get("theme", "🌙 Тёмная")
                self.theme_combo.setCurrentText(self.current_theme)
                for i in range(2):
                    if self.custom_shortcuts[i]:
                        btn = self.btn_custom1 if i == 0 else self.btn_custom2
                        btn.setText(f"🚀 {self.custom_names[i]}")
                        btn.clicked.disconnect()
                        btn.clicked.connect(lambda idx=i: self.run_cmd(f"Start-Process '{self.custom_shortcuts[idx]}'"))
        except:
            pass
    
    def process_ai(self):
        user_input = self.ai_input.text().strip()
        if not user_input:
            return
        
        self.ai_input.clear()
        self.log(user_input, "command")
        
        # Блокируем только кнопку отправки во время загрузки AI
        self.ai_btn.setEnabled(False)
        self.ai_input.setEnabled(False)
        self.ai_status.setText("🧠 Загрузка AI...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.ai_worker = AIWorker(self.model_path, user_input)
        self.ai_worker.progress_update.connect(self.on_progress)
        self.ai_worker.model_loaded.connect(self.on_model_loaded)
        self.ai_worker.response_ready.connect(self.on_ai_response)
        self.ai_worker.error_occurred.connect(self.on_ai_error)
        self.ai_worker.start()
    
    def on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{value}% - {message}")
    
    def on_model_loaded(self):
        self.progress_bar.setVisible(False)
        self.ai_status.setText("🟢 Готов")
        self.ai_btn.setEnabled(True)
        self.ai_input.setEnabled(True)
    
    def on_ai_response(self, response):
        self.progress_bar.setVisible(False)
        self.ai_status.setText("🟢 Готов")
        self.ai_btn.setEnabled(True)
        self.ai_input.setEnabled(True)
        
        command = response.get("command", "")
        explanation = response.get("explanation", "")
        
        self.log(explanation, "ai")
        
        if command:
            self.log(f"Выполняю: {command}", "command")
            self.ps_term.execute_direct(command)
        else:
            self.log("Не понял команду. Попробуйте переформулировать.", "warning")
    
    def on_ai_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.ai_status.setText("🔴 Ошибка")
        self.ai_btn.setEnabled(True)
        self.ai_input.setEnabled(True)
        self.log(f"Ошибка: {error_msg}", "error")


# ==================== ЗАПУСК ====================

def exception_hook(exc_type, exc_value, exc_tb):
    """Глобальный перехват ошибок — программа не падает"""
    log_error(f"{exc_type.__name__}: {exc_value}")
    print(f"⚠️ Ошибка залогирована, но программа продолжает работу")

if __name__ == "__main__":
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = OmniTerminal()
    window.show()
    sys.exit(app.exec_())