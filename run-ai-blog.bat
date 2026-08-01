@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%PROJECT_DIR%.venv\Scripts\python.exe"
set "ENV_FILE=%PROJECT_DIR%.env"
set "GENERATION_SCRIPT=%PROJECT_DIR%blog\generate.sh"
set "RUNTIME_DIR=%PROJECT_DIR%.runtime"
set "GENERATION_MARKER=%RUNTIME_DIR%\last-generation-attempt-utc.txt"
set "REFRESH_TASK=AI Blog - RSS Refresh"
set "GENERATION_TASK=AI Blog - Post Generation"

set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%BASH_EXE%" set "BASH_EXE=%ProgramFiles%\Git\usr\bin\bash.exe"
if not exist "%BASH_EXE%" if defined ProgramFiles(x86) set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"

if "%~1"=="" goto default
if /I "%~1"=="check" goto check
if /I "%~1"=="install-schedule" goto install_schedule
if /I "%~1"=="refresh" goto refresh
if /I "%~1"=="generate" goto generate
if /I "%~1"=="generate-if-due" goto generate_if_due
if /I "%~1"=="server" goto server

echo ERROR: Unknown command: %~1 1>&2
echo Usage: %~nx0 [check^|install-schedule^|refresh^|generate^|generate-if-due^|server] 1>&2
exit /b 2

:default
call :check_requirements
if errorlevel 1 exit /b %ERRORLEVEL%

call :install_scheduled_tasks install
if errorlevel 1 exit /b %ERRORLEVEL%

call :run_server
exit /b %ERRORLEVEL%

:check
call :check_requirements
exit /b %ERRORLEVEL%

:install_schedule
call :check_requirements
if errorlevel 1 exit /b %ERRORLEVEL%

call :install_scheduled_tasks install
exit /b %ERRORLEVEL%

:refresh
call :run_refresh
exit /b %ERRORLEVEL%

:generate
call :run_generation
exit /b %ERRORLEVEL%

:generate_if_due
call :run_generation_if_due
exit /b %ERRORLEVEL%

:server
call :check_requirements
if errorlevel 1 exit /b %ERRORLEVEL%

call :run_server
exit /b %ERRORLEVEL%

:check_requirements
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python virtual environment not found: "%PYTHON_EXE%" 1>&2
    echo Create it with: py -3.12 -m venv .venv 1>&2
    exit /b 1
)

if not exist "%ENV_FILE%" (
    echo ERROR: Missing environment file: "%ENV_FILE%" 1>&2
    echo Copy .env.example to .env and configure it first. 1>&2
    exit /b 1
)

if not exist "%GENERATION_SCRIPT%" (
    echo ERROR: Missing generation script: "%GENERATION_SCRIPT%" 1>&2
    exit /b 1
)

if not exist "%BASH_EXE%" (
    echo ERROR: Git Bash was not found. Install Git for Windows. 1>&2
    exit /b 1
)

where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo ERROR: Windows PowerShell was not found. 1>&2
    exit /b 1
)

powershell.exe -NoProfile -Command "if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) { exit 1 }"
if errorlevel 1 (
    echo ERROR: The Windows ScheduledTasks module is unavailable. 1>&2
    exit /b 1
)

pushd "%PROJECT_DIR%" >nul
"%PYTHON_EXE%" -c "from config import settings; import uvicorn" >nul 2>&1
set "CONFIG_STATUS=%ERRORLEVEL%"
if not "%CONFIG_STATUS%"=="0" (
    popd
    echo ERROR: Python could not load the project configuration. Check .env. 1>&2
    exit /b %CONFIG_STATUS%
)

"%PYTHON_EXE%" -m blog.generate_helpers --help >nul 2>&1
set "HELPER_STATUS=%ERRORLEVEL%"
if not "%HELPER_STATUS%"=="0" (
    popd
    echo ERROR: The blog helper CLI could not start. 1>&2
    exit /b %HELPER_STATUS%
)

"%BASH_EXE%" -n ./blog/generate.sh >nul 2>&1
set "BASH_STATUS=%ERRORLEVEL%"
if not "%BASH_STATUS%"=="0" (
    popd
    echo ERROR: blog/generate.sh failed its Bash syntax check. 1>&2
    exit /b %BASH_STATUS%
)

"%BASH_EXE%" -lc "command -v claude >/dev/null 2>&1"
set "CLAUDE_STATUS=%ERRORLEVEL%"
popd
if not "%CLAUDE_STATUS%"=="0" (
    echo ERROR: Claude Code CLI was not found in the Git Bash PATH. 1>&2
    exit /b %CLAUDE_STATUS%
)

call :install_scheduled_tasks validate
if errorlevel 1 (
    echo ERROR: The Windows scheduled-task definition is invalid. 1>&2
    exit /b 1
)

echo Prerequisite check passed.
exit /b 0

:install_scheduled_tasks
set "AI_BLOG_LAUNCHER=%~f0"
set "AI_BLOG_PROJECT=%PROJECT_DIR%"
set "AI_BLOG_SCHEDULE_MODE=%~1"
if not defined AI_BLOG_SCHEDULE_MODE set "AI_BLOG_SCHEDULE_MODE=install"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop';" ^
    "$script = $env:AI_BLOG_LAUNCHER;" ^
    "$project = $env:AI_BLOG_PROJECT;" ^
    "$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name;" ^
    "$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited;" ^
    "$quote = [char]34;" ^
    "$refreshArguments = '/d /c ' + $quote + $quote + $script + $quote + ' refresh' + $quote;" ^
    "$generationArguments = '/d /c ' + $quote + $quote + $script + $quote + ' generate-if-due' + $quote;" ^
    "$refreshAction = New-ScheduledTaskAction -Execute $env:ComSpec -Argument $refreshArguments -WorkingDirectory $project;" ^
    "$generationAction = New-ScheduledTaskAction -Execute $env:ComSpec -Argument $generationArguments -WorkingDirectory $project;" ^
    "$now = Get-Date;" ^
    "$refreshStart = $now.Date.AddMinutes(5);" ^
    "while ($refreshStart -le $now) { $refreshStart = $refreshStart.AddHours(1) };" ^
    "$generationStart = $now.Date.AddMinutes(12);" ^
    "while ($generationStart -le $now) { $generationStart = $generationStart.AddHours(1) };" ^
    "$refreshTrigger = New-ScheduledTaskTrigger -Once -At $refreshStart -RepetitionInterval (New-TimeSpan -Hours 1);" ^
    "$generationTrigger = New-ScheduledTaskTrigger -Once -At $generationStart -RepetitionInterval (New-TimeSpan -Hours 1);" ^
    "$refreshSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew;" ^
    "$generationSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -MultipleInstances IgnoreNew;" ^
    "if ($env:AI_BLOG_SCHEDULE_MODE -eq 'validate') {" ^
    "    if ($refreshAction.Arguments -notlike ('*' + $quote + $quote + $script + $quote + ' refresh' + $quote)) { throw 'Refresh action arguments are malformed' };" ^
    "    if ($generationAction.Arguments -notlike ('*' + $quote + $quote + $script + $quote + ' generate-if-due' + $quote)) { throw 'Generation action arguments are malformed' };" ^
    "    if ($refreshTrigger.Repetition.Interval -ne 'PT1H') { throw 'Refresh trigger is not hourly' };" ^
    "    if ($generationTrigger.Repetition.Interval -ne 'PT1H') { throw 'Generation trigger is not hourly' };" ^
    "    exit 0;" ^
    "};" ^
    "Register-ScheduledTask -TaskName $env:REFRESH_TASK -Action $refreshAction -Trigger $refreshTrigger -Settings $refreshSettings -Principal $principal -Force | Out-Null;" ^
    "Register-ScheduledTask -TaskName $env:GENERATION_TASK -Action $generationAction -Trigger $generationTrigger -Settings $generationSettings -Principal $principal -Force | Out-Null;"

if errorlevel 1 (
    echo ERROR: Failed to create Windows scheduled tasks. 1>&2
    echo Try running this batch file from an Administrator command prompt. 1>&2
    exit /b 1
)

if /I "%~1"=="validate" exit /b 0

echo Scheduled tasks installed or updated:
echo   %REFRESH_TASK% - hourly at minute 05
echo   %GENERATION_TASK% - checks hourly at minute 12 and posts Mon/Wed/Fri after 14:12 UTC
echo Tasks run as %USERNAME% while that user is logged on.
exit /b 0

:run_refresh
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python virtual environment not found: "%PYTHON_EXE%" 1>&2
    exit /b 1
)

pushd "%PROJECT_DIR%" >nul
"%PYTHON_EXE%" -m blog.refresh_sources
set "RUN_STATUS=%ERRORLEVEL%"
popd
exit /b %RUN_STATUS%

:run_generation
if not exist "%BASH_EXE%" (
    echo ERROR: Git Bash was not found. 1>&2
    exit /b 1
)

pushd "%PROJECT_DIR%" >nul
"%BASH_EXE%" -lc "./blog/generate.sh"
set "RUN_STATUS=%ERRORLEVEL%"
popd
exit /b %RUN_STATUS%

:run_generation_if_due
powershell.exe -NoProfile -Command ^
    "$now = [DateTime]::UtcNow;" ^
    "$postingDays = @([DayOfWeek]::Monday, [DayOfWeek]::Wednesday, [DayOfWeek]::Friday);" ^
    "if (($postingDays -contains $now.DayOfWeek) -and ($now.TimeOfDay -ge [TimeSpan]::Parse('14:12:00'))) { exit 0 };" ^
    "exit 10;"
set "DUE_STATUS=%ERRORLEVEL%"

if "%DUE_STATUS%"=="10" exit /b 0
if not "%DUE_STATUS%"=="0" (
    echo ERROR: Could not evaluate the UTC generation schedule. 1>&2
    exit /b %DUE_STATUS%
)

set "UTC_DATE="
for /f "usebackq delims=" %%D in (`powershell.exe -NoProfile -Command "[DateTime]::UtcNow.ToString('yyyy-MM-dd')"`) do set "UTC_DATE=%%D"
if not defined UTC_DATE (
    echo ERROR: Could not determine the current UTC date. 1>&2
    exit /b 1
)

set "LAST_ATTEMPT="
if exist "%GENERATION_MARKER%" set /p "LAST_ATTEMPT=" < "%GENERATION_MARKER%"
if "%LAST_ATTEMPT%"=="%UTC_DATE%" (
    echo Generation was already evaluated for %UTC_DATE% UTC. Skipped.
    exit /b 0
)

set "AI_BLOG_CHECK_FILE=%TEMP%\ai-blog-check-%RANDOM%-%RANDOM%.json"
pushd "%PROJECT_DIR%" >nul
"%PYTHON_EXE%" -m blog.generate_helpers check-today > "%AI_BLOG_CHECK_FILE%"
set "CHECK_COMMAND_STATUS=%ERRORLEVEL%"
popd
if not "%CHECK_COMMAND_STATUS%"=="0" (
    del /q "%AI_BLOG_CHECK_FILE%" >nul 2>&1
    echo ERROR: Could not check whether today's post already exists. 1>&2
    exit /b %CHECK_COMMAND_STATUS%
)

powershell.exe -NoProfile -Command ^
    "try {" ^
    "    $result = Get-Content -Raw -LiteralPath $env:AI_BLOG_CHECK_FILE | ConvertFrom-Json;" ^
    "    if ($result.exists) { exit 0 };" ^
    "    exit 10;" ^
    "} catch {" ^
    "    Write-Error $_;" ^
    "    exit 2;" ^
    "}"
set "POST_STATUS=%ERRORLEVEL%"
del /q "%AI_BLOG_CHECK_FILE%" >nul 2>&1

if "%POST_STATUS%"=="0" (
    call :record_generation_attempt
    if errorlevel 1 exit /b 1
    echo A blog post already exists for the current UTC date. Generation skipped.
    exit /b 0
)
if not "%POST_STATUS%"=="10" (
    echo ERROR: Could not parse the existing-post check. 1>&2
    exit /b %POST_STATUS%
)

call :record_generation_attempt
if errorlevel 1 exit /b %ERRORLEVEL%

call :run_generation
exit /b %ERRORLEVEL%

:record_generation_attempt
if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%" >nul 2>&1
if not exist "%RUNTIME_DIR%" (
    echo ERROR: Could not create runtime state directory: "%RUNTIME_DIR%" 1>&2
    exit /b 1
)

> "%GENERATION_MARKER%" echo %UTC_DATE%
if errorlevel 1 (
    echo ERROR: Could not record the generation attempt. 1>&2
    exit /b 1
)
exit /b 0

:run_server
pushd "%PROJECT_DIR%" >nul
echo Starting AI Blog API using API_HOST and API_PORT from .env.
echo Press Ctrl+C to stop the server. Scheduled tasks will remain installed.
"%PYTHON_EXE%" -c "from config import settings; import uvicorn; uvicorn.run('api.main:app', host=settings.api_host, port=settings.api_port)"
set "RUN_STATUS=%ERRORLEVEL%"
popd
exit /b %RUN_STATUS%
