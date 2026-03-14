# QQ Monitor - Napcat QQ账号掉线监测工具

## 功能特性

- ✅ 监测 Napcat QQ 账号在线状态
- ✅ 掉线/上线自动发送邮件提醒
- ✅ 可视化配置界面 (PyQt5)
- ✅ 支持多账号管理
- ✅ 跨平台支持 (Windows/macOS/Linux)
- ✅ 命令行模式 (无GUI环境)

## 安装

### 方式一：直接运行

```bash
pip install -r requirements.txt
python qq_monitor.py
```

### 方式二：打包成可执行文件

```bash
# 安装打包工具
pip install pyinstaller

# 打包
pyinstaller --onefile --windowed --name "QQMonitor" qq_monitor.py
```

打包后的可执行文件在 `dist/` 目录下。

## 使用说明

### 1. 配置账号

在"账号管理"标签页添加要监测的QQ账号：
- **QQ号**: 要监测的QQ号
- **昵称**: 备注名称（用于识别）
- **Napcat地址**: Napcat HTTP API 地址，默认 `http://127.0.0.1:3000`
- **检查间隔**: 检测间隔时间（秒）

### 2. 配置邮件

在"邮件配置"标签页设置SMTP信息：
- **SMTP服务器**: 如 `smtp.qq.com`
- **端口**: SSL通常为465
- **发件邮箱**: 你的邮箱地址
- **授权码**: 邮箱授权码（非密码）
- **收件邮箱**: 接收告警的邮箱

### 3. 开始监测

点击"开始监测"按钮启动监测服务。

## 配置文件

配置文件位置：
- Windows: `%APPDATA%\QQMonitor\config.yaml`
- macOS: `~/Library/Application Support/QQMonitor/config.yaml`
- Linux: `~/.config/qq-monitor/config.yaml`

## 手动配置示例

```yaml
accounts:
  - uin: "123456789"
    nickname: "测试账号"
    napcat_url: "http://127.0.0.1:3000"
    check_interval: 60
    enabled: true

email:
  smtp_server: "smtp.qq.com"
  smtp_port: 465
  smtp_user: "your@qq.com"
  smtp_password: "授权码"
  receiver: "receiver@example.com"
  use_ssl: true

auto_start: false
```

## 常见问题

### Q: 提示"无法连接到Napcat服务"？
A: 检查Napcat是否正常运行，HTTP API是否开启。

### Q: 邮件发送失败？
A: 确认SMTP配置正确，使用授权码而非密码。

### Q: 如何获取QQ邮箱授权码？
A: 登录QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 生成授权码

## 许可证

MIT License
