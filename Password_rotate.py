#!/usr/bin/env python3
"""
Magento & Server Password Update Script
Clean, professional version that only acts on explicit user commands
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

class PasswordManager:
    def __init__(self):
        self.magento_root = ""
        self.magento_env_file = ""
        self.log_file = f"/tmp/password_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            else:
                result = subprocess.run(shlex.split(command), check=True, capture_output=True, text=True)
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.stderr if e.stderr else e}"
            self.logger.error(error_msg)
            return False, error_msg

    def prompt_yes_no(self, question):
        """Prompt for yes/no confirmation"""
        while True:
            response = input(f"{question} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer with 'y' or 'n'")

    def prompt_input(self, question, default=None):
        """Prompt for input with optional default"""
        if default:
            question = f"{question} [{default}]: "
        else:
            question = f"{question}: "
        
        response = input(question).strip()
        return response if response else default

    def generate_password(self, length=16):
        """Generate strong random password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))

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
            if not path:
                print("Magento root directory is required")
                return False
            
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

    def validate_n98_magerun(self):
        """Validate n98-magerun2 is available and working"""
        n98_path = Path(self.magento_root) / Config.N98_MAGERUN_PATH
        if not n98_path.exists():
            print(f"n98-magerun2.phar not found in {self.magento_root}")
            return False
        
        # Test n98-magerun
        magento_owner = self.get_magento_owner()
        test_cmd = f"su - {magento_owner} -c 'cd {shlex.quote(self.magento_root)} && php {Config.N98_MAGERUN_PATH} --version'"
        success, output = self.run_command(test_cmd, shell=True)
        
        if success:
            print("n98-magerun2.phar is working")
            return True
        else:
            print("n98-magerun2.phar is not working")
            return False

    def validate_configuration(self):
        """Validate system configuration"""
        print("=== System Validation ===")
        
        # Check Magento root
        if not Path(self.magento_root).exists():
            print("ERROR: Magento root directory not found")
            return False
        else:
            print("Magento root directory exists")
        
        # Check env.php
        if not Path(self.magento_env_file).exists():
            print("ERROR: Magento env.php not found")
            return False
        else:
            print("Magento env.php exists")
        
        # Check Magento owner
        magento_owner = self.get_magento_owner()
        if not magento_owner:
            print("ERROR: Could not determine Magento owner")
            return False
        else:
            print(f"Magento owner: {magento_owner}")
        
        # Validate n98-magerun
        if not self.validate_n98_magerun():
            return False
        
        print("All system checks passed")
        return True

    def update_magento_passwords(self):
        """Update Magento admin passwords - ONLY when explicitly requested"""
        print("=== Update Magento Admin Passwords ===")
        
        # Show users that will be updated
        print("The following users will be updated:")
        for user in Config.MAGENTO_USERS:
            print(f"  - {user}")
        
        # Ask for confirmation
        if not self.prompt_yes_no("Do you want to update passwords for these Magento users?"):
            print("Magento password updates cancelled")
            return
        
        # Generate passwords
        passwords = {}
        print("Generating passwords...")
        for user in Config.MAGENTO_USERS:
            passwords[user] = self.generate_password(16)
        
        # Show generated passwords
        print("Generated passwords:")
        for user, password in passwords.items():
            print(f"  {user}: {password}")
        
        # Final confirmation before making changes
        if not self.prompt_yes_no("CONFIRM: Update these Magento user passwords now?"):
            print("Magento password updates cancelled")
            return
        
        # Update each user
        magento_owner = self.get_magento_owner()
        success_count = 0
        
        for user, password in passwords.items():
            print(f"Updating password for {user}...")
            
            # Use the exact command format from original script
            escaped_password = shlex.quote(password)
            cmd = f"su - {magento_owner} -c 'cd {shlex.quote(self.magento_root)} && php {Config.N98_MAGERUN_PATH} admin:user:change-password {shlex.quote(user)} {escaped_password}'"
            
            success, output = self.run_command(cmd, shell=True)
            
            if success and "Password successfully changed" in output:
                print(f"Successfully updated password for {user}")
                success_count += 1
            else:
                print(f"Failed to update password for {user}")
        
        print(f"Summary: {success_count}/{len(Config.MAGENTO_USERS)} users updated successfully")

    def update_virtualmin_password(self):
        """Update Virtualmin password - ONLY when explicitly requested"""
        print("=== Update Virtualmin Password ===")
        
        print(f"Domain: {Config.VIRTUALMIN_DOMAIN}")
        print(f"User: {Config.VIRTUALMIN_USER}")
        
        # Ask for confirmation
        if not self.prompt_yes_no(f"Do you want to update Virtualmin password for {Config.VIRTUALMIN_USER}?"):
            print("Virtualmin password update cancelled")
            return
        
        # Generate password
        new_password = self.generate_password(16)
        print(f"Generated password: {new_password}")
        
        # Final confirmation
        if not self.prompt_yes_no("CONFIRM: Update Virtualmin password now?"):
            print("Virtualmin password update cancelled")
            return
        
        # Use the exact command from original script
        cmd = f"virtualmin modify-domain --domain {Config.VIRTUALMIN_DOMAIN} --pass {shlex.quote(new_password)}"
        
        success, output = self.run_command(cmd, shell=False)
        
        if success:
            print(f"Successfully updated Virtualmin password for {Config.VIRTUALMIN_USER}")
            print(f"New password: {new_password}")
        else:
            print(f"Failed to update Virtualmin password for {Config.VIRTUALMIN_USER}")

    def update_database_password(self):
        """Update MySQL database password - ONLY when explicitly requested"""
        print("=== Update MySQL Database Password ===")
        
        print(f"MySQL User: {Config.MYSQL_USER}")
        print(f"MySQL Host: {Config.MYSQL_HOST}")
        print(f"Magento Env File: {self.magento_env_file}")
        
        # Ask for confirmation
        if not self.prompt_yes_no(f"Do you want to update MySQL password for {Config.MYSQL_USER}?"):
            print("MySQL password update cancelled")
            return
        
        # Generate password
        new_password = self.generate_password(16)
        print(f"Generated password: {new_password}")
        
        # Final confirmation
        if not self.prompt_yes_no("CONFIRM: Update MySQL password and Magento configuration now?"):
            print("MySQL password update cancelled")
            return
        
        # Update MySQL password - using exact command from original script
        mysql_cmd = f"mysql -e \"ALTER USER '{Config.MYSQL_USER}'@'{Config.MYSQL_HOST}' IDENTIFIED BY '{new_password}'; FLUSH PRIVILEGES;\""
        
        success, output = self.run_command(mysql_cmd, shell=True)
        
        if not success:
            print(f"Failed to update MySQL password for {Config.MYSQL_USER}")
            return
        
        print(f"Successfully updated MySQL password for {Config.MYSQL_USER}")
        
        # Update Magento env.php
        print("Updating Magento configuration file...")
        
        # Create backup
        backup_file = f"{self.magento_env_file}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.run_command(f"cp {shlex.quote(self.magento_env_file)} {shlex.quote(backup_file)}", shell=True)
        
        # Update password in env.php using sed (same as original script)
        sed_cmd = f"sed -i \"s/'password' => '.*'/'password' => '{new_password}'/\" {shlex.quote(self.magento_env_file)}"
        success, output = self.run_command(sed_cmd, shell=True)
        
        if success:
            print("Successfully updated Magento configuration file")
            print(f"New MySQL password: {new_password}")
        else:
            print("Failed to update Magento configuration file")
            print("The MySQL password was updated but the config file was not.")
            print(f"Please manually update {self.magento_env_file} with the new password.")

    def update_all_passwords(self):
        """Update all passwords - ONLY when explicitly requested"""
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
        print(f"Magento Owner: {self.get_magento_owner()}")
        print(f"Log File: {self.log_file}")
        print(f"Magento Users: {', '.join(Config.MAGENTO_USERS)}")
        print(f"Virtualmin User: {Config.VIRTUALMIN_USER}")
        print(f"MySQL User: {Config.MYSQL_USER}")

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
            print("6. Exit")
            print("="*50)
            
            choice = self.prompt_input("Select option", "1")
            
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
        except Exception as e:
            print(f"Unexpected error: {e}")
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
