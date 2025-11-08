# Magento & Server Password Rotation Script

## 📋 Overview

A robust Python script designed to automate password rotation across Magento admin panels, Virtualmin control panels, and MySQL databases. This tool provides a secure, interactive way to manage credentials across multiple system components with comprehensive logging and email notification capabilities.

## 🎯 Purpose

- **Automate password rotation** for security compliance and access management
- **Centralize credential management** across multiple systems
- **Generate secure passwords** automatically
- **Create professional email drafts** for credential distribution
- **Maintain audit trails** with detailed logging

## 🛠️ Supported Systems

### 1. Magento Admin Panel
- Updates passwords for multiple admin users
- Uses n98-magerun2 for Magento operations
- Supports multiple Magento installations

### 2. Virtualmin Control Panel
- Updates Virtualmin user passwords
- Affects SSH, SFTP, and web control panel access

### 3. MySQL Database
- Rotates database user passwords
- Automatically updates Magento configuration files
- Creates backup of configuration before changes

## ⚙️ Configuration

### Core Settings (Edit in Config class)

```python
class Config:
    # Magento Admin Users
    MAGENTO_USERS = ["user1", "user2", "user3"]
    
    # Virtualmin Configuration
    VIRTUALMIN_DOMAIN = "yourdomain.com"
    VIRTUALMIN_USER = "your_virtualmin_user"
    
    # MySQL Configuration
    MYSQL_USER = "magentouser"
    MYSQL_HOST = "localhost"
    
    # Server Details (for email templates)
    SERVER_IP = "your.server.ip"
    SSH_PORT = "22"
    MAGENTO_URL = "https://yoursite.com/admin"
    VIRTUALMIN_URL = "https://yourdomain.com:10000"
    DB_NAME = "your_database"
    DB_USER = "your_db_user"
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.6+
- Root access
- n98-magerun2.phar in Magento root
- Virtualmin installed
- MySQL/MariaDB

### Quick Start
```bash
# Clone or download the script
cd /path/to/script

# Make executable
chmod +x password_rotation.py

# Run as root
sudo ./password_rotation.py
```

## 🚀 Usage

### Interactive Menu System
The script provides a clean menu interface:

```
Password Update Menu
==================================================
1. Update Magento Admin Passwords
2. Update Virtualmin Password
3. Update MySQL Database Password
4. Update ALL Passwords
5. Show Current Configuration
6. Exit and Generate Email Draft
==================================================
```

### Operation Flow
1. **Auto-detects** Magento installations
2. **Validates** system configuration
3. **Generates** secure passwords (16 characters)
4. **Requests confirmation** before each operation
5. **Executes changes** with proper error handling
6. **Generates email drafts** with updated credentials

## 🔒 Security Features

### Password Generation
- **Length**: 16 characters
- **Character Set**: A-Z, a-z, 0-9, -_+=@~.
- **Excluded Characters**: !$&*#'"\|;<>()[]{} (shell-safe)
- **Strength**: 72^16 possible combinations

### Safety Measures
- **Shell-safe passwords** prevent command injection
- **Multiple confirmation prompts** prevent accidental changes
- **Comprehensive logging** for audit trails
- **Configuration backups** before modifications

## 📧 Email System

### Smart Draft Generation
- **Only includes updated sections** (no empty credentials)
- **Professional formatting** ready for distribution
- **Automatic file saving** to `/tmp/password_update_email_*.txt`
- **Section tracking** shows what was actually changed

### Email Template Includes
- Virtualmin/SSH/SFTP credentials
- Database access information
- Magento admin user credentials
- Generation timestamp and log reference

## 🗄️ Logging & Monitoring

### Log Files
- **Location**: `/tmp/password_update_YYYYMMDD_HHMMSS.log`
- **Content**: All operations, commands, errors, and timestamps
- **Retention**: Manual cleanup required

### Error Handling
- **Continues on individual failures**
- **Clear error messages** with troubleshooting info
- **Graceful recovery** from partial failures

## 🔍 Technical Details

### Commands Used
```bash
# Magento password update
su - user -c 'cd /path/to/magento && php n98-magerun2.phar admin:user:change-password username password'

# Virtualmin password update
virtualmin modify-domain --domain domain.com --pass password

# MySQL password update
mysql -e 'ALTER USER "user"@"host" IDENTIFIED BY "password"; FLUSH PRIVILEGES;'

# Magento config update
sed -i "s/'password' => '.*'/'password' => 'new_password'/" app/etc/env.php
```

### File Structure
```
/path/to/magento/
├── app/etc/env.php              # Magento configuration
├── n98-magerun2.phar           # Magento CLI tool
└── var/log/                    # Magento logs (if enabled)

/tmp/
├── password_update_*.log       # Script execution logs
└── password_update_email_*.txt # Generated email drafts
```

## ⚠️ Important Notes

### Requirements
- Must be run as **root** user
- Requires **working Magento installation**
- Needs **n98-magerun2.phar** in Magento root
- **Virtualmin access** for control panel updates

### Safety Considerations
- **Test in staging** before production use
- **Backup configurations** before mass updates
- **Verify email recipients** before sending credentials
- **Monitor logs** for any issues

## 🆘 Troubleshooting

### Common Issues
1. **Permission denied errors**
   - Ensure script is run as root
   - Verify Magento file permissions

2. **n98-magerun2 not found**
   - Download to Magento root directory
   - Ensure PHP is installed and working

3. **MySQL connection failures**
   - Verify MySQL user exists
   - Check current password in env.php

4. **Virtualmin command failures**
   - Confirm Virtualmin is installed
   - Verify domain and user exist

### Debug Mode
Check the log file for detailed execution information:
```bash
tail -f /tmp/password_update_*.log
```

---

**Note**: This tool is designed for system administrators with appropriate access rights. Always follow your organization's security policies and change management procedures.
