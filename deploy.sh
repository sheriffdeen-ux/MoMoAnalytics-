#!/bin/bash

echo "🚀 Starting MoMo Analytics on Railway..."

# Check if all dependencies are installed
pip install -r requirements.txt

# Check if the app can be imported
python3 -c "from whatsapp_fraud_webhook import app; print('✅ App imported successfully')"

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --worker-class gevent --timeout 120 --log-level info whatsapp_fraud_webhook:app
