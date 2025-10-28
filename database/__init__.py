"""
Veritabanı modelleri ve bağlantı yönetimi (PyInstaller UYUMLU)
"""
import sqlite3
import os
import sys  # sys import edildi
from datetime import datetime
from typing import Optional, List, Dict, Any

# --- PYINSTALLER İÇİN YARDIMCI FONKSİYON ---
def resource_path(relative_path):
    """
    Geliştirme ortamında (normal .py) ve paketlenmiş (.exe) 
    uygulamada dosya yolunu doğru bulmayı sağlar.
    """
    try:
        # PyInstaller geçici bir yol oluşturur ve bunu _MEIPASS'e atar
        base_path = sys._MEIPASS
    except Exception:
        # PyInstaller ile çalışmıyorken (geliştirme ortamı)
        # Bu dosyanın (db_manager.py) olduğu yerin bir üst klasörüne (forkpy/) git
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)
# --- YARDIMCI FONKSİYON SONU ---


class DatabaseConnection:
    """SQLite veritabanı bağlantı yöneticisi"""
    
    def __init__(self, db_path: str = "forklift_system.db"):
        # --- VERİTABANI YOLU GÜNCELLENDİ ---
        # self.db_path = db_path # ESKİ
        self.db_path = resource_path(db_path) # YENİ
        # --- GÜNCELLEME SONU ---
        self.connection = None
        print(f"DEBUG: Veritabanı yolu ayarlandı: {self.db_path}") # Yolu kontrol et
        
    def connect(self):
        """Veritabanına bağlan (YEREL SAAT ZORUNLULUĞU DÜZELTMESİ)"""
        
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                timeout=10
            )
            self.connection.create_function("DATETIME_LOCAL", 1, lambda ts: datetime.fromisoformat(ts).astimezone().isoformat())
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA encoding = 'UTF-8'")
            return self.connection
            
        except sqlite3.OperationalError as e:
            print(f"KRİTİK HATA: Veritabanı dosyasına bağlanılamadı!")
            print(f"Hata: {e}")
            print(f"Aranan Yol: {self.db_path}")
            # Hata durumunda kullanıcıya bir mesaj kutusu göster
            try:
                 from PySide6.QtWidgets import QApplication, QMessageBox
                 app = QApplication.instance() or QApplication(sys.argv)
                 QMessageBox.critical(None, "Veritabanı Hatası", 
                                      f"Veritabanı dosyasına bağlanılamadı:\n{e}\n\nYol: {self.db_path}")
            except Exception as qe:
                 print(f"Hata mesaj kutusu gösterilemedi: {qe}")
            sys.exit("Veritabanı bağlantı hatası.")
    
    def disconnect(self):
        """Veritabanı bağlantısını kapat"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_cursor(self):
        """Cursor nesnesi al"""
        if not self.connection or self.connection.total_changes == -1: # Bağlantı kapalıysa veya kopmuşsa
             print("DEBUG: Veritabanı bağlantısı yok veya kapalı, yeniden bağlanılıyor.")
             self.connect()
        return self.connection.cursor()


class DatabaseManager:
    """Veritabanı işlemleri yöneticisi"""
    
    def __init__(self):
        self.db = DatabaseConnection() # resource_path'ı kullanan sınıfı başlat
        self.init_database()
    
    def init_database(self):
        """Veritabanı tablolarını oluştur (Son isteklere göre güncellendi)"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # Müşteriler tablosu (Telefon/Eposta YOK)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                address TEXT,
                tax_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ürünler tablosu (birim fiyatı eklendi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                unit_price NUMERIC(10, 2) DEFAULT 0.0,
                category TEXT,
                brand TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Fişler tablosu (discount_amount eklendi, fiyatlar REAL yerine NUMERIC)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_address TEXT,
                delivery_person TEXT,
                receiver_person TEXT,
                subtotal NUMERIC(10, 2) DEFAULT 0.0,
                discount_amount NUMERIC(10, 2) DEFAULT 0.0, -- İNDİRİM ALANI EKLENDİ
                tax_rate NUMERIC(5, 2) DEFAULT 0.20,
                tax_amount NUMERIC(10, 2) DEFAULT 0.0,
                total_amount NUMERIC(10, 2) DEFAULT 0.0,
                invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE SET NULL -- Müşteri silinirse fiş kalsın
            )
        """)
        
        # Fiş detayları tablosu (fiyatlar REAL yerine NUMERIC)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price NUMERIC(10, 2) NOT NULL,
                total_price NUMERIC(10, 2) NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE, -- Fiş silinince item'lar da silinsin
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL -- Ürün silinirse item kalsın (kodu/adı tutulur)
            )
        """)
        
        # Kullanıcılar tablosu (Değişiklik yok)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # E-posta ayarları tablosu (Değişiklik yok)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                smtp_host TEXT NOT NULL,
                smtp_port INTEGER NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                use_ssl BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # --- TABLO GÜNCELLEMELERİ (ALTER TABLE) ---
        # Bu kısım, mevcut tablolara eksik sütunları ekler (hata vermez)
        print("DEBUG: Tablo sütunları kontrol ediliyor/güncelleniyor...")
        self._add_column_if_not_exists(cursor, "invoices", "discount_amount", "NUMERIC(10, 2) DEFAULT 0.0")
        self._add_column_if_not_exists(cursor, "products", "description", "TEXT")
        self._add_column_if_not_exists(cursor, "products", "unit_price", "NUMERIC(10, 2) DEFAULT 0.0")
        self._add_column_if_not_exists(cursor, "products", "category", "TEXT")
        self._add_column_if_not_exists(cursor, "products", "brand", "TEXT")
        # Müşteriden tel/eposta kaldırma (ALTER TABLE DROP COLUMN SQLite'ta zordur, şimdilik kalabilirler)
        # self._remove_column_... (Bu işlemi yapmak karmaşıktır, veriyi kaybetmemek için yapılmaz)
        print("DEBUG: Tablo güncelleme kontrolü bitti.")
        # --- GÜNCELLEME SONU ---
        
        conn.commit()
        conn.close()
    
    def _add_column_if_not_exists(self, cursor, table_name, column_name, column_type):
        """Tabloya sütun ekler (eğer zaten yoksa)"""
        try:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [info[1] for info in cursor.fetchall()]
            if column_name not in columns:
                print(f"DEBUG: '{table_name}' tablosuna '{column_name}' sütunu ekleniyor...")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
                print(f"DEBUG: '{column_name}' sütunu eklendi.")
            # else:
            #     print(f"DEBUG: '{column_name}' sütunu '{table_name}' tablosunda zaten var.")
        except sqlite3.Error as e:
            print(f"UYARI: '{column_name}' sütunu eklenirken hata (belki zaten vardı?): {e}")

    def get_connection(self):
        """Veritabanı bağlantısı al"""
        return self.db.connect()


# Singleton instance
db_manager = DatabaseManager()