function Get-ProcessList {
    param(
        [int]$Top = 20
    )

    Get-Process -ErrorAction SilentlyContinue |
        Sort-Object CPU -Descending |
        Select-Object -First $Top |
        ForEach-Object {
            [PSCustomObject]@{
                Nom    = $_.Name
                PID    = $_.Id
                CPU    = [math]::Round($_.CPU, 2)
                RAM_MB = [math]::Round($_.WorkingSet64 / 1MB, 2)
            }
        }
}

function Show-ProcessList {
    param([int]$Top = 20)
    $procs = Get-ProcessList -Top $Top
    Write-Host "`n=== Top $Top Processus (par CPU) ===" -ForegroundColor Cyan
    $procs | Format-Table -AutoSize
}

function Stop-ProcessByName {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name
    )

    $procs = Get-Process -Name $Name -ErrorAction SilentlyContinue
    if (-not $procs) {
        Write-Warning "Aucun processus trouvé avec le nom : $Name"
        return
    }

    Write-Host "$($procs.Count) processus trouvé(s) : $Name" -ForegroundColor Yellow
    $confirm = Read-Host "Voulez-vous les arrêter ? (o/n)"
    if ($confirm -eq 'o') {
        $procs | Stop-Process -Force
        Write-Host "Processus arrêté(s)." -ForegroundColor Green
    } else {
        Write-Host "Annulé." -ForegroundColor Gray
    }
}

Export-ModuleMember -Function Get-ProcessList, Show-ProcessList, Stop-ProcessByName
