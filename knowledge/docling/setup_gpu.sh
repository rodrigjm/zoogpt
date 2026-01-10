#!/bin/bash
# ============================================================
# GPU Detection and Docker Configuration Script
# ============================================================
# Detects available GPU and configures Docker appropriately:
# - Linux + NVIDIA: Enables GPU passthrough
# - macOS (Apple Silicon): Uses cloud TTS (GPU not available in Docker)
# - No GPU: Uses cloud TTS
# ============================================================

set -e

echo "========================================"
echo "Zoocari GPU Detection & Configuration"
echo "========================================"
echo ""

# Detect OS
OS=$(uname -s)
ARCH=$(uname -m)

echo "Detected: $OS ($ARCH)"
echo ""

# ============================================================
# macOS Detection
# ============================================================
if [[ "$OS" == "Darwin" ]]; then
    echo "Platform: macOS"

    # Check for Apple Silicon
    if [[ "$ARCH" == "arm64" ]]; then
        # Get chip name
        CHIP=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")
        echo "Chip: $CHIP"
        echo ""
        echo "WARNING: Docker on macOS CANNOT access Apple Silicon GPU."
        echo "MPS acceleration is only available when running natively."
        echo ""
        echo "Options:"
        echo "  1. [Docker] Use cloud TTS (OpenAI) - ~300-800ms (RECOMMENDED)"
        echo "  2. [Native] Run without Docker to use MPS GPU"
        echo ""

        # Check if running natively is possible
        if python3 -c "import torch; exit(0 if torch.backends.mps.is_available() else 1)" 2>/dev/null; then
            echo "MPS Status: Available for native execution"
            echo ""
            echo "To run natively with GPU:"
            echo "  pip install -r requirements.txt"
            echo "  TTS_PROVIDER=kokoro streamlit run zoo_chat.py"
        fi

        echo ""
        echo "Configuration: Setting TTS_PROVIDER=openai for Docker"

        # Update .env file
        if [[ -f .env ]]; then
            # Remove existing TTS_PROVIDER line and add new one
            grep -v "^TTS_PROVIDER=" .env > .env.tmp || true
            echo "TTS_PROVIDER=openai" >> .env.tmp
            mv .env.tmp .env
        else
            echo "TTS_PROVIDER=openai" >> .env
        fi

        echo "Done. Run: docker-compose up --build"
        exit 0
    else
        echo "Intel Mac detected. No GPU acceleration available for Docker."
        echo "Using cloud TTS."
        exit 0
    fi
fi

# ============================================================
# Linux Detection
# ============================================================
if [[ "$OS" == "Linux" ]]; then
    echo "Platform: Linux"
    echo ""

    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        echo "NVIDIA GPU detected:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
        echo ""

        # Check for NVIDIA Container Toolkit
        if command -v nvidia-container-cli &> /dev/null || docker info 2>/dev/null | grep -q "nvidia"; then
            echo "NVIDIA Container Toolkit: Installed"
            echo ""
            echo "Enabling GPU support in docker-compose.yml..."

            # Check if GPU config already exists
            if grep -q "driver: nvidia" docker-compose.yml 2>/dev/null; then
                echo "GPU configuration already present in docker-compose.yml"
            else
                echo ""
                echo "Add this to your docker-compose.yml under 'zoocari' service:"
                echo ""
                cat << 'EOF'
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
EOF
                echo ""
                echo "Then set in .env:"
                echo "  TTS_PROVIDER=kokoro"
                echo ""
            fi

            # Update .env for GPU usage
            if [[ -f .env ]]; then
                grep -v "^TTS_PROVIDER=" .env > .env.tmp || true
                echo "TTS_PROVIDER=kokoro" >> .env.tmp
                mv .env.tmp .env
            else
                echo "TTS_PROVIDER=kokoro" >> .env
            fi

            echo "Configuration: Setting TTS_PROVIDER=kokoro for GPU"
            echo "Done. Run: docker-compose up --build"
            exit 0
        else
            echo "NVIDIA Container Toolkit: NOT INSTALLED"
            echo ""
            echo "To enable GPU in Docker, install NVIDIA Container Toolkit:"
            echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
            echo ""
            echo "Quick install (Ubuntu/Debian):"
            echo "  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg"
            echo "  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list"
            echo "  sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit"
            echo "  sudo nvidia-ctk runtime configure --runtime=docker"
            echo "  sudo systemctl restart docker"
            echo ""
            echo "For now, using cloud TTS."
        fi
    else
        echo "No NVIDIA GPU detected."
        echo "Using cloud TTS (OpenAI)."
    fi

    # Default to cloud TTS
    if [[ -f .env ]]; then
        grep -v "^TTS_PROVIDER=" .env > .env.tmp || true
        echo "TTS_PROVIDER=openai" >> .env.tmp
        mv .env.tmp .env
    else
        echo "TTS_PROVIDER=openai" >> .env
    fi

    exit 0
fi

# ============================================================
# Unknown OS
# ============================================================
echo "Unknown platform: $OS"
echo "Using cloud TTS as default."

if [[ -f .env ]]; then
    grep -v "^TTS_PROVIDER=" .env > .env.tmp || true
    echo "TTS_PROVIDER=openai" >> .env.tmp
    mv .env.tmp .env
else
    echo "TTS_PROVIDER=openai" >> .env
fi

exit 0
