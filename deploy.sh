#!/bin/bash

if [ "$EUID" -ne 0 ]; then exit 1; fi

apt-get update
apt-get install -y python3 python3-venv python3-pip mariadb-server nginx gcc libmariadb-dev

if ! id "student" &>/dev/null; then
    useradd -m -s /bin/bash -G sudo -p $(openssl passwd -1 studentpass) student
fi

if ! id "teacher" &>/dev/null; then
    useradd -m -s /bin/bash -G sudo -p $(openssl passwd -1 12345678) teacher
    chage -d 0 teacher 
fi

if ! id "app" &>/dev/null; then
    useradd -r -s /bin/false app
fi

if ! id "operator" &>/dev/null; then
    useradd -m -s /bin/bash -p $(openssl passwd -1 12345678) operator
    chage -d 0 operator 
fi

cat <<EOF > /etc/sudoers.d/operator
operator ALL=(root) NOPASSWD: /usr/bin/systemctl start mywebapp, /usr/bin/systemctl stop mywebapp, /usr/bin/systemctl restart mywebapp, /usr/bin/systemctl status mywebapp, /usr/bin/systemctl reload nginx
EOF
chmod 0440 /etc/sudoers.d/operator

systemctl start mariadb
systemctl enable mariadb

mysql -u root -e "CREATE DATABASE IF NOT EXISTS task_tracker;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'taskuser'@'localhost' IDENTIFIED BY 'taskpass';"
mysql -u root -e "GRANT ALL PRIVILEGES ON task_tracker.* TO 'taskuser'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"

APP_DIR="/opt/mywebapp"
mkdir -p $APP_DIR

cp app.py migrate.py $APP_DIR/

python3 -m venv $APP_DIR/venv
$APP_DIR/venv/bin/pip install flask mariadb werkzeug

chown -R app:app $APP_DIR

cat <<EOF > /etc/systemd/system/mywebapp.socket
[Unit]
Description=Task Tracker Socket
[Socket]
ListenStream=127.0.0.1:5000
[Install]
WantedBy=sockets.target
EOF

cat <<EOF > /etc/systemd/system/mywebapp.service
[Unit]
Description=Task Tracker Web Application
After=network.target mariadb.service
Requires=mariadb.service mywebapp.socket
[Service]
Type=simple
User=app
Group=app
WorkingDirectory=/opt/mywebapp
ExecStartPre=/opt/mywebapp/venv/bin/python /opt/mywebapp/migrate.py --db-host 127.0.0.1 --db-user taskuser --db-password taskpass --db-name task_tracker
ExecStart=/opt/mywebapp/venv/bin/python /opt/mywebapp/app.py --db-host 127.0.0.1 --db-user taskuser --db-password taskpass --db-name task_tracker --port 5000
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mywebapp.socket
systemctl start mywebapp.socket
systemctl enable mywebapp.service

cat <<EOF > /etc/nginx/sites-available/mywebapp
server {
    listen 80;
    server_name _;
    access_log /var/log/nginx/mywebapp_access.log;
    error_log /var/log/nginx/mywebapp_error.log;
    location = / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
    }
    location /tasks {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
    }
    location / { return 403; }
}
EOF

ln -sf /etc/nginx/sites-available/mywebapp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

echo "4" > /home/student/gradebook
chown student:student /home/student/gradebook

if [ -n "\$SUDO_USER" ]; then
    usermod -L "\$SUDO_USER"
fi