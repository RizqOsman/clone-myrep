# MyRepublic Website Clone dengan Sistem Login & Register

Website clone dari MyRepublic Broadband Promo yang dilengkapi dengan sistem login, pendaftaran, dan admin panel (akses langsung via URL).

## 🚀 Fitur Utama

### 1. **Halaman Utama (index-2.html)**
- Landing page MyRepublic dengan desain responsif
- Tombol Login dan Register
- Informasi produk dan promo

### 2. **Admin Panel (admin.html)**
- Dashboard dengan statistik pengguna
- Tabel data pengguna dengan fitur:
  - Pencarian berdasarkan nama, email, username, atau telepon
  - Pagination
  - View detail pengguna
  - Edit pengguna (simulasi)
  - Delete pengguna
- Export data ke CSV
- Responsive design
- **Akses langsung via URL: `localhost:8000/admin`**

### 3. **Sistem Login (login.html)**
- Form login dengan email dan password
- Login dengan Google (simulasi)
- Validasi form
- Redirect otomatis setelah login

### 4. **Sistem Pendaftaran (register.html)**
- Form pendaftaran lengkap dengan field:
  - Nama Depan & Belakang
  - Username
  - Email
  - Password (dengan strength checker)
  - Nomor Telepon
  - Tanggal Lahir
  - Alamat Lengkap
  - Kota, Kode Pos, Provinsi
  - Pekerjaan (opsional)
  - Kode Referral (opsional)
- Validasi form yang komprehensif
- Pendaftaran dengan Google (simulasi)



### 5. **User Management System (js/user-management.js)**
- Class untuk mengelola data pengguna
- CRUD operations (Create, Read, Update, Delete)
- Validasi data
- Local storage management
- Password strength checker
- Email dan phone validation

## 📁 Struktur File

```
ISPclone/
├── index-2.html              # Halaman utama
├── admin.html                # Admin panel (akses via URL)
├── login.html                # Halaman login
├── register.html             # Halaman pendaftaran
├── js/
│   └── user-management.js    # Sistem manajemen user
├── wp-content/               # Asset WordPress
├── wp-includes/              # File WordPress core
└── README.md                 # Dokumentasi ini
```

## 🛠️ Cara Menjalankan

### **Cara 1: Buka File HTML Langsung**
1. Buka file `index-2.html` di browser
2. Website akan langsung berjalan tanpa server

### **Cara 2: Menggunakan Live Server (VS Code)**
1. Install extension "Live Server" di VS Code
2. Klik kanan pada `index-2.html`
3. Pilih "Open with Live Server"

### **Cara 3: Menggunakan Python HTTP Server**
```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000
```
Kemudian buka `http://localhost:8000/index-2.html`

### **Cara 4: Menggunakan Node.js HTTP Server**
```bash
# Install http-server globally
npm install -g http-server

# Jalankan server
http-server -p 8000
```
Kemudian buka `http://localhost:8000/index-2.html`

## 🔐 Cara Menggunakan Sistem

### **1. Pendaftaran User Baru**
1. Buka halaman utama
2. Klik tombol "Daftar"
3. Isi form pendaftaran dengan lengkap
4. Klik "Daftar Sekarang"
5. Data akan tersimpan di localStorage browser

### **2. Login User**
1. Klik tombol "Login" di halaman utama
2. Masukkan email dan password yang sudah didaftarkan
3. Klik "Masuk"
4. Setelah berhasil, akan kembali ke halaman utama

### **3. Akses Admin Panel**
1. Jalankan server lokal (misalnya: `python -m http.server 8000`)
2. Buka browser dan akses: `http://localhost:8000/admin`
3. Lihat statistik pengguna
4. Kelola data pengguna dengan fitur:
   - Pencarian
   - View detail
   - Edit (simulasi)
   - Delete
   - Export CSV



## 💾 Penyimpanan Data

Data pengguna disimpan di **localStorage browser** dengan struktur:

```javascript
// Data users
localStorage.setItem('users', JSON.stringify([
  {
    userId: 'user_1234567890_abc123',
    firstName: 'John',
    lastName: 'Doe',
    username: 'johndoe',
    email: 'john@example.com',
    password: 'password123',
    phone: '08123456789',
    birthDate: '1990-01-01',
    address: 'Jl. Contoh No. 123',
    city: 'Jakarta',
    postalCode: '12345',
    province: 'DKI Jakarta',
    occupation: 'Developer',
    referralCode: '',
    registrationDate: '2025-01-01T00:00:00.000Z',
    status: 'active',
    lastLogin: '2025-01-01T00:00:00.000Z'
  }
]));

// Current user
localStorage.setItem('currentUser', JSON.stringify(userObject));
```

## 🎨 Desain & UI/UX

- **Color Scheme**: Menggunakan warna brand MyRepublic (ungu #662a81, #992f8f)
- **Typography**: Font Poppins untuk konsistensi
- **Responsive**: Desain responsif untuk desktop, tablet, dan mobile
- **Modern UI**: Gradient backgrounds, rounded corners, shadows
- **Interactive**: Hover effects, transitions, animations

## 🔧 Fitur Teknis

### **Validasi Form**
- Email format validation
- Password strength checker
- Required field validation
- Phone number validation (format Indonesia)

### **Security Features**
- Password strength indicator
- Input sanitization
- Duplicate email/username check

### **User Experience**
- Loading states
- Success/error messages
- Auto-redirect after actions
- Responsive design
- Intuitive navigation

## 📱 Responsive Design

Website didesain responsif dengan breakpoints:
- **Desktop**: > 1024px
- **Tablet**: 768px - 1024px
- **Mobile**: < 768px

## 🚀 Deployment

Website ini dapat di-deploy ke:
- **GitHub Pages**
- **Netlify**
- **Vercel**
- **Firebase Hosting**
- **Shared hosting**

## 🔄 Update & Maintenance

### **Menambah User Baru**
1. Buka halaman register
2. Isi form dengan data lengkap
3. Data otomatis tersimpan di localStorage

### **Mengelola Data User**
1. Akses admin panel via `http://localhost:8000/admin`
2. Gunakan fitur search untuk menemukan user
3. View, edit, atau delete user sesuai kebutuhan

### **Export Data**
1. Di admin panel, klik tombol "Export Data"
2. File CSV akan otomatis terdownload
3. Data dapat dibuka di Excel atau Google Sheets



## 🐛 Troubleshooting

### **Data Tidak Tersimpan**
- Pastikan browser mendukung localStorage
- Cek console browser untuk error
- Clear browser cache jika diperlukan

### **Form Tidak Berfungsi**
- Pastikan JavaScript enabled di browser
- Cek console untuk error JavaScript
- Refresh halaman jika diperlukan

### **Admin Panel Tidak Bisa Diakses**
- Pastikan server lokal berjalan (misalnya: `python -m http.server 8000`)
- Akses via URL yang benar: `http://localhost:8000/admin`
- Pastikan sudah ada user yang mendaftar
- Cek localStorage di browser developer tools



## 📞 Support

Untuk bantuan teknis atau pertanyaan:
- Cek console browser untuk error messages
- Pastikan semua file ter-load dengan benar
- Verifikasi struktur folder sesuai dokumentasi

---

**Note**: Ini adalah website demo untuk keperluan pembelajaran. Data disimpan di localStorage browser dan akan hilang jika cache dibersihkan. 