Write-Host "[*] Stopping Meridian processes on ports 8000 and 5173..." -ForegroundColor Yellow

$ports = @(8000, 5173)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $pidToKill = $conn.OwningProcess
            try {
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                Write-Host "  [OK] Stopped process PID $pidToKill on port $port" -ForegroundColor Green
            } catch {
                # Ignore process termination errors
            }
        }
    }
}

Write-Host "[OK] All Meridian services stopped." -ForegroundColor Green
