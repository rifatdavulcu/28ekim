"""
Veri içe/dışa aktarma modülü (Telefon/Eposta Yok)
"""
import pandas as pd
from typing import Dict, List, Any
import os
import sys # sys import'u ekle

# db_manager'ı import edebilmek için proje yolunu ekle (önceki kodda yoktu, ekledim)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Product, Customer
# db_manager'ı doğru import et
try:
    from database import db_manager
except ImportError:
    print("HATA: db_manager modülü bulunamadı. Veritabanı işlemleri çalışmayacak.")
    db_manager = None # Hata durumunda None ata


class DataImporter:
    """Veri içe/dışa aktarma sınıfı"""

    def __init__(self):
        # db_manager None ise hata ver
        if db_manager is None:
            raise ImportError("db_manager başlatılamadı.")
        self.db = db_manager

    def import_products(self, file_path: str) -> Dict[str, int]:
        """Ürünleri Excel/CSV dosyasından içe aktar"""
        print("\n--- DEBUG: import_products fonksiyonu başladı ---")
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8', na_filter=False)
            else:
                df = pd.read_excel(file_path, sheet_name=0, keep_default_na=False)

            if len(df) == 0: print("DEBUG: UYARI! Dosyada veri satırı (0) bulundu.")

            required_columns = ['code', 'name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Eksik sütunlar: {', '.join(missing_columns)}")

            conn = self.db.get_connection(); cursor = conn.cursor()
            imported_count = 0; updated_count = 0; skipped_count = 0

            try:
                for index, row in df.iterrows():
                    excel_row_num = index + 2
                    product_code_raw = str(row.get('code', '')).strip()
                    product_name_raw = str(row.get('name', '')).strip()
                    if not product_code_raw or not product_name_raw:
                        print(f"DEBUG: Satır {excel_row_num} ATLANDI. Kod/Ad boş.")
                        skipped_count += 1; continue

                    cursor.execute("SELECT id FROM products WHERE code = ?", (product_code_raw,))
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute("UPDATE products SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE code = ?", (product_name_raw, product_code_raw))
                        updated_count += 1
                    else:
                        cursor.execute("INSERT INTO products (code, name) VALUES (?, ?)", (product_code_raw, product_name_raw))
                        imported_count += 1
                conn.commit()
            except Exception as e:
                conn.rollback(); print(f"DEBUG: Veritabanı döngüsünde HATA: {e}"); raise e
            finally:
                conn.close()

            print(f"-> Yeni: {imported_count}, Güncel: {updated_count}, Atlanan: {skipped_count}")
            return {'imported': imported_count, 'updated': updated_count, 'total': imported_count + updated_count}
        except Exception as e:
            print(f"DEBUG: İçe aktarma sırasında genel HATA: {str(e)}"); raise Exception(f"Ürünler içe aktarılamadı: {str(e)}")

    def import_customers(self, file_path: str) -> Dict[str, int]:
        """Müşterileri Excel/CSV dosyasından içe aktar (Telefon/Eposta YOK)"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8', na_filter=False)
            else:
                df = pd.read_excel(file_path, sheet_name=0, keep_default_na=False)

            required_columns = ['name'] # Sadece 'name' zorunlu
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Eksik sütunlar: {', '.join(missing_columns)}")

            conn = self.db.get_connection(); cursor = conn.cursor()
            imported_count = 0; updated_count = 0

            try:
                for index, row in df.iterrows(): # index eklendi
                    excel_row_num = index + 2 # Excel satır no debug için
                    customer_name = str(row['name']).strip()
                    if not customer_name:
                        print(f"DEBUG: Satır {excel_row_num} ATLANDI. Müşteri adı boş.")
                        continue

                    # Sadece adres ve vergi no okunuyor
                    customer_data = {
                        'name': customer_name,
                        'address': str(row.get('address', '')).strip(),
                        'tax_number': str(row.get('tax_number', '')).strip()
                    }

                    # Sadece isme göre kontrol
                    cursor.execute("SELECT id FROM customers WHERE name = ?", (customer_data['name'],))
                    existing = cursor.fetchone()

                    if existing:
                        # Sadece adresi ve vergi numarasını güncelle
                        cursor.execute("""
                            UPDATE customers
                            SET address = ?, tax_number = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (
                            customer_data['address'],
                            customer_data['tax_number'],
                            existing['id'] # ID ile güncellemek daha güvenli
                        ))
                        updated_count += 1
                    else:
                        # Sadece isim, adres, vergi no ekle
                        cursor.execute("""
                            INSERT INTO customers (name, address, tax_number)
                            VALUES (?, ?, ?)
                        """, (
                            customer_data['name'],
                            customer_data['address'],
                            customer_data['tax_number']
                        ))
                        imported_count += 1
                conn.commit()
            except Exception as e:
                conn.rollback(); raise e
            finally:
                conn.close()

            print(f"-> Müşteri Yeni: {imported_count}, Güncel: {updated_count}")
            return {'imported': imported_count, 'updated': updated_count, 'total': imported_count + updated_count}
        except Exception as e:
            raise Exception(f"Müşteriler içe aktarılamadı: {str(e)}")

    def create_product_template(self, file_path: str):
        """Ürün şablonu oluştur"""
        template_data = {'code': ['PRD001'], 'name': ['Örnek Ürün 1']}
        df = pd.DataFrame(template_data); df.to_excel(file_path, index=False, engine='openpyxl')

    def create_customer_template(self, file_path: str):
        """Müşteri şablonu oluştur (Telefon/Eposta YOK)"""
        template_data = {
            'name': ['Örnek Müşteri 1'],
            'address': ['Adres 1'],
            'tax_number': ['1234567890']
        }
        df = pd.DataFrame(template_data); df.to_excel(file_path, index=False, engine='openpyxl')

    def export_products(self, file_path: str):
        """Ürünleri Excel dosyasına dışa aktar"""
        conn = self.db.get_connection(); cursor = conn.cursor()
        cursor.execute("SELECT code, name FROM products ORDER BY name")
        products = [{'code': row['code'],'name': row['name']} for row in cursor.fetchall()]
        conn.close(); df = pd.DataFrame(products); df.to_excel(file_path, index=False, engine='openpyxl')

    def export_customers(self, file_path: str):
        """Müşterileri Excel dosyasına dışa aktar (Telefon/Eposta YOK)"""
        conn = self.db.get_connection(); cursor = conn.cursor()
        cursor.execute("SELECT name, address, tax_number FROM customers ORDER BY name")
        customers = [{'name': row['name'], 'address': row['address'], 'tax_number': row['tax_number']} for row in cursor.fetchall()]
        conn.close(); df = pd.DataFrame(customers); df.to_excel(file_path, index=False, engine='openpyxl')

    def export_invoices(self, file_path: str, start_date: str = None, end_date: str = None):
        """Fişleri Excel dosyasına dışa aktar"""
        conn = self.db.get_connection(); cursor = conn.cursor()
        query = """
            SELECT i.invoice_number, i.invoice_date, i.customer_name, i.customer_address,
                   i.delivery_person, i.receiver_person, i.subtotal, i.tax_amount, i.total_amount,
                   ii.product_code, ii.product_name, ii.quantity, ii.unit_price, ii.total_price
            FROM invoices i LEFT JOIN invoice_items ii ON i.id = ii.invoice_id """
        params = []
        if start_date and end_date:
            query += " WHERE i.invoice_date BETWEEN ? AND ?"
            params = [start_date, end_date]
        query += " ORDER BY i.invoice_date DESC, i.invoice_number, ii.id"
        cursor.execute(query, params)
        invoices_data = []
        for row in cursor.fetchall():
            invoices_data.append({
                'Fiş No': row['invoice_number'], 'Tarih': row['invoice_date'], 'Müşteri': row['customer_name'], 'Adres': row['customer_address'],
                'Teslim Eden': row['delivery_person'], 'Teslim Alan': row['receiver_person'], 'Ara Toplam': row['subtotal'], 'KDV': row['tax_amount'], 'Toplam': row['total_amount'],
                'Ürün Kodu': row['product_code'], 'Ürün Adı': row['product_name'], 'Miktar': row['quantity'], 'Birim Fiyat': row['unit_price'], 'Satır Toplamı': row['total_price']
            })
        conn.close(); df = pd.DataFrame(invoices_data); df.to_excel(file_path, index=False, engine='openpyxl')