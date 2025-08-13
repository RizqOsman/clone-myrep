#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import datetime
from database import Database

class DataHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = Database()
        super().__init__(*args, **kwargs)
    
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
        elif self.path == '/get-login-logs':
            self.get_login_logs()
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
    
    def get_login_logs(self):
        """Endpoint untuk mengambil data login logs"""
        try:
            login_logs = self.db.get_login_logs()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response = {"status": "success", "data": login_logs}
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            print(f"Error sending login logs: {e}")
            self.send_error(500, "Internal server error")
    
    def save_login_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            print(f"Error reading login data: {e}")
            self.send_error(400, "Invalid request data")
            return
        
        # Simpan ke database
        success = self.db.save_login_log(data)
        
        if not success:
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
        
        # Simpan ke database
        success = self.db.save_user(data)
        
        if not success:
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
            response_data['users'] = self.db.get_all_users()
        
        if data_type in ['all', 'login_logs']:
            response_data['loginLogs'] = self.db.get_all_login_logs()
        
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