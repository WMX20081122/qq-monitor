#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QQ Monitor - Napcat QQ账号掉线监测与邮件提醒工具"""

import sys, os, yaml, time, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict, field
from pathlib import Path

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("警告: PyQt5 未安装，将使用命令行模式")

import requests

# 数据模型
@dataclass
class QQAccount:
    uin: str = ""
    nickname: str = ""
    napcat_url: str = "http://127.0.0.1:3000"
    check_interval: int = 60
    enabled: bool = True

@dataclass
class EmailConfig:
    smtp_server: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    receiver: str = ""
    use_ssl: bool = True

@dataclass
class AppConfig:
    accounts: List[Dict] = field(default_factory=list)
    email: Dict = field(default_factory=dict)
    auto_start: bool = False
    
    def __post_init__(self):
        if not self.email:
            self.email = asdict(EmailConfig())

# 配置管理
class ConfigManager:
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or self._get_default_config_dir())
        self.config_file = self.config_dir / "config.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_default_config_dir(self) -> str:
        if sys.platform == "win32":
            return os.path.join(os.environ.get("APPDATA", ""), "QQMonitor")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/QQMonitor")
        return os.path.expanduser("~/.config/qq-monitor")
    
    def load(self) -> AppConfig:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return AppConfig(**(yaml.safe_load(f) or {}))
            except: pass
        return AppConfig()
    
    def save(self, config: AppConfig):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(config), f, allow_unicode=True, default_flow_style=False)

# QQ状态检测
class QQMonitor:
    def __init__(self, account: QQAccount):
        self.account = account
        self.last_status = None
        self.failures = 0
    
    def check_status(self) -> Dict:
        result = {"uin": self.account.uin, "online": False, "error": None, "timestamp": datetime.now().isoformat()}
        try:
            r = requests.get(f"{self.account.napcat_url.rstrip('/')}/get_login_info", timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("retcode") == 0 and data.get("data"):
                    result["online"], result["nickname"], self.failures = True, data["data"].get("nickname", ""), 0
                else:
                    result["error"] = data.get("msg", "未登录")
            else:
                result["error"] = f"HTTP {r.status_code}"
        except Exception as e:
            result["error"] = str(e)
        
        if not result["online"]:
            self.failures += 1
            if self.failures < 3:
                result["error"] = f"检测失败 ({self.failures}/3)"
        else:
            self.failures = 0
        
        if self.last_status is not None:
            if self.last_status and not result["online"]:
                result["status_changed"], result["change_type"] = True, "offline"
            elif not self.last_status and result["online"]:
                result["status_changed"], result["change_type"] = True, "online"
        self.last_status = result["online"]
        return result

# 邮件发送
class EmailSender:
    def __init__(self, config: EmailConfig):
        self.config = config
    
    def send(self, subject: str, content: str) -> bool:
        if not self.config.smtp_user or not self.config.receiver:
            return False
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = self.config.smtp_user, self.config.receiver, subject
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port) if self.config.use_ssl else smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            if not self.config.use_ssl: server.starttls()
            server.login(self.config.smtp_user, self.config.smtp_password)
            server.sendmail(self.config.smtp_user, [self.config.receiver], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def send_offline(self, acc: QQAccount, error: str):
        return self.send(f"【QQ掉线】{acc.nickname or acc.uin}", f"QQ号: {acc.uin}\n昵称: {acc.nickname}\n时间: {datetime.now()}\n错误: {error}")
    
    def send_online(self, acc: QQAccount):
        return self.send(f"【QQ上线】{acc.nickname or acc.uin}", f"QQ号: {acc.uin}\n昵称: {acc.nickname}\n时间: {datetime.now()}")

# 监测线程
class MonitorThread(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.running = False
    
    def run(self):
        self.running = True
        monitors = {a['uin']: QQMonitor(QQAccount(**a)) for a in self.config.accounts if a.get('enabled') and a.get('uin')}
        sender = EmailSender(EmailConfig(**self.config.email)) if self.config.email.get('smtp_user') else None
        
        while self.running:
            for uin, m in monitors.items():
                try:
                    s = m.check_status()
                    if s.get("status_changed"):
                        if s["change_type"] == "offline":
                            if sender: sender.send_offline(m.account, s.get("error", "未知"))
                            self.log_signal.emit(f"[掉线] {m.account.nickname or uin}")
                        else:
                            if sender: sender.send_online(m.account)
                            self.log_signal.emit(f"[上线] {m.account.nickname or uin}")
                except Exception as e:
                    self.log_signal.emit(f"[错误] {uin}: {e}")
            time.sleep(min((m.account.check_interval for m in monitors.values()), default=60))
    
    def stop(self):
        self.running = False

# GUI
if PYQT_AVAILABLE:
    class AccountDialog(QDialog):
        def __init__(self, parent=None, data=None):
            super().__init__(parent)
            self.setWindowTitle("账号配置")
            self.setModal(True)
            layout = QFormLayout(self)
            
            self.uin = QLineEdit()
            self.uin.setPlaceholderText("QQ号")
            layout.addRow("QQ号:", self.uin)
            
            self.nickname = QLineEdit()
            self.nickname.setPlaceholderText("备注名称")
            layout.addRow("昵称:", self.nickname)
            
            self.url = QLineEdit()
            self.url.setText("http://127.0.0.1:3000")
            layout.addRow("Napcat地址:", self.url)
            
            self.interval = QSpinBox()
            self.interval.setRange(10, 3600)
            self.interval.setValue(60)
            layout.addRow("检查间隔(秒):", self.interval)
            
            self.enabled = QCheckBox()
            self.enabled.setChecked(True)
            layout.addRow("启用:", self.enabled)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addRow(buttons)
            
            if data:
                self.uin.setText(data.get('uin', ''))
                self.nickname.setText(data.get('nickname', ''))
                self.url.setText(data.get('napcat_url', 'http://127.0.0.1:3000'))
                self.interval.setValue(data.get('check_interval', 60))
                self.enabled.setChecked(data.get('enabled', True))
        
        def get_account(self):
            return {'uin': self.uin.text(), 'nickname': self.nickname.text(), 
                    'napcat_url': self.url.text(), 'check_interval': self.interval.value(), 'enabled': self.enabled.isChecked()}
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load()
            self.monitor_thread = None
            
            self.setWindowTitle("QQ Monitor - QQ掉线监测工具")
            self.setGeometry(100, 100, 700, 500)
            self._init_ui()
            self._load_config()
        
        def _init_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            
            tabs = QTabWidget()
            layout.addWidget(tabs)
            
            # 账号管理
            acc_widget = QWidget()
            acc_layout = QVBoxLayout(acc_widget)
            
            list_group = QGroupBox("账号列表")
            list_layout = QVBoxLayout(list_group)
            self.account_list = QListWidget()
            list_layout.addWidget(self.account_list)
            
            btn_row = QHBoxLayout()
            for text, slot in [("添加", self._add_account), ("编辑", self._edit_account), ("删除", self._del_account)]:
                btn = QPushButton(text)
                btn.clicked.connect(slot)
                btn_row.addWidget(btn)
            list_layout.addLayout(btn_row)
            acc_layout.addWidget(list_group)
            tabs.addTab(acc_widget, "账号管理")
            
            # 邮件配置
            email_widget = QWidget()
            email_layout = QVBoxLayout(email_widget)
            email_group = QGroupBox("SMTP配置")
            form = QFormLayout(email_group)
            
            self.smtp_server = QLineEdit("smtp.qq.com")
            self.smtp_port = QSpinBox()
            self.smtp_port.setRange(1, 65535)
            self.smtp_port.setValue(465)
            self.smtp_user = QLineEdit()
            self.smtp_password = QLineEdit()
            self.smtp_password.setEchoMode(QLineEdit.Password)
            self.smtp_receiver = QLineEdit()
            self.use_ssl = QCheckBox()
            self.use_ssl.setChecked(True)
            
            form.addRow("SMTP服务器:", self.smtp_server)
            form.addRow("端口:", self.smtp_port)
            form.addRow("发件邮箱:", self.smtp_user)
            form.addRow("授权码:", self.smtp_password)
            form.addRow("收件邮箱:", self.smtp_receiver)
            form.addRow("SSL:", self.use_ssl)
            
            test_btn = QPushButton("测试邮件")
            test_btn.clicked.connect(self._test_email)
            form.addRow(test_btn)
            
            email_layout.addWidget(email_group)
            tabs.addTab(email_widget, "邮件配置")
            
            # 日志
            log_widget = QWidget()
            log_layout = QVBoxLayout(log_widget)
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            log_layout.addWidget(self.log_text)
            tabs.addTab(log_widget, "日志")
            
            # 底部按钮
            btn_row = QHBoxLayout()
            self.start_btn = QPushButton("开始监测")
            self.start_btn.clicked.connect(self._toggle)
            btn_row.addWidget(self.start_btn)
            
            save_btn = QPushButton("保存配置")
            save_btn.clicked.connect(self._save)
            btn_row.addWidget(save_btn)
            layout.addLayout(btn_row)
        
        def _load_config(self):
            for acc in self.config.accounts:
                item = QListWidgetItem(f"{acc.get('nickname', '')} ({acc.get('uin', '')})")
                item.setData(Qt.UserRole, acc)
                self.account_list.addItem(item)
            
            e = self.config.email
            self.smtp_server.setText(e.get('smtp_server', 'smtp.qq.com'))
            self.smtp_port.setValue(e.get('smtp_port', 465))
            self.smtp_user.setText(e.get('smtp_user', ''))
            self.smtp_password.setText(e.get('smtp_password', ''))
            self.smtp_receiver.setText(e.get('receiver', ''))
            self.use_ssl.setChecked(e.get('use_ssl', True))
        
        def _save(self):
            self.config.accounts = [self.account_list.item(i).data(Qt.UserRole) for i in range(self.account_list.count())]
            self.config.email = {'smtp_server': self.smtp_server.text(), 'smtp_port': self.smtp_port.value(),
                                 'smtp_user': self.smtp_user.text(), 'smtp_password': self.smtp_password.text(),
                                 'receiver': self.smtp_receiver.text(), 'use_ssl': self.use_ssl.isChecked()}
            self.config_manager.save(self.config)
            QMessageBox.information(self, "成功", "配置已保存")
        
        def _add_account(self):
            dlg = AccountDialog(self)
            if dlg.exec_():
                acc = dlg.get_account()
                item = QListWidgetItem(f"{acc['nickname']} ({acc['uin']})")
                item.setData(Qt.UserRole, acc)
                self.account_list.addItem(item)
        
        def _edit_account(self):
            item = self.account_list.currentItem()
            if not item:
                return QMessageBox.warning(self, "提示", "请选择账号")
            dlg = AccountDialog(self, item.data(Qt.UserRole))
            if dlg.exec_():
                acc = dlg.get_account()
                item.setData(Qt.UserRole, acc)
                item.setText(f"{acc['nickname']} ({acc['uin']})")
        
        def _del_account(self):
            row = self.account_list.currentRow()
            if row >= 0:
                self.account_list.takeItem(row)
        
        def _toggle(self):
            if self.monitor_thread and self.monitor_thread.running:
                self.monitor_thread.stop()
                self.monitor_thread = None
                self.start_btn.setText("开始监测")
                self._log("监测已停止")
            else:
                self._save()
                self.monitor_thread = MonitorThread(self.config)
                self.monitor_thread.log_signal.connect(self._log)
                self.monitor_thread.start()
                self.start_btn.setText("停止监测")
                self._log("监测已启动")
        
        def _log(self, msg):
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        
        def _test_email(self):
            sender = EmailSender(EmailConfig(smtp_server=self.smtp_server.text(), smtp_port=self.smtp_port.value(),
                                             smtp_user=self.smtp_user.text(), smtp_password=self.smtp_password.text(),
                                             receiver=self.smtp_receiver.text(), use_ssl=self.use_ssl.isChecked()))
            if sender.send("QQ Monitor 测试邮件", f"测试时间: {datetime.now()}"):
                QMessageBox.information(self, "成功", "邮件发送成功")
            else:
                QMessageBox.warning(self, "失败", "邮件发送失败")

# 命令行模式
def cli_mode():
    print("=== QQ Monitor 命令行模式 ===")
    config_manager = ConfigManager()
    config = config_manager.load()
    
    if not config.accounts:
        print("请先配置账号 (使用GUI模式)")
        return
    
    print(f"已加载 {len(config.accounts)} 个账号")
    
    monitors = {a['uin']: QQMonitor(QQAccount(**a)) for a in config.accounts if a.get('enabled')}
    sender = EmailSender(EmailConfig(**config.email)) if config.email.get('smtp_user') else None
    
    print("开始监测... (Ctrl+C 退出)")
    try:
        while True:
            for uin, m in monitors.items():
                s = m.check_status()
                status = "在线" if s['online'] else f"离线 ({s.get('error', '')})"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {m.account.nickname or uin}: {status}")
                
                if s.get("status_changed"):
                    if s["change_type"] == "offline" and sender:
                        sender.send_offline(m.account, s.get('error', ''))
                    elif s["change_type"] == "online" and sender:
                        sender.send_online(m.account)
            
            time.sleep(min((m.account.check_interval for m in monitors.values()), default=60))
    except KeyboardInterrupt:
        print("\n监测已停止")

if __name__ == "__main__":
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    else:
        cli_mode()