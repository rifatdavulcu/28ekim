"""
E-posta servisi modülü
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List
import hashlib

from database.models import EmailSettings, User
from database import db_manager


class EmailService:
    """E-posta servisi sınıfı"""
    
    def __init__(self):
        self.db = db_manager
        self.current_settings = None
    
    def get_email_settings(self) -> Optional[EmailSettings]:
        """E-posta ayarlarını getir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM email_settings WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            settings = EmailSettings(
                id=row['id'],
                smtp_host=row['smtp_host'],
                smtp_port=row['smtp_port'],
                username=row['username'],
                password=row['password'],
                use_ssl=bool(row['use_ssl']),
                is_active=bool(row['is_active'])
            )
            self.current_settings = settings
            return settings
        
        return None
    
    def save_email_settings(self, settings: EmailSettings) -> bool:
        """E-posta ayarlarını kaydet"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Mevcut aktif ayarları pasif yap
            cursor.execute("UPDATE email_settings SET is_active = 0")
            
            # Yeni ayarları kaydet
            cursor.execute("""
                INSERT INTO email_settings (
                    smtp_host, smtp_port, username, password, use_ssl, is_active
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                settings.smtp_host,
                settings.smtp_port,
                settings.username,
                settings.password,
                settings.use_ssl,
                True
            ))
            
            conn.commit()
            self.current_settings = settings
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def test_email_connection(self) -> bool:
        """E-posta bağlantısını test et"""
        if not self.current_settings:
            self.get_email_settings()
        
        if not self.current_settings:
            return False
        
        try:
            if self.current_settings.use_ssl:
                # SSL bağlantısı
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.current_settings.smtp_host, 
                    self.current_settings.smtp_port, 
                    context=context
                )
            else:
                # TLS bağlantısı
                server = smtplib.SMTP(
                    self.current_settings.smtp_host, 
                    self.current_settings.smtp_port
                )
                server.starttls()
            
            server.login(self.current_settings.username, self.current_settings.password)
            server.quit()
            return True
            
        except Exception as e:
            print(f"E-posta bağlantı hatası: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   attachment_path: Optional[str] = None) -> bool:
        """E-posta gönder"""
        if not self.current_settings:
            self.get_email_settings()
        
        if not self.current_settings:
            raise Exception("E-posta ayarları bulunamadı!")
        
        try:
            # E-posta mesajı oluştur
            msg = MIMEMultipart()
            msg['From'] = self.current_settings.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Mesaj gövdesi
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Ek dosya varsa ekle
            if attachment_path:
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=attachment_path.split('/')[-1]
                    )
                    msg.attach(attachment)
            
            # SMTP bağlantısı
            if self.current_settings.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.current_settings.smtp_host, 
                    self.current_settings.smtp_port, 
                    context=context
                )
            else:
                server = smtplib.SMTP(
                    self.current_settings.smtp_host, 
                    self.current_settings.smtp_port
                )
                server.starttls()
            
            server.login(self.current_settings.username, self.current_settings.password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            raise Exception(f"E-posta gönderilemedi: {str(e)}")
    
    def send_invoice_email(self, invoice, customer_email: str, pdf_path: str) -> bool:
        """Fiş e-postası gönder"""
        subject = f"Fiş No: {invoice.invoice_number}"
        
        body = f"""
        <html>
        <body>
            <h2>Sayın {invoice.customer_name},</h2>
            <p>Fişiniz hazırlanmıştır. Detaylar ekteki PDF dosyasında bulunmaktadır.</p>
            
            <h3>Fiş Özeti:</h3>
            <ul>
                <li><strong>Fiş No:</strong> {invoice.invoice_number}</li>
                <li><strong>Tarih:</strong> {invoice.invoice_date.strftime('%d.%m.%Y')}</li>
                <li><strong>Ara Toplam:</strong> {invoice.subtotal:.2f} ₺</li>
                <li><strong>KDV:</strong> {invoice.tax_amount:.2f} ₺</li>
                <li><strong>Toplam:</strong> {invoice.total_amount:.2f} ₺</li>
            </ul>
            
            <p>Teşekkür ederiz.</p>
            <p><strong>Forklift Yedek Parça Sistemi</strong></p>
        </body>
        </html>
        """
        
        return self.send_email(customer_email, subject, body, pdf_path)
    
    def get_all_users(self) -> List[User]:
        """Tüm kullanıcıları getir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY username")
        
        users = []
        for row in cursor.fetchall():
            user = User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                full_name=row['full_name'],
                role=row['role'],
                is_active=bool(row['is_active'])
            )
            users.append(user)
        
        conn.close()
        return users
    
    def add_user(self, user: User) -> bool:
        """Yeni kullanıcı ekle"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.username,
                user.password_hash,
                user.full_name,
                user.role,
                user.is_active
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_user(self, user: User) -> bool:
        """Kullanıcı güncelle"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET username = ?, password_hash = ?, full_name = ?, role = ?, is_active = ?
                WHERE id = ?
            """, (
                user.username,
                user.password_hash,
                user.full_name,
                user.role,
                user.is_active,
                user.id
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_user(self, user_id: int) -> bool:
        """Kullanıcı sil"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Kullanıcı doğrulama"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT * FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, password_hash))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                full_name=row['full_name'],
                role=row['role'],
                is_active=bool(row['is_active'])
            )
        
        return None
