# 多平台打包说明

## 重要提示
**PyInstaller 只能打包当前系统的可执行文件**，无法交叉编译。

如需打包不同平台的版本，请在对应系统上运行打包脚本。

## Windows 打包
```bash
# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 运行打包
build.bat
# 或
python build_all.py
```

## macOS 打包
```bash
# 安装依赖
pip3 install -r requirements.txt
pip3 install pyinstaller

# 运行打包
chmod +x build.sh
./build.sh
# 或
python3 build_all.py
```

## Linux 打包
```bash
# 安装依赖
pip3 install -r requirements.txt
pip3 install pyinstaller

# 运行打包
chmod +x build.sh
./build.sh
# 或
python3 build_all.py
```

## Docker 方式 (推荐)
如果你有 Docker，可以用 Docker 打包：

```bash
# Windows
docker run --rm -v "%cd%":/app -w /app python:3.9-windowsservercore pip install pyinstaller && pyinstaller --onefile qq_monitor.py

# Linux
docker run --rm -v "$PWD":/app -w /app python:3.9-slim bash -c "pip install -r requirements.txt && pip install pyinstaller && pyinstaller --onefile qq_monitor.py"
```

## GitHub Actions 自动打包
可以在仓库中添加 `.github/workflows/build.yml` 实现自动多平台打包：

```yaml
name: Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build
        run: pyinstaller --onefile --name QQMonitor qq_monitor.py
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: QQMonitor-${{ matrix.os }}
          path: dist/
```