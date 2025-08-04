// User Management System for MyRepublic
class UserManager {
    constructor() {
        this.users = this.loadUsers();
        this.currentUser = this.loadCurrentUser();
    }
    
    // Load users from localStorage
    loadUsers() {
        return JSON.parse(localStorage.getItem('users') || '[]');
    }
    
    // Load current user from localStorage
    loadCurrentUser() {
        return JSON.parse(localStorage.getItem('currentUser') || 'null');
    }
    
    // Save users to localStorage
    saveUsers() {
        localStorage.setItem('users', JSON.stringify(this.users));
    }
    
    // Save current user to localStorage
    saveCurrentUser(user) {
        localStorage.setItem('currentUser', JSON.stringify(user));
        this.currentUser = user;
    }
    
    // Register new user
    registerUser(userData) {
        // Validate required fields
        const requiredFields = ['firstName', 'lastName', 'username', 'email', 'password', 'phone', 'birthDate', 'address', 'city', 'postalCode', 'province'];
        
        for (let field of requiredFields) {
            if (!userData[field]) {
                throw new Error(`Field ${field} is required`);
            }
        }
        
        // Check if email already exists
        if (this.users.find(user => user.email === userData.email)) {
            throw new Error('Email sudah terdaftar');
        }
        
        // Check if username already exists
        if (this.users.find(user => user.username === userData.username)) {
            throw new Error('Username sudah digunakan');
        }
        
        // Validate password strength
        if (userData.password.length < 8) {
            throw new Error('Password minimal 8 karakter');
        }
        
        // Create new user object
        const newUser = {
            ...userData,
            userId: this.generateUserId(),
            registrationDate: new Date().toISOString(),
            status: 'active',
            lastLogin: null
        };
        
        // Add to users array
        this.users.push(newUser);
        this.saveUsers();
        
        return newUser;
    }
    
    // Login user
    loginUser(email, password) {
        const user = this.users.find(u => u.email === email && u.password === password);
        
        if (!user) {
            throw new Error('Email atau password salah');
        }
        
        // Update last login
        user.lastLogin = new Date().toISOString();
        this.saveUsers();
        
        // Save current user
        this.saveCurrentUser(user);
        
        return user;
    }
    
    // Logout user
    logoutUser() {
        localStorage.removeItem('currentUser');
        this.currentUser = null;
    }
    
    // Get user by ID
    getUserById(userId) {
        return this.users.find(user => user.userId === userId);
    }
    
    // Update user
    updateUser(userId, updateData) {
        const userIndex = this.users.findIndex(user => user.userId === userId);
        
        if (userIndex === -1) {
            throw new Error('User tidak ditemukan');
        }
        
        // Update user data
        this.users[userIndex] = { ...this.users[userIndex], ...updateData };
        this.saveUsers();
        
        return this.users[userIndex];
    }
    
    // Delete user
    deleteUser(userId) {
        const userIndex = this.users.findIndex(user => user.userId === userId);
        
        if (userIndex === -1) {
            throw new Error('User tidak ditemukan');
        }
        
        // Remove user
        this.users.splice(userIndex, 1);
        this.saveUsers();
        
        return true;
    }
    
    // Search users
    searchUsers(searchTerm) {
        const term = searchTerm.toLowerCase();
        return this.users.filter(user => 
            user.firstName?.toLowerCase().includes(term) ||
            user.lastName?.toLowerCase().includes(term) ||
            user.email?.toLowerCase().includes(term) ||
            user.username?.toLowerCase().includes(term) ||
            user.phone?.includes(term)
        );
    }
    
    // Get users by date range
    getUsersByDateRange(startDate, endDate) {
        return this.users.filter(user => {
            const userDate = new Date(user.registrationDate);
            return userDate >= startDate && userDate <= endDate;
        });
    }
    
    // Get statistics
    getStatistics() {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        
        return {
            totalUsers: this.users.length,
            activeUsers: this.users.filter(user => user.status === 'active').length,
            todayUsers: this.users.filter(user => new Date(user.registrationDate) >= today).length,
            monthUsers: this.users.filter(user => new Date(user.registrationDate) >= thisMonth).length
        };
    }
    
    // Generate unique user ID
    generateUserId() {
        return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Validate email format
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Validate phone number
    validatePhone(phone) {
        const phoneRegex = /^(\+62|62|0)8[1-9][0-9]{6,9}$/;
        return phoneRegex.test(phone);
    }
    
    // Check password strength
    checkPasswordStrength(password) {
        let strength = 0;
        let message = '';
        
        if (password.length >= 8) strength++;
        if (password.match(/[a-z]/)) strength++;
        if (password.match(/[A-Z]/)) strength++;
        if (password.match(/[0-9]/)) strength++;
        if (password.match(/[^a-zA-Z0-9]/)) strength++;
        
        if (strength < 3) {
            message = 'Password lemah';
        } else if (strength < 5) {
            message = 'Password sedang';
        } else {
            message = 'Password kuat';
        }
        
        return { strength, message };
    }
    
    // Export users to CSV
    exportToCSV() {
        const headers = ['Nama', 'Username', 'Email', 'Telepon', 'Alamat', 'Kota', 'Provinsi', 'Tanggal Daftar'];
        const csvContent = [
            headers.join(','),
            ...this.users.map(user => [
                `"${user.firstName} ${user.lastName}"`,
                `"${user.username}"`,
                `"${user.email}"`,
                `"${user.phone}"`,
                `"${user.address}"`,
                `"${user.city}"`,
                `"${user.province}"`,
                `"${this.formatDate(user.registrationDate)}"`
            ].join(','))
        ].join('\n');
        
        return csvContent;
    }
    
    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('id-ID', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Check if user is logged in
    isLoggedIn() {
        return this.currentUser !== null;
    }
    
    // Get current user
    getCurrentUser() {
        return this.currentUser;
    }
}

// Initialize user manager
const userManager = new UserManager();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserManager;
} 