#!/usr/bin/env python3
"""
Magento & Server Password Update Script
Final robust version with auto n98-magerun2 download
"""

import os
import sys
import subprocess
import random
import string
import logging
from datetime import datetime
from pathlib import Path
import re
import shlex

# Configuration
class Config:
    MAGENTO_USERS = ["yasmin.ahmed", "vinod.jaiswal", "deepika", "alex", "amit.mishra", "Smartfeed"]
    VIRTUALMIN_DOMAIN = "smartcellular.com"
    VIRTUALMIN_USER = "smartcellular"
    MYSQL_USER = "magentouser"
    MYSQL_HOST = "localhost"
    N98_MAGERUN_PATH = "n98-magerun2.phar"
    N98_MAGERUN_URL = "https://files.magerun.net/n98-magerun2.phar"
    
    # Server details for email
    SERVER_IP = "18.133.102.195"
    SSH_PORT = "2283"
    MAGENTO_URL = "https://www.smartcellular.co.uk/ServerAdmin/"
    VIRTUALMIN_URL = "https://18-133-102-195.hyperxapps.com:10000"
    DB_NAME = "smrtcell_db"
    DB_USER = "smart_usr"

class PasswordManager:
    def __init__(self):
        self.magento_root = ""
        self.magento_env_file = ""
        self.log_file = f"/tmp/password_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.password_changes = {
            "virtualmin": {"password": "", "updated": False},
            "mysql": {"password": "", "updated": False},
            "magento_users": {}
        }
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_message(self, message):
        """Log message with timestamp"""
        self.logger.info(message)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

    def run_command(self, command, shell=False):
        """Run shell command and return success status"""
        try:
            self.logger.info(f"Executing: {command}")
            if shell:
                # Use subprocess with proper escaping for shell commands
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, executable='/bin/bash')
            else:
                # Use list format for non-shell commands
                result = subprocess.run(shlex.split(command), check=True, capture_output=True, text=True)
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.stderr if e.stderr else str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error executing command: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def prompt_yes_no(self, question):
        """Prompt for yes/no confirmation"""
        while True:
            try:
                response = input(f"{question} (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    print("Please answer with 'y' or 'n'")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled by user")
                return False

    def prompt_input(self, question, default=None):
        """Prompt for input with optional default"""
        try:
            if default:
                question = f"{question} [{default}]: "
            else:
                question = f"{question}: "
            
            response = input(question).strip()
            return response if response else default
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user")
            return None

    def generate_safe_password(self, length=16):
        """Generate strong random password WITHOUT problematic shell characters"""
        # SAFE characters only - no !, $, &, *, #, ', ", `, \, |, ;, <, >, (, ), [, ], {, }
        upper = string.ascii_uppercase
        lower = string.ascii_lowercase
        digits = string.digits
        # Only safe special characters that don't break shell commands
        safe_special = "-_+=@~."
        
        all_chars = upper + lower + digits + safe_special
        
        # Ensure password has at least one of each type
        password = [
            random.choice(upper),
            random.choice(lower),
            random.choice(digits),
            random.choice(safe_special)
        ]
        
        # Fill remaining characters
        password.extend(random.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle and join
        random.shuffle(password)
        return ''.join(password)

    def detect_magento_root(self):
        """Detect Magento root directory"""
        print("=== Magento Directory Detection ===")
        
        common_paths = [
            f"/home/{Config.VIRTUALMIN_USER}/public_html",
            f"/home/{Config.VIRTUALMIN_USER}/domains/{Config.VIRTUALMIN_DOMAIN}/public_html",
            "/home/deepak-1.hyperx.cloud/public_html",
            "/home/smartcellular/public_html",
            "/var/www/html",
            str(Path.cwd())
        ]
        
        detected_paths = []
        for path in common_paths:
            env_file = Path(path) / "app/etc/env.php"
            if env_file.exists():
                detected_paths.append(path)
                print(f"Found Magento at: {path}")
        
        if detected_paths:
            print("\nDetected Magento installations:")
            for i, path in enumerate(detected_paths, 1):
                print(f"{i}. {path}")
            
            while True:
                try:
                    choice = self.prompt_input(f"Select installation (1-{len(detected_paths)})", "1")
                    if choice is None:
                        return False
                    selected_index = int(choice) - 1
                    if 0 <= selected_index < len(detected_paths):
                        self.magento_root = detected_paths[selected_index]
                        self.magento_env_file = str(Path(self.magento_root) / "app/etc/env.php")
                        return True
                    else:
                        print(f"Please enter a number between 1 and {len(detected_paths)}")
                except ValueError:
                    print("Please enter a valid number")
        else:
            print("No Magento installations auto-detected")
            return self.manual_magento_path()

    def manual_magento_path(self):
        """Manual Magento path input"""
        while True:
            path = self.prompt_input("Please enter Magento root directory")
            if path is None:
                return False
            if not path:
                print("Magento root directory is required")
                continue
            
            path = path.rstrip('/')
            env_file = Path(path) / "app/etc/env.php"
            
            if not env_file.exists():
                print("Magento env.php not found at this location")
                continue
            
            self.magento_root = path
            self.magento_env_file = str(env_file)
            return True

    def get_magento_owner(self):
        """Extract username from Magento path"""
        parts = self.magento_root.split('/')
        return parts[2] if len(parts) > 2 else None

    def download_n98_magerun(self):
        """Download n98-magerun2 to Magento root directory"""
        magento_owner = self.get_magento_owner()
        if not magento_owner:
            print("ERROR: Cannot determine Magento owner for download")
            return False
        
        print(f"📥 Downloading n98-magerun2.phar to {self.magento_root}...")
        
        # Download commands
        download_cmd = f"su - {magento_owner} -c 'cd {shlex.quote(self.magento_root)} && wget -q {Config.N98_MAGERUN_URL} -O {Config.N98_MAGERUN_PATH}'"
        chmod_cmd = f"su - {magento_owner} -c 'cd {shlex.quote(self.magento_root)} && chmod +x {Config.N98_MAGERUN_PATH}'"
        
        # Execute download and setup
        download_success, download_output = self.run_command(download_cmd, shell=True)
        if not download_success:
            print(f"❌ Failed to download n98-magerun2.phar: {download_output}")
            return False
        
        chmod_success, chmod_output = self.run_command(chmod_cmd, shell=True)
        if not chmod_success:
            print(f"❌ Downloaded but failed to make executable: {chmod_output}")
            return False
        
        # Verify the download worked
        n98_path = Path(self.magento_root) / Config.N98_MAGERUN_PATH
        if n98_path.exists():
            print("✅ Successfully downloaded n98-magerun2.phar")
            
            # Test if it works
            test_cmd = f"su - {magento_owner} -c 'cd {shlex.quote(self.magento_root)} && php {Config.N98_MAGERUN_PATH} --version'"
            test_success, test_output = self.run_command(test_cmd, shell=True)
            
            if test_success:
                print("✅ n98-magerun2.phar is working correctly")
                return True
            else:
                print("❌ n98-magerun2.phar downloaded but not working")
                return False
        else:
            print("❌ Download completed but file not found")
            return False

    def validate_n98_magerun(self):
        """Validate n98-magerun2 is available and working, download if missing"""
        n98_path = Path(self.magento_root) / Config.N98_MAGERUN_PATH
        
        # Check if n98-magerun exists and is working
        if n98_path.exists():
            # Test n98-magerun
            magento_owner = self.get_magento_owner()
            if not magento_owner:
                print("Cannot determine Magento owner")
                return False
                
            test_cmd = f"su - {magento_owner} -c 'cd {shlex.quote(self.magento_root)} && php {Config.N98_MAGERUN_PATH} --version'"
            success, output = self.run_command(test_cmd, shell=True)
            
            if success:
                print("✅ n98-magerun2.phar is working")
                return True
            else:
                print("⚠️ n98-magerun2.phar exists but not working. Reinstalling...")
        
        # Download n98-magerun2 if missing or not working
        print("n98-magerun2.phar not found. Downloading...")
        return self.download_n98_magerun()

    def validate_configuration(self):
        """Validate system configuration"""
        print("=== System Validation ===")
        
        # Check Magento root
        if not Path(self.magento_root).exists():
            print("❌ ERROR: Magento root directory not found")
            return False
        else:
            print("✅ Magento root directory exists")
        
        # Check env.php
        if not Path(self.magento_env_file).exists():
            print("❌ ERROR: Magento env.php not found")
            return False
        else:
            print("✅ Magento env.php exists")
        
        # Check Magento owner
        magento_owner = self.get_magento_owner()
        if not magento_owner:
            print("❌ ERROR: Could not determine Magento owner")
            return False
        else:
            print(f"✅ Magento owner: {magento_owner}")
        
        # Validate n98-magerun (this will auto-download if missing)
        if not self.validate_n98_magerun():
            return False
        
        print("✅ All system checks passed")
        return True

    def update_magento_passwords(self):
        """Update Magento admin passwords"""
        print("=== Update Magento Admin Passwords ===")
        
        # Show users that will be updated
        print("The following users will be updated:")
        for user in Config.MAGENTO_USERS:
            print(f"  - {user}")
        
        # Ask for confirmation
        if not self.prompt_yes_no("Do you want to update passwords for these Magento users?"):
            print("Magento password updates cancelled")
            return
        
        # Generate SAFE passwords
        passwords = {}
        print("Generating safe passwords...")
        for user in Config.MAGENTO_USERS:
            passwords[user] = self.generate_safe_password(16)
        
        # Show generated passwords
        print("Generated passwords (safe characters only):")
        for user, password in passwords.items():
            print(f"  {user}: {password}")
        
        # Final confirmation before making changes
        if not self.prompt_yes_no("CONFIRM: Update these Magento user passwords now?"):
            print("Magento password updates cancelled")
            return
        
        # Update each user
        magento_owner = self.get_magento_owner()
        if not magento_owner:
            print("ERROR: Cannot determine Magento owner")
            return
            
        success_count = 0
        
        for user, password in passwords.items():
            print(f"Updating password for {user}...")
            
            # Use HEREDOC style to avoid all shell escaping issues
            cmd = f"""su - {magento_owner} << 'EOF'
cd {shlex.quote(self.magento_root)}
php {Config.N98_MAGERUN_PATH} admin:user:change-password {shlex.quote(user)} {shlex.quote(password)}
EOF"""
            
            success, output = self.run_command(cmd, shell=True)
            
            if success and "Password successfully changed" in output:
                print(f"✅ Successfully updated password for {user}")
                self.password_changes["magento_users"][user] = password
                success_count += 1
            else:
                print(f"❌ Failed to update password for {user}")
                if output:
                    # Show only first line of error to avoid clutter
                    error_line = output.split('\n')[0] if output else "Unknown error"
                    print(f"Error: {error_line}")
        
        print(f"📊 Summary: {success_count}/{len(Config.MAGENTO_USERS)} users updated successfully")

    def update_virtualmin_password(self):
        """Update Virtualmin password"""
        print("=== Update Virtualmin Password ===")
        
        print(f"Domain: {Config.VIRTUALMIN_DOMAIN}")
        print(f"User: {Config.VIRTUALMIN_USER}")
        
        # Ask for confirmation
        if not self.prompt_yes_no(f"Do you want to update Virtualmin password for {Config.VIRTUALMIN_USER}?"):
            print("Virtualmin password update cancelled")
            return
        
        # Generate SAFE password
        new_password = self.generate_safe_password(16)
        print(f"Generated password: {new_password}")
        
        # Final confirmation
        if not self.prompt_yes_no("CONFIRM: Update Virtualmin password now?"):
            print("Virtualmin password update cancelled")
            return
        
        # Use list format to avoid shell escaping issues
        cmd = ["virtualmin", "modify-domain", "--domain", Config.VIRTUALMIN_DOMAIN, "--pass", new_password]
        
        success, output = self.run_command(" ".join(shlex.quote(arg) for arg in cmd), shell=False)
        
        if success:
            print(f"✅ Successfully updated Virtualmin password for {Config.VIRTUALMIN_USER}")
            self.password_changes["virtualmin"]["password"] = new_password
            self.password_changes["virtualmin"]["updated"] = True
        else:
            print(f"❌ Failed to update Virtualmin password for {Config.VIRTUALMIN_USER}")

    def update_database_password(self):
        """Update MySQL database password"""
        print("=== Update MySQL Database Password ===")
        
        print(f"MySQL User: {Config.MYSQL_USER}")
        print(f"MySQL Host: {Config.MYSQL_HOST}")
        print(f"Magento Env File: {self.magento_env_file}")
        
        # Ask for confirmation
        if not self.prompt_yes_no(f"Do you want to update MySQL password for {Config.MYSQL_USER}?"):
            print("MySQL password update cancelled")
            return
        
        # Generate SAFE password
        new_password = self.generate_safe_password(16)
        print(f"Generated password: {new_password}")
        
        # Final confirmation
        if not self.prompt_yes_no("CONFIRM: Update MySQL password and Magento configuration now?"):
            print("MySQL password update cancelled")
            return
        
        # Use single quotes for MySQL command with safe password
        mysql_cmd = f"mysql -e 'ALTER USER \"{Config.MYSQL_USER}\"@\"{Config.MYSQL_HOST}\" IDENTIFIED BY \"{new_password}\"; FLUSH PRIVILEGES;'"
        
        success, output = self.run_command(mysql_cmd, shell=True)
        
        if not success:
            print(f"❌ Failed to update MySQL password for {Config.MYSQL_USER}")
            if output:
                print(f"Error: {output}")
            return
        
        print(f"✅ Successfully updated MySQL password for {Config.MYSQL_USER}")
        
        # Update Magento env.php
        print("Updating Magento configuration file...")
        
        # Create backup
        backup_file = f"{self.magento_env_file}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        backup_success, backup_output = self.run_command(f"cp {shlex.quote(self.magento_env_file)} {shlex.quote(backup_file)}", shell=True)
        
        if backup_success:
            print(f"Created backup: {backup_file}")
        else:
            print(f"Warning: Failed to create backup: {backup_output}")
        
        # Update password in env.php using Python for reliability
        try:
            with open(self.magento_env_file, 'r') as f:
                content = f.read()
            
            # Use regex to find and replace the password line
            pattern = r"('password' => ')(.*?)(')"
            new_content = re.sub(pattern, f"'password' => '{new_password}'", content)
            
            with open(self.magento_env_file, 'w') as f:
                f.write(new_content)
            
            print("✅ Successfully updated Magento configuration file")
            self.password_changes["mysql"]["password"] = new_password
            self.password_changes["mysql"]["updated"] = True
        except Exception as e:
            print(f"❌ Failed to update Magento configuration file: {e}")
            print("The MySQL password was updated but the config file was not.")
            print(f"Please manually update {self.magento_env_file} with the new password.")

    def update_all_passwords(self):
        """Update all passwords"""
        print("=== Update All Passwords ===")
        
        print("This will update:")
        print("  - All Magento admin users")
        print("  - Virtualmin user")
        print("  - MySQL database user")
        print("  - Magento configuration file")
        
        # Ask for confirmation
        if not self.prompt_yes_no("Do you want to update ALL passwords?"):
            print("All operations cancelled")
            return
        
        # Final warning confirmation
        if not self.prompt_yes_no("FINAL WARNING: This will change multiple system passwords. Continue?"):
            print("All operations cancelled")
            return
        
        # Execute each operation with user confirmation at each step
        print("\n" + "="*50)
        self.update_magento_passwords()
        
        print("\n" + "="*50)
        self.update_virtualmin_password()
        
        print("\n" + "="*50)
        self.update_database_password()
        
        print("\n" + "="*50)
        print("All password updates completed")

    def show_configuration(self):
        """Display current configuration"""
        print("=== Current Configuration ===")
        print(f"Magento Root: {self.magento_root}")
        print(f"Magento Env File: {self.magento_env_file}")
        magento_owner = self.get_magento_owner()
        print(f"Magento Owner: {magento_owner if magento_owner else 'Unknown'}")
        print(f"Log File: {self.log_file}")
        print(f"Magento Users: {', '.join(Config.MAGENTO_USERS)}")
        print(f"Virtualmin User: {Config.VIRTUALMIN_USER}")
        print(f"MySQL User: {Config.MYSQL_USER}")

    def generate_email_draft(self):
        """Generate email draft with only updated sections"""
        email_sections = []
        
        # Check what was updated
        virtualmin_updated = self.password_changes["virtualmin"]["updated"]
        mysql_updated = self.password_changes["mysql"]["updated"]
        magento_updated = bool(self.password_changes["magento_users"])
        
        # If nothing was updated, return None
        if not virtualmin_updated and not mysql_updated and not magento_updated:
            return None
        
        email_content = "Hi,\n\nPlease find the new server credentials as below:\n\n"
        
        # Virtualmin section - only if updated
        if virtualmin_updated:
            email_content += f"""Virtualmin:
=================================
URL: {Config.VIRTUALMIN_URL}
User: {Config.VIRTUALMIN_USER}
Password: {self.password_changes["virtualmin"]["password"]}
=================================

SSH
=============================
IP: {Config.SERVER_IP}
User: {Config.VIRTUALMIN_USER}
Password: {self.password_changes["virtualmin"]["password"]}
Port: {Config.SSH_PORT}
=============================

SFTP
=============================
Host: sftp://{Config.SERVER_IP}
User: {Config.VIRTUALMIN_USER}
Password: {self.password_changes["virtualmin"]["password"]}
Port: {Config.SSH_PORT}
=============================

"""

        # Database section - only if updated
        if mysql_updated:
            email_content += f"""Database
=================================
DB_user: {Config.DB_USER}
Password: {self.password_changes["mysql"]["password"]}
DB_name: {Config.DB_NAME}
=================================

"""

        # Magento users section - only if any were updated
        if magento_updated:
            email_content += f"""Magento Users:
================================
URL: {Config.MAGENTO_URL}
"""
            # Add only updated Magento users
            for user in Config.MAGENTO_USERS:
                if user in self.password_changes["magento_users"]:
                    password = self.password_changes["magento_users"][user]
                    email_content += f"""
username: {user}
Password: {password}
"""
            email_content += "================================\n"

        # Add footer
        email_content += f"""
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Log file: {self.log_file}

Best regards,
System Administrator
"""
        return email_content

    def save_email_draft(self):
        """Save email draft to file and display it"""
        email_content = self.generate_email_draft()
        if not email_content:
            print("No password changes were made during this session.")
            return
        
        # Save to file
        email_file = f"/tmp/password_update_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(email_file, 'w') as f:
                f.write(email_content)
            
            print("\n" + "="*70)
            print("EMAIL DRAFT GENERATED SUCCESSFULLY")
            print("="*70)
            
            # Show what was updated
            updates = []
            if self.password_changes["virtualmin"]["updated"]:
                updates.append("Virtualmin/SSH/SFTP")
            if self.password_changes["mysql"]["updated"]:
                updates.append("MySQL Database")
            if self.password_changes["magento_users"]:
                updated_magento_count = len(self.password_changes["magento_users"])
                updates.append(f"Magento Users ({updated_magento_count} users)")
            
            print(f"Sections updated: {', '.join(updates)}")
            print(f"Email draft saved to: {email_file}")
            print("\nEmail Content:")
            print("="*70)
            print(email_content)
            print("="*70)
            print("\nYou can copy this content and send it via your email client.")
            
        except Exception as e:
            print(f"Error saving email draft: {e}")

    def show_menu(self):
        """Main menu system"""
        while True:
            print("\n" + "="*50)
            print("Password Update Menu")
            print("="*50)
            print("1. Update Magento Admin Passwords")
            print("2. Update Virtualmin Password")
            print("3. Update MySQL Database Password")
            print("4. Update ALL Passwords")
            print("5. Show Current Configuration")
            print("6. Exit and Generate Email Draft")
            print("="*50)
            
            choice = self.prompt_input("Select option", "1")
            
            if choice is None:
                continue
                
            if choice == "1":
                self.update_magento_passwords()
            elif choice == "2":
                self.update_virtualmin_password()
            elif choice == "3":
                self.update_database_password()
            elif choice == "4":
                self.update_all_passwords()
            elif choice == "5":
                self.show_configuration()
            elif choice == "6":
                self.save_email_draft()
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")

    def run(self):
        """Main execution function"""
        try:
            print("Magento & Server Password Update Script")
            print("========================================")
            print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Log file: {self.log_file}")
            print()
            
            # Auto-detect Magento
            if not self.detect_magento_root():
                print("Failed to locate Magento installation")
                return
            
            print()
            print(f"Using Magento: {self.magento_root}")
            print()
            
            # Validate configuration
            if not self.validate_configuration():
                print("System validation failed. Please check the errors above.")
                return
            
            # Show menu
            self.show_menu()
            
        except KeyboardInterrupt:
            print("\nScript interrupted by user")
            self.save_email_draft()
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.logger.exception("Unexpected error occurred")
            sys.exit(1)

def main():
    """Main function"""
    # Check if running as root
    if os.geteuid() != 0:
        print("This script must be run as root")
        sys.exit(1)
    
    manager = PasswordManager()
    manager.run()

if __name__ == "__main__":
    main()
