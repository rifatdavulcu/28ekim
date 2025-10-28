import sys
import os
import sqlite3 # Doğrudan sqlite3 kullanmak daha basit olabilir

# Proje kök dizinini path'e ekle (db_manager için gerekli olabilir ama sqlite3 direkt kullanacağız)
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# from database import db_manager # Şimdilik db_manager'a gerek yok

DB_FILE = "forklift_system.db" # Veritabanı dosyanın adı bu mu kontrol et

def add_discount_column():
    conn = None # Bağlantıyı başta None yapalım
    try:
        print(f"Veritabanı dosyası '{DB_FILE}' açılıyor...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        print("Mevcut 'invoices' tablosu sütunları kontrol ediliyor...")
        cursor.execute("PRAGMA table_info(invoices);")
        columns = [info[1] for info in cursor.fetchall()]

        if 'discount_amount' in columns:
            print("'discount_amount' sütunu zaten var. İşlem yapılmadı.")
        else:
            print("'discount_amount' sütunu ekleniyor...")
            # Yeni sütunu ekle
            cursor.execute("ALTER TABLE invoices ADD COLUMN discount_amount NUMERIC(10, 2) DEFAULT 0.0;")
            conn.commit()
            print("'discount_amount' sütunu başarıyla eklendi.")

    except sqlite3.Error as e:
        print(f"Veritabanı hatası oluştu: {e}")
        if conn:
            conn.rollback() # Hata olursa yapılan değişikliği geri al (ALTER TABLE için pek işlemez ama alışkanlık)
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")
    finally:
        if conn:
            print("Veritabanı bağlantısı kapatılıyor.")
            conn.close()

if __name__ == "__main__":
    # Veritabanı dosyasının yedeğini almayı unutma!
    input("ÖNEMLİ: Devam etmeden önce 'forklift_system.db' dosyasının yedeğini aldınız mı? (Devam etmek için Enter'a basın)")
    add_discount_column()
    input("İşlem tamamlandı. Kapatmak için Enter'a basın.")