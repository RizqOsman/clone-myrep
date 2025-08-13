#!/usr/bin/env python3
"""
Script untuk migrasi data dari JSON ke SQLite
"""

from database import Database

def main():
    print("Memulai migrasi data dari JSON ke SQLite...")
    
    # Inisialisasi database
    db = Database()
    
    # Jalankan migrasi
    db.migrate_from_json()
    
    print("Migrasi selesai!")
    print("Database SQLite telah dibuat di: data/ispclone.db")
    
    # Tampilkan statistik
    users_data = db.get_all_users()
    logs_data = db.get_all_login_logs()
    
    print(f"\nStatistik setelah migrasi:")
    print(f"- Total Users: {users_data['totalUsers']}")
    print(f"- Total Login Logs: {logs_data['totalLogins']}")

if __name__ == "__main__":
    main()

