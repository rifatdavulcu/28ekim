"""
Veri doğrulama modülü
"""
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime
import email_validator


class Validators:
    """Veri doğrulama sınıfı"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """E-posta adresi doğrulama"""
        if not email or not email.strip():
            return False
        
        try:
            email_validator.validate_email(email.strip())
            return True
        except email_validator.EmailNotValidError:
            return False
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Telefon numarası doğrulama"""
        if not phone:
            return True  # Telefon opsiyonel
        
        # Türkiye telefon numarası formatı
        phone_pattern = r'^(\+90|0)?[5][0-9]{9}$'
        return bool(re.match(phone_pattern, phone.strip()))
    
    @staticmethod
    def validate_tax_number(tax_number: str) -> bool:
        """Vergi numarası doğrulama"""
        if not tax_number:
            return True  # Vergi numarası opsiyonel
        
        # 10 haneli sayı kontrolü
        if not re.match(r'^\d{10}$', tax_number.strip()):
            return False
        
        # Basit kontrol toplamı
        digits = [int(d) for d in tax_number.strip()]
        if len(digits) != 10:
            return False
        
        # İlk 9 hanenin toplamının son hanesi ile kontrolü
        check_sum = sum(digits[:9])
        return check_sum % 10 == digits[9]
    
    @staticmethod
    def validate_price(price: Any) -> bool:
        """Fiyat doğrulama"""
        if price is None:
            return False
        
        try:
            price_decimal = Decimal(str(price))
            return price_decimal >= 0
        except (InvalidOperation, ValueError):
            return False
    
    @staticmethod
    def validate_quantity(quantity: Any) -> bool:
        """Miktar doğrulama"""
        if quantity is None:
            return False
        
        try:
            qty = int(quantity)
            return qty > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_product_code(code: str) -> bool:
        """Ürün kodu doğrulama"""
        if not code or not code.strip():
            return False
        
        # Ürün kodu en az 3 karakter olmalı
        return len(code.strip()) >= 3
    
    @staticmethod
    def validate_customer_name(name: str) -> bool:
        """Müşteri adı doğrulama"""
        if not name or not name.strip():
            return False
        
        # Müşteri adı en az 2 karakter olmalı
        return len(name.strip()) >= 2
    
    @staticmethod
    def validate_invoice_number(invoice_number: str) -> bool:
        """Fiş numarası doğrulama"""
        if not invoice_number or not invoice_number.strip():
            return False
        
        # Fiş numarası formatı: YYYYMMDD-XXX
        pattern = r'^\d{8}-\d{3}$'
        return bool(re.match(pattern, invoice_number.strip()))
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
        """Tarih aralığı doğrulama"""
        if not start_date or not end_date:
            return False
        
        return start_date <= end_date
    
    @staticmethod
    def validate_smtp_settings(host: str, port: int, username: str, password: str) -> List[str]:
        """SMTP ayarları doğrulama"""
        errors = []
        
        if not host or not host.strip():
            errors.append("SMTP Host gerekli")
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("Geçersiz SMTP Port (1-65535 arası olmalı)")
        
        if not username or not username.strip():
            errors.append("Kullanıcı adı gerekli")
        
        if not password or not password.strip():
            errors.append("Şifre gerekli")
        
        # E-posta formatı kontrolü
        if username and not Validators.validate_email(username):
            errors.append("Geçersiz e-posta adresi")
        
        return errors
    
    @staticmethod
    def validate_user_data(username: str, password: str, full_name: str) -> List[str]:
        """Kullanıcı verisi doğrulama"""
        errors = []
        
        if not username or not username.strip():
            errors.append("Kullanıcı adı gerekli")
        elif len(username.strip()) < 3:
            errors.append("Kullanıcı adı en az 3 karakter olmalı")
        elif not re.match(r'^[a-zA-Z0-9_]+$', username.strip()):
            errors.append("Kullanıcı adı sadece harf, rakam ve _ içerebilir")
        
        if not password or not password.strip():
            errors.append("Şifre gerekli")
        elif len(password.strip()) < 6:
            errors.append("Şifre en az 6 karakter olmalı")
        
        if not full_name or not full_name.strip():
            errors.append("Tam ad gerekli")
        elif len(full_name.strip()) < 2:
            errors.append("Tam ad en az 2 karakter olmalı")
        
        return errors
    
    @staticmethod
    def validate_invoice_data(invoice: Any) -> List[str]:
        """Fiş verisi doğrulama"""
        errors = []
        
        if not invoice:
            errors.append("Fiş verisi gerekli")
            return errors
        
        # Müşteri adı kontrolü
        if not Validators.validate_customer_name(invoice.customer_name):
            errors.append("Geçerli müşteri adı gerekli")
        
        # Fiş kalemleri kontrolü
        if not invoice.items or len(invoice.items) == 0:
            errors.append("En az bir ürün gerekli")
        else:
            for i, item in enumerate(invoice.items):
                if not Validators.validate_product_code(item.product_code):
                    errors.append(f"Ürün {i+1}: Geçersiz ürün kodu")
                
                if not Validators.validate_quantity(item.quantity):
                    errors.append(f"Ürün {i+1}: Geçersiz miktar")
                
                if not Validators.validate_price(item.unit_price):
                    errors.append(f"Ürün {i+1}: Geçersiz birim fiyat")
        
        # Toplam tutar kontrolü
        if not Validators.validate_price(invoice.total_amount):
            errors.append("Geçersiz toplam tutar")
        
        return errors
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """Metin temizleme"""
        if not text:
            return ""
        
        # Başta ve sonda boşlukları temizle
        text = text.strip()
        
        # Çoklu boşlukları tek boşluğa çevir
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    @staticmethod
    def sanitize_price(price: Any) -> Optional[Decimal]:
        """Fiyat temizleme"""
        if price is None:
            return None
        
        try:
            # Virgülü nokta ile değiştir
            price_str = str(price).replace(',', '.')
            return Decimal(price_str)
        except (InvalidOperation, ValueError):
            return None
    
    @staticmethod
    def sanitize_quantity(quantity: Any) -> Optional[int]:
        """Miktar temizleme"""
        if quantity is None:
            return None
        
        try:
            return int(float(quantity))
        except (ValueError, TypeError):
            return None
