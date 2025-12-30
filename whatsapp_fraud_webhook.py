"""
MoMo Analytics WhatsApp Webhook with Real-Time Fraud Detection
Complete implementation for Ghana MoMo SMS analysis and fraud prevention
"""

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import re
import json
import hashlib
from typing import Dict, List, Tuple, Optional
import os
from dataclasses import dataclass
from enum import Enum

app = Flask(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class MoMoProvider(Enum):
    MTN = "MTN"
    VODAFONE = "VODAFONE"
    AIRTELTIGO = "AIRTELTIGO"

# Risk score thresholds
RISK_THRESHOLDS = {
    RiskLevel.CRITICAL: 80,
    RiskLevel.HIGH: 60,
    RiskLevel.MEDIUM: 40,
    RiskLevel.LOW: 0
}

# SMS patterns for each provider
SMS_PATTERNS = {
    MoMoProvider.MTN: {
        'sent': r'You have sent GHS?([\d,\.]+) to (\d+)',
        'received': r'You have received GHS?([\d,\.]+) from (\d+)',
        'balance': r'Your new balance is GHS?([\d,\.]+)',
        'reference': r'Ref[:\.]?\s*(\w+)'
    },
    MoMoProvider.VODAFONE: {
        'sent': r'You sent GHS?([\d,\.]+) to (\d+)',
        'received': r'You received GHS?([\d,\.]+) from (\d+)',
        'balance': r'Balance: GHS?([\d,\.]+)',
        'reference': r'Reference[:\.]?\s*(\w+)'
    },
    MoMoProvider.AIRTELTIGO: {
        'sent': r'Sent GHS?([\d,\.]+) to (\d+)',
        'received': r'Received GHS?([\d,\.]+) from (\d+)',
        'balance': r'Balance GHS?([\d,\.]+)',
        'reference': r'Ref[:\.]?\s*(\w+)'
    }
}

# Fraud detection parameters
FRAUD_PARAMS = {
    'late_night_hours': [2, 3, 4, 5],
    'suspicious_hours': [22, 23, 0, 1],
    'velocity_window_minutes': 60,
    'velocity_threshold': 3,
    'amount_spike_multiplier': 3.0,
    'round_amounts': [100, 200, 500, 1000, 2000, 5000],
    'scam_keywords': ['REWARD', 'WINNINGS', 'GIFT', 'PRIZE', 'MISTAKE', 'REFUND', 'URGENT']
}

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Transaction:
    amount: float
    direction: str  # 'in' or 'out'
    counterparty: str
    reference: str
    balance: float
    provider: MoMoProvider
    raw_text: str
    timestamp: datetime
    user_id: str

@dataclass
class UserProfile:
    user_id: str
    avg_daily_amount: float
    avg_transaction_amount: float
    trusted_merchants: List[str]
    blocked_merchants: List[str]
    transaction_history: List[Transaction]
    daily_limit: float
    weekly_pattern: Dict[int, float]  # day_of_week: avg_amount

@dataclass
class FraudAlert:
    risk_score: int
    risk_level: RiskLevel
    transaction: Transaction
    reasons: List[str]
    recommended_actions: List[str]
    alert_type: str

# ============================================================================
# DATABASE SIMULATION (Replace with actual DB in production)
# ============================================================================

# In-memory storage (use PostgreSQL/MongoDB in production)
user_profiles: Dict[str, UserProfile] = {}
recent_transactions: Dict[str, List[Transaction]] = {}

def get_user_profile(user_id: str) -> Optional[UserProfile]:
    """Fetch user profile from database"""
    if user_id not in user_profiles:
        # Create default profile for new user
        user_profiles[user_id] = UserProfile(
            user_id=user_id,
            avg_daily_amount=200.0,
            avg_transaction_amount=50.0,
            trusted_merchants=[],
            blocked_merchants=[],
            transaction_history=[],
            daily_limit=2000.0,
            weekly_pattern={i: 0.0 for i in range(7)}
        )
    return user_profiles[user_id]

def save_transaction(transaction: Transaction):
    """Save transaction to database"""
    user_id = transaction.user_id
    profile = get_user_profile(user_id)
    profile.transaction_history.append(transaction)
    
    # Update recent transactions for velocity checks
    if user_id not in recent_transactions:
        recent_transactions[user_id] = []
    recent_transactions[user_id].append(transaction)
    
    # Keep only last 100 transactions in memory
    recent_transactions[user_id] = recent_transactions[user_id][-100:]
    
    # Update profile statistics
    update_user_statistics(user_id)

def update_user_statistics(user_id: str):
    """Update user's spending patterns"""
    profile = get_user_profile(user_id)
    
    if len(profile.transaction_history) > 0:
        # Calculate averages
        outgoing = [t for t in profile.transaction_history if t.direction == 'out']
        if outgoing:
            amounts = [t.amount for t in outgoing]
            profile.avg_transaction_amount = sum(amounts) / len(amounts)
            
            # Daily average (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_outgoing = [t for t in outgoing if t.timestamp >= thirty_days_ago]
            if recent_outgoing:
                total = sum(t.amount for t in recent_outgoing)
                days = (datetime.now() - recent_outgoing[0].timestamp).days + 1
                profile.avg_daily_amount = total / days

# ============================================================================
# SMS PARSING
# ============================================================================

def detect_provider(sms_text: str) -> Optional[MoMoProvider]:
    """Detect MoMo provider from SMS text"""
    text_lower = sms_text.lower()
    
    if 'mtn' in text_lower or 'momo' in text_lower:
        return MoMoProvider.MTN
    elif 'vodafone' in text_lower or 'vodacash' in text_lower:
        return MoMoProvider.VODAFONE
    elif 'airtel' in text_lower or 'tigo' in text_lower:
        return MoMoProvider.AIRTELTIGO
    
    return None

def parse_momo_sms(sms_text: str, user_id: str) -> Optional[Transaction]:
    """Parse MoMo SMS and extract transaction details"""
    provider = detect_provider(sms_text)
    
    if not provider:
        return None
    
    patterns = SMS_PATTERNS[provider]
    
    # Determine direction and extract details
    direction = None
    amount = None
    counterparty = None
    
    # Try sent pattern
    sent_match = re.search(patterns['sent'], sms_text, re.IGNORECASE)
    if sent_match:
        direction = 'out'
        amount = float(sent_match.group(1).replace(',', ''))
        counterparty = sent_match.group(2)
    
    # Try received pattern
    received_match = re.search(patterns['received'], sms_text, re.IGNORECASE)
    if received_match:
        direction = 'in'
        amount = float(received_match.group(1).replace(',', ''))
        counterparty = received_match.group(2)
    
    if not direction or not amount:
        return None
    
    # Extract balance
    balance = 0.0
    balance_match = re.search(patterns['balance'], sms_text, re.IGNORECASE)
    if balance_match:
        balance = float(balance_match.group(1).replace(',', ''))
    
    # Extract reference
    reference = ''
    ref_match = re.search(patterns['reference'], sms_text, re.IGNORECASE)
    if ref_match:
        reference = ref_match.group(1)
    
    return Transaction(
        amount=amount,
        direction=direction,
        counterparty=counterparty,
        reference=reference,
        balance=balance,
        provider=provider,
        raw_text=sms_text,
        timestamp=datetime.now(),
        user_id=user_id
    )

# ============================================================================
# FRAUD DETECTION ENGINE
# ============================================================================

def calculate_fraud_risk(transaction: Transaction, profile: UserProfile) -> Tuple[int, List[str]]:
    """
    Calculate fraud risk score (0-100) and return reasons
    Returns: (risk_score, list_of_reasons)
    """
    score = 0
    reasons = []
    
    # Only analyze outgoing transactions
    if transaction.direction != 'out':
        return (0, ["Incoming transaction - no fraud risk"])
    
    hour = transaction.timestamp.hour
    
    # ========================================================================
    # LAYER 1: TIME-BASED ANOMALIES
    # ========================================================================
    
    # Late night transactions (2am-5am)
    if hour in FRAUD_PARAMS['late_night_hours']:
        score += 35
        reasons.append(f"❗ Unusual hour: {hour}:00 (late night activity)")
    
    # Suspicious hours (10pm-1am)
    elif hour in FRAUD_PARAMS['suspicious_hours']:
        score += 15
        reasons.append(f"⚠️ Late hour transaction: {hour}:00")
    
    # ========================================================================
    # LAYER 2: AMOUNT-BASED ANOMALIES
    # ========================================================================
    
    # Amount spike detection
    if transaction.amount > profile.avg_transaction_amount * FRAUD_PARAMS['amount_spike_multiplier']:
        multiplier = transaction.amount / profile.avg_transaction_amount
        score += 25
        reasons.append(f"💰 Amount spike: {multiplier:.1f}x your average (GHS {profile.avg_transaction_amount:.2f})")
    
    # Round suspicious amounts
    if transaction.amount in FRAUD_PARAMS['round_amounts']:
        score += 10
        reasons.append(f"🔢 Round amount: GHS {transaction.amount:.0f} (common in scams)")
    
    # Large amount threshold
    if transaction.amount > 1000:
        score += 15
        reasons.append(f"💵 Large amount: GHS {transaction.amount:.2f}")
    
    # ========================================================================
    # LAYER 3: VELOCITY CHECKS
    # ========================================================================
    
    # Check recent transactions in the last hour
    recent = [t for t in profile.transaction_history 
              if t.direction == 'out' 
              and (transaction.timestamp - t.timestamp).total_seconds() < 3600]
    
    if len(recent) >= FRAUD_PARAMS['velocity_threshold']:
        score += 20
        reasons.append(f"⚡ Rapid transactions: {len(recent)} payments in last hour")
    
    # Check for very quick successive transactions (< 5 minutes)
    if recent and (transaction.timestamp - recent[-1].timestamp).total_seconds() < 300:
        score += 15
        reasons.append(f"⏱️ Back-to-back transaction (< 5 min apart)")
    
    # ========================================================================
    # LAYER 4: MERCHANT/COUNTERPARTY ANALYSIS
    # ========================================================================
    
    # New merchant (never paid before)
    if transaction.counterparty not in [t.counterparty for t in profile.transaction_history]:
        score += 15
        reasons.append(f"🆕 New recipient: {transaction.counterparty[-4:]} (first time)")
    
    # Blocked merchant
    if transaction.counterparty in profile.blocked_merchants:
        score += 40
        reasons.append(f"🚫 BLOCKED merchant: You've blocked this number before!")
    
    # Not a trusted merchant for large amounts
    if transaction.amount > 200 and transaction.counterparty not in profile.trusted_merchants:
        score += 10
        reasons.append(f"❓ Untrusted merchant for large payment")
    
    # ========================================================================
    # LAYER 5: DAILY/WEEKLY PATTERN BREAKS
    # ========================================================================
    
    # Daily limit exceeded
    today_total = sum(t.amount for t in profile.transaction_history 
                      if t.direction == 'out' 
                      and t.timestamp.date() == transaction.timestamp.date())
    
    if today_total > profile.daily_limit:
        score += 20
        reasons.append(f"📊 Daily limit exceeded: GHS {today_total:.2f} / {profile.daily_limit:.2f}")
    
    # Weekly pattern deviation
    day_of_week = transaction.timestamp.weekday()
    avg_for_day = profile.weekly_pattern.get(day_of_week, 0)
    
    if avg_for_day > 0 and today_total > avg_for_day * 2:
        score += 15
        reasons.append(f"📅 Unusual spending for {transaction.timestamp.strftime('%A')}")
    
    # ========================================================================
    # LAYER 6: SCAM KEYWORD DETECTION
    # ========================================================================
    
    for keyword in FRAUD_PARAMS['scam_keywords']:
        if keyword.lower() in transaction.raw_text.lower():
            score += 25
            reasons.append(f"⚠️ Scam keyword detected: '{keyword}'")
            break
    
    # ========================================================================
    # LAYER 7: DUPLICATE DETECTION
    # ========================================================================
    
    # Check for duplicate amounts in last hour
    duplicate_amounts = [t for t in recent 
                         if abs(t.amount - transaction.amount) < 1.0]
    
    if len(duplicate_amounts) >= 2:
        score += 20
        reasons.append(f"🔁 Duplicate amount: GHS {transaction.amount:.2f} charged multiple times")
    
    # Cap score at 100
    score = min(score, 100)
    
    return (score, reasons)

def get_risk_level(score: int) -> RiskLevel:
    """Convert risk score to risk level"""
    if score >= RISK_THRESHOLDS[RiskLevel.CRITICAL]:
        return RiskLevel.CRITICAL
    elif score >= RISK_THRESHOLDS[RiskLevel.HIGH]:
        return RiskLevel.HIGH
    elif score >= RISK_THRESHOLDS[RiskLevel.MEDIUM]:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW

def generate_recommended_actions(risk_level: RiskLevel, transaction: Transaction) -> List[str]:
    """Generate recommended actions based on risk level"""
    actions = []
    
    if risk_level == RiskLevel.CRITICAL:
        actions = [
            "🛑 Reply '1' to report fraud to your provider",
            "📞 Reply '2' to call fraud hotline immediately",
            "✅ Reply '3' if this was you (mark legitimate)",
            "🚫 Reply 'BLOCK' to prevent future payments to this number"
        ]
    elif risk_level == RiskLevel.HIGH:
        actions = [
            "✅ Reply 'YES' if this was you",
            "❌ Reply 'NO' to report as fraud",
            "🔍 Reply 'DETAILS' for more info"
        ]
    elif risk_level == RiskLevel.MEDIUM:
        actions = [
            "ℹ️ Reply 'DETAILS' for breakdown",
            "🚫 Reply 'BLOCK' to block this merchant"
        ]
    else:
        actions = [
            "✓ Transaction looks normal",
            "🚫 Reply 'BLOCK' if you want to block this merchant"
        ]
    
    return actions

# ============================================================================
# WHATSAPP MESSAGING
# ============================================================================

def format_whatsapp_alert(alert: FraudAlert) -> str:
    """Format fraud alert for WhatsApp"""
    
    emoji_map = {
        RiskLevel.CRITICAL: "🚨",
        RiskLevel.HIGH: "⚠️",
        RiskLevel.MEDIUM: "🔔",
        RiskLevel.LOW: "ℹ️"
    }
    
    emoji = emoji_map[alert.risk_level]
    
    if alert.risk_level == RiskLevel.CRITICAL:
        message = f"""{emoji} *FRAUD ALERT - ACT NOW*

GHS {alert.transaction.amount:.2f} sent to {alert.transaction.counterparty[-4:]}
Time: {alert.transaction.timestamp.strftime('%I:%M%p')}

⚠️ *Risk Score: {alert.risk_score}/100*

*Why we're concerned:*
"""
    elif alert.risk_level == RiskLevel.HIGH:
        message = f"""{emoji} *Suspicious Transaction*

GHS {alert.transaction.amount:.2f} to {alert.transaction.counterparty[-4:]}

*Risk Score: {alert.risk_score}/100*

*Reasons:*
"""
    elif alert.risk_level == RiskLevel.MEDIUM:
        message = f"""{emoji} *Unusual Activity*

GHS {alert.transaction.amount:.2f} to {alert.transaction.counterparty[-4:]}

*Risk Score: {alert.risk_score}/100*

*Notes:*
"""
    else:
        message = f"""{emoji} *Transaction Recorded*

GHS {alert.transaction.amount:.2f} to {alert.transaction.counterparty[-4:]}

Everything looks normal.
"""
    
    # Add reasons
    for reason in alert.reasons[:5]:  # Limit to top 5 reasons
        message += f"\n{reason}"
    
    message += "\n\n*ACTIONS:*\n"
    for action in alert.recommended_actions:
        message += f"{action}\n"
    
    if alert.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
        message += "\n⚠️ _This could be unauthorized access._"
    
    return message

def send_whatsapp_message(to: str, message: str):
    """
    Send WhatsApp message via Twilio/Meta WhatsApp Business API
    Replace with actual implementation
    """
    # Example with Twilio
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # message = client.messages.create(
    #     from_='whatsapp:+233XXXXXXXXX',
    #     body=message,
    #     to=f'whatsapp:{to}'
    # )
    
    print(f"[WHATSAPP] Sending to {to}:")
    print(message)
    print("-" * 50)

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.route('/whatsapp-webhook', methods=['POST'])
def whatsapp_webhook():
    """
    Main webhook endpoint for receiving WhatsApp messages
    Expects JSON payload with message content
    """
    try:
        data = request.json
        
        # Extract message details
        from_number = data.get('From', '').replace('whatsapp:', '')
        message_body = data.get('Body', '')
        
        if not message_body:
            return jsonify({"status": "error", "message": "Empty message"}), 400
        
        # Generate user ID (hash of phone number)
        user_id = hashlib.sha256(from_number.encode()).hexdigest()[:16]
        
        # Check if message is a command
        if handle_command(message_body.strip().upper(), from_number, user_id):
            return jsonify({"status": "command_processed"}), 200
        
        # Try to parse as MoMo SMS
        transaction = parse_momo_sms(message_body, user_id)
        
        if not transaction:
            # Not a valid MoMo SMS
            send_whatsapp_message(
                from_number,
                "❓ I didn't recognize that as a MoMo transaction.\n\n"
                "Forward your MoMo SMS here or type HELP for commands."
            )
            return jsonify({"status": "unrecognized_message"}), 200
        
        # Get user profile
        profile = get_user_profile(user_id)
        
        # Calculate fraud risk
        risk_score, reasons = calculate_fraud_risk(transaction, profile)
        risk_level = get_risk_level(risk_score)
        
        # Create fraud alert
        alert = FraudAlert(
            risk_score=risk_score,
            risk_level=risk_level,
            transaction=transaction,
            reasons=reasons,
            recommended_actions=generate_recommended_actions(risk_level, transaction),
            alert_type="real_time"
        )
        
        # Send alert based on risk level
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM]:
            message = format_whatsapp_alert(alert)
            send_whatsapp_message(from_number, message)
        elif risk_level == RiskLevel.LOW:
            # Send confirmation for low risk
            send_whatsapp_message(
                from_number,
                f"✅ GHS {transaction.amount:.2f} {'sent' if transaction.direction == 'out' else 'received'}\n"
                f"Category: Processing...\n"
                f"Today's total: Calculating..."
            )
        
        # Save transaction
        save_transaction(transaction)
        
        # Log fraud attempt if critical
        if risk_level == RiskLevel.CRITICAL:
            log_fraud_attempt(transaction, risk_score, reasons)
        
        return jsonify({
            "status": "success",
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "transaction_id": transaction.reference
        }), 200
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def handle_command(command: str, from_number: str, user_id: str) -> bool:
    """Handle bot commands - returns True if command was processed"""
    
    profile = get_user_profile(user_id)
    
    if command == 'HELP':
        help_text = """📱 *MoMo Analytics Bot Commands*

*Transactions:*
TODAY - Today's spending
WEEK - Weekly summary
MONTH - Monthly overview

*Budget:*
BUDGET 500 - Set daily budget

*Security:*
BLOCK [last 4 digits] - Block merchant
TRUSTED [last 4 digits] - Mark as trusted

*Account:*
UPGRADE - View premium plans
STOP - Pause alerts

Forward any MoMo SMS to track automatically! 🚀"""
        
        send_whatsapp_message(from_number, help_text)
        return True
    
    elif command == 'TODAY':
        today_total = sum(t.amount for t in profile.transaction_history 
                          if t.direction == 'out' 
                          and t.timestamp.date() == datetime.now().date())
        
        message = f"""📊 *Today's Spending*

Total: GHS {today_total:.2f}
Transactions: {len([t for t in profile.transaction_history if t.timestamp.date() == datetime.now().date()])}
Average: GHS {today_total / max(len([t for t in profile.transaction_history if t.timestamp.date() == datetime.now().date()]), 1):.2f}

Budget: GHS {profile.daily_limit:.2f}
Remaining: GHS {max(profile.daily_limit - today_total, 0):.2f}"""
        
        send_whatsapp_message(from_number, message)
        return True
    
    elif command.startswith('BUDGET '):
        try:
            amount = float(command.split()[1])
            profile.daily_limit = amount
            send_whatsapp_message(
                from_number,
                f"✅ Daily budget set to GHS {amount:.2f}\n\n"
                f"You'll get alerts when you approach this limit."
            )
            return True
        except:
            send_whatsapp_message(from_number, "❌ Invalid format. Use: BUDGET 500")
            return True
    
    elif command == 'STOP':
        send_whatsapp_message(
            from_number,
            "⏸️ Alerts paused.\n\nType START to resume."
        )
        return True
    
    # Check for YES/NO responses to fraud alerts
    elif command in ['YES', 'NO', '1', '2', '3']:
        handle_fraud_response(command, from_number, user_id)
        return True
    
    return False

def handle_fraud_response(response: str, from_number: str, user_id: str):
    """Handle user response to fraud alert"""
    
    if response == 'YES':
        send_whatsapp_message(
            from_number,
            "✅ Marked as legitimate.\n\nWe'll learn from this to improve your security."
        )
    
    elif response == 'NO':
        send_whatsapp_message(
            from_number,
            "🚨 *Fraud Report Initiated*\n\n"
            "1. Contact your MoMo provider immediately\n"
            "2. Report the transaction reference\n"
            "3. Request account freeze if needed\n\n"
            "*Hotlines:*\n"
            "MTN: 100\n"
            "Vodafone: 200\n"
            "AirtelTigo: 111"
        )
    
    elif response == '1':
        send_whatsapp_message(
            from_number,
            "📞 *Report to Provider*\n\n"
            "Calling your MoMo provider...\n\n"
            "Or dial:\n"
            "MTN: 100\n"
            "Vodafone: 200\n"
            "AirtelTigo: 111"
        )
    
    elif response == '2':
        send_whatsapp_message(
            from_number,
            "📞 *Fraud Hotline*\n\n"
            "Ghana Fraud Hotline: 112\n"
            "Police Emergency: 191"
        )
    
    elif response == '3':
        send_whatsapp_message(
            from_number,
            "✅ Transaction verified.\n\n"
            "This merchant will be marked as trusted."
        )

def log_fraud_attempt(transaction: Transaction, risk_score: int, reasons: List[str]):
    """Log critical fraud attempts for analysis"""
    fraud_log = {
        'timestamp': transaction.timestamp.isoformat(),
        'user_id': transaction.user_id,
        'amount': transaction.amount,
        'counterparty': transaction.counterparty,
        'risk_score': risk_score,
        'reasons': reasons,
        'reference': transaction.reference
    }
    
    # In production, save to database
    print(f"[FRAUD LOG] {json.dumps(fraud_log, indent=2)}")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "MoMo Analytics Fraud Detection",
        "version": "1.0.0"
    }), 200

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
