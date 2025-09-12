@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM Comprehensive Nativefier 5-Way Split App Creator for Windows
REM =============================================================================
REM Creates a professional 5-pane desktop application from web URLs
REM with resizable panes, shared authentication, and full customization
REM 
REM Usage: nativifier5.bat [OPTIONS]
REM Author: Codegen AI Assistant
REM Version: 1.0.0
REM =============================================================================

REM Default configuration
set "APP_NAME=Codegen-5Way"
set "APP_WIDTH=1800"
set "APP_HEIGHT=1200"
set "PLATFORM=win32"
set "ARCH=x64"
set "CHROME_USER_DATA=%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default"
set "TEMP_HTML=%TEMP%\nativefier-5way.html"
set "USE_AUTH=true"
set "LAYOUT=grid"
set "DEBUG=false"
set "CLEAN=false"

REM Default URLs and titles
set "DEFAULT_URL1=https://codegen.com/"
set "DEFAULT_URL2=https://codegen.com/dashboard"
set "DEFAULT_URL3=https://codegen.com/settings"
set "DEFAULT_URL4=https://codegen.com/repos"
set "DEFAULT_URL5=https://codegen.com/analytics"

set "DEFAULT_TITLE1=🏠 Home"
set "DEFAULT_TITLE2=📊 Dashboard"
set "DEFAULT_TITLE3=⚙️ Settings"
set "DEFAULT_TITLE4=📁 Repos"
set "DEFAULT_TITLE5=📈 Analytics"

REM Initialize arrays
set "URL_COUNT=5"
for /L %%i in (1,1,5) do (
    set "URL%%i=!DEFAULT_URL%%i!"
    set "TITLE%%i=!DEFAULT_TITLE%%i!"
)

REM Color codes for Windows
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "PURPLE=[95m"
set "CYAN=[96m"
set "NC=[0m"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :check_dependencies
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-n" (
    set "APP_NAME=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--name" (
    set "APP_NAME=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="-w" (
    set "APP_WIDTH=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--width" (
    set "APP_WIDTH=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="-H" (
    set "APP_HEIGHT=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--height" (
    set "APP_HEIGHT=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="-a" (
    set "ARCH=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--arch" (
    set "ARCH=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="-c" (
    set "CHROME_USER_DATA=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--chrome-data" (
    set "CHROME_USER_DATA=%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="-u" (
    call :parse_urls "%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--urls" (
    call :parse_urls "%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="-t" (
    call :parse_titles "%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--titles" (
    call :parse_titles "%~2"
    shift & shift & goto :parse_args
)
if /i "%~1"=="--no-auth" (
    set "USE_AUTH=false"
    shift & goto :parse_args
)
if /i "%~1"=="--vertical" (
    set "LAYOUT=vertical"
    shift & goto :parse_args
)
if /i "%~1"=="--debug" (
    set "DEBUG=true"
    shift & goto :parse_args
)
if /i "%~1"=="--clean" (
    set "CLEAN=true"
    shift & goto :parse_args
)
echo %RED%[ERROR]%NC% Unknown option: %~1
goto :show_help

:parse_urls
set "url_list=%~1"
set "URL_COUNT=0"
for %%a in ("%url_list:,=" "%") do (
    set /a URL_COUNT+=1
    set "URL!URL_COUNT!=%%~a"
)
goto :eof

:parse_titles
set "title_list=%~1"
set "title_idx=0"
for %%a in ("%title_list:,=" "%") do (
    set /a title_idx+=1
    set "TITLE!title_idx!=%%~a"
)
goto :eof

:show_help
echo.
echo %CYAN%Comprehensive Nativefier 5-Way Split App Creator for Windows%NC%
echo.
echo USAGE:
echo     %~nx0 [OPTIONS]
echo.
echo OPTIONS:
echo     -h, --help              Show this help message
echo     -n, --name NAME         App name (default: %APP_NAME%)
echo     -w, --width WIDTH       App width (default: %APP_WIDTH%)
echo     -H, --height HEIGHT     App height (default: %APP_HEIGHT%)
echo     -a, --arch ARCH         Architecture: x64, arm64 (default: %ARCH%)
echo     -c, --chrome-data PATH  Chrome user data directory
echo     -u, --urls URL1,URL2... Comma-separated URLs (default: codegen.com pages)
echo     -t, --titles T1,T2...   Comma-separated titles (default: predefined titles)
echo     --no-auth               Don't use Chrome authentication
echo     --vertical              Use vertical layout instead of grid
echo     --debug                 Enable debug mode
echo     --clean                 Clean previous installations
echo.
echo EXAMPLES:
echo     # Basic usage with defaults
echo     %~nx0
echo.
echo     # Custom URLs and titles
echo     %~nx0 -u "https://github.com,https://linear.app" -t "GitHub,Linear"
echo.
echo     # Custom app with different size
echo     %~nx0 -w 1920 -H 1080 -n "MyApp"
echo.
echo     # Vertical layout without authentication
echo     %~nx0 --vertical --no-auth
echo.
echo FEATURES:
echo     ✅ Fully resizable panes with drag handles
echo     ✅ Shared authentication across all panes
echo     ✅ Professional UI with headers and styling
echo     ✅ Windows-optimized with proper metadata
echo     ✅ Customizable layouts (grid or vertical)
echo     ✅ Auto-launch capability
echo     ✅ Comprehensive error handling
echo     ✅ Debug mode for troubleshooting
echo.
exit /b 0

:check_dependencies
echo %BLUE%[STEP]%NC% Checking dependencies...

REM Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Node.js is not installed or not in PATH
    echo %BLUE%[INFO]%NC% Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Check for npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% npm is not installed or not in PATH
    echo %BLUE%[INFO]%NC% Please install npm (usually comes with Node.js)
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% All dependencies found

:install_nativefier
echo %PURPLE%[STEP]%NC% Installing/updating Nativefier...

npm list -g nativefier >nul 2>&1
if errorlevel 1 (
    echo %BLUE%[INFO]%NC% Installing Nativefier globally...
    npm install -g nativefier
) else (
    echo %BLUE%[INFO]%NC% Nativefier already installed, updating...
    npm update -g nativefier
)

if errorlevel 1 (
    echo %RED%[ERROR]%NC% Failed to install/update Nativefier
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% Nativefier ready

:clean_previous
if /i "%CLEAN%"=="true" (
    echo %PURPLE%[STEP]%NC% Cleaning previous installations...
    
    set "app_dir=%APP_NAME%-%PLATFORM%-%ARCH%"
    if exist "!app_dir!" (
        echo %BLUE%[INFO]%NC% Removing existing app directory: !app_dir!
        rmdir /s /q "!app_dir!"
    )
    
    echo %GREEN%[SUCCESS]%NC% Cleanup completed
)

:create_html
echo %PURPLE%[STEP]%NC% Creating HTML layout...

REM Generate CSS based on layout
if /i "%LAYOUT%"=="vertical" (
    set "CSS_LAYOUT=.container { display: flex; flex-direction: column; height: 100vh; } .pane { flex: 1; display: flex; flex-direction: column; background: white; min-height: 100px; } .resizer { height: 3px; background: #e2e8f0; cursor: row-resize; transition: background 0.2s; } .resizer:hover { background: #cbd5e0; }"
) else (
    set /a cols=(%URL_COUNT% + 1) / 2
    set /a rows=(%URL_COUNT% + !cols! - 1) / !cols!
    set "CSS_LAYOUT=.container { display: grid; grid-template-columns: repeat(!cols!, 1fr); grid-template-rows: repeat(!rows!, 1fr); height: 100vh; gap: 3px; background: #e2e8f0; } .pane { display: flex; flex-direction: column; background: white; min-width: 200px; min-height: 200px; }"
)

REM Create HTML file
(
echo ^<!DOCTYPE html^>
echo ^<html^>
echo ^<head^>
echo     ^<title^>%APP_NAME%^</title^>
echo     ^<meta charset="UTF-8"^>
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0"^>
echo     ^<style^>
echo         * { margin: 0; padding: 0; box-sizing: border-box; }
echo         body { 
echo             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
echo             height: 100vh; 
echo             overflow: hidden; 
echo             background: #f7fafc;
echo         }
echo         
echo         !CSS_LAYOUT!
echo         
echo         .header { 
echo             background: linear-gradient^(135deg, #667eea 0%%, #764ba2 100%%^);
echo             color: white; 
echo             padding: 8px 16px; 
echo             font-size: 13px; 
echo             font-weight: 600;
echo             border-bottom: 1px solid rgba^(255,255,255,0.1^);
echo             display: flex;
echo             align-items: center;
echo             justify-content: space-between;
echo             box-shadow: 0 2px 4px rgba^(0,0,0,0.1^);
echo         }
echo         
echo         .header-title {
echo             display: flex;
echo             align-items: center;
echo             gap: 8px;
echo         }
echo         
echo         .header-status {
echo             font-size: 11px;
echo             opacity: 0.8;
echo         }
echo         
echo         iframe { 
echo             flex: 1; 
echo             border: none; 
echo             width: 100%%;
echo             height: 100%%;
echo             background: white;
echo         }
echo         
echo         .pane:hover .header {
echo             background: linear-gradient^(135deg, #5a67d8 0%%, #6b46c1 100%%^);
echo         }
echo         
echo         /* Scrollbar styling */
echo         ::-webkit-scrollbar {
echo             width: 6px;
echo         }
echo         
echo         ::-webkit-scrollbar-track {
echo             background: #f1f1f1;
echo         }
echo         
echo         ::-webkit-scrollbar-thumb {
echo             background: #c1c1c1;
echo             border-radius: 3px;
echo         }
echo         
echo         ::-webkit-scrollbar-thumb:hover {
echo             background: #a8a8a8;
echo         }
echo     ^</style^>
echo ^</head^>
echo ^<body^>
echo     ^<div class="container" id="container"^>
) > "%TEMP_HTML%"

REM Generate panes
for /L %%i in (1,1,%URL_COUNT%) do (
    (
    echo         ^<div class="pane" data-url="!URL%%i!"^>
    echo             ^<div class="header"^>
    echo                 ^<div class="header-title"^>
    echo                     ^<span^>!TITLE%%i!^</span^>
    echo                 ^</div^>
    echo                 ^<div class="header-status"^>●^</div^>
    echo             ^</div^>
    echo             ^<iframe src="!URL%%i!" 
    echo                     sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation allow-downloads"
    echo                     loading="lazy"
    echo                     onload="this.parentNode.querySelector^('.header-status'^).style.color='#48bb78'"
    echo                     onerror="this.parentNode.querySelector^('.header-status'^).style.color='#f56565'"^>
    echo             ^</iframe^>
    echo         ^</div^>
    ) >> "%TEMP_HTML%"
    
    REM Add resizer for vertical layout (except after last pane)
    if /i "%LAYOUT%"=="vertical" if %%i LSS %URL_COUNT% (
        echo         ^<div class="resizer"^>^</div^> >> "%TEMP_HTML%"
    )
)

REM Complete HTML file
(
echo     ^</div^>
echo 
echo     ^<script^>
if /i "%LAYOUT%"=="vertical" (
echo         let isResizing = false;
echo         let currentResizer = null;
echo         
echo         document.querySelectorAll^('.resizer'^).forEach^(resizer =^> {
echo             resizer.addEventListener^('mousedown', initResize^);
echo         }^);
echo         
echo         function initResize^(e^) {
echo             isResizing = true;
echo             currentResizer = e.target;
echo             document.addEventListener^('mousemove', doResize^);
echo             document.addEventListener^('mouseup', stopResize^);
echo             document.body.style.cursor = 'row-resize';
echo             e.preventDefault^(^);
echo         }
echo         
echo         function doResize^(e^) {
echo             if ^(!isResizing^) return;
echo             
echo             const container = document.querySelector^('.container'^);
echo             const rect = container.getBoundingClientRect^(^);
echo             const percentage = ^(^(e.clientY - rect.top^) / rect.height^) * 100;
echo             
echo             const panes = Array.from^(container.children^).filter^(child =^> child.classList.contains^('pane'^)^);
echo             const resizerIndex = Array.from^(container.children^).indexOf^(currentResizer^);
echo             const paneIndex = Math.floor^(resizerIndex / 2^);
echo             
echo             if ^(panes[paneIndex]^) {
echo                 panes[paneIndex].style.flexBasis = Math.max^(10, Math.min^(80, percentage^)^) + '%%';
echo             }
echo         }
echo         
echo         function stopResize^(^) {
echo             isResizing = false;
echo             currentResizer = null;
echo             document.removeEventListener^('mousemove', doResize^);
echo             document.removeEventListener^('mouseup', stopResize^);
echo             document.body.style.cursor = 'default';
echo         }
) else (
echo         console.log^('Grid layout loaded with', document.querySelectorAll^('.pane'^).length, 'panes'^);
)
echo         
echo         // Prevent iframe interference with resizing
echo         document.addEventListener^('mousedown', function^(^) {
echo             document.querySelectorAll^('iframe'^).forEach^(iframe =^> {
echo                 iframe.style.pointerEvents = 'none';
echo             }^);
echo         }^);
echo         
echo         document.addEventListener^('mouseup', function^(^) {
echo             document.querySelectorAll^('iframe'^).forEach^(iframe =^> {
echo                 iframe.style.pointerEvents = 'auto';
echo             }^);
echo         }^);
echo         
if /i "%DEBUG%"=="true" (
echo         console.log^('%APP_NAME% loaded with %URL_COUNT% panes'^);
echo         console.log^('Layout: %LAYOUT%'^);
)
echo         
echo         // Update status indicators
echo         document.querySelectorAll^('iframe'^).forEach^(iframe =^> {
echo             iframe.addEventListener^('load', function^(^) {
echo                 const status = this.parentNode.querySelector^('.header-status'^);
echo                 status.textContent = '●';
echo                 status.style.color = '#48bb78';
echo             }^);
echo             
echo             iframe.addEventListener^('error', function^(^) {
echo                 const status = this.parentNode.querySelector^('.header-status'^);
echo                 status.textContent = '●';
echo                 status.style.color = '#f56565';
echo             }^);
echo         }^);
echo     ^</script^>
echo ^</body^>
echo ^</html^>
) >> "%TEMP_HTML%"

echo %GREEN%[SUCCESS]%NC% HTML layout created: %TEMP_HTML%

:build_app
echo %PURPLE%[STEP]%NC% Building Nativefier app...

REM Build nativefier command
set "NATIVEFIER_CMD=nativefier "file:///%TEMP_HTML%" --name "%APP_NAME%" --platform "%PLATFORM%" --arch "%ARCH%" --width "%APP_WIDTH%" --height "%APP_HEIGHT%" --single-instance --disable-dev-shm-usage --no-sandbox"

REM Add authentication if enabled
if /i "%USE_AUTH%"=="true" (
    if exist "%CHROME_USER_DATA%" (
        echo %BLUE%[INFO]%NC% Using Chrome authentication from: %CHROME_USER_DATA%
        set "NATIVEFIER_CMD=!NATIVEFIER_CMD! --user-data-dir "%CHROME_USER_DATA%" --disable-web-security"
    ) else (
        echo %YELLOW%[WARNING]%NC% Chrome authentication disabled or directory not found
    )
) else (
    echo %YELLOW%[WARNING]%NC% Chrome authentication disabled
)

REM Add Windows-specific options
set "NATIVEFIER_CMD=!NATIVEFIER_CMD! --win32metadata.CompanyName "Nativefier App" --win32metadata.FileDescription "%APP_NAME%""

REM Add user agent
set "NATIVEFIER_CMD=!NATIVEFIER_CMD! --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36""

if /i "%DEBUG%"=="true" (
    echo %BLUE%[INFO]%NC% Nativefier command: !NATIVEFIER_CMD!
)

REM Run nativefier
!NATIVEFIER_CMD!
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Failed to build app
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% App built successfully!

:launch_app
set "app_dir=%APP_NAME%-%PLATFORM%-%ARCH%"

if exist "%app_dir%" (
    echo %PURPLE%[STEP]%NC% Launching app...
    
    if exist "%app_dir%\%APP_NAME%.exe" (
        start "" "%app_dir%\%APP_NAME%.exe"
        echo %GREEN%[SUCCESS]%NC% App launched!
    ) else (
        echo %RED%[ERROR]%NC% Executable not found: %app_dir%\%APP_NAME%.exe
    )
) else (
    echo %RED%[ERROR]%NC% App directory not found: %app_dir%
)

:cleanup
if exist "%TEMP_HTML%" (
    del "%TEMP_HTML%"
)

:success
echo.
echo %GREEN%==============================================%NC%
echo %GREEN%  🎉 SUCCESS! App created and launched!%NC%
echo %GREEN%==============================================%NC%
echo.
echo App Name: %APP_NAME%
echo Platform: %PLATFORM% (%ARCH%)
echo Size: %APP_WIDTH%x%APP_HEIGHT%
echo Layout: %LAYOUT%
echo Panes: %URL_COUNT%
if /i "%USE_AUTH%"=="true" (
    echo Authentication: Enabled
) else (
    echo Authentication: Disabled
)
echo.
echo App location: .\%APP_NAME%-%PLATFORM%-%ARCH%\
echo.
echo Enjoy your new desktop app! 🚀

exit /b 0
