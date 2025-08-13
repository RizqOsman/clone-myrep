#!/usr/bin/env python3
"""
Script untuk melihat isi database SQLite
"""

import sqlite3
import json
from database import Database

def view_database():
    """Menampilkan isi database SQLite"""
    db_path = 'data/ispclone.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== DATABASE SQLITE ISPCLONE ===\n")
        
        # Tampilkan tabel users
        print("📋 TABEL USERS:")
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Total users: {user_count}")
        
        if user_count > 0:
            cursor.execute("SELECT id, first_name, last_name, email, created_at FROM users ORDER BY created_at DESC LIMIT 5")
            users = cursor.fetchall()
            print("5 user terbaru:")
            for user in users:
                print(f"  - {user[1]} {user[2]} ({user[3]}) - {user[4]}")
        
        print("\n" + "="*50 + "\n")
        
        # Tampilkan tabel login_logs
        print("🔐 TABEL LOGIN LOGS:")
        cursor.execute("SELECT COUNT(*) FROM login_logs")
        log_count = cursor.fetchone()[0]
        print(f"Total login logs: {log_count}")
        
        if log_count > 0:
            cursor.execute("SELECT id, email, platform, login_time, created_at FROM login_logs ORDER BY created_at DESC LIMIT 5")
            logs = cursor.fetchall()
            print("5 login log terbaru:")
            for log in logs:
                print(f"  - {log[1]} ({log[2]}) - {log[3]}")
        
        conn.close()
        
    except FileNotFoundError:
        print("❌ Database belum dibuat. Jalankan server terlebih dahulu atau jalankan migrate_to_sqlite.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def view_raw_data():
    """Menampilkan data mentah dari database"""
    db = Database()
    
    print("\n=== DATA MENTAH DARI DATABASE ===\n")
    
    # Tampilkan semua users
    users_data = db.get_all_users()
    print("USERS:")
    print(json.dumps(users_data, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Tampilkan semua login logs
    logs_data = db.get_all_login_logs()
    print("LOGIN LOGS:")
    print(json.dumps(logs_data, indent=2))

if __name__ == "__main__":
    view_database()
    print("\n" + "="*50)
    view_raw_data()

