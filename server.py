#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import datetime

class DataHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/save-login':
            self.save_login_data()
        elif self.path == '/save-user':
            self.save_user_data()
        elif self.path == '/get-data':
            self.get_data()
        else:
            self.send_error(404)
    
    def do_GET(self):
        if self.path == '/get-data':
            self.get_data()
        else:
            try:
                super().do_GET()
            except BrokenPipeError:
                # Handle broken pipe error gracefully
                pass
            except Exception as e:
                # Log other errors but don't crash
                print(f"Error serving GET request: {e}")
                pass
    
    def save_login_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            print(f"Error reading login data: {e}")
            self.send_error(400, "Invalid request data")
            return
        
        # Baca data yang sudah ada
        try:
            with open('data/login_logs.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {"loginLogs": [], "lastUpdated": None, "totalLogins": 0}
        except Exception as e:
            print(f"Error reading login logs file: {e}")
            existing_data = {"loginLogs": [], "lastUpdated": None, "totalLogins": 0}
        
        # Tambahkan data baru
        login_entry = {
            "id": data.get('id'),
            "email": data.get('email'),
            "password": data.get('password'),
            "name": data.get('name'),
            "platform": data.get('platform'),
            "loginTime": data.get('loginTime'),
            "ipAddress": data.get('ipAddress'),
            "userAgent": data.get('userAgent'),
            "timestamp": data.get('timestamp'),
            "status": data.get('status', 'success')
        }
        
        existing_data["loginLogs"].append(login_entry)
        existing_data["lastUpdated"] = datetime.datetime.now().isoformat()
        existing_data["totalLogins"] = len(existing_data["loginLogs"])
        
        # Simpan ke file
        try:
            with open('data/login_logs.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving login data to file: {e}")
            self.send_error(500, "Internal server error")
            return
        
        # Kirim response
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response = {"status": "success", "message": "Login data saved successfully"}
            self.wfile.write(json.dumps(response).encode())
        except BrokenPipeError:
            # Handle broken pipe error gracefully
            pass
        except Exception as e:
            print(f"Error sending login response: {e}")
            pass
    
    def save_user_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            print(f"Error reading user data: {e}")
            self.send_error(400, "Invalid request data")
            return
        
        # Baca data yang sudah ada
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {"users": [], "lastUpdated": None, "totalUsers": 0}
        except Exception as e:
            print(f"Error reading users file: {e}")
            existing_data = {"users": [], "lastUpdated": None, "totalUsers": 0}
        
        # Tambahkan data baru
        user_entry = {
            "id": data.get('id'),
            "firstName": data.get('firstName'),
            "lastName": data.get('lastName'),
            "username": data.get('username'),
            "email": data.get('email'),
            "password": data.get('password'),
            "phone": data.get('phone'),
            "birthDate": data.get('birthDate'),
            "address": data.get('address'),
            "city": data.get('city'),
            "postalCode": data.get('postalCode'),
            "province": data.get('province'),
            "occupation": data.get('occupation'),
            "referralCode": data.get('referralCode'),
            "registrationDate": data.get('registrationDate'),
            "status": "active"
        }
        
        existing_data["users"].append(user_entry)
        existing_data["lastUpdated"] = datetime.datetime.now().isoformat()
        existing_data["totalUsers"] = len(existing_data["users"])
        
        # Simpan ke file
        try:
            with open('data/users.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving user data to file: {e}")
            self.send_error(500, "Internal server error")
            return
        
        # Kirim response
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response = {"status": "success", "message": "User data saved successfully"}
            self.wfile.write(json.dumps(response).encode())
        except BrokenPipeError:
            # Handle broken pipe error gracefully
            pass
        except Exception as e:
            print(f"Error sending user response: {e}")
            pass
    
    def get_data(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        data_type = query_params.get('type', ['all'])[0]
        
        response_data = {}
        
        if data_type in ['all', 'users']:
            try:
                with open('data/users.json', 'r', encoding='utf-8') as f:
                    response_data['users'] = json.load(f)
            except FileNotFoundError:
                response_data['users'] = {"users": [], "lastUpdated": None, "totalUsers": 0}
            except Exception as e:
                print(f"Error reading users file in get_data: {e}")
                response_data['users'] = {"users": [], "lastUpdated": None, "totalUsers": 0}
        
        if data_type in ['all', 'login_logs']:
            try:
                with open('data/login_logs.json', 'r', encoding='utf-8') as f:
                    response_data['loginLogs'] = json.load(f)
            except FileNotFoundError:
                response_data['loginLogs'] = {"loginLogs": [], "lastUpdated": None, "totalLogins": 0}
            except Exception as e:
                print(f"Error reading login logs file in get_data: {e}")
                response_data['loginLogs'] = {"loginLogs": [], "lastUpdated": None, "totalLogins": 0}
        
        # Kirim response
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
        except BrokenPipeError:
            # Handle broken pipe error gracefully
            pass
        except Exception as e:
            print(f"Error sending data response: {e}")
            pass
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=8000):
    # Buat direktori data jika belum ada
    os.makedirs('data', exist_ok=True)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DataHandler)
    print(f"Server berjalan di http://localhost:{port}")
    print("Tekan Ctrl+C untuk menghentikan server")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 