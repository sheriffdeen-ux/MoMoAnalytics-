#!/bin/bash

# MoMo Analytics - Quick Deployment Script
# This script helps you deploy the WhatsApp fraud detection bot

echo "🚀 MoMo Analytics - Deployment Script"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

echo "Choose your deployment platform:"
echo "1) Railway (Recommended - Fastest)"
echo "2) Heroku (Popular - Free tier available)"
echo "3) DigitalOcean App Platform"
echo "4) Manual setup (VPS/Cloud Server)"
echo ""
read -p "Enter your choice (1-4): " platform_choice

case $platform_choice in
    1)
        echo ""
        echo "📦 RAILWAY DEPLOYMENT"
        echo "===================="
        echo ""
        print_info "Prerequisites:"
        echo "  - GitHub account"
        echo "  - Railway account (sign up at railway.app)"
        echo ""
        echo "Steps to deploy:"
        echo ""
        echo "1. Install Railway CLI:"
        echo "   npm install -g @railway/cli"
        echo ""
        echo "2. Login to Railway:"
        echo "   railway login"
        echo ""
        echo "3. Initialize Railway project:"
        echo "   railway init"
        echo ""
        echo "4. Add PostgreSQL database:"
        echo "   railway add --service postgresql"
        echo ""
        echo "5. Set environment variables:"
        echo "   railway variables set TWILIO_ACCOUNT_SID=your_sid"
        echo "   railway variables set TWILIO_AUTH_TOKEN=your_token"
        echo "   railway variables set TWILIO_WHATSAPP_NUMBER=whatsapp:+233XXXXXXXXX"
        echo "   railway variables set SECRET_KEY=\$(python -c 'import secrets; print(secrets.token_hex(32))')"
        echo ""
        echo "6. Deploy:"
        echo "   railway up"
        echo ""
        print_success "Your webhook will be live at: https://your-app.railway.app"
        echo ""
        print_warning "Don't forget to:"
        echo "  - Configure WhatsApp webhook URL in Twilio/Meta dashboard"
        echo "  - Test the /health endpoint"
        ;;
        
    2)
        echo ""
        echo "📦 HEROKU DEPLOYMENT"
        echo "==================="
        echo ""
        print_info "Prerequisites:"
        echo "  - Heroku account"
        echo "  - Heroku CLI installed"
        echo ""
        echo "Steps to deploy:"
        echo ""
        echo "1. Login to Heroku:"
        echo "   heroku login"
        echo ""
        echo "2. Create Heroku app:"
        echo "   heroku create momo-analytics-api"
        echo ""
        echo "3. Add PostgreSQL addon:"
        echo "   heroku addons:create heroku-postgresql:mini"
        echo ""
        echo "4. Set environment variables:"
        echo "   heroku config:set TWILIO_ACCOUNT_SID=your_sid"
        echo "   heroku config:set TWILIO_AUTH_TOKEN=your_token"
        echo "   heroku config:set TWILIO_WHATSAPP_NUMBER=whatsapp:+233XXXXXXXXX"
        echo "   heroku config:set SECRET_KEY=\$(python -c 'import secrets; print(secrets.token_hex(32))')"
        echo ""
        echo "5. Deploy:"
        echo "   git init"
        echo "   git add ."
        echo "   git commit -m 'Initial deployment'"
        echo "   git push heroku main"
        echo ""
        print_success "Your webhook will be live at: https://momo-analytics-api.herokuapp.com"
        echo ""
        print_warning "Note: Heroku removed free tier. You'll need a paid plan."
        ;;
        
    3)
        echo ""
        echo "📦 DIGITALOCEAN DEPLOYMENT"
        echo "========================="
        echo ""
        print_info "Prerequisites:"
        echo "  - DigitalOcean account"
        echo "  - GitHub repository with your code"
        echo ""
        echo "Steps to deploy:"
        echo ""
        echo "1. Go to DigitalOcean App Platform"
        echo "2. Click 'Create App'"
        echo "3. Connect your GitHub repository"
        echo "4. Select 'Python' as runtime"
        echo "5. Add PostgreSQL managed database"
        echo "6. Set environment variables in the dashboard:"
        echo "   - TWILIO_ACCOUNT_SID"
        echo "   - TWILIO_AUTH_TOKEN"
        echo "   - TWILIO_WHATSAPP_NUMBER"
        echo "   - SECRET_KEY"
        echo "7. Deploy!"
        echo ""
        print_success "DigitalOcean will auto-deploy on every git push"
        ;;
        
    4)
        echo ""
        echo "📦 MANUAL VPS DEPLOYMENT"
        echo "======================="
        echo ""
        print_info "This assumes you have a VPS (Ubuntu/Debian) with SSH access"
        echo ""
        echo "Steps:"
        echo ""
        echo "1. SSH into your server:"
        echo "   ssh user@your-server-ip"
        echo ""
        echo "2. Install Python and dependencies:"
        echo "   sudo apt update"
        echo "   sudo apt install python3-pip python3-venv nginx postgresql"
        echo ""
        echo "3. Clone your repository or upload files"
        echo ""
        echo "4. Create virtual environment:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo ""
        echo "5. Install requirements:"
        echo "   pip install -r requirements.txt"
        echo ""
        echo "6. Setup PostgreSQL database:"
        echo "   sudo -u postgres createdb momo_analytics"
        echo "   sudo -u postgres createuser momo_user"
        echo ""
        echo "7. Create .env file with your credentials"
        echo ""
        echo "8. Run with systemd (create service file in /etc/systemd/system/momo-analytics.service):"
        echo ""
        cat << 'EOF'
[Unit]
Description=MoMo Analytics WhatsApp Bot
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/momo-analytics
Environment="PATH=/var/www/momo-analytics/venv/bin"
ExecStart=/var/www/momo-analytics/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 whatsapp_fraud_webhook:app

[Install]
WantedBy=multi-user.target
EOF
        echo ""
        echo "9. Start the service:"
        echo "   sudo systemctl start momo-analytics"
        echo "   sudo systemctl enable momo-analytics"
        echo ""
        echo "10. Setup Nginx reverse proxy (optional but recommended)"
        ;;
esac

echo ""
echo ""
echo "🔐 SECURITY CHECKLIST"
echo "===================="
echo ""
print_warning "Before going live, ensure you:"
echo "  ☐ Set strong SECRET_KEY (use: python -c 'import secrets; print(secrets.token_hex(32))')"
echo "  ☐ Enable HTTPS (required for WhatsApp webhooks)"
echo "  ☐ Set up database backups"
echo "  ☐ Configure rate limiting"
echo "  ☐ Set up monitoring (Sentry, Datadog, etc.)"
echo "  ☐ Test webhook with real MoMo SMS"
echo "  ☐ Review GDPR/data protection compliance"
echo ""

echo "📱 WHATSAPP API SETUP"
echo "===================="
echo ""
echo "Choose your WhatsApp provider:"
echo ""
echo "Option 1: TWILIO (Easiest for MVP)"
echo "  - Sign up: https://www.twilio.com/try-twilio"
echo "  - Get WhatsApp Sandbox number (instant)"
echo "  - Or request production WhatsApp number (2-3 days)"
echo "  - Set webhook URL: https://your-domain.com/whatsapp-webhook"
echo ""
echo "Option 2: META WhatsApp Business API (Best for Scale)"
echo "  - Sign up: https://business.facebook.com"
echo "  - Create Business App"
echo "  - Add WhatsApp product"
echo "  - Get permanent access token"
echo "  - Configure webhook with verify token"
echo ""

echo "🧪 TESTING YOUR DEPLOYMENT"
echo "========================="
echo ""
echo "1. Health check:"
echo "   curl https://your-domain.com/health"
echo ""
echo "2. Test webhook (replace with your URL):"
cat << 'EOF'
curl -X POST https://your-domain.com/whatsapp-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "From": "whatsapp:+233244123456",
    "Body": "You have sent GHS50.00 to 0244987654. Your new balance is GHS200.00"
  }'
EOF
echo ""
echo "3. Forward real MoMo SMS to your WhatsApp bot"
echo ""

echo ""
print_success "Deployment guide complete!"
echo ""
print_info "Need help? Check:"
echo "  - DEPLOYMENT_GUIDE.md (detailed instructions)"
echo "  - README.md (project overview)"
echo "  - GitHub Issues (if using version control)"
echo ""
print_warning "Remember: Test thoroughly before launching to real users!"
echo ""
