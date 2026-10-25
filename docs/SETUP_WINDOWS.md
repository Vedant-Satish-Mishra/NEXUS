# NEXUS Windows Setup Runbook

Target hardware: **Intel Core i7-13650H · NVIDIA RTX 4060 (8 GB VRAM) · 16 GB RAM · 512 GB SSD · Windows 11**.

---

## 1. Tool Versions & Prerequisites

Verify installed versions in PowerShell:
```powershell
python --version   # Required: Python 3.11+ (verified: 3.14 / 3.11)
node -v            # Required: Node.js 20 LTS (verified: v24.20.0)
npm -v             # Required: npm 10+ (verified: 11.19.0)
docker --version   # Docker Desktop with WSL 2 backend
nvidia-smi         # NVIDIA driver 535+ (CUDA 12.x support)
ollama --version   # Ollama for Windows (v0.3+)
```

---

## 2. Docker & WSL 2 Memory Limits

To protect system stability and avoid out-of-memory lockups on a 16 GB laptop, cap WSL 2 resources.

Create or edit `%UserProfile%\.wslconfig`:
```ini
[wsl2]
memory=5GB
processors=6
swap=4GB
localhostForwarding=true
```

Apply changes:
```powershell
wsl --shutdown
# Then restart Docker Desktop
```

---

## 3. Ollama Optimization for RTX 4060 (8 GB VRAM)

Configure Ollama for optimal VRAM utilization, Flash Attention, and quantized KV caching:

```powershell
# Set environment variables for Ollama host process
setx OLLAMA_FLASH_ATTENTION 1
setx OLLAMA_KV_CACHE_TYPE q8_0
setx OLLAMA_MAX_LOADED_MODELS 1
setx OLLAMA_NUM_PARALLEL 1
setx OLLAMA_KEEP_ALIVE 10m
```

Restart the Ollama Windows application from the system tray or run:
```powershell
Stop-Process -Name "ollama" -ErrorAction SilentlyContinue
Start-Process ollama app
```

Pull the required Qwen3 profiles:
```powershell
# Default Fast Profile (Weight footprint: ~2.5 GB)
ollama pull qwen3:4b

# Optional Quality Profile (Weight footprint: ~5.2 GB)
ollama pull qwen3:8b
```

Verify GPU loading:
```powershell
ollama run qwen3:4b "hi"
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv
ollama ps
```
The output should report `100% GPU` under processor allocation.

---

## 4. Container-to-Host Network Access (`host.docker.internal`)

Backend containers running in Docker need to reach the Ollama host process at `http://host.docker.internal:11434`.

Test container connectivity:
```powershell
docker run --rm curlimages/curl curl -s http://host.docker.internal:11434/api/tags
```

### Safe Resolution if Connection is Refused:
1. Bind Ollama to all network interfaces on the host:
   ```powershell
   setx OLLAMA_HOST "0.0.0.0:11434"
   ```
2. Restart Ollama.
3. Block external inbound connections to port 11434 from the local network (LAN) in Windows Firewall:
   ```powershell
   New-NetFirewallRule -DisplayName "Block Ollama Remote LAN" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Block -RemoteAddress LocalSubnet
   ```
   This ensures only localhost and Docker WSL 2 can access port 11434.

---

## 5. Troubleshooting Matrix

| Symptom | Probable Cause | Verified Resolution |
|---|---|---|
| **Answers extremely slow (< 5 tok/s)** | Model spilled from VRAM into system RAM | Check `ollama ps`. Lower `num_ctx` to 4096, ensure `q8_0` KV cache is active, and switch to `qwen3:4b`. |
| **Backend container cannot reach Ollama** | Docker bridge cannot resolve `host.docker.internal` | Ensure `host.docker.internal:host-gateway` is present in `docker-compose.yml` extra_hosts. |
| **Laptop freezes during Docker runs** | WSL 2 unconstrained memory usage | Ensure `%UserProfile%\.wslconfig` sets `memory=5GB`. Run `wsl --shutdown`. |
| **Port 5432 or 8000 already in use** | Local PostgreSQL or dev server running | Change mapped host port in `.env` (e.g. `POSTGRES_PORT=5433`). |
| **Slow file I/O or bind mounts** | Docker mounting Windows NTFS paths | Store development repositories inside the WSL 2 root filesystem (`\\wsl$\...`) or use Docker named volumes. |
| **JSON decoding error from small LLM** | Small model drifted from schema | Verify schema constraint in Ollama payload; ensure `think: false` for structured calls. |
