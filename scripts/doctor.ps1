# NEXUS System Diagnostics Doctor (Step 5.D.2)
# Checks Ollama, models, GPU visibility, required ports, and memory

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " NEXUS System Diagnostics & Health Check " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$allPass = $true

# 1. Check Ollama server
Write-Host "`n1. Checking Ollama server (http://localhost:11434)..." -NoNewline
try {
    $res = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host " [ONLINE]" -ForegroundColor Green
    $models = $res.models | ForEach-Object { $_.name }
    Write-Host "   Available models: $($models -join ', ')" -ForegroundColor Gray
    if ($models -contains "qwen3:4b" -or $models -contains "qwen3:8b" -or ($models | Where-Object { $_ -like "qwen*" })) {
        Write-Host "   Qwen3 model verified." -ForegroundColor Green
    } else {
        Write-Host "   WARNING: Qwen3 model not found. Run 'ollama pull qwen3:4b'" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [OFFLINE]" -ForegroundColor Red
    Write-Host "   Run 'ollama serve' in a terminal." -ForegroundColor Red
    $allPass = $false
}

# 2. Check NVIDIA GPU
Write-Host "`n2. Checking NVIDIA GPU & VRAM..." -NoNewline
try {
    $gpuOut = nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>$null
    if ($gpuOut) {
        Write-Host " [DETECTED]" -ForegroundColor Green
        Write-Host "   $gpuOut" -ForegroundColor Gray
    } else {
        Write-Host " [NOT DETECTED (CPU Fallback Active)]" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [NOT DETECTED (CPU Fallback Active)]" -ForegroundColor Yellow
}

# 3. Check Ports
Write-Host "`n3. Checking required ports availability..."
$portsToCheck = @(8000, 5173, 5432, 8001)
foreach ($p in $portsToCheck) {
    $conn = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "   Port $p : In use by PID $($conn[0].OwningProcess)" -ForegroundColor Yellow
    } else {
        Write-Host "   Port $p : Free" -ForegroundColor Green
    }
}

# 4. Check Data directories
Write-Host "`n4. Checking storage directories..."
$dirs = @("data\chroma", "data\uploads", "data\knowledge")
foreach ($d in $dirs) {
    if (Test-Path $d) {
        Write-Host "   $d : Exists" -ForegroundColor Green
    } else {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Host "   $d : Created" -ForegroundColor Yellow
    }
}

Write-Host "`n==========================================" -ForegroundColor Cyan
if ($allPass) {
    Write-Host " Diagnostics Complete: NEXUS is ready to run!" -ForegroundColor Green
} else {
    Write-Host " Diagnostics Complete: Review warnings above." -ForegroundColor Yellow
}
Write-Host "==========================================" -ForegroundColor Cyan
