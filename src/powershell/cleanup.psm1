function Get-TempSize {
    $tempPaths = @($env:TEMP, "C:\Windows\Temp") | Where-Object { Test-Path $_ }
    $totalBytes = 0
    foreach ($path in $tempPaths) {
        $totalBytes += (Get-ChildItem -Path $path -Recurse -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
    }
    return [math]::Round($totalBytes / 1MB, 2)
}

function Invoke-CleanTemp {
    [CmdletBinding(SupportsShouldProcess)]
    param()

    $tempPaths = @($env:TEMP, "C:\Windows\Temp") | Where-Object { Test-Path $_ }
    $totalDeleted = 0

    foreach ($path in $tempPaths) {
        $files = Get-ChildItem -Path $path -Recurse -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            if ($PSCmdlet.ShouldProcess($file.FullName, "Supprimer")) {
                try {
                    Remove-Item -Path $file.FullName -Force -Recurse -ErrorAction Stop
                    $totalDeleted++
                } catch {
                    Write-Host "Erreur lors de la suppression de $($file.FullName) : $_" -ForegroundColor Red
                }
            }
        }
    }

    if (-not $WhatIfPreference) {
        Write-Host "$totalDeleted fichier(s) supprimé(s)." -ForegroundColor Green
    }
}

function Show-CleanTemp {
    $sizeMB = Get-TempSize
    Write-Host "`nFichiers temporaires : $sizeMB MB" -ForegroundColor Yellow
    $confirm = Read-Host "Voulez-vous nettoyer les fichiers temporaires ? (o/n)"
    if ($confirm -eq 'o') {
        Invoke-CleanTemp
    } else {
        Write-Host "Nettoyage annulé." -ForegroundColor Gray
    }
}

Export-ModuleMember -Function Get-TempSize, Invoke-CleanTemp, Show-CleanTemp
