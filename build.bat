@echo off
REM QQ Monitor Windows打包脚本

echo === QQ Monitor 打包脚本 ===

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    pause
    exit /b 1
)

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt
pip install pyinstaller

REM 打包
echo 开始打包...
pyinstaller --onefile --windowed ^
    --name "QQMonitor" ^
    --add-data "README.md;." ^
    --hidden-import=PyQt5 ^
    --hidden-import=requests ^
    --hidden-import=yaml ^
    qq_monitor.py

REM 检查结果
if exist "dist\QQMonitor.exe" (
    echo 打包成功！
    echo 可执行文件位置: dist\
    dir dist\
) else (
    echo 打包失败，请检查错误信息
)

pause