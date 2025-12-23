# PowerShell script to build Windows executable with PyInstaller

Write-Host "Building Seed Library Task Tracker for Windows..." -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create PyInstaller spec file with bundled templates and static assets
$specContent = @"
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app/templates', 'app/templates'),
        ('app/static', 'app/static'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SeedLibraryTaskTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
"@

Write-Host "Creating PyInstaller spec file..." -ForegroundColor Yellow
$specContent | Out-File -FilePath "seed_tracker.spec" -Encoding UTF8

# Build with PyInstaller (one-file, windowed)
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller seed_tracker.spec --clean --noconfirm --onefile --windowed

# Check if build was successful
if (Test-Path "dist/SeedLibraryTaskTracker.exe") {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "Executable location: dist/SeedLibraryTaskTracker.exe" -ForegroundColor Cyan
    Write-Host "`nTo run the application:" -ForegroundColor Yellow
    Write-Host "  1. Navigate to the dist folder" -ForegroundColor White
    Write-Host "  2. Run SeedLibraryTaskTracker.exe" -ForegroundColor White
    Write-Host "  3. Open your browser to http://127.0.0.1:8000" -ForegroundColor White
} else {
    Write-Host "`nBuild failed! Please check the error messages above." -ForegroundColor Red
    exit 1
}

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
