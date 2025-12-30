"""
MoMo SMS Auto-Forwarder - Android Implementation Guide
This provides the architecture and code for automatic SMS detection
"""

# ============================================================================
# SOLUTION OVERVIEW
# ============================================================================

"""
THREE APPROACHES TO AUTO-DETECT MOMO SMS:

1. ANDROID APP (RECOMMENDED)
   - Intercepts SMS in real-time
   - Automatically forwards to WhatsApp bot
   - Best user experience
   
2. ANDROID ACCESSIBILITY SERVICE
   - Reads SMS notifications
   - No SMS permission required
   - Works on all Android versions
   
3. USSD/STK INTEGRATION (ADVANCED)
   - Direct integration with MoMo providers
   - Requires partnership with MTN/Vodafone
   - Most seamless experience
"""

# ============================================================================
# APPROACH 1: ANDROID APP WITH SMS BROADCAST RECEIVER
# ============================================================================

# FILE: AndroidManifest.xml
ANDROID_MANIFEST = """
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.momoanalytics.smsforwarder">

    <!-- Permissions -->
    <uses-permission android:name="android.permission.RECEIVE_SMS" />
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.SEND_SMS" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/AppTheme">
        
        <!-- Main Activity -->
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- SMS Broadcast Receiver -->
        <receiver
            android:name=".MoMoSmsReceiver"
            android:enabled="true"
            android:exported="true"
            android:permission="android.permission.BROADCAST_SMS">
            <intent-filter android:priority="999">
                <action android:name="android.provider.Telephony.SMS_RECEIVED" />
            </intent-filter>
        </receiver>

        <!-- Background Service -->
        <service
            android:name=".MoMoForwarderService"
            android:enabled="true"
            android:exported="false" />

    </application>
</manifest>
"""

# FILE: MoMoSmsReceiver.java
MOMO_SMS_RECEIVER = """
package com.momoanalytics.smsforwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;
import java.util.regex.Pattern;

public class MoMoSmsReceiver extends BroadcastReceiver {
    
    private static final String TAG = "MoMoSmsReceiver";
    
    // MoMo provider sender IDs
    private static final String MTN_SENDER = "MTN";
    private static final String VODAFONE_SENDER = "Vodafone";
    private static final String AIRTELTIGO_SENDER = "AirtelTigo";
    
    // Regex patterns to identify MoMo transaction SMS
    private static final Pattern MOMO_PATTERN = Pattern.compile(
        ".*(sent|received|balance|transfer|momo|mobile money).*",
        Pattern.CASE_INSENSITIVE
    );
    
    @Override
    public void onReceive(Context context, Intent intent) {
        Log.d(TAG, "SMS received");
        
        Bundle bundle = intent.getExtras();
        if (bundle == null) return;
        
        try {
            Object[] pdus = (Object[]) bundle.get("pdus");
            if (pdus == null) return;
            
            for (Object pdu : pdus) {
                SmsMessage smsMessage = SmsMessage.createFromPdu((byte[]) pdu);
                
                String sender = smsMessage.getDisplayOriginatingAddress();
                String messageBody = smsMessage.getMessageBody();
                
                Log.d(TAG, "Sender: " + sender);
                Log.d(TAG, "Message: " + messageBody);
                
                // Check if this is a MoMo SMS
                if (isMoMoSms(sender, messageBody)) {
                    Log.d(TAG, "MoMo SMS detected!");
                    
                    // Forward to WhatsApp bot
                    forwardToWhatsApp(context, messageBody);
                    
                    // Send to backend API (optional backup)
                    sendToBackend(context, sender, messageBody);
                }
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Error processing SMS: " + e.getMessage());
        }
    }
    
    /**
     * Check if SMS is from a MoMo provider
     */
    private boolean isMoMoSms(String sender, String message) {
        // Check sender
        if (sender.contains(MTN_SENDER) || 
            sender.contains(VODAFONE_SENDER) || 
            sender.contains(AIRTELTIGO_SENDER)) {
            return true;
        }
        
        // Check message content
        return MOMO_PATTERN.matcher(message).matches();
    }
    
    /**
     * Forward SMS to WhatsApp bot
     */
    private void forwardToWhatsApp(Context context, String message) {
        Intent serviceIntent = new Intent(context, MoMoForwarderService.class);
        serviceIntent.putExtra("message", message);
        serviceIntent.putExtra("destination", "whatsapp");
        context.startService(serviceIntent);
    }
    
    /**
     * Send SMS to backend API
     */
    private void sendToBackend(Context context, String sender, String message) {
        Intent serviceIntent = new Intent(context, MoMoForwarderService.class);
        serviceIntent.putExtra("sender", sender);
        serviceIntent.putExtra("message", message);
        serviceIntent.putExtra("destination", "api");
        context.startService(serviceIntent);
    }
}
"""

# FILE: MoMoForwarderService.java
MOMO_FORWARDER_SERVICE = """
package com.momoanalytics.smsforwarder;

import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.IBinder;
import android.util.Log;
import org.json.JSONObject;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class MoMoForwarderService extends Service {
    
    private static final String TAG = "MoMoForwarderService";
    private static final String PREFS_NAME = "MoMoAnalyticsPrefs";
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String message = intent.getStringExtra("message");
        String destination = intent.getStringExtra("destination");
        
        if ("whatsapp".equals(destination)) {
            forwardToWhatsApp(message);
        } else if ("api".equals(destination)) {
            String sender = intent.getStringExtra("sender");
            sendToBackendAPI(sender, message);
        }
        
        stopSelf(startId);
        return START_NOT_STICKY;
    }
    
    /**
     * Forward message to WhatsApp bot
     */
    private void forwardToWhatsApp(String message) {
        try {
            // Get user's WhatsApp bot number from preferences
            SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
            String botNumber = prefs.getString("bot_number", "");
            
            if (botNumber.isEmpty()) {
                Log.e(TAG, "Bot number not configured");
                return;
            }
            
            // Open WhatsApp with pre-filled message
            Intent whatsappIntent = new Intent(Intent.ACTION_VIEW);
            String url = "https://api.whatsapp.com/send?phone=" + botNumber + 
                         "&text=" + Uri.encode(message);
            whatsappIntent.setData(Uri.parse(url));
            whatsappIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            
            // Auto-send if user enabled it
            boolean autoSend = prefs.getBoolean("auto_send", false);
            if (autoSend) {
                whatsappIntent.putExtra("sendImmediately", true);
            }
            
            startActivity(whatsappIntent);
            
            Log.d(TAG, "Forwarded to WhatsApp: " + message);
            
        } catch (Exception e) {
            Log.e(TAG, "Error forwarding to WhatsApp: " + e.getMessage());
        }
    }
    
    /**
     * Send SMS to backend API (direct integration)
     */
    private void sendToBackendAPI(String sender, String message) {
        new Thread(() -> {
            try {
                SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
                String apiUrl = prefs.getString("api_url", 
                    "https://your-domain.com/api/sms-webhook");
                String userId = prefs.getString("user_id", "");
                
                URL url = new URL(apiUrl);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                
                // Create JSON payload
                JSONObject json = new JSONObject();
                json.put("user_id", userId);
                json.put("sender", sender);
                json.put("message", message);
                json.put("timestamp", System.currentTimeMillis());
                
                // Send request
                OutputStream os = conn.getOutputStream();
                os.write(json.toString().getBytes());
                os.flush();
                os.close();
                
                int responseCode = conn.getResponseCode();
                Log.d(TAG, "API response code: " + responseCode);
                
                if (responseCode == 200) {
                    Log.d(TAG, "Successfully sent to backend API");
                }
                
                conn.disconnect();
                
            } catch (Exception e) {
                Log.e(TAG, "Error sending to backend: " + e.getMessage());
            }
        }).start();
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
"""

# FILE: MainActivity.java
MAIN_ACTIVITY = """
package com.momoanalytics.smsforwarder;

import android.Manifest;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Switch;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {
    
    private static final int SMS_PERMISSION_CODE = 123;
    private static final String PREFS_NAME = "MoMoAnalyticsPrefs";
    
    private EditText botNumberInput;
    private Switch autoSendSwitch;
    private Button saveButton;
    private SharedPreferences prefs;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        
        // Initialize views
        botNumberInput = findViewById(R.id.bot_number_input);
        autoSendSwitch = findViewById(R.id.auto_send_switch);
        saveButton = findViewById(R.id.save_button);
        
        // Load saved settings
        loadSettings();
        
        // Request SMS permissions
        requestSmsPermissions();
        
        // Save button click
        saveButton.setOnClickListener(v -> saveSettings());
    }
    
    private void requestSmsPermissions() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECEIVE_SMS)
                != PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.READ_SMS)
                != PackageManager.PERMISSION_GRANTED) {
            
            ActivityCompat.requestPermissions(this,
                new String[]{
                    Manifest.permission.RECEIVE_SMS,
                    Manifest.permission.READ_SMS
                },
                SMS_PERMISSION_CODE);
        }
    }
    
    private void loadSettings() {
        String botNumber = prefs.getString("bot_number", "");
        boolean autoSend = prefs.getBoolean("auto_send", false);
        
        botNumberInput.setText(botNumber);
        autoSendSwitch.setChecked(autoSend);
    }
    
    private void saveSettings() {
        String botNumber = botNumberInput.getText().toString().trim();
        boolean autoSend = autoSendSwitch.isChecked();
        
        if (botNumber.isEmpty()) {
            Toast.makeText(this, "Please enter WhatsApp bot number", 
                Toast.LENGTH_SHORT).show();
            return;
        }
        
        // Save to preferences
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString("bot_number", botNumber);
        editor.putBoolean("auto_send", autoSend);
        editor.apply();
        
        Toast.makeText(this, "Settings saved!", Toast.LENGTH_SHORT).show();
    }
    
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, 
                                          int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        
        if (requestCode == SMS_PERMISSION_CODE) {
            if (grantResults.length > 0 && 
                grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "SMS permissions granted", 
                    Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "SMS permissions required for auto-detection", 
                    Toast.LENGTH_LONG).show();
            }
        }
    }
}
"""

# FILE: activity_main.xml (Layout)
LAYOUT_XML = """
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="24dp">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="MoMo Analytics Auto-Forwarder"
        android:textSize="24sp"
        android:textStyle="bold"
        android:layout_marginBottom="32dp" />

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="WhatsApp Bot Number"
        android:textSize="16sp"
        android:layout_marginBottom="8dp" />

    <EditText
        android:id="@+id/bot_number_input"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="+233XXXXXXXXX"
        android:inputType="phone"
        android:layout_marginBottom="24dp" />

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:layout_marginBottom="32dp">

        <TextView
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="Auto-send to WhatsApp"
            android:textSize="16sp" />

        <Switch
            android:id="@+id/auto_send_switch"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content" />
    </LinearLayout>

    <Button
        android:id="@+id/save_button"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Save Settings"
        android:textSize="16sp" />

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="How it works:"
        android:textStyle="bold"
        android:textSize="16sp"
        android:layout_marginTop="32dp"
        android:layout_marginBottom="8dp" />

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="1. App detects MoMo SMS automatically\\n2. Forwards to your WhatsApp bot\\n3. Get instant fraud alerts\\n4. All happens in the background"
        android:textSize="14sp"
        android:lineSpacingExtra="4dp" />

</LinearLayout>
"""

print("Android SMS Auto-Forwarder Implementation Complete!")
