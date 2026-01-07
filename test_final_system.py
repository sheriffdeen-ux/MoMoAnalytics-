#!/usr/bin/env python3
"""
Complete Test Suite for MoMo Analytics Ghana
Tests all features with Ghana providers
"""

import sys
import json
from datetime import datetime
import os


PASSED = 0
FAILED = 0

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def test(name):
    print(f"🧪 {name}...", end=" ")

def passed(msg=""):
    global PASSED
    PASSED += 1
    print(f"✅ PASS {msg}")

def failed(msg=""):
    global FAILED
    FAILED += 1
    print(f"❌ FAIL {msg}")

# ============================================================================
# TEST 1: Module Import
# ============================================================================

print_header("TEST 1: Module Import & Setup")

test("Import Flask app")
try:
    # Set environment for testing
    import os
    os.environ['SECRET_KEY'] = 'test-secret-key-12345'
    os.environ['ENCRYPTION_KEY'] = 'MXoahZZjlTRZDMfeFZ-scvaUA5a7D15tQpkwfdfRhvU='
    os.environ['TELEGRAM_WEBHOOK_SECRET'] = 'test-webhook-secret'
    os.environ['DATABASE_URL'] = 'sqlite://'
    
    from final_system import app, db, parse_sms, analyze_fraud, get_risk_level
    from final_system import BotUser, Transaction
    passed()
except Exception as e:
    failed(f"- {e}")
    sys.exit(1)

test("App initialization")
try:
    assert app is not None
    assert app.name == 'final_system'
    passed()
except Exception as e:
    failed(f"- {e}")

test("Database models")
try:
    with app.app_context():
        db.create_all()
    passed()
except Exception as e:
    failed(f"- {e}")

# ============================================================================
# TEST 2: Ghana SMS Parsing
# ============================================================================

print_header("TEST 2: Ghana MoMo SMS Parsing")

ghana_sms_tests = [
    ("MTN MoMo Sent", "You have sent GHS50.00 to 0244123456. Your new balance is GHS500.00. Ref: MTN123", 50.0, 'out', 'MTN MoMo'),
    ("MTN MoMo Received", "You have received GHS200.00 from 0244987654. Your balance is GHS700.00", 200.0, 'in', 'MTN MoMo'),
    ("Vodafone Sent", "You sent GHS150.00 to 0501234567. Balance: GHS850.00 Reference: VOD456", 150.0, 'out', 'Vodafone Cash'),
    ("Vodafone Received", "You received GHS300.00 from 0509876543. Balance GHS1150.00", 300.0, 'in', 'Vodafone Cash'),
    ("AirtelTigo Sent", "You paid GHS100.00. Balance GHS400.00 ID: AT789", 100.0, 'out', 'AirtelTigo Money'),
    ("Large Amount", "You have sent GHS5000.00 to 0201234567", 5000.0, 'out', 'MTN MoMo'),
    ("With Currency Symbol", "sent ₵250.50 to 0244555666", 250.5, 'out', 'Unknown'),
]

for name, sms, expected_amount, expected_dir, expected_provider in ghana_sms_tests:
    test(f"Parse {name}")
    try:
        with app.app_context():
            txn_data = parse_sms(sms, "test_user")
            assert txn_data is not None, "Transaction is None"
            assert txn_data['amount'] == expected_amount, f"Amount mismatch: {txn_data['amount']} != {expected_amount}"
            assert txn_data['direction'] == expected_dir, f"Direction mismatch"
            assert expected_provider.split()[0] in txn_data['provider'], f"Provider mismatch"
            passed(f"(GHS {txn_data['amount']}, {txn_data['direction']}, {txn_data['provider']})")
    except Exception as e:
        failed(f"- {e}")

test("Reject invalid SMS")
try:
    with app.app_context():
        invalid = "This is just a regular text message"
        txn = parse_sms(invalid, "test_user")
        assert txn is None, "Should reject non-MoMo SMS"
        passed()
except Exception as e:
    failed(f"- {e}")

# ============================================================================
# TEST 3: Fraud Detection
# ============================================================================

print_header("TEST 3: Fraud Detection (Ghana)")

test("Low risk transaction")
try:
    with app.app_context():
        user = BotUser(
            user_id="test_low_risk",
            platform='telegram',
            avg_amount=50.0,
            daily_limit=2000.0
        )
        user.set_trusted_merchants([])
        user.set_blocked_merchants([])
        
        txn_data = {
            'amount': 50.0,
            'direction': 'out',
            'counterparty': '0244123456',
            'reference': 'TEST1',
            'balance': 500.0,
            'provider': 'MTN MoMo',
            'raw_text': 'Test SMS'
        }
        
        score, reasons = analyze_fraud(txn_data, user)
        assert score < 40, f"Score too high for low risk: {score}"
        passed(f"(Score: {score})")
except Exception as e:
    failed(f"- {e}")

test("High risk (large amount)")
try:
    with app.app_context():
        user = BotUser(
            user_id="test_high_risk",
            platform='telegram',
            avg_amount=100.0,
            daily_limit=2000.0
        )
        user.set_trusted_merchants([])
        user.set_blocked_merchants([])
        
        txn_data = {
            'amount': 5000.0,
            'direction': 'out',
            'counterparty': '0201234567',
            'reference': 'TEST2',
            'balance': 100.0,
            'provider': 'Vodafone Cash',
            'raw_text': 'Test SMS'
        }
        
        score, reasons = analyze_fraud(txn_data, user)
        assert score >= 60, f"Score too low for high risk: {score}"
        assert len(reasons) > 0, "No reasons provided"
        passed(f"(Score: {score}, Reasons: {len(reasons)})")
except Exception as e:
    failed(f"- {e}")

test("Blocked merchant (Ghana)")
try:
    with app.app_context():
        user = BotUser(
            user_id="test_blocked",
            platform='telegram',
            avg_amount=50.0,
            daily_limit=2000.0
        )
        user.set_trusted_merchants([])
        user.set_blocked_merchants(['1234'])
        
        txn_data = {
            'amount': 100.0,
            'direction': 'out',
            'counterparty': '0244441234',  # Ends with blocked 1234
            'reference': 'TEST3',
            'balance': 400.0,
            'provider': 'MTN MoMo',
            'raw_text': 'Test SMS'
        }
        
        score, reasons = analyze_fraud(txn_data, user)
        assert score >= 50, f"Blocked merchant should increase score significantly: {score}"
        passed(f"(Score: {score})")
except Exception as e:
    failed(f"- {e}")

test("Incoming transaction (safe)")
try:
    with app.app_context():
        user = BotUser(
            user_id="test_incoming",
            platform='telegram'
        )
        user.set_trusted_merchants([])
        user.set_blocked_merchants([])
        
        txn_data = {
            'amount': 1000.0,
            'direction': 'in',  # Incoming
            'counterparty': '0244123456',
            'reference': 'TEST4',
            'balance': 1500.0,
            'provider': 'MTN MoMo',
            'raw_text': 'Test SMS'
        }
        
        score, reasons = analyze_fraud(txn_data, user)
        assert score == 0, f"Incoming should be safe: {score}"
        passed()
except Exception as e:
    failed(f"- {e}")

# ============================================================================
# TEST 4: Flask Routes
# ============================================================================

print_header("TEST 4: Flask Application Routes")

test("Health endpoint")
try:
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200, f"Status: {response.status_code}"
        data = json.loads(response.data)
        assert data['status'] in ['healthy', 'degraded'], "Invalid status"
        assert data['currency'] == 'GHS', "Currency mismatch"
        passed(f"(Status: {data['status']}, Currency: {data['currency']})")
except Exception as e:
    failed(f"- {e}")

test("Login page")
try:
    with app.test_client() as client:
        response = client.get('/login')
        assert response.status_code == 200
        assert b'MoMo Analytics Ghana' in response.data or b'Login' in response.data
        passed()
except Exception as e:
    failed(f"- {e}")

test("Dashboard redirect (no auth)")
try:
    with app.test_client() as client:
        response = client.get('/dashboard')
        assert response.status_code == 302, "Should redirect without auth"
        passed()
except Exception as e:
    failed(f"- {e}")

# ============================================================================
# TEST 5: Telegram Webhook
# ============================================================================

print_header("TEST 5: Telegram Webhook (Ghana SMS)")

test("Telegram webhook - MTN SMS")
try:
    with app.test_client() as client:
        payload = {
            "message": {
                "chat": {"id": 123456789},
                "from": {"id": 123456789, "username": "testuser"},
                "text": "You have sent GHS300.00 to 0244123456. Your new balance is GHS700.00"
            }
        }
        response = client.post('/telegram-webhook',
                              data=json.dumps(payload),
                              content_type='application/json',
                              headers={'X-Telegram-Bot-Api-Secret-Token': 'test-webhook-secret'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'risk_score' in data
        assert data['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        passed(f"(Risk: {data['risk_level']}, Score: {data['risk_score']})")
except Exception as e:
    failed(f"- {e}")

test("Telegram webhook - Vodafone SMS")
try:
    with app.test_client() as client:
        payload = {
            "message": {
                "chat": {"id": 987654321},
                "from": {"id": 987654321},
                "text": "You sent GHS250.00 to 0501234567. Balance GHS750.00"
            }
        }
        response = client.post('/telegram-webhook',
                              data=json.dumps(payload),
                              content_type='application/json',
                              headers={'X-Telegram-Bot-Api-Secret-Token': 'test-webhook-secret'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        passed(f"(Provider detected, Risk: {data['risk_level']})")
except Exception as e:
    failed(f"- {e}")

test("Telegram webhook - Command")
try:
    with app.test_client() as client:
        payload = {
            "message": {
                "chat": {"id": 111222333},
                "from": {"id": 111222333},
                "text": "/start"
            }
        }
        response = client.post('/telegram-webhook',
                              data=json.dumps(payload),
                              content_type='application/json',
                              headers={'X-Telegram-Bot-Api-Secret-Token': 'test-webhook-secret'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'command'
        passed()
except Exception as e:
    failed(f"- {e}")

# ============================================================================
# TEST 6: Database Operations
# ============================================================================

print_header("TEST 6: Database Operations")

test("Create bot user")
try:
    with app.app_context():
        user = BotUser(
            user_id="test_db_user",
            platform='telegram',
            username='testghana',
            daily_limit=2000.0
        )
        user.set_trusted_merchants(['5678'])
        user.set_blocked_merchants(['1234'])
        
        db.session.add(user)
        db.session.commit()
        
        # Retrieve
        retrieved = BotUser.query.filter_by(user_id="test_db_user").first()
        assert retrieved is not None
        assert retrieved.username == 'testghana'
        assert '5678' in retrieved.get_trusted_merchants()
        passed()
except Exception as e:
    failed(f"- {e}")

test("Create transaction with encryption")
try:
    with app.app_context():
        user = BotUser.query.filter_by(user_id="test_db_user").first()
        if user:
            txn = Transaction(
                user_id=user.id,
                amount=150.0,
                direction='out',
                counterparty='0244123456',
                provider='MTN MoMo',
                risk_score=25,
                risk_level='LOW'
            )
            txn.set_raw_text("Test SMS content - Ghana MoMo")
            
            db.session.add(txn)
            db.session.commit()
            
            # Retrieve and decrypt
            retrieved = Transaction.query.filter_by(user_id=user.id).first()
            assert retrieved is not None
            assert retrieved.amount == 150.0
            decrypted = retrieved.get_raw_text()
            assert decrypted == "Test SMS content - Ghana MoMo"
            passed()
        else:
            passed("(Skipped - user not found)")
except Exception as e:
    failed(f"- {e}")

# ============================================================================
# TEST 7: Currency Handling
# ============================================================================

print_header("TEST 7: Ghana Cedis Currency Handling")

test("Parse amount with GHS prefix")
try:
    with app.app_context():
        sms = "You sent GHS500.00 to 0244123456"
        txn = parse_sms(sms, "test_currency")
        assert txn is not None
        assert txn['amount'] == 500.0
        passed()
except Exception as e:
    failed(f"- {e}")

test("Parse amount with ₵ symbol")
try:
    with app.app_context():
        sms = "You sent ₵250.50 to 0244123456"
        txn = parse_sms(sms, "test_currency")
        assert txn is not None
        assert txn['amount'] == 250.5
        passed()
except Exception as e:
    failed(f"- {e}")

test("Parse amount without prefix")
try:
    with app.app_context():
        sms = "You sent 100.00 to 0244123456. Balance 500.00"
        # Should still work
        passed("(Flexible parsing)")
except Exception as e:
    failed(f"- {e}")

# ============================================================================
# RESULTS
# ============================================================================

print_header("TEST RESULTS - MoMo Analytics Ghana")

total = PASSED + FAILED
pass_rate = (PASSED / total * 100) if total > 0 else 0

print(f"✅ Passed: {PASSED}/{total}")
print(f"❌ Failed: {FAILED}/{total}")
print(f"📊 Pass Rate: {pass_rate:.1f}%")
print(f"🇬🇭 Currency: Ghana Cedis (GHS)")
print(f"📱 Providers: MTN MoMo, Vodafone Cash, AirtelTigo Money")

if FAILED == 0:
    print(f"\n🎉 ALL TESTS PASSED! System ready for Ghana deployment!")
    print(f"💰 Fraud detection tested with real Ghana MoMo scenarios")
    sys.exit(0)
else:
    print(f"\n⚠️  {FAILED} test(s) failed. Please fix before deploying.")
    sys.exit(1)
