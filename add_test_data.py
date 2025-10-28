"""
Test verisi ekleme scripti
"""
import sys
import os
from decimal import Decimal

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db_manager
from database.models import Product, Customer


def add_test_data():
    """Test verilerini ekle"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Test ürünleri ekle
        test_products = [
            # Mevcut ürünler
            ('PRD001', 'Forklift Motor Yağı', 'Motor yağı 5W-30', 150.00, 'Yağlar', 'Shell'),
            ('PRD002', 'Forklift Fren Balata', 'Fren balata seti', 300.00, 'Fren Sistemi', 'Brembo'),
            ('PRD003', 'Forklift Lastik', 'Lastik 8.25-15', 800.00, 'Lastikler', 'Michelin'),
            ('PRD004', 'Forklift Akü', 'Akü 12V 100Ah', 1200.00, 'Elektrik', 'Varta'),
            ('PRD005', 'Forklift Hidrolik Yağı', 'Hidrolik yağı ISO 46', 200.00, 'Yağlar', 'Mobil'),
            ('NAK', 'NAKLİYE BEDELİ', 'Nakliye ücreti', 45.00, 'Hizmet', 'Genel'),
            ('AKS001', 'AKS KEÇE - BAOLİ / T3Z / ÇİN  78,4*95*8', 'Aks keçe parçası', 25.50, 'Aks Sistemi', 'BAOLİ'),
            ('AKS002', 'AKS KİLİT PULU - HELİ / BAOLİ / ÇİN', 'Aks kilit pulu', 15.75, 'Aks Sistemi', 'HELİ'),
            
            # Yeni forklift parçaları
            ('PRD006', 'Forklift Conta Seti', 'Motor conta seti', 85.00, 'Motor', 'Victor Reinz'),
            ('PRD007', 'Forklift Filtre', 'Hava filtresi', 45.00, 'Filtreler', 'Mann'),
            ('PRD008', 'Forklift Bujiler', 'Buji seti 4 adet', 120.00, 'Elektrik', 'NGK'),
            ('PRD009', 'Forklift Alternatör', 'Alternatör 12V 90A', 450.00, 'Elektrik', 'Bosch'),
            ('PRD010', 'Forklift Marş Motoru', 'Marş motoru 12V', 380.00, 'Elektrik', 'Bosch'),
            ('PRD011', 'Forklift Direksiyon Pompası', 'Hidrolik pompa', 650.00, 'Hidrolik', 'Eaton'),
            ('PRD012', 'Forklift Hidrolik Silindir', 'Kaldırma silindiri', 850.00, 'Hidrolik', 'Parker'),
            ('PRD013', 'Forklift Zincir', 'Kaldırma zinciri', 180.00, 'Mekanik', 'Renold'),
            ('PRD014', 'Forklift Rulman', 'Rulman seti', 95.00, 'Mekanik', 'SKF'),
            ('PRD015', 'Forklift Kayış', 'V kayışı seti', 65.00, 'Mekanik', 'Gates'),
            
            # Aksesuar ve yedek parçalar
            ('AKS003', 'Forklift Aynası', 'Yan ayna', 35.00, 'Aksesuar', 'Genel'),
            ('AKS004', 'Forklift Sinyal Lambası', 'LED sinyal lambası', 25.00, 'Elektrik', 'Philips'),
            ('AKS005', 'Forklift Korna', 'Elektrikli korna', 40.00, 'Elektrik', 'Bosch'),
            ('AKS006', 'Forklift Koltuğu', 'Operatör koltuğu', 180.00, 'Aksesuar', 'Grammer'),
            ('AKS007', 'Forklift Emniyet Kemeri', '3 nokta emniyet kemeri', 55.00, 'Güvenlik', 'Schroth'),
            ('AKS008', 'Forklift Kova', 'Çelik kova', 220.00, 'Aksesuar', 'Genel'),
            ('AKS009', 'Forklift Çatal', 'Çatal seti', 150.00, 'Aksesuar', 'Genel'),
            ('AKS010', 'Forklift Kılavuz', 'Çatal kılavuzu', 75.00, 'Aksesuar', 'Genel'),
            
            # Yağ ve sıvılar
            ('YAG001', 'Motor Yağı 5W-30', 'Sentetik motor yağı 4L', 85.00, 'Yağlar', 'Shell'),
            ('YAG002', 'Motor Yağı 10W-40', 'Mineral motor yağı 4L', 65.00, 'Yağlar', 'Castrol'),
            ('YAG003', 'Hidrolik Yağı ISO 46', 'Hidrolik yağı 20L', 180.00, 'Yağlar', 'Mobil'),
            ('YAG004', 'Hidrolik Yağı ISO 68', 'Hidrolik yağı 20L', 195.00, 'Yağlar', 'Shell'),
            ('YAG005', 'Fren Hidroliği', 'DOT 4 fren hidroliği', 25.00, 'Yağlar', 'Brembo'),
            ('YAG006', 'Soğutma Sıvısı', 'Antifriz 5L', 45.00, 'Yağlar', 'Prestone'),
            
            # Lastik ve tekerlek
            ('LAST001', 'Forklift Lastik 8.25-15', 'Solid lastik', 800.00, 'Lastikler', 'Michelin'),
            ('LAST002', 'Forklift Lastik 7.00-12', 'Pneumatik lastik', 350.00, 'Lastikler', 'Bridgestone'),
            ('LAST003', 'Forklift Lastik 6.00-9', 'Solid lastik', 280.00, 'Lastikler', 'Continental'),
            ('LAST004', 'Forklift Jant', 'Çelik jant 15"', 120.00, 'Lastikler', 'Genel'),
            
            # Elektrik parçaları
            ('ELEK001', 'Forklift Sigorta Kutusu', 'Sigorta kutusu', 35.00, 'Elektrik', 'Bosch'),
            ('ELEK002', 'Forklift Röle', 'Ana röle', 25.00, 'Elektrik', 'Bosch'),
            ('ELEK003', 'Forklift Kablo Seti', 'Elektrik kablosu seti', 85.00, 'Elektrik', 'Genel'),
            ('ELEK004', 'Forklift Anahtar', 'Kontak anahtarı', 15.00, 'Elektrik', 'Genel'),
            ('ELEK005', 'Forklift Ampul', 'Far ampulü H4', 8.00, 'Elektrik', 'Osram'),
            
            # Hizmetler
            ('HIZ001', 'Forklift Bakım', 'Genel bakım hizmeti', 150.00, 'Hizmet', 'Teknik Servis'),
            ('HIZ002', 'Forklift Onarım', 'Ariza onarım hizmeti', 200.00, 'Hizmet', 'Teknik Servis'),
            ('HIZ003', 'Forklift Kalibrasyon', 'Hidrolik kalibrasyon', 100.00, 'Hizmet', 'Teknik Servis'),
            ('HIZ004', 'Forklift Test', 'Güvenlik testi', 75.00, 'Hizmet', 'Teknik Servis')
        ]
        
        for product_data in test_products:
            cursor.execute("""
                INSERT OR IGNORE INTO products (code, name)
                VALUES (?, ?)
            """, product_data)
        
        # Test müşterileri ekle
        test_customers = [
            ('ABC Lojistik', 'İstanbul Merkez Mah. Lojistik Cad. No:123', '05551234567', 'abc@email.com', '1234567890'),
            ('XYZ Nakliyat', 'Ankara Çankaya Mah. Nakliyat Sok. No:45', '05559876543', 'xyz@email.com', '0987654321'),
            ('DEF Kargo', 'İzmir Konak Mah. Kargo Cad. No:67', '05555555555', 'def@email.com', '5555555555')
        ]
        
        for customer_data in test_customers:
            cursor.execute("""
                INSERT OR IGNORE INTO customers (name, address, phone, email, tax_number)
                VALUES (?, ?, ?, ?, ?)
            """, customer_data)
        
        conn.commit()
        print("Test verileri başarıyla eklendi!")
        
    except Exception as e:
        print(f"Hata: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    add_test_data()
