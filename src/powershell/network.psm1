function Show-NetworkDiag {
    Write-Host ""
    Write-Host "=== Diagnostic Reseau ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "-- IP locale --" -ForegroundColor Yellow
    Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
        Select-Object IPAddress, InterfaceAlias |
        Format-Table -AutoSize
    Write-Host "-- IP publique --" -ForegroundColor Yellow
    try {
        $publicIP = (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 5)
        Write-Host "  $publicIP" -ForegroundColor White
    } catch {
        Write-Host "  Impossible de recuperer l'IP publique." -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "-- Test connectivite (8.8.8.8) --" -ForegroundColor Yellow
    $ping = Test-Connection 8.8.8.8 -Count 2 -ErrorAction SilentlyContinue
    if ($ping) {
        $avg = [math]::Round(($ping | Measure-Object -Property ResponseTime -Average).Average, 1)
        Write-Host "  OK - Latence moyenne : ${avg}ms" -ForegroundColor Green
    } else {
        Write-Host "  Echec - Pas de reponse." -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "-- Flush DNS --" -ForegroundColor Yellow
    Clear-DnsClientCache
    Write-Host "  Cache DNS vide." -ForegroundColor Green
    Write-Host "" 
    Write-Host "-- Ports en ecoute (top 15) --" -ForegroundColor Yellow # Afficher les ports en écoute et les processus associés
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Sort-Object LocalPort |
        Select-Object LocalPort, LocalAddress, OwningProcess, @{Name="ProcessName";Expression={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} |
        Format-Table -AutoSize

    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host ""
}

function Invoke-ScanPort {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Hote,

        [Parameter(Mandatory=$false)]
        [int]$PortDebut = 1,

        [Parameter(Mandatory=$false)]
        [int]$PortFin = 1024,

        [Parameter(Mandatory=$false)]
        [int]$TimeoutMs = 200
    )

    $services = @{
        21='FTP'; 22='SSH'; 23='Telnet'; 25='SMTP'; 53='DNS'; 80='HTTP';
        110='POP3'; 135='RPC'; 139='NetBIOS'; 143='IMAP'; 443='HTTPS';
        445='SMB'; 3306='MySQL'; 3389='RDP'; 5432='PostgreSQL'; 5900='VNC';
        6379='Redis'; 8080='HTTP-Alt'; 8443='HTTPS-Alt'; 27017='MongoDB'
    }

    $total = $PortFin - $PortDebut + 1
    Write-Host ""
    Write-Host "=== Scan de ports : $Hote ($PortDebut - $PortFin) ===" -ForegroundColor Cyan
    Write-Host "  Timeout par port : ${TimeoutMs}ms" -ForegroundColor DarkGray
    Write-Host ""

    $ouverts = [System.Collections.Generic.List[PSCustomObject]]::new()
    $compteur = 0

    for ($port = $PortDebut; $port -le $PortFin; $port++) {
        $compteur++
        $pct = [math]::Round(($compteur / $total) * 100)
        Write-Progress -Activity "Scan en cours..." -Status "Port $port / $PortFin" -PercentComplete $pct

        $tcp = New-Object System.Net.Sockets.TcpClient
        try {
            $result = $tcp.BeginConnect($Hote, $port, $null, $null)
            $ok = $result.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
            if ($ok -and $tcp.Connected) {
                $service = if ($services.ContainsKey($port)) { $services[$port] } else { "-" }
                $ouverts.Add([PSCustomObject]@{ Port = $port; Service = $service })
                Write-Host ("  [OUVERT] Port {0,-6} {1}" -f $port, $service) -ForegroundColor Green
            }
        } catch {

        } finally {
            $tcp.Close()
        }
    }

    Write-Progress -Completed -Activity "Scan termine"

    Write-Host ""
    if ($ouverts.Count -eq 0) {
        Write-Host "  Aucun port ouvert detecte dans cette plage." -ForegroundColor Yellow
    } else {
        Write-Host "  $($ouverts.Count) port(s) ouvert(s) sur $total scanne(s)." -ForegroundColor Cyan
    }
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
}

Export-ModuleMember -Function Show-NetworkDiag, Invoke-ScanPort
