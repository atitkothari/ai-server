# Stable Diffusion WebUI Installation Guide

This guide provides instructions for setting up AUTOMATIC1111's Stable Diffusion WebUI on a Linux system with systemd service configuration.

## Prerequisites

- Git installed
- Ubuntu/Debian-based system
- Sufficient disk space
- Root/sudo access

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
```

### 2. Configure WebUI Settings

Modify the `webui-user.sh` file to enable external access and API functionality:

```bash
# Open the file in your preferred editor
nano webui-user.sh

# Add or modify the COMMANDLINE_ARGS line
export COMMANDLINE_ARGS="--no-half --api --listen --enable-insecure-extension-access"
```

### 3. Create Systemd Service

Create a new service file at `/etc/systemd/system/stable-diffusion-webui.service`:

```ini
[Unit]
Description=Stable Diffusion WebUI
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/stable-diffusion-webui
ExecStart=/bin/bash /home/ubuntu/stable-diffusion-webui/webui.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start the Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable stable-diffusion

# Start the service
sudo systemctl start stable-diffusion

# Check service status
sudo systemctl status stable-diffusion
```

## Configuration Details

### Command Line Arguments Explanation

- `--no-half`: Disables half-precision floating point calculations
- `--api`: Enables API functionality
- `--listen`: Allows external access to the WebUI
- `--enable-insecure-extension-access`: Enables installation of third-party extensions

### Service File Explanation

- `User=ubuntu`: Service runs under the ubuntu user
- `WorkingDirectory`: Sets the working directory to the installation folder
- `Restart=always`: Automatically restarts the service if it crashes
- `After=network.target`: Ensures network is available before starting

## Troubleshooting

If the service fails to start:

1. Check logs using: `sudo journalctl -u stable-diffusion`
2. Verify file permissions in the installation directory
3. Ensure all dependencies are installed
4. Check available system resources (RAM, GPU)

## Security Considerations

⚠️ **Warning**: The `--enable-insecure-extension-access` flag reduces security. Only use in trusted environments.
