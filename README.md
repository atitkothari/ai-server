# AI-Server

This repository houses the code for the ai-server.

TODO(manish): Add precommit and other details.


Stored at: `/etc/systemd/system/ai-server.service`
Commands:
1. `sudo systemctl [start|stop|status] ai-server.servce`
```
[Unit]
Description=AI Server Service
After=network.target

[Service]
User=immer-dev
WorkingDirectory=/home/immer-dev/ai-server
ExecStart=/home/immer-dev/envs/ai-server/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

# Logging
StandardOutput=file:/home/immer-dev/ai-server/output.log
StandardError=file:/home/immer-dev/ai-server/error.log

[Install]
WantedBy=multi-user.target
```