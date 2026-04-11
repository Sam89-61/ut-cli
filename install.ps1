
$repoUrl    = "https://github.com/Sam89-61/ut-cli/archive/refs/heads/main.zip"
$installDir = "$env:LOCALAPPDATA\Programs\ut-cli"
$zipPath    = "$env:TEMP\ut-cli.zip"
$extractDir = "$env:TEMP\ut-cli-extract"

Write-Host ""
Write-Host "  Useful Tool (ut) — Installation" -ForegroundColor Cyan
Write-Host "  ================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Téléchargement..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $repoUrl -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Host "  Erreur : impossible de télécharger le dépôt." -ForegroundColor Red
    Write-Host "  Vérifiez votre connexion internet." -ForegroundColor DarkGray
    exit 1
}
Write-Host "  Extraction..." -ForegroundColor Yellow
if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
$sourceDir = (Get-ChildItem $extractDir -Directory | Select-Object -First 1).FullName
Write-Host "  Installation dans $installDir..." -ForegroundColor Yellow
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}
Copy-Item -Path "$sourceDir\*" -Destination $installDir -Recurse -Force
$reqPath = Join-Path $installDir "requirements.txt"
if (Test-Path $reqPath) {
    Write-Host "  Installation des dépendances Python..." -ForegroundColor Yellow
    $pythonCheck = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCheck) {
        Write-Host "  Python non trouvé. Installation via winget..." -ForegroundColor Yellow
        $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
        if (-not $wingetCheck) {
            Write-Host ""
            Write-Host "  Erreur : winget n'est pas disponible sur ce système." -ForegroundColor Red
            Write-Host "  Installez Python manuellement : https://www.python.org/downloads/" -ForegroundColor Yellow
            Write-Host "  Cochez 'Add Python to PATH' lors de l'installation." -ForegroundColor Yellow
            Write-Host ""
            exit 1
        }
        winget install --id Python.Python.3 --source winget --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Erreur : échec de l'installation de Python." -ForegroundColor Red
            exit 1
        }
        # Recharger le PATH pour que python soit disponible
        $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [Environment]::GetEnvironmentVariable("PATH", "User")
        $pythonCheck = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCheck) {
            Write-Host "  Python installé. Relance le terminal et réexécute l'installation." -ForegroundColor Yellow
            exit 0
        }
        Write-Host "  Python installé." -ForegroundColor Green
    }
    python -m pip install -r $reqPath --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Dépendances Python installées." -ForegroundColor Green
    } else {
        Write-Host "  Erreur : échec de l'installation des dépendances Python." -ForegroundColor Red
        exit 1
    }
}

$installedScript = Join-Path $installDir "ut.ps1"
$batContent = "@echo off`r`npowershell.exe -ExecutionPolicy Bypass -File `"$installedScript`" %*"
Set-Content -Path (Join-Path $installDir "ut.bat") -Value $batContent -Encoding ASCII
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$installDir", "User")
}
$env:PATH = "$env:PATH;$installDir"

Remove-Item $zipPath    -Force -ErrorAction SilentlyContinue
Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  Installation terminée !" -ForegroundColor Green
Write-Host "  Tape 'ut help' depuis n'importe où." -ForegroundColor Cyan
Write-Host "  (Redémarre le terminal si 'ut' n'est pas reconnu)" -ForegroundColor DarkGray
Write-Host ""
