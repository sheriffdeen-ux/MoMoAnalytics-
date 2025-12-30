#!/bin/bash

# MoMo Analytics - One-Command Railway Deployment
# This script automates the entire Railway deployment process

set -e  # Exit on any error

echo "🚀 MoMo Analytics - Railway Auto-Deploy"
echo "========================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed"
fi

# Check if user is logged in
echo "📝 Checking Railway login status..."
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
fi

echo "✅ Logged in to Railway"
echo ""

# Initialize project if not already done
if [ ! -f "railway.json" ]; then
    echo "🎯 Initializing Railway project..."
    railway init
    echo "✅ Project initialized"
else
    echo "✅ Railway project already initialized"
fi

echo ""
echo "📦 Setting up PostgreSQL database..."
railway add --service postgresql || echo "✅ PostgreSQL already added"

echo ""
echo "🔐 ENVIRONMENT VARIABLES SETUP"
echo "=============================="
echo ""
echo "Please provide the following information:"
echo ""

# Get Twilio credentials
read -p "Enter your Twilio Account SID (starts with AC): " TWILIO_SID
read -p "Enter your Twilio Auth Token: " TWILIO_TOKEN
read -p "Enter your Twilio WhatsApp Number (format: whatsapp:+233XXXXXXXXX): " TWILIO_WHATSAPP

# Generate secret keys
echo ""
echo "🔑 Generating secure keys..."
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
WEBHOOK_TOKEN=$(python3 -c 'import secrets; print(secrets.token_hex(16))')

echo "✅ Keys generated"

# Set all environment variables
echo ""
echo "📝 Setting environment variables..."

railway variables set TWILIO_ACCOUNT_SID="$TWILIO_SID"
railway variables set TWILIO_AUTH_TOKEN="$TWILIO_TOKEN"
railway variables set TWILIO_WHATSAPP_NUMBER="$TWILIO_WHATSAPP"
railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set WEBHOOK_VERIFY_TOKEN="$WEBHOOK_TOKEN"

echo "✅ Environment variables set"

# Deploy
echo ""
echo "🚀 Deploying to Railway..."
echo ""

railway up

echo ""
echo "✅ Deployment complete!"
echo ""

# Get the deployment URL
echo "🌐 Getting your deployment URL..."
RAILWAY_URL=$(railway domain 2>&1 || echo "")

if [ ! -z "$RAILWAY_URL" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                   🎉 DEPLOYMENT SUCCESSFUL!                    ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📱 Your WhatsApp Bot is now live at:"
    echo "   $RAILWAY_URL"
    echo ""
    echo "🔗 Webhook URL (configure in Twilio/Meta):"
    echo "   ${RAILWAY_URL}/whatsapp-webhook"
    echo ""
    echo "🔐 Webhook Verify Token (for Meta API):"
    echo "   $WEBHOOK_TOKEN"
    echo ""
    echo "✅ Next Steps:"
    echo ""
    echo "1. Configure WhatsApp Webhook:"
    echo "   - For Twilio: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox"
    echo "   - Set webhook URL to: ${RAILWAY_URL}/whatsapp-webhook"
    echo ""
    echo "2. Test your deployment:"
    echo "   curl ${RAILWAY_URL}/health"
    echo ""
    echo "3. Test webhook:"
    echo "   curl -X POST ${RAILWAY_URL}/whatsapp-webhook \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"From\":\"whatsapp:+233244123456\",\"Body\":\"You have sent GHS50.00 to 0244987654\"}'"
    echo ""
    echo "4. Forward a real MoMo SMS to your WhatsApp bot number"
    echo ""
    echo "📊 View logs:"
    echo "   railway logs"
    echo ""
    echo "⚙️  Manage environment variables:"
    echo "   railway variables"
    echo ""
    echo "🔄 Redeploy after changes:"
    echo "   railway up"
    echo ""
else
    echo ""
    echo "⚠️  Could not retrieve deployment URL automatically"
    echo ""
    echo "Run this command to get your URL:"
    echo "   railway domain"
    echo ""
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Need help? Check DEPLOYMENT_CHECKLIST.md for detailed guide  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
