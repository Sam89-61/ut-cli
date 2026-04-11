function Get-SystemInfo {
    $cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name

    $os = Get-CimInstance Win32_OperatingSystem
    $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $freeGB  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)

    $disques = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null } | ForEach-Object {
        [PSCustomObject]@{
            Nom     = $_.Name
            TotalGB = [math]::Round(($_.Used + $_.Free) / 1GB, 2)
            LibreGB = [math]::Round($_.Free / 1GB, 2)
        }
    }

    $ips = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.IPAddress -notlike "169.254.*" } |
        Select-Object IPAddress, InterfaceAlias

    return [PSCustomObject]@{
        CPU     = $cpu
        RAM     = [PSCustomObject]@{ TotalGB = $totalGB; FreeGB = $freeGB }
        Disques = $disques
        IPs     = $ips
    }
}

function Show-SystemInfo {
    $info = Get-SystemInfo
    Write-Host "`n=== Informations Système ===" -ForegroundColor Cyan
    Write-Host "CPU    : $($info.CPU)" -ForegroundColor White
    Write-Host "RAM    : $($info.RAM.FreeGB) GB libres / $($info.RAM.TotalGB) GB total" -ForegroundColor White
    Write-Host "`nDisques :" -ForegroundColor Cyan
    foreach ($d in $info.Disques) {
        Write-Host "  [$($d.Nom)] $($d.LibreGB) GB libres / $($d.TotalGB) GB total" -ForegroundColor White
    }
    Write-Host "`nAdresses IP :" -ForegroundColor Cyan
    foreach ($ip in $info.IPs) {
        Write-Host "  $($ip.IPAddress)  ($($ip.InterfaceAlias))" -ForegroundColor White
    }
    Write-Host "==========================`n" -ForegroundColor Cyan
}

Export-ModuleMember -Function Get-SystemInfo, Show-SystemInfo
