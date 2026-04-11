<#
.SYNOPSIS
    Useful Tool (ut) - Une app simple utilisant PowerShell et Python à utilisé dans le CLI.

.DESCRIPTION
    Ce script sert de point d'entrée principal pour le CLI 'ut'.
    Utilisez 'ut <action>' pour exécuter une commande.

.PARAMETER Action
    L'action que vous souhaitez effectuer (ex: 'info', 'clean', 'ps', 'tri', 'install').

.PARAMETER Params
    Arguments supplémentaires passés à l'action.

.EXAMPLE
    ut info
    ut clean
    ut ps list
    ut ps kill notepad
    ut tri C:\Downloads maison
    ut tri C:\Downloads --type pdf
#>

param (
    [Parameter(Mandatory=$true, Position=0, HelpMessage="Veuillez spécifier une action.")]
    [string]$Action,

    [Parameter(Mandatory=$false, Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Params = @()
)

function Show-Help {
    $sep = "=" * 50
    $sub = "-" * 50

    Write-Host ""
    Write-Host "  Useful Tool (ut)" -ForegroundColor Cyan
    Write-Host "  $sep" -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "  SYSTEME" -ForegroundColor Yellow
    Write-Host ("    {0,-30} {1}" -f "ut info", "Affiche CPU, RAM, disques, IP") -ForegroundColor White
    Write-Host ("    {0,-30} {1}" -f "ut clean", "Nettoie les fichiers temporaires") -ForegroundColor White
    Write-Host ("    {0,-30} {1}" -f "ut ps list", "Liste les processus actifs (top 20)") -ForegroundColor White
    Write-Host ("    {0,-30} {1}" -f "ut ps kill <nom>", "Arrete un processus par nom") -ForegroundColor White

    Write-Host ""
    Write-Host "  RESEAU" -ForegroundColor Yellow
    Write-Host ("    {0,-45} {1}" -f "ut network diag", "IP locale/publique, ping, flush DNS, ports") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut network scanport <hote> [debut] [fin]", "Scanne une plage de ports") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut network speed", "Test de debit Download / Upload") -ForegroundColor White

    Write-Host ""
    Write-Host "  TRI DE FICHIERS" -ForegroundColor Yellow
    Write-Host ("    {0,-30} {1}" -f "ut tri <chemin> <motcle>", "Groupe les fichiers contenant <motcle>") -ForegroundColor White
    Write-Host ("    {0,-30} {1}" -f "ut tri <chemin> --type <ext>", "Groupe les fichiers par extension") -ForegroundColor White
    Write-Host ""
    Write-Host "  GESTION DE FICHIERS" -ForegroundColor Yellow
    Write-Host ("    {0,-45} {1}" -f "ut file doublons <chemin>", "Liste les fichiers en double (SHA-256)") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut file doublons <chemin> --delete", "Suppression interactive des doublons") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut file heavy <chemin> --min <taille>", "Liste les gros fichiers (ex: --min 500MB)") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut file rename <chemin> <regex> <rempl>", "Renommage en masse par expression reguliere") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "  --dry-run", "Apercu sans appliquer") -ForegroundColor DarkGray
    Write-Host ("    {0,-45} {1}" -f "ut file zip <chemin> --age <duree>", "Archive les fichiers anciens (ex: --age 30d)") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut file tree <chemin> [--depth N]", "Arborescence visuelle avec tailles") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut file encrypt <fichier>", "Chiffre un fichier (Fernet/AES + PBKDF2)") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut file decrypt <fichier.enc>", "Dechiffre un fichier .enc") -ForegroundColor White
    Write-Host ""
    Write-Host "  $sub" -ForegroundColor DarkGray
    Write-Host "    Exemples :" -ForegroundColor DarkGray
    Write-Host "      ut tri C:\Downloads maison" -ForegroundColor DarkGray
    Write-Host "      ut tri C:\Downloads --type pdf" -ForegroundColor DarkGray
    Write-Host "      ut file doublons C:\Downloads --delete" -ForegroundColor DarkGray
    Write-Host "      ut file heavy C:\Users --min 1GB" -ForegroundColor DarkGray
    Write-Host "      ut file rename C:\Photos '(\d{4})' 'photo_\1' --dry-run" -ForegroundColor DarkGray
    Write-Host "      ut file zip C:\Archives --age 30d" -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "  RECHERCHE DE TEXTE" -ForegroundColor Yellow
    Write-Host ("    {0,-45} {1}" -f "ut text search <mot_cle> <dossier>", "Cherche un texte dans tous les fichiers") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "  --ext py,ps1", "Filtrer par extension(s)") -ForegroundColor DarkGray
    Write-Host ("    {0,-45} {1}" -f "  -i / --ignore-case", "Ignorer la casse") -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "  DONNEES" -ForegroundColor Yellow
    Write-Host ("    {0,-45} {1}" -f "ut data convert <fichier> <format>", "Convertir CSV <-> JSON") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "  --output <fichier>", "Chemin du fichier de sortie") -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "  OUTILS DEVELOPPEUR" -ForegroundColor Yellow
    Write-Host ("    {0,-45} {1}" -f "ut dev pwd", "Genere un mot de passe securise (16 car.)") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "  --length <n>", "Longueur (defaut : 16)") -ForegroundColor DarkGray
    Write-Host ("    {0,-45} {1}" -f "  --no-special", "Sans caracteres speciaux") -ForegroundColor DarkGray
    Write-Host ("    {0,-45} {1}" -f "  --copy", "Copier dans le presse-papiers") -ForegroundColor DarkGray
    Write-Host ("    {0,-45} {1}" -f "ut dev hash <fichier>", "Calcule MD5 / SHA-1 / SHA-256 d'un fichier") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "  --compare <hash>", "Verifier l'integrite contre un hash connu") -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "  AUTRES" -ForegroundColor Yellow
    Write-Host ("    {0,-45} {1}" -f "ut style", "Affiche le logo et la carte des commandes") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut style --compact", "Logo seul (version courte)") -ForegroundColor DarkGray
    Write-Host ("    {0,-45} {1}" -f "ut bonjour <nom>", "Message de bienvenue") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut install", "Installe l alias ut dans le profil") -ForegroundColor White
    Write-Host ("    {0,-45} {1}" -f "ut help", "Affiche cette aide") -ForegroundColor White

    Write-Host ""
    Write-Host "  $sep" -ForegroundColor DarkGray
    Write-Host ""
}

function Install-CLI {
    $sourceDir  = $PSScriptRoot
    $installDir = "$env:LOCALAPPDATA\Programs\ut-cli"

    Write-Host "Installation de 'ut' dans $installDir..." -ForegroundColor Cyan

    if (-not (Test-Path $installDir)) {
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    }
    Copy-Item -Path "$sourceDir\*" -Destination $installDir -Recurse -Force
    Write-Host "Fichiers copiés dans $installDir" -ForegroundColor Green

    #Dépendances Python
    $requirementsPath = Join-Path $installDir "requirements.txt"
    if (Test-Path $requirementsPath) {
        Write-Host "Installation des dépendances Python..." -ForegroundColor Cyan
        python -m pip install -r $requirementsPath --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Dépendances Python installées." -ForegroundColor Green
        } else {
            Write-Warning "Erreur : Python n'est pas installé ou inaccessible."
        }
    }

    # ut.bat
    $installedScript = Join-Path $installDir "ut.ps1"
    $batPath = Join-Path $installDir "ut.bat"
    $batContent = "@echo off`r`npowershell.exe -ExecutionPolicy Bypass -File `"$installedScript`" %*"
    Set-Content -Path $batPath -Value $batContent -Encoding ASCII

    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$installDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$installDir", "User")
        Write-Host "Ajouté au PATH : $installDir" -ForegroundColor Green
    } else {
        Write-Host "Déjà dans le PATH." -ForegroundColor Gray
    }

    $env:PATH = "$env:PATH;$installDir"

    Write-Host ""
    Write-Host "Installation terminée !" -ForegroundColor Green
    Write-Host "Tape 'ut help' depuis n'importe où." -ForegroundColor Cyan
    Write-Host "(Redémarre le terminal pour les nouvelles fenêtres)" -ForegroundColor DarkGray
}

switch ($Action.ToLower()) {
    "bonjour" {
        $name = if ($Params.Count -gt 0) { $Params[0] } else { "Invite" }
        Write-Host "Bonjour, $name ! Bienvenue dans 'Useful Tool' (ut)." -ForegroundColor Green
    }
    "install" {
        Install-CLI
    }
    "python-test" {
        Write-Host "Exécution d'un script Python..." -ForegroundColor Cyan
        $pythonScript = Join-Path $PSScriptRoot "src\python\hello.py"
        $name = if ($Params.Count -gt 0) { $Params[0] } else { "Invite" }
        if (Test-Path $pythonScript) {
            python $pythonScript $name
        } else {
            Write-Error "Script Python non trouvé : $pythonScript"
        }
    }
    "info" {
        Import-Module (Join-Path $PSScriptRoot "src\powershell\system.psm1") -Force
        Show-SystemInfo
    }
    "clean" {
        Import-Module (Join-Path $PSScriptRoot "src\powershell\cleanup.psm1") -Force
        Show-CleanTemp
    }
    "ps" {
        Import-Module (Join-Path $PSScriptRoot "src\powershell\process.psm1") -Force
        $sousAction = if ($Params.Count -gt 0) { $Params[0] } else { "list" }
        switch ($sousAction.ToLower()) {
            "list" {
                Show-ProcessList
            }
            "kill" {
                if ($Params.Count -lt 2) {
                    Write-Warning "Usage : ut ps kill <nom_processus>"
                } else {
                    Stop-ProcessByName -Name $Params[1]
                }
            }
            default {
                Write-Warning "Sous-action inconnue : $sousAction. Options : list, kill"
            }
        }
    }
    "network" {
        $sousAction = if ($Params.Count -gt 0) { $Params[0] } else { "diag" }
        if ($sousAction.ToLower() -eq "speed") {
            $networkScript = Join-Path $PSScriptRoot "src\python\network.py"
            python $networkScript speed
        } else {
            Import-Module (Join-Path $PSScriptRoot "src\powershell\network.psm1") -Force
            switch ($sousAction.ToLower()) {
                "diag" {
                    Show-NetworkDiag
                }
                "scanport" {
                    if ($Params.Count -lt 2) {
                        Write-Warning "Usage : ut network scanport <hote> [portDebut] [portFin]"
                        Write-Warning "Ex    : ut network scanport 192.168.1.1 1 1024"
                        Write-Warning "Ex    : ut network scanport localhost 80 443"
                    } else {
                        $hote      = $Params[1]
                        $portDebut = if ($Params.Count -gt 2) { [int]$Params[2] } else { 1 }
                        $portFin   = if ($Params.Count -gt 3) { [int]$Params[3] } else { 1024 }
                        Invoke-ScanPort -Hote $hote -PortDebut $portDebut -PortFin $portFin
                    }
                }
                default {
                    Write-Warning "Sous-action inconnue : $sousAction. Options : diag, scanport, speed"
                }
            }
        }
    }
    "pomodoro" {
        Import-Module (Join-Path $PSScriptRoot "src\powershell\pomodoro.psm1") -Force
        if ($Params.Count -eq 0) {
            Invoke-PomodoroSetup
        } else {
            switch ($Params[0].ToLower()) {
                "start" {
                    $duree   = 25
                    $sites   = @()
                    $musique = ""
                    $i = 1
                    while ($i -lt $Params.Count) {
                        switch ($Params[$i]) {
                            "--duree"   { $duree   = [int]$Params[$i+1]; $i += 2 }
                            "--sites"   { $sites   = ($Params[$i+1]) -split ','; $i += 2 }
                            "--musique" { $musique = $Params[$i+1].Trim('"').Trim("'"); $i += 2 }
                            default     { $i++ }
                        }
                    }
                    Start-Pomodoro -Duree $duree -Sites $sites -Musique $musique
                }
                "stop" {
                    Remove-PomodoroBlock
                }
                default {
                    Write-Warning "Sous-action inconnue : $($Params[0]). Options : start, stop"
                }
            }
        }
    }
    "text" {
        if ($Params.Count -lt 2) {
            Write-Warning "Usage : ut text search <mot_cle> <dossier> [--ext py,ps1] [-i]"
        } else {
            $textScript = Join-Path $PSScriptRoot "src\python\text.py"
            python $textScript @Params
        }
    }
    "data" {
        if ($Params.Count -lt 2) {
            Write-Warning "Usage : ut data convert <fichier.csv> json"
            Write-Warning "   ou : ut data convert <fichier.json> csv [--output <sortie>]"
        } else {
            $dataScript = Join-Path $PSScriptRoot "src\python\data.py"
            python $dataScript @Params
        }
    }
    "dev" {
        if ($Params.Count -lt 1) {
            Write-Warning "Usage : ut dev <pwd|hash> [options]"
            Write-Warning "   ex : ut dev pwd --length 20 --copy"
            Write-Warning "   ex : ut dev hash C:\fichier.zip --compare <sha256>"
        } else {
            $devScript = Join-Path $PSScriptRoot "src\python\dev.py"
            python $devScript @Params
        }
    }
    "file" {
        if ($Params.Count -lt 1) {
            Write-Warning "Usage : ut file <doublons|heavy|rename|zip> <chemin> [options]"
            Write-Warning "   ex : ut file doublons C:\Downloads"
            Write-Warning "   ex : ut file heavy C:\Downloads --min 500MB"
            Write-Warning "   ex : ut file rename C:\Downloads '(\d+)' 'num_\1'"
            Write-Warning "   ex : ut file zip C:\Downloads --age 30d"
        } else {
            $fileScript = Join-Path $PSScriptRoot "src\python\file.py"
            python $fileScript @Params
        }
    }
    "tri" {
        if ($Params.Count -lt 1) {
            Write-Warning "Usage : ut tri <chemin> <motcle>"
            Write-Warning "   ou : ut tri <chemin> --type <extension>"
        } else {
            $triScript = Join-Path $PSScriptRoot "src\python\tri.py"
            python $triScript @Params
        }
    }
    "style" {
        $styleScript = Join-Path $PSScriptRoot "src\python\style.py"
        python $styleScript
    }
    "help" {
        $styleScript = Join-Path $PSScriptRoot "src\python\style.py"
        python $styleScript --banner
        Show-Help
    }
    default {
        Write-Warning "Action inconnue : $Action. Utilisez 'ut help' pour voir l'aide."
    }
}
