@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY=C:\Users\LV\AppData\Local\Programs\Python\Python312\python.exe"
set "SRC=图章重构\图章生成器.py"
set "ICO=%~dp0图章重构\app.ico"
set "VER=%~dp0图章重构\version_info.txt"

if not exist "%PY%" (
  echo [错误] 找不到 Python：%PY%
  pause
  exit /b 1
)

echo ============================================
echo  0/2  同步网页版到 docs\index.html
echo ============================================
rem docs\index.html 是 GitHub Pages 的入口，内容必须与 图章重构\图章生成器.html 完全一致
copy /Y "图章重构\图章生成器.html" "docs\index.html"
if errorlevel 1 goto fail

echo.
echo ============================================
echo  1/2  目录版（推荐，启动约 1 秒）
echo ============================================
"%PY%" -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name "图章生成器" --icon "%ICO%" --version-file "%VER%" ^
  --collect-all customtkinter --distpath "发布" --workpath ".build" --specpath ".build" ^
  "%SRC%"
if errorlevel 1 goto fail

echo.
echo ============================================
echo  2/2  单文件版（一个 exe，启动约 5 秒）
echo ============================================
"%PY%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "图章生成器" --icon "%ICO%" --version-file "%VER%" ^
  --collect-all customtkinter --distpath "发布\单文件版" --workpath ".build_one" --specpath ".build_one" ^
  "%SRC%"
if errorlevel 1 goto fail

echo.
echo 打包完成：
echo   发布\图章生成器\图章生成器.exe
echo   发布\单文件版\图章生成器.exe
pause
exit /b 0

:fail
echo.
echo [失败] 往上翻看报错。
pause
exit /b 1
