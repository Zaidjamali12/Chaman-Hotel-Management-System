import cv2
import face_recognition
import numpy as np
import pickle
import os
import sqlite3
import hashlib
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import threading
import time
import winsound
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from PIL import Image, ImageTk
import sys
import warnings
warnings.filterwarnings('ignore')

# ============================================
# FACE RECOGNITION SETTINGS - OPTIMIZED
# ============================================
FACE_MATCH_THRESHOLD = 0.55  # Lower = More strict (0.55 works well)
PROCESSING_SCALE = 0.25  # For faster processing
FRAME_SKIP = 2  # Process every 3rd frame for speed
ALERT_COOLDOWN = 10  # Seconds between alerts

# ============================================
# EMAIL CONFIGURATION - SIMPLIFIED
# ============================================
class EmailConfig:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    
    # SIMPLIFIED: Just alert recipient, sender will be configured separately
    ALERT_RECIPIENT = "zaidj6463@gmail.com"
    
    # Store email credentials from settings
    SENDER_EMAIL = "mirhajisulemanjamali@gmail.com"
    SENDER_PASSWORD = "srye eiwr zxyo fbse"  # Use App Password for Gmail
    
    @staticmethod
    def configure_email(email, password):
        """Configure email settings from user input"""
        EmailConfig.SENDER_EMAIL = email
        EmailConfig.SENDER_PASSWORD = password
    
    @staticmethod
    def send_email(to_email, subject, body, attachment_path=None):
        """Send email with improved error handling"""
        try:
            # Check if email is configured
            if not EmailConfig.SENDER_EMAIL or not EmailConfig.SENDER_PASSWORD:
                print("⚠️ Email not configured. Please set up email in Email Settings.")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = EmailConfig.SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            if attachment_path and os.path.exists(attachment_path):
                try:
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 
                                       f'attachment; filename="{os.path.basename(attachment_path)}"')
                        msg.attach(part)
                except Exception as e:
                    print(f"Attachment error: {e}")
            
            try:
                server = smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT)
                server.starttls()
                server.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)
                
                text = msg.as_string()
                server.sendmail(EmailConfig.SENDER_EMAIL, to_email, text)
                server.quit()
                print(f"✅ Email sent to {to_email}")
                return True
            except smtplib.SMTPAuthenticationError:
                print("❌ Email authentication failed. Please check your email and password.")
                print("   Make sure you're using an App Password, not your regular password.")
                print("   Enable 2-Step Verification and create an App Password at:")
                print("   https://myaccount.google.com/apppasswords")
                return False
            except Exception as e:
                print(f"❌ Email sending error: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    @staticmethod
    def send_alert_email(frame, alert_time):
        """Send alert email with captured frame"""
        try:
            timestamp = alert_time.strftime("%Y%m%d_%H%M%S")
            os.makedirs("temp_alerts", exist_ok=True)
            temp_image_path = f"temp_alerts/alert_{timestamp}.jpg"
            
            # Save the frame
            cv2.imwrite(temp_image_path, frame)
            
            subject = "🔴 SECURITY ALERT: Unauthorized Person Detected!"
            body = f"""
SECURITY ALERT SYSTEM

🚨 UNAUTHORIZED PERSON DETECTED!

Detection Details:
• Time: {alert_time.strftime('%Y-%m-%d %H:%M:%S')}
• Location: Security Camera 1
• Status: UNKNOWN PERSON DETECTED

IMMEDIATE ACTION REQUIRED:
1. Check the attached image
2. Verify security footage
3. Take appropriate security measures

This is an automated alert from your Security System.
Please investigate immediately.

Best regards,
AI Security System
"""
            
            success = EmailConfig.send_email(
                EmailConfig.ALERT_RECIPIENT,
                subject,
                body,
                temp_image_path
            )
            
            # Clean up temp file after sending
            try:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            except:
                pass
            
            return success
            
        except Exception as e:
            print(f"❌ Alert email error: {e}")
            return False

# ============================================
# DATABASE SETUP
# ============================================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('security_system_new.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Admin table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                reset_token TEXT,
                token_expiry REAL
            )
        ''')
        
        # Known faces table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS known_faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                encoding BLOB NOT NULL,
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alert logs table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                description TEXT,
                image_path TEXT,
                email_sent BOOLEAN DEFAULT 0
            )
        ''')
        
        # Email settings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                sender_email TEXT,
                sender_password TEXT,
                alert_recipient TEXT NOT NULL,
                email_alerts_enabled BOOLEAN DEFAULT 1,
                alert_cooldown INTEGER DEFAULT 300
            )
        ''')
        
        self.conn.commit()
        
        self.create_default_admin()
        self.create_default_email_settings()
    
    def create_default_admin(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM admin WHERE username='admin'")
            if self.cursor.fetchone()[0] == 0:
                default_password = "admin123"
                password_hash = hashlib.sha256(default_password.encode()).hexdigest()
                
                self.cursor.execute(
                    "INSERT INTO admin (username, password_hash, email) VALUES (?, ?, ?)",
                    ("admin", password_hash, "admin@security.com")
                )
                self.conn.commit()
                print("✅ Default admin created: admin / admin123")
        except Exception as e:
            print(f"❌ Error creating default admin: {e}")
    
    def create_default_email_settings(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM email_settings")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute(
                    "INSERT INTO email_settings (alert_recipient, email_alerts_enabled, alert_cooldown) VALUES (?, ?, ?)",
                    ("zaidj6463@gmail.com", 1, 300)
                )
                self.conn.commit()
                print("✅ Default email settings created")
        except Exception as e:
            print(f"❌ Error creating email settings: {e}")
    
    def get_email_settings(self):
        try:
            self.cursor.execute("SELECT * FROM email_settings WHERE id=1")
            result = self.cursor.fetchone()
            if result:
                # Update EmailConfig with stored credentials
                EmailConfig.SENDER_EMAIL = result[1] if result[1] else ""
                EmailConfig.SENDER_PASSWORD = result[2] if result[2] else ""
                EmailConfig.ALERT_RECIPIENT = result[3]
            return result
        except Exception as e:
            print(f"❌ Error getting email settings: {e}")
            return None
    
    def update_email_settings(self, sender_email, sender_password, recipient_email, alerts_enabled, cooldown):
        try:
            # Store password securely (in real app, use encryption)
            self.cursor.execute('''
                INSERT OR REPLACE INTO email_settings 
                (id, sender_email, sender_password, alert_recipient, email_alerts_enabled, alert_cooldown)
                VALUES (1, ?, ?, ?, ?, ?)
            ''', (sender_email, sender_password, recipient_email, 
                  1 if alerts_enabled else 0, cooldown))
            self.conn.commit()
            
            # Update EmailConfig
            EmailConfig.configure_email(sender_email, sender_password)
            EmailConfig.ALERT_RECIPIENT = recipient_email
            
            print(f"✅ Email settings updated for {sender_email}")
            return True
        except Exception as e:
            print(f"❌ Error updating email settings: {e}")
            return False
    
    def add_admin(self, username, password, email):
        try:
            # Check if username or email already exists
            self.cursor.execute("SELECT id FROM admin WHERE username=? OR email=?", (username, email))
            if self.cursor.fetchone():
                return False
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            self.cursor.execute(
                "INSERT INTO admin (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
            )
            self.conn.commit()
            print(f"✅ Admin {username} created successfully")
            return True
        except Exception as e:
            print(f"❌ Add admin error: {e}")
            return False
    
    def verify_admin(self, username, password):
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            self.cursor.execute(
                "SELECT * FROM admin WHERE username=? AND password_hash=?",
                (username, password_hash)
            )
            result = self.cursor.fetchone() is not None
            if result:
                print(f"✅ Login successful for {username}")
            else:
                print(f"❌ Login failed for {username}")
            return result
        except Exception as e:
            print(f"❌ Verify admin error: {e}")
            return False
    
    def get_admin_by_email(self, email):
        try:
            self.cursor.execute(
                "SELECT username, email FROM admin WHERE email=?",
                (email,)
            )
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ Get admin by email error: {e}")
            return None
    
    def save_face_encoding(self, name, encoding):
        try:
            encoding_bytes = pickle.dumps(encoding)
            self.cursor.execute(
                "INSERT INTO known_faces (name, encoding) VALUES (?, ?)",
                (name, encoding_bytes)
            )
            self.conn.commit()
            print(f"✅ Face encoding saved for {name}")
            return True
        except Exception as e:
            print(f"❌ Save face encoding error: {e}")
            return False
    
    def delete_face(self, name):
        try:
            self.cursor.execute(
                "DELETE FROM known_faces WHERE name=?",
                (name,)
            )
            self.conn.commit()
            deleted = self.cursor.rowcount > 0
            if deleted:
                print(f"✅ Face deleted: {name}")
            return deleted
        except Exception as e:
            print(f"❌ Delete face error: {e}")
            return False
    
    def load_known_faces(self):
        known_faces = {}
        try:
            self.cursor.execute("SELECT name, encoding FROM known_faces")
            rows = self.cursor.fetchall()
            
            for name, encoding_bytes in rows:
                try:
                    encoding = pickle.loads(encoding_bytes)
                    known_faces[name] = encoding
                    print(f"✅ Loaded face: {name}")
                except Exception as e:
                    print(f"❌ Error loading face {name}: {e}")
                    continue
            
            print(f"✅ Total faces loaded: {len(known_faces)}")
        except Exception as e:
            print(f"❌ Load known faces error: {e}")
        
        return known_faces
    
    def log_alert(self, alert_type, description, image_path=None, email_sent=False):
        try:
            self.cursor.execute(
                "INSERT INTO alerts (alert_type, description, image_path, email_sent) VALUES (?, ?, ?, ?)",
                (alert_type, description, image_path, 1 if email_sent else 0)
            )
            self.conn.commit()
            alert_id = self.cursor.lastrowid
            print(f"✅ Alert logged: {description}")
            return alert_id
        except Exception as e:
            print(f"❌ Log alert error: {e}")
            return None
    
    def update_alert_email_status(self, alert_id, email_sent=True):
        try:
            self.cursor.execute(
                "UPDATE alerts SET email_sent=? WHERE id=?",
                (1 if email_sent else 0, alert_id)
            )
            self.conn.commit()
        except Exception as e:
            print(f"❌ Update alert email status error: {e}")
    
    def get_all_admins(self):
        try:
            self.cursor.execute(
                "SELECT id, username, email FROM admin ORDER BY username"
            )
            return self.cursor.fetchall()
        except Exception as e:
            print(f"❌ Get all admins error: {e}")
            return []
    
    def close(self):
        try:
            self.conn.close()
            print("✅ Database connection closed")
        except:
            pass

# ============================================
# LOGIN WINDOW
# ============================================
class LoginWindow:
    def __init__(self):
        self.db = Database()
        self.root = tk.Tk()
        self.root.title("🔐 Security System - Login")
        self.root.geometry("450x450")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(False, False)
        
        self.center_window()
        self.setup_ui()
        self.root.mainloop()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        # Main title
        title_frame = tk.Frame(self.root, bg='#1a1a2e')
        title_frame.pack(pady=30)
        
        tk.Label(
            title_frame,
            text="🔒",
            font=("Arial", 40),
            bg='#1a1a2e',
            fg='#3498db'
        ).pack()
        
        tk.Label(
            title_frame,
            text="AI SECURITY SYSTEM",
            font=("Arial", 20, "bold"),
            bg='#1a1a2e',
            fg='white'
        ).pack(pady=10)
        
        tk.Label(
            title_frame,
            text="Unauthorized Person Detection",
            font=("Arial", 12),
            bg='#1a1a2e',
            fg='#95a5a6'
        ).pack()
        
        # Login form
        login_frame = tk.Frame(self.root, bg='#2c3e50', padx=30, pady=30, relief='ridge', bd=1)
        login_frame.pack(pady=10, padx=30)
        
        # Username
        tk.Label(
            login_frame,
            text="👤 Username:",
            font=("Arial", 12),
            bg='#2c3e50',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        self.username_entry = tk.Entry(
            login_frame, 
            font=("Arial", 12), 
            width=25,
            bg='#34495e',
            fg='white',
            insertbackground='white'
        )
        self.username_entry.grid(row=0, column=1, pady=(0, 15), padx=15)
        self.username_entry.insert(0, "admin")
        self.username_entry.focus()
        
        # Password
        tk.Label(
            login_frame,
            text="🔑 Password:",
            font=("Arial", 12),
            bg='#2c3e50',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 5))
        
        self.password_entry = tk.Entry(
            login_frame, 
            font=("Arial", 12), 
            width=25, 
            show="•",
            bg='#34495e',
            fg='white',
            insertbackground='white'
        )
        self.password_entry.grid(row=1, column=1, pady=(0, 15), padx=15)
        self.password_entry.insert(0, "admin123")
        
        # Login button
        login_btn = tk.Button(
            login_frame,
            text="🚀 LOGIN",
            font=("Arial", 12, "bold"),
            bg='#2ecc71',
            fg='white',
            width=25,
            height=2,
            command=self.login,
            activebackground='#27ae60',
            cursor='hand2',
            relief='raised',
            bd=2
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Forgot password link
        forgot_btn = tk.Button(
            login_frame,
            text="Forgot Password?",
            font=("Arial", 10),
            bg='#2c3e50',
            fg='#3498db',
            bd=0,
            command=self.forgot_password,
            activeforeground='#2980b9',
            cursor='hand2'
        )
        forgot_btn.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # Register button
        register_btn = tk.Button(
            login_frame,
            text="📝 Create New Account",
            font=("Arial", 10, "bold"),
            bg='#3498db',
            fg='white',
            width=25,
            command=self.register_account,
            activebackground='#2980b9',
            cursor='hand2'
        )
        register_btn.grid(row=4, column=0, columnspan=2)
        
        # Footer note
        note = tk.Label(
            self.root,
            text="Default: admin / admin123",
            font=("Arial", 10, "italic"),
            bg='#1a1a2e',
            fg='#7f8c8d'
        )
        note.pack(pady=20)
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("⚠️ Input Error", "Please enter both username and password!")
            return
        
        if self.db.verify_admin(username, password):
            self.root.destroy()
            app = SecuritySystem(self.db, username)
        else:
            messagebox.showerror("❌ Login Failed", "Invalid username or password!")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def forgot_password(self):
        messagebox.showinfo("ℹ️ Forgot Password", 
            "Please contact the system administrator to reset your password.")
    
    def register_account(self):
        messagebox.showinfo("ℹ️ Registration", 
            "New account creation is disabled. Please contact the administrator.")

# ============================================
# EMAIL SETTINGS WINDOW - IMPROVED
# ============================================
class EmailSettingsWindow:
    def __init__(self, db, parent):
        self.db = db
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("📧 Email Alert Settings")
        self.window.geometry("550x550")
        self.window.configure(bg='#1a1a2e')
        self.window.resizable(False, False)
        self.window.grab_set()
        
        self.center_window()
        self.setup_ui()
        self.load_settings()
    
    def center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        # Title
        tk.Label(
            self.window, 
            text="📧 Email Alert Settings", 
            font=("Arial", 18, "bold"),
            bg='#1a1a2e',
            fg='white'
        ).pack(pady=20)
        
        # Instructions
        instr = tk.Label(
            self.window,
            text="Configure Gmail for sending alert emails. Use App Password, not regular password.",
            font=("Arial", 10),
            bg='#1a1a2e',
            fg='#95a5a6',
            wraplength=500
        )
        instr.pack(pady=(0, 20))
        
        # Settings frame
        settings_frame = tk.Frame(self.window, bg='#2c3e50', padx=25, pady=25)
        settings_frame.pack(pady=10, fill='x', padx=30)
        
        # Sender Email
        tk.Label(
            settings_frame,
            text="📨 Sender Email:",
            font=("Arial", 11, "bold"),
            bg='#2c3e50',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=10)
        
        self.sender_email = tk.Entry(
            settings_frame, 
            font=("Arial", 11), 
            width=35,
            bg='#34495e',
            fg='white'
        )
        self.sender_email.grid(row=0, column=1, pady=10, padx=15)
        
        # Sender Password (App Password)
        tk.Label(
            settings_frame,
            text="🔑 App Password:",
            font=("Arial", 11, "bold"),
            bg='#2c3e50',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=10)
        
        self.sender_password = tk.Entry(
            settings_frame, 
            font=("Arial", 11), 
            width=35,
            show="•",
            bg='#34495e',
            fg='white'
        )
        self.sender_password.grid(row=1, column=1, pady=10, padx=15)
        
        # Help text for App Password
        help_text = tk.Label(
            settings_frame,
            text="• Enable 2-Step Verification in Google Account\n• Generate App Password at: myaccount.google.com/apppasswords",
            font=("Arial", 9),
            bg='#2c3e50',
            fg='#3498db',
            justify='left'
        )
        help_text.grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 15))
        
        # Alert Recipient
        tk.Label(
            settings_frame,
            text="👤 Alert Recipient:",
            font=("Arial", 11, "bold"),
            bg='#2c3e50',
            fg='white'
        ).grid(row=3, column=0, sticky='w', pady=10)
        
        self.recipient_email = tk.Entry(
            settings_frame, 
            font=("Arial", 11), 
            width=35,
            bg='#34495e',
            fg='white'
        )
        self.recipient_email.grid(row=3, column=1, pady=10, padx=15)
        
        # Email enabled checkbox
        self.email_enabled_var = tk.BooleanVar(value=True)
        email_check = tk.Checkbutton(
            settings_frame,
            text="Enable Email Alerts",
            font=("Arial", 11, "bold"),
            bg='#2c3e50',
            fg='white',
            selectcolor='#2c3e50',
            variable=self.email_enabled_var,
            activebackground='#2c3e50',
            activeforeground='white'
        )
        email_check.grid(row=4, column=0, columnspan=2, sticky='w', pady=15)
        
        # Alert Cooldown
        tk.Label(
            settings_frame,
            text="⏰ Alert Cooldown (minutes):",
            font=("Arial", 11, "bold"),
            bg='#2c3e50',
            fg='white'
        ).grid(row=5, column=0, sticky='w', pady=10)
        
        self.cooldown_spinbox = tk.Spinbox(
            settings_frame,
            from_=1,
            to=30,
            width=10,
            font=("Arial", 11),
            bg='#34495e',
            fg='white',
            buttonbackground='#3498db'
        )
        self.cooldown_spinbox.grid(row=5, column=1, pady=10, padx=15, sticky='w')
        self.cooldown_spinbox.delete(0, tk.END)
        self.cooldown_spinbox.insert(0, "5")
        
        # Buttons frame
        btn_frame = tk.Frame(settings_frame, bg='#2c3e50')
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Test Email button
        test_btn = tk.Button(
            btn_frame,
            text="🧪 Test Email",
            font=("Arial", 10, "bold"),
            bg='#3498db',
            fg='white',
            command=self.test_email,
            width=12,
            pady=8,
            activebackground='#2980b9',
            cursor='hand2'
        )
        test_btn.grid(row=0, column=0, padx=5)
        
        # Save button
        save_btn = tk.Button(
            btn_frame,
            text="💾 Save Settings",
            font=("Arial", 10, "bold"),
            bg='#2ecc71',
            fg='white',
            width=12,
            command=self.save_settings,
            pady=8,
            activebackground='#27ae60',
            cursor='hand2'
        )
        save_btn.grid(row=0, column=1, padx=5)
        
        # Cancel button
        cancel_btn = tk.Button(
            btn_frame,
            text="❌ Cancel",
            font=("Arial", 10, "bold"),
            bg='#e74c3c',
            fg='white',
            width=12,
            command=self.window.destroy,
            pady=8,
            activebackground='#c0392b',
            cursor='hand2'
        )
        cancel_btn.grid(row=0, column=2, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            settings_frame,
            text="",
            font=("Arial", 10),
            bg='#2c3e50',
            fg='#e74c3c'
        )
        self.status_label.grid(row=7, column=0, columnspan=2, pady=10)
    
    def load_settings(self):
        settings = self.db.get_email_settings()
        if settings:
            self.sender_email.delete(0, tk.END)
            self.sender_email.insert(0, settings[1] if settings[1] else "")
            
            self.sender_password.delete(0, tk.END)
            self.sender_password.insert(0, settings[2] if settings[2] else "")
            
            self.recipient_email.delete(0, tk.END)
            self.recipient_email.insert(0, settings[3])
            
            self.email_enabled_var.set(bool(settings[4]))
            
            self.cooldown_spinbox.delete(0, tk.END)
            self.cooldown_spinbox.insert(0, str(settings[5] // 60))
    
    def save_settings(self):
        sender_email = self.sender_email.get().strip()
        sender_password = self.sender_password.get().strip()
        recipient_email = self.recipient_email.get().strip()
        enabled = self.email_enabled_var.get()
        
        # Validate emails
        if sender_email and ('@' not in sender_email or '.' not in sender_email):
            self.status_label.config(text="❌ Please enter a valid sender email", fg='#e74c3c')
            return
        
        if not recipient_email or '@' not in recipient_email or '.' not in recipient_email:
            self.status_label.config(text="❌ Please enter a valid recipient email", fg='#e74c3c')
            return
        
        try:
            cooldown_minutes = int(self.cooldown_spinbox.get())
            if cooldown_minutes < 1 or cooldown_minutes > 30:
                raise ValueError
        except:
            self.status_label.config(text="❌ Cooldown must be 1-30 minutes", fg='#e74c3c')
            return
        
        # If email is enabled, check credentials
        if enabled and (not sender_email or not sender_password):
            self.status_label.config(text="⚠️ Email enabled but credentials incomplete", fg='#f39c12')
            response = messagebox.askyesno("Confirm", 
                "Email alerts are enabled but credentials are incomplete.\n"
                "Alerts won't work until you configure email.\n\n"
                "Do you want to save anyway?")
            if not response:
                return
        
        if self.db.update_email_settings(sender_email, sender_password, 
                                        recipient_email, enabled, cooldown_minutes * 60):
            self.status_label.config(text="✅ Settings saved successfully!", fg='#2ecc71')
            self.window.after(1500, self.window.destroy)
        else:
            self.status_label.config(text="❌ Failed to save settings", fg='#e74c3c')
    
    def test_email(self):
        sender_email = self.sender_email.get().strip()
        sender_password = self.sender_password.get().strip()
        recipient_email = self.recipient_email.get().strip()
        
        if not sender_email or not sender_password:
            self.status_label.config(text="❌ Please enter sender email and password", fg='#e74c3c')
            return
        
        if not recipient_email:
            self.status_label.config(text="❌ Please enter recipient email", fg='#e74c3c')
            return
        
        # Configure EmailConfig temporarily for test
        EmailConfig.configure_email(sender_email, sender_password)
        
        subject = "✅ Security System - Test Email"
        body = """This is a test email from your Security System.

If you're receiving this email, your email alert settings are working correctly.

You will receive alerts when unauthorized persons are detected.

📧 Email Configuration:
• Sender: """ + sender_email + """
• Recipient: """ + recipient_email + """

Best regards,
AI Security System"""
        
        self.status_label.config(text="📤 Sending test email...", fg='#3498db')
        
        if EmailConfig.send_email(recipient_email, subject, body):
            self.status_label.config(text="✅ Test email sent successfully!", fg='#2ecc71')
        else:
            self.status_label.config(text="❌ Failed to send test email", fg='#e74c3c')

# ============================================
# MAIN SECURITY SYSTEM - FIXED FACE RECOGNITION
# ============================================
class SecuritySystem:
    def __init__(self, db, username):
        self.db = db
        self.username = username
        self.known_faces = self.db.load_known_faces()
        
        print(f"✅ Loaded {len(self.known_faces)} known faces")
        for name in self.known_faces:
            print(f"   - {name}")
        
        self.camera_running = False
        self.last_alert_time = 0
        self.frame_counter = 0
        
        # Load email settings
        self.load_email_settings()
        
        # Stats
        self.detection_count = 0
        self.known_count = 0
        self.unknown_count = 0
        self.email_alert_count = 0
        
        self.root = tk.Tk()
        self.root.title(f"🔐 AI Security System - Logged in as {username}")
        self.root.geometry("1300x750")
        self.root.configure(bg='#1a1a2e')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.cap = None
        self.setup_ui()
        self.root.mainloop()
    
    def load_email_settings(self):
        settings = self.db.get_email_settings()
        if settings:
            self.email_alerts_enabled = bool(settings[4])
            self.email_cooldown = settings[5]
            print(f"✅ Email settings loaded: Alerts {'ENABLED' if self.email_alerts_enabled else 'DISABLED'}")
        else:
            self.email_alerts_enabled = False
            self.email_cooldown = 300
    
    def setup_ui(self):
        # Left Panel
        left_panel = tk.Frame(self.root, bg='#16213e', width=350)
        left_panel.pack(side='left', fill='y')
        left_panel.pack_propagate(False)
        
        # Title
        tk.Label(
            left_panel,
            text="🔒 AI SECURITY SYSTEM",
            font=("Arial", 16, "bold"),
            bg='#16213e',
            fg='white'
        ).pack(pady=25)
        
        # User info
        tk.Label(
            left_panel,
            text=f"👤 {self.username}",
            font=("Arial", 12, "bold"),
            bg='#16213e',
            fg='#3498db'
        ).pack(pady=5)
        
        self.email_status_label = tk.Label(
            left_panel,
            text="📧 Email Alerts: ACTIVE ✅" if self.email_alerts_enabled else "📧 Email Alerts: DISABLED ❌",
            font=("Arial", 10),
            bg='#16213e',
            fg='#2ecc71' if self.email_alerts_enabled else '#e74c3c'
        )
        self.email_status_label.pack(pady=5)
        
        tk.Label(
            left_panel,
            text="─────────────",
            font=("Arial", 10),
            bg='#16213e',
            fg='#34495e'
        ).pack(pady=10)
        
        # Camera Control Frame
        cam_frame = tk.LabelFrame(
            left_panel,
            text=" 📷 CAMERA CONTROL ",
            font=("Arial", 12, "bold"),
            bg='#16213e',
            fg='#3498db',
            padx=15,
            pady=15
        )
        cam_frame.pack(padx=20, pady=10, fill='x')
        
        self.camera_status = tk.Label(
            cam_frame,
            text="🔴 Camera OFF",
            font=("Arial", 11),
            bg='#16213e',
            fg='#e74c3c'
        )
        self.camera_status.pack(pady=5)
        
        # Camera buttons
        self.start_btn = tk.Button(
            cam_frame,
            text="🚀 START DETECTION",
            font=("Arial", 11, "bold"),
            bg='#2ecc71',
            fg='white',
            width=20,
            height=2,
            command=self.start_detection,
            activebackground='#27ae60',
            cursor='hand2'
        )
        self.start_btn.pack(pady=5)
        
        self.stop_btn = tk.Button(
            cam_frame,
            text="🛑 STOP DETECTION",
            font=("Arial", 11, "bold"),
            bg='#e74c3c',
            fg='white',
            width=20,
            height=2,
            command=self.stop_detection,
            state='disabled',
            activebackground='#c0392b',
            cursor='hand2'
        )
        self.stop_btn.pack(pady=5)
        
        tk.Label(
            left_panel,
            text="─────────────",
            font=("Arial", 10),
            bg='#16213e',
            fg='#34495e'
        ).pack(pady=10)
        
        # Add Face Frame
        add_frame = tk.LabelFrame(
            left_panel,
            text=" 👤 ADD AUTHORIZED FACE ",
            font=("Arial", 12, "bold"),
            bg='#16213e',
            fg='#3498db',
            padx=15,
            pady=15
        )
        add_frame.pack(padx=20, pady=10, fill='x')
        
        tk.Label(
            add_frame,
            text="Name:",
            font=("Arial", 10),
            bg='#16213e',
            fg='white'
        ).pack(anchor='w', pady=(0, 5))
        
        self.name_entry = tk.Entry(
            add_frame, 
            font=("Arial", 10), 
            width=25,
            bg='#34495e',
            fg='white'
        )
        self.name_entry.pack(pady=(0, 10))
        
        add_btn = tk.Button(
            add_frame,
            text="📸 Capture & Add Face",
            font=("Arial", 10, "bold"),
            bg='#3498db',
            fg='white',
            command=self.capture_authorized_face,
            width=20,
            pady=8,
            activebackground='#2980b9',
            cursor='hand2'
        )
        add_btn.pack()
        
        # Authorized Persons List
        persons_frame = tk.LabelFrame(
            left_panel,
            text=" ✅ AUTHORIZED PERSONS ",
            font=("Arial", 12, "bold"),
            bg='#16213e',
            fg='#3498db',
            padx=15,
            pady=15
        )
        persons_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(persons_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.persons_listbox = tk.Listbox(
            persons_frame,
            height=10,
            font=("Arial", 10),
            bg='#0f3460',
            fg='white',
            selectbackground='#3498db',
            selectmode='single',
            yscrollcommand=scrollbar.set
        )
        self.persons_listbox.pack(fill='both', expand=True)
        scrollbar.config(command=self.persons_listbox.yview)
        
        self.update_persons_list()
        
        delete_btn = tk.Button(
            persons_frame,
            text="🗑️ Delete Selected",
            font=("Arial", 9, "bold"),
            bg='#e74c3c',
            fg='white',
            command=self.delete_selected_face,
            width=15,
            pady=5,
            activebackground='#c0392b',
            cursor='hand2'
        )
        delete_btn.pack(pady=(10, 0))
        
        # Right Panel
        right_panel = tk.Frame(self.root, bg='#1a1a2e')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Top Right - Camera and Admin Controls
        top_right = tk.Frame(right_panel, bg='#1a1a2e')
        top_right.pack(fill='x', padx=10, pady=10)
        
        # Camera Feed
        camera_frame = tk.LabelFrame(
            top_right,
            text=" 📹 LIVE CAMERA FEED ",
            font=("Arial", 12, "bold"),
            bg='#1a1a2e',
            fg='white',
            padx=10,
            pady=10
        )
        camera_frame.pack(side='left', fill='both', expand=True)
        
        self.camera_label = tk.Label(
            camera_frame, 
            bg='black',
            text="📷 Camera Feed\n\nClick 'START DETECTION' to begin",
            font=("Arial", 14),
            fg='white',
            compound='center'
        )
        self.camera_label.pack(expand=True, fill='both')
        
        # Admin Controls
        admin_frame = tk.LabelFrame(
            top_right,
            text=" ⚙️ ADMIN CONTROLS ",
            font=("Arial", 12, "bold"),
            bg='#1a1a2e',
            fg='white',
            padx=10,
            pady=10,
            width=220
        )
        admin_frame.pack(side='right', fill='y')
        admin_frame.pack_propagate(False)
        
        buttons = [
            ("📧 Email Settings", self.open_email_settings, '#3498db'),
            ("👥 View Admins", self.view_admins, '#9b59b6'),
            ("🔑 Change Password", self.change_password, '#e67e22'),
            ("🚪 Logout", self.logout, '#e74c3c')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                admin_frame,
                text=text,
                font=("Arial", 10, "bold"),
                bg=color,
                fg='white',
                command=command,
                width=18,
                pady=8,
                activebackground=color,
                cursor='hand2'
            )
            btn.pack(pady=8)
        
        # Alert Status
        self.alert_label = tk.Label(
            right_panel,
            text="✅ SYSTEM READY",
            font=("Arial", 14, "bold"),
            bg='#1a1a2e',
            fg='#2ecc71',
            pady=10
        )
        self.alert_label.pack(fill='x')
        
        # Stats
        stats_frame = tk.Frame(right_panel, bg='#1a1a2e')
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = tk.Label(
            stats_frame,
            text="📊 Detections: 0 | ✅ Authorized: 0 | ❌ Unauthorized: 0 | 📧 Email Alerts: 0",
            font=("Arial", 11),
            bg='#1a1a2e',
            fg='#f1c40f'
        )
        self.stats_label.pack()
        
        # Alerts Log
        alerts_frame = tk.LabelFrame(
            right_panel,
            text=" 📋 RECENT ALERTS ",
            font=("Arial", 12, "bold"),
            bg='#1a1a2e',
            fg='white',
            padx=10,
            pady=10
        )
        alerts_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        text_frame = tk.Frame(alerts_frame, bg='#0f3460')
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.alerts_text = tk.Text(
            text_frame,
            height=10,
            font=("Consolas", 9),
            bg='#0f3460',
            fg='white',
            state='disabled',
            wrap='word',
            yscrollcommand=scrollbar.set
        )
        self.alerts_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.alerts_text.yview)
        
        self.add_alert_to_display("✅ System initialized successfully")
        self.add_alert_to_display(f"👤 Logged in as: {self.username}")
        self.add_alert_to_display(f"✅ Loaded {len(self.known_faces)} authorized faces")
    
    def open_email_settings(self):
        EmailSettingsWindow(self.db, self.root)
        self.load_email_settings()
        self.email_status_label.config(
            text="📧 Email Alerts: ACTIVE ✅" if self.email_alerts_enabled else "📧 Email Alerts: DISABLED ❌",
            fg='#2ecc71' if self.email_alerts_enabled else '#e74c3c'
        )
    
    def update_persons_list(self):
        self.persons_listbox.delete(0, tk.END)
        if self.known_faces:
            for name in sorted(self.known_faces.keys()):
                self.persons_listbox.insert(tk.END, f"👤 {name}")
        else:
            self.persons_listbox.insert(tk.END, "No authorized persons yet")
            self.persons_listbox.insert(tk.END, "Add faces using the form above")
    
    def capture_authorized_face(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("⚠️ Warning", "Please enter a name!")
            return
        
        if not self.cap or not self.cap.isOpened():
            messagebox.showwarning("⚠️ Warning", "Please start camera first!")
            return
        
        # Capture face with better method
        encodings = []
        messagebox.showinfo("ℹ️ Instructions", 
            "Look directly at the camera. The system will capture your face in 3 seconds.")
        
        time.sleep(1)
        
        for i in range(3):
            ret, frame = self.cap.read()
            if ret:
                # Display countdown on frame
                display_frame = frame.copy()
                cv2.putText(display_frame, f"Capturing... {3-i}", (50, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                self.update_camera_display(display_frame)
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                
                if len(face_locations) > 0:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    if face_encodings:
                        encodings.append(face_encodings[0])
                        print(f"✅ Captured face encoding {i+1} for {name}")
                
                time.sleep(0.5)
        
        if not encodings:
            messagebox.showerror("❌ Error", "No face detected! Please try again.")
            return
        
        # Use average encoding
        avg_encoding = np.mean(encodings, axis=0)
        
        # Save to database
        if self.db.save_face_encoding(name, avg_encoding):
            self.known_faces[name] = avg_encoding
            self.update_persons_list()
            
            # Show success message on camera
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                if face_locations:
                    top, right, bottom, left = face_locations[0]
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, f"Added: {name}", (left, top-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                self.update_camera_display(frame)
            
            self.name_entry.delete(0, tk.END)
            self.add_alert_to_display(f"✅ Added authorized person: {name}")
            messagebox.showinfo("✅ Success", f"{name} added successfully!")
        else:
            messagebox.showerror("❌ Error", "Failed to save to database!")
    
    def delete_selected_face(self):
        selection = self.persons_listbox.curselection()
        if not selection:
            messagebox.showwarning("⚠️ Warning", "Please select a person to delete!")
            return
        
        selected_text = self.persons_listbox.get(selection[0])
        if selected_text.startswith("👤 "):
            selected_name = selected_text[2:]
        else:
            selected_name = selected_text
        
        if selected_name in ["No authorized persons yet", "Add faces using the form above"]:
            messagebox.showwarning("⚠️ Warning", "Please select a valid person!")
            return
        
        if messagebox.askyesno("❓ Confirm Delete", f"Are you sure you want to delete '{selected_name}'?"):
            if self.db.delete_face(selected_name):
                if selected_name in self.known_faces:
                    del self.known_faces[selected_name]
                
                self.update_persons_list()
                self.add_alert_to_display(f"🗑️ Deleted authorized person: {selected_name}")
                messagebox.showinfo("✅ Success", f"{selected_name} deleted successfully!")
            else:
                messagebox.showerror("❌ Error", "Failed to delete from database!")
    
    def view_admins(self):
        admins = self.db.get_all_admins()
        
        admin_window = tk.Toplevel(self.root)
        admin_window.title("👥 Admin Accounts")
        admin_window.geometry("400x300")
        admin_window.configure(bg='#2c3e50')
        admin_window.grab_set()
        
        tk.Label(
            admin_window,
            text="👥 ADMIN ACCOUNTS",
            font=("Arial", 16, "bold"),
            bg='#2c3e50',
            fg='white'
        ).pack(pady=20)
        
        list_frame = tk.Frame(admin_window, bg='#34495e')
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        admin_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 11),
            bg='#0f3460',
            fg='white',
            selectbackground='#3498db',
            yscrollcommand=scrollbar.set,
            height=10
        )
        admin_listbox.pack(fill='both', expand=True)
        scrollbar.config(command=admin_listbox.yview)
        
        for admin_id, username, email in admins:
            admin_listbox.insert(tk.END, f"👤 {username} | 📧 {email}")
        
        close_btn = tk.Button(
            admin_window,
            text="❌ Close",
            font=("Arial", 11, "bold"),
            bg='#3498db',
            fg='white',
            command=admin_window.destroy,
            width=15,
            pady=5
        )
        close_btn.pack(pady=20)
    
    def change_password(self):
        messagebox.showinfo("ℹ️ Change Password", 
            "Please use the 'Forgot Password' feature on the login screen.")
    
    def logout(self):
        if messagebox.askyesno("❓ Logout", "Are you sure you want to logout?"):
            self.stop_detection()
            self.db.close()
            self.root.destroy()
            LoginWindow()
    
    def update_camera_display(self, frame):
        try:
            display_frame = cv2.resize(frame, (640, 480))
            img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(image=img)
            
            self.camera_label.config(image=img, text="")
            self.camera_label.image = img
        except Exception as e:
            print(f"❌ Display update error: {e}")
    
    def start_detection(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("❌ Error", "Cannot open camera! Please check your camera connection.")
            return
        
        # Set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.camera_running = True
        self.camera_status.config(text="🟢 Camera ON", fg='#2ecc71')
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Reset counters
        self.detection_count = 0
        self.known_count = 0
        self.unknown_count = 0
        self.email_alert_count = 0
        self.frame_counter = 0
        self.update_stats_display()
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()
        
        self.add_alert_to_display("🚀 Detection started - System is now monitoring")
    
    def stop_detection(self):
        self.camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.camera_status.config(text="🔴 Camera OFF", fg='#e74c3c')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.camera_label.config(image='', 
                               text="📷 Camera Feed\n\nClick 'START DETECTION' to begin")
        self.alert_label.config(text="🛑 SYSTEM STOPPED", fg='#2ecc71')
        
        self.add_alert_to_display("🛑 Detection stopped")
    
    def detection_loop(self):
        print("🔍 Face detection loop started")
        
        while self.camera_running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                self.frame_counter += 1
                
                # Process every 3rd frame for performance
                if self.frame_counter % FRAME_SKIP != 0:
                    self.update_camera_display(frame)
                    continue
                
                # Resize for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=PROCESSING_SCALE, fy=PROCESSING_SCALE)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
                
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    for i, face_encoding in enumerate(face_encodings):
                        self.detection_count += 1
                        name = "Unknown"
                        authorized = False
                        
                        if self.known_faces:
                            # Get list of known encodings
                            known_encodings = list(self.known_faces.values())
                            known_names = list(self.known_faces.keys())
                            
                            # Calculate distances
                            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                            
                            if len(face_distances) > 0:
                                best_match_index = np.argmin(face_distances)
                                best_distance = face_distances[best_match_index]
                                
                                # DEBUG: Print distance
                                print(f"Distance to best match: {best_distance:.4f} (threshold: {FACE_MATCH_THRESHOLD})")
                                
                                if best_distance < FACE_MATCH_THRESHOLD:
                                    name = known_names[best_match_index]
                                    authorized = True
                                    self.known_count += 1
                                    print(f"✅ Recognized: {name} (distance: {best_distance:.4f})")
                                else:
                                    self.unknown_count += 1
                                    current_time = time.time()
                                    if current_time - self.last_alert_time > ALERT_COOLDOWN:
                                        print(f"❌ Unauthorized! (distance: {best_distance:.4f})")
                                        self.trigger_alert(frame.copy())
                                        self.last_alert_time = current_time
                            else:
                                self.unknown_count += 1
                                current_time = time.time()
                                if current_time - self.last_alert_time > ALERT_COOLDOWN:
                                    print("❌ Unauthorized! (no known faces to compare)")
                                    self.trigger_alert(frame.copy())
                                    self.last_alert_time = current_time
                        else:
                            # No known faces in database
                            self.unknown_count += 1
                            current_time = time.time()
                            if current_time - self.last_alert_time > ALERT_COOLDOWN:
                                print("❌ Unauthorized! (no known faces in database)")
                                self.trigger_alert(frame.copy())
                                self.last_alert_time = current_time
                        
                        # Draw on frame
                        top, right, bottom, left = face_locations[i]
                        # Scale back up
                        top = int(top / PROCESSING_SCALE)
                        right = int(right / PROCESSING_SCALE)
                        bottom = int(bottom / PROCESSING_SCALE)
                        left = int(left / PROCESSING_SCALE)
                        
                        if authorized:
                            color = (0, 255, 0)  # Green
                            label = f"✅ {name}"
                        else:
                            color = (0, 0, 255)  # Red
                            label = "❌ UNAUTHORIZED!"
                        
                        # Draw rectangle
                        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                        cv2.putText(frame, label, (left + 6, bottom - 6), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Update display
                self.update_camera_display(frame)
                
                # Update stats every second
                if self.frame_counter % (30 // FRAME_SKIP) == 0:  # About once per second
                    self.root.after(0, self.update_stats_display)
                
                time.sleep(0.03)
                
            except Exception as e:
                print(f"❌ Detection error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
    
    def trigger_alert(self, frame):
        try:
            current_time = datetime.now()
            print(f"🚨 Triggering alert at {current_time.strftime('%H:%M:%S')}")
            
            # Play alert sound
            try:
                for _ in range(3):
                    winsound.Beep(1000, 300)
                    time.sleep(0.1)
            except:
                pass
            
            # Save alert image
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            os.makedirs("alerts", exist_ok=True)
            image_path = f"alerts/alert_{timestamp}.jpg"
            cv2.imwrite(image_path, frame)
            print(f"📸 Alert image saved: {image_path}")
            
            # Log alert
            alert_msg = f"Unauthorized person detected at {current_time.strftime('%H:%M:%S')}"
            alert_id = self.db.log_alert("Unauthorized Person", alert_msg, image_path, email_sent=False)
            
            # Send email alert
            email_sent = False
            if self.email_alerts_enabled:
                current_timestamp = time.time()
                if current_timestamp - self.last_alert_time >= self.email_cooldown:
                    print("📧 Sending email alert...")
                    email_thread = threading.Thread(
                        target=self.send_email_alert,
                        args=(frame.copy(), current_time, alert_id),
                        daemon=True
                    )
                    email_thread.start()
                    self.email_alert_count += 1
                    email_sent = True
                    print("📧 Email alert thread started")
                else:
                    print(f"⏰ Email alert cooldown active ({self.email_cooldown}s)")
            
            # Update UI
            self.root.after(0, self.update_alert_ui, alert_msg, email_sent)
            
        except Exception as e:
            print(f"❌ Alert error: {e}")
            import traceback
            traceback.print_exc()
    
    def send_email_alert(self, frame, alert_time, alert_id):
        try:
            print("📧 Starting email sending process...")
            email_sent = EmailConfig.send_alert_email(frame, alert_time)
            
            if alert_id:
                self.db.update_alert_email_status(alert_id, email_sent)
            
            if email_sent:
                print(f"✅ Email alert sent to {EmailConfig.ALERT_RECIPIENT}")
                self.root.after(0, self.add_alert_to_display, 
                              f"📧 Email alert sent to {EmailConfig.ALERT_RECIPIENT}")
            else:
                print("❌ Failed to send email alert")
                self.root.after(0, self.add_alert_to_display, 
                              "❌ Failed to send email alert")
                
        except Exception as e:
            print(f"❌ Email alert thread error: {e}")
    
    def update_alert_ui(self, alert_msg, email_sent=False):
        self.alert_label.config(
            text="🚨 UNAUTHORIZED PERSON DETECTED!" + (" 📧" if email_sent else ""),
            fg='#e74c3c'
        )
        
        # Reset after 5 seconds
        self.root.after(5000, self.reset_alert_label)
        
        display_msg = alert_msg + (" (Email alert sent)" if email_sent else "")
        self.add_alert_to_display(display_msg)
    
    def reset_alert_label(self):
        if self.camera_running:
            self.alert_label.config(
                text="✅ SYSTEM MONITORING",
                fg='#2ecc71'
            )
    
    def add_alert_to_display(self, message):
        self.alerts_text.config(state='normal')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        alert_line = f"[{timestamp}] {message}\n"
        
        self.alerts_text.insert('1.0', alert_line)
        
        # Keep only last 20 alerts
        lines = self.alerts_text.get('1.0', 'end-1c').split('\n')
        if len(lines) > 20:
            self.alerts_text.delete('20.0', 'end')
        
        self.alerts_text.config(state='disabled')
        self.alerts_text.see('1.0')
    
    def update_stats_display(self):
        self.stats_label.config(
            text=f"📊 Detections: {self.detection_count} | ✅ Authorized: {self.known_count} | ❌ Unauthorized: {self.unknown_count} | 📧 Email Alerts: {self.email_alert_count}"
        )
    
    def on_closing(self):
        if messagebox.askokcancel("❓ Quit", "Do you want to quit the security system?"):
            self.stop_detection()
            self.db.close()
            self.root.destroy()

# ============================================
# MAIN EXECUTION
# ============================================
def main():
    print("=" * 60)
    print("🔐 AI SECURITY SYSTEM - UNAUTHORIZED PERSON DETECTION")
    print("=" * 60)
    print("\n🔄 Starting system...")
    
    # Clean up old database
    if os.path.exists('security_system.db'):
        try:
            os.remove('security_system.db')
            print("🗑️ Removed old database file")
        except:
            pass
    
    print("\n✅ Starting Security System...")
    print("   Default Login Credentials:")
    print("   👤 Username: admin")
    print("   🔑 Password: admin123")
    print("\n📝 To add authorized faces:")
    print("   1. Login and start camera")
    print("   2. Enter name and click 'Capture & Add Face'")
    print("   3. Look directly at camera")
    print("\n📧 To configure email alerts:")
    print("   1. Click 'Email Settings' in main window")
    print("   2. Enter your Gmail and App Password")
    print("   3. Click 'Test Email' to verify")
    print("=" * 60)
    
    # Start the application
    login = LoginWindow()

if __name__ == "__main__":
    main()