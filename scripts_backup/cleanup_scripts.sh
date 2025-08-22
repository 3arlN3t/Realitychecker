#!/bin/bash

# Script Cleanup - Remove redundant and unnecessary scripts
echo "🧹 Cleaning up redundant scripts..."

# Create backup directory
mkdir -p scripts_backup
echo "📦 Creating backup in scripts_backup/"

# Backup all scripts before deletion
cp *.py scripts_backup/ 2>/dev/null || true
cp *.sh scripts_backup/ 2>/dev/null || true

# Remove duplicate startup scripts
echo "Removing duplicate startup scripts..."
rm -f dev.sh
rm -f init_db.py

# Remove debug scripts (created for specific debugging sessions)
echo "Removing debug scripts..."
rm -f debug_*.py
rm -f test_pdf_auth.py

# Remove redundant test scripts
echo "Removing redundant test scripts..."
rm -f test_development.py
rm -f test_whatsapp_bot.py
rm -f test_text_message.py
rm -f test_twilio.py
rm -f test_twilio_auth.py
rm -f test_twilio_message.py
rm -f test_twilio_direct.py
rm -f test_twilio_download.py
rm -f test_real_scenario.py
rm -f test_url_recognition.py
rm -f test_error_handling_fix.py
rm -f test_webhook_flow.py
rm -f test_webhook_pdf.py

# Remove one-time fix scripts
echo "Removing one-time fix scripts..."
rm -f fix_security_validation.py
rm -f update_sandbox_webhook.py
rm -f update_webhook_url.py
rm -f configure_webhook.py
rm -f create_test_job_pdf.py
rm -f check_twilio_setup.py

# Remove specific debug files
echo "Removing debug phone validation scripts..."
rm -f debug_phone_validation.py
rm -f debug_real_phone.py
rm -f debug_actual_download.py

echo "✅ Cleanup complete!"
echo ""
echo "📊 Scripts remaining (essential only):"
ls -la *.py *.sh 2>/dev/null | grep -E '\.(py|sh)$' || echo "No scripts found"$' || echo "No scripts found"
echo ""
echo "📦 Backup created in: scripts_backup/"
echo "🗑️  You can safely delete scripts_backup/ after verifying everything works"