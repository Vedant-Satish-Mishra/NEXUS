# NEXUS Environment Generator (Step 5.D.2)
# Generates a fresh .env file with cryptographically random secrets

Write-Host "Generating cryptographically secure secrets for NEXUS..." -ForegroundColor Cyan

function New-Secret([int]$length = 32) {
    $bytes = New-Object byte[] $length
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes) -replace '[/+=]', ''
}

$jwtSecret = New-Secret 32
$dbPass = New-Secret 24
$sandboxKey = New-Secret 24

$envContent = @"
# NEXUS Environment Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Security Secrets (Generated)
JWT_SECRET=$jwtSecret
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Connection
DATABASE_URL=sqlite+aiosqlite:///./data/nexus.db
POSTGRES_USER=nexus
POSTGRES_PASSWORD=$dbPass
POSTGRES_DB=nexus

# Local Ollama & LLM Providers
OLLAMA_BASE_URL=http://localhost:11434
QWEN3_4B_URL=http://localhost:8080
QWEN3_8B_URL=http://localhost:8081
DEFAULT_MODEL=qwen3:4b
DEFAULT_PROFILE=fast

# Sandbox Execution Service
SANDBOX_URL=http://localhost:8001
SANDBOX_KEY=$sandboxKey

# Local Vector Storage & Uploads
CHROMA_PATH=./data/chroma
UPLOAD_DIR=./data/uploads
"@

$envPath = Join-Path $PSScriptRoot "..\.env"
Set-Content -Path $envPath -Value $envContent -Encoding UTF8
Write-Host "Successfully written .env file at $envPath" -ForegroundColor Green
