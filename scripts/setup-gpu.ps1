$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv-gpu/Scripts/python.exe')) { & .venv/Scripts/python.exe -m venv .venv-gpu }
if ($LASTEXITCODE -ne 0) { throw 'GPU environment creation failed' }
& .venv-gpu/Scripts/python.exe -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cu128
if ($LASTEXITCODE -ne 0) { throw 'CUDA PyTorch installation failed' }
& .venv-gpu/Scripts/python.exe -m pip install -r requirements-gpu.txt
if ($LASTEXITCODE -ne 0) { throw 'GPU research dependency installation failed' }
& .venv-gpu/Scripts/python.exe -m pdm.gpu_probe
if ($LASTEXITCODE -ne 0) { throw 'GPU verification failed' }
& .venv-gpu/Scripts/python.exe -m pip freeze | Set-Content artifacts/gpu-environment.lock.txt
