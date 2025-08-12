#!/bin/bash
# Fix the golf-app.service to include WorkingDirectory

echo "Fixing golf-app.service with WorkingDirectory..."

# Check if WorkingDirectory is already set
if grep -q "WorkingDirectory=" /etc/systemd/system/golf-app.service; then
    echo "WorkingDirectory already set in golf-app.service"
else
    # Add WorkingDirectory after the [Service] section
    sudo sed -i '/\[Service\]/a WorkingDirectory=/root/golfllm/frontend/golf-directory' /etc/systemd/system/golf-app.service
    echo "Added WorkingDirectory to golf-app.service"
fi

# Reload systemd and restart the service
sudo systemctl daemon-reload
sudo systemctl restart golf-app
sudo systemctl status golf-app --no-pager

echo "golf-app.service has been fixed and restarted"