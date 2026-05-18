#!/bin/bash
set -e

APP_DIR="/home/sasha/lab1_task_tracker"

cat <<EOF | sudo tee /etc/systemd/system/task-tracker.service
[Unit]
Description=Task Tracker Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose up -d --build
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable task-tracker.service
sudo systemctl restart task-tracker.service

cat <<EOF | sudo tee /etc/nginx/sites-available/task-tracker
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/task-tracker /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx