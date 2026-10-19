Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Repo = "https://github.com/tc4dy/privmeta.git"
$ArchiveUrl = "https://github.com/tc4dy/privmeta/archive/refs/heads/main.zip"
$MinVersion = [version]"3.9"
$PkgName = "privmeta"

function Write-Step($msg) {
    Write-Host "[>] " -ForegroundColor Cyan -NoNewline
    Write-Host $msg
}

function Write-Ok($msg) {
    Write-Host "[+] " -ForegroundColor Green -NoNewline
    Write-Host $msg
}

function Write-Warn($msg) {
    Write-Host "[!] " -ForegroundColor Yellow -NoNewline
    Write-Host $msg
}

function Write-Fail($msg) {
    Write-Host "[-] " -ForegroundColor Red -NoNewline
    Write-Host $msg
}

function Stop-Install($msg) {
    Write-Fail $msg
    exit 1
}

function Get-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $version = & py -3 --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $version) {
            return @("py", "-3")
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $version = & python --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $version) {
            return @("python")
        }
    }
    Stop-Install "Python is not installed or not on PATH."
}

function Get-PythonVersion($Cmd) {
    $parts = $Cmd
    $exe = $parts[0]
    $args = @()
    if ($parts.Count -gt 1) { $args = $parts[1..($parts.Count - 1)] }
    $raw = & $exe @args -c "import sys; print('{}.{}.{}'.format(*sys.version_info[:3]))" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        Stop-Install "Python is not usable."
    }
    return $raw.Trim()
}

function Test-Version($Current, $Minimum) {
    $c = [version]$Current
    return $c -ge $Minimum
}

Write-Step "PrivMeta installer"
Write-Host "    repo: " -NoNewline
Write-Host $Repo -ForegroundColor DarkGray
Write-Host ""

$PythonCmd = Get-Python
Write-Step ("python: " + ($PythonCmd -join " "))

$CurrentVersion = Get-PythonVersion $PythonCmd
if (-not (Test-Version $CurrentVersion $MinVersion)) {
    Stop-Install ("Python " + $MinVersion + " or newer is required (found " + $CurrentVersion + ").")
}
Write-Ok ("python version: " + $CurrentVersion)

Write-Step "checking pip"
$pyExe = $PythonCmd[0]
$pyArgs = @()
if ($PythonCmd.Count -gt 1) { $pyArgs = $PythonCmd[1..($PythonCmd.Count - 1)] }
& $pyExe @pyArgs -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
    Stop-Install "pip is not available for this Python."
}

$TempDir = Join-Path $env:TEMP ("privmeta-install-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempDir | Out-Null

try {
    Write-Step "fetching repository"
    $cloneTarget = Join-Path $TempDir "privmeta"
    if (Get-Command git -ErrorAction SilentlyContinue) {
        & git clone --depth 1 $Repo $cloneTarget *> $null
        if ($LASTEXITCODE -ne 0) {
            Stop-Install "git clone failed. Check your network."
        }
    } else {
        Write-Warn "git is not installed, downloading archive"
        $archive = Join-Path $TempDir "src.zip"
        try {
            Invoke-WebRequest -Uri $ArchiveUrl -OutFile $archive -UseBasicParsing
        } catch {
            Stop-Install "download failed. Install git or check your network."
        }
        try {
            Expand-Archive -Path $archive -DestinationPath $TempDir -Force
            Rename-Item -Path (Join-Path $TempDir "privmeta-main") -NewName "privmeta"
        } catch {
            Stop-Install "extracting archive failed."
        }
    }
    Write-Ok "source ready"

    Write-Step "installing package"
    Push-Location $cloneTarget
    try {
        & $pyExe @pyArgs -m pip install --user --upgrade . *> (Join-Path $TempDir "pip.log")
        if ($LASTEXITCODE -ne 0) {
            $log = Get-Content (Join-Path $TempDir "pip.log") -ErrorAction SilentlyContinue | Select-Object -Last 30
            if ($log) { $log | Write-Host }
            Stop-Install "pip install failed."
        }
    } finally {
        Pop-Location
    }
    Write-Ok "package installed"

    Write-Step "checking optional dependencies"
    function Ask-Optional($prompt, $module, $label) {
        Write-Host "[?] " -ForegroundColor Cyan -NoNewline
        Write-Host ($prompt + " (y/N): ") -NoNewline
        $reply = Read-Host
        if ($reply -match "^[yY]") {
            Push-Location $cloneTarget
            try {
                & $pyExe @pyArgs -m pip install --user $module *> $null
            } finally {
                Pop-Location
            }
            if ($LASTEXITCODE -eq 0) {
                Write-Ok ("installed " + $label)
            } else {
                Write-Warn ("could not install " + $label)
            }
        } else {
            Write-Host "[>] " -ForegroundColor DarkGray -NoNewline
            Write-Host ("skipping " + $label)
        }
    }

    & $pyExe @pyArgs -c "import pypdf" *> $null
    if ($LASTEXITCODE -ne 0) {
        Ask-Optional "install PDF support (pypdf)" "pypdf" "pypdf"
    }

    & $pyExe @pyArgs -c "import mutagen" *> $null
    if ($LASTEXITCODE -ne 0) {
        Ask-Optional "install audio support (mutagen)" "mutagen" "mutagen"
    }

    if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
        Write-Warn "ffmpeg is not installed. Video shredding will fail until you install it."
        Write-Host "    install with: winget install ffmpeg"
    }

    Write-Step "verifying installation"
    $userScripts = Join-Path $env:APPDATA "Python\Scripts"
    if (-not (($env:PATH -split ';') -contains $userScripts)) {
        Write-Warn ($userScripts + " is not in PATH")
        Write-Host "[?] " -ForegroundColor Cyan -NoNewline
        Write-Host ("add it to your user PATH now? (y/N): ") -NoNewline
        $reply = Read-Host
        if ($reply -match "^[yY]") {
            $oldPath = [Environment]::GetEnvironmentVariable("Path", "User")
            if ($oldPath -notlike "*$userScripts*") {
                [Environment]::SetEnvironmentVariable("Path", $oldPath + ";" + $userScripts, "User")
                Write-Ok "PATH updated (open a new terminal)"
            } else {
                Write-Ok "already present"
            }
        } else {
            Write-Warn ("add manually: " + $userScripts)
        }
    }

    $privmetaCmd = Get-Command privmeta -ErrorAction SilentlyContinue
    if ($privmetaCmd) {
        Write-Ok "privmeta is available on PATH"
    } else {
        Write-Warn ("privmeta is not on PATH yet, try: " + (Join-Path $userScripts "privmeta.exe"))
    }

    Write-Host ""
    Write-Ok "install finished"
    Write-Host "[>] " -ForegroundColor Cyan -NoNewline
    Write-Host "run: " -NoNewline
    Write-Host "privmeta" -ForegroundColor White
} finally {
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    }
}