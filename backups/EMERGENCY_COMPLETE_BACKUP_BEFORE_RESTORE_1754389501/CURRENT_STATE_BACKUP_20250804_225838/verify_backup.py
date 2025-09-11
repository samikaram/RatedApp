#!/usr/bin/env python3
"""
Quick verification script for RatedApp backup
Run this to verify backup integrity
"""
import os
import sqlite3

def verify_backup():
    print("🔍 VERIFYING RATEDAPP BACKUP...")
    
    # Check critical files
    critical_files = [
        'patient_rating/models.py',
        'patient_rating/views.py', 
        'patient_rating/admin.py',
        'patient_rating/templates/patient_rating/unified_dashboard.html',
        'db.sqlite3'
    ]
    
    missing_files = []
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All critical files present")
    
    # Check database
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'patient_rating_%'")
        tables = cursor.fetchall()
        print(f"✅ Database: {len(tables)} patient_rating tables found")
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Check template size (should be ~47KB)
    template_path = 'patient_rating/templates/patient_rating/unified_dashboard.html'
    if os.path.exists(template_path):
        size = os.path.getsize(template_path)
        print(f"✅ Template size: {size:,} characters")
        if size < 40000:
            print("⚠️ Template seems smaller than expected")
    
    print("🎉 BACKUP VERIFICATION COMPLETE")
    return True

if __name__ == "__main__":
    verify_backup()
