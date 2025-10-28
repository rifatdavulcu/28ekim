"""
Fiş yönetimi modülü (Zaman Düzeltmesi Dahil)
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid
import sqlite3

# Diğer modüllerden bağımlılıklar
from database.models import Invoice, InvoiceItem, Customer, Product
from database import db_manager


class InvoiceManager:
    """Fiş yönetimi sınıfı"""
    
    def __init__(self):
        self.db = db_manager
        self._product_cache = None
        self._cache_timestamp = None
    
    def search_products(self, search_text: str):
        """Ürün koduna veya adına göre ürün arar (SADECE VAR OLAN SÜTUNLAR ÇEKİLİYOR)"""
        if not search_text.strip():
            return []

        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Düzeltme: Yalnızca Product modelinde tanımlı olan ve DB'de VAR OLAN sütunları çekin.
        query = """
            SELECT id, code, name FROM products 
            WHERE LOWER(code) LIKE LOWER(?) 
              OR LOWER(name) LIKE LOWER(?) 
            ORDER BY name
            LIMIT 20
        """

        search_pattern = f"%{search_text}%"
        cursor.execute(query, (search_pattern, search_pattern))

        products = []
        for row in cursor.fetchall():
            product = Product(
                id=row["id"],
                code=row["code"],
                name=row["name"]
            )
            products.append(product)

        conn.close()
        return products
    
    def get_all_product_codes(self) -> List[str]:
        """Tüm ürün kodlarını getir (autocomplete için)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT code FROM products ORDER BY code")
        codes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return codes
    
    def get_product_code_suggestions(self, search_text: str, limit: int = 10) -> List[str]:
        """Ürün kodu önerileri getir (autocomplete için)"""
        if not search_text.strip():
            return []
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT code FROM products
            WHERE LOWER(code) LIKE LOWER(?)
            ORDER BY code
            LIMIT ?
        """
        
        search_pattern = f"%{search_text}%"
        cursor.execute(query, (search_pattern, limit))
        
        suggestions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return suggestions
    
    def get_cached_product_codes(self) -> List[str]:
        """Cache'den ürün kodlarını getir (performans için)"""
        from datetime import datetime, timedelta
        
        # Cache 5 dakika geçerli
        if (self._product_cache is None or 
            self._cache_timestamp is None or 
            datetime.now() - self._cache_timestamp > timedelta(minutes=5)):
            
            self._product_cache = self.get_all_product_codes()
            self._cache_timestamp = datetime.now()
        
        return self._product_cache
    
    def get_product_by_code(self, code: str) -> Optional[Product]:
        """Ürün koduna göre ürün getir (SADECE VAR OLAN SÜTUNLAR ÇEKİLİYOR)"""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, code, name FROM products WHERE code = ?", (code,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return Product(
                id=row['id'],
                code=row['code'],
                name=row['name']
            )
        return None
    
    def get_customer_by_name(self, name: str) -> Optional[Customer]:
        """Müşteri adına göre müşteri getir"""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return Customer(
                id=row['id'],
                name=row['name'],
                address=row['address'],
                phone=row['phone'],
                email=row['email'],
                tax_number=row['tax_number']
            )
        return None
    
    def get_all_customers(self) -> List[Customer]:
        """Tüm müşterileri getir"""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers ORDER BY name")
        
        customers = []
        for row in cursor.fetchall():
            customer = Customer(
                id=row['id'],
                name=row['name'],
                address=row['address'],
                phone=row['phone'],
                email=row['email'],
                tax_number=row['tax_number']
            )
            customers.append(customer)
        
        conn.close()
        return customers
    
    def save_customer(self, customer: Customer) -> Customer:
        """Müşteri kaydet"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO customers (name, address, phone, email, tax_number)
                VALUES (?, ?, ?, ?, ?)
            """, (
                customer.name,
                customer.address,
                customer.phone,
                customer.email,
                customer.tax_number
            ))
            
            customer.id = cursor.lastrowid
            conn.commit()
            return customer
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def save_invoice(self, invoice: Invoice) -> Invoice:
        """Fişi kaydet"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Fiş numarası oluştur
            if not invoice.invoice_number:
                invoice.invoice_number = self.generate_invoice_number()
            
            # YENİ EKLENEN SATIR: Yerel saat dilimi farkındalıklı zamanı kaydet
            from datetime import datetime, timezone
            # datetime.now(timezone.utc) ile UTC zamanını alıp, veritabanına kaydederiz. 
            # Veritabanı da bunu okurken yerel saate göre yorumlar.
            invoice.invoice_date = datetime.now() # Bu kez varsayılan saati bırakalım
            
            # Fişi kaydet
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, customer_id, customer_name, customer_address,
                    delivery_person, receiver_person, subtotal, tax_rate, tax_amount, total_amount, invoice_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice.invoice_number,
                invoice.customer_id,
                invoice.customer_name,
                invoice.customer_address,
                invoice.delivery_person,
                invoice.receiver_person,
                str(invoice.subtotal),
                # YENİ EKLENDİ: (getattr ile None ise 0.0 olmasını sağlıyoruz)
                str(getattr(invoice, 'discount_amount', Decimal('0.0'))), 
                str(invoice.tax_rate),
                str(invoice.tax_amount),
                str(invoice.total_amount),
                # KRİTİK: SQLite, isoformat ile kaydederken bunu düzgünce saklamalı.
                invoice.invoice_date.strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            invoice_id = cursor.lastrowid
            
            # Fiş kalemlerini kaydet
            for item in invoice.items:
                cursor.execute("""
                    INSERT INTO invoice_items (
                        invoice_id, product_id, product_code, product_name,
                        quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    item.product_id,
                    item.product_code,
                    item.product_name,
                    item.quantity,
                    str(item.unit_price),
                    str(item.total_price)
                ))
            
            conn.commit()
            invoice.id = invoice_id
            
            print(f"Fiş başarıyla kaydedildi: {invoice.invoice_number} (ID: {invoice_id})")
            
            return invoice
            
        except Exception as e:
            conn.rollback()
            print(f"Fiş kaydetme hatası: {e}")
            raise e
        finally:
            conn.close()
    
    def generate_invoice_number(self) -> str:
        """Fiş numarası oluştur"""
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM invoices 
            WHERE DATE(invoice_date) = DATE('now', 'localtime')
        """) # 'localtime' eklendi
        
        count_row = cursor.fetchone()
        count = count_row['count'] if count_row else 0
        conn.close()
        
        invoice_number = f"{date_str}-{count + 1:03d}"
        return invoice_number
    
    def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Fiş numarasına göre fiş getir"""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,))
        invoice_row = cursor.fetchone()
        
        if not invoice_row:
            conn.close()
            return None
        
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_row['id'],))
        item_rows = cursor.fetchall()
        
        conn.close()
        
        # Invoice objesi oluştur
        invoice = Invoice(
            id=invoice_row['id'],
            invoice_number=invoice_row['invoice_number'],
            customer_id=invoice_row['customer_id'],
            customer_name=invoice_row['customer_name'],
            customer_address=invoice_row['customer_address'],
            delivery_person=invoice_row['delivery_person'],
            receiver_person=invoice_row['receiver_person'],
            subtotal=Decimal(str(invoice_row['subtotal'])),
            tax_rate=Decimal(str(invoice_row['tax_rate'])),
            tax_amount=Decimal(str(invoice_row['tax_amount'])),
            total_amount=Decimal(str(invoice_row['total_amount'])),
            # DÜZELTME: Artık row['invoice_date'] zaten datetime objesi gelmeli
            invoice_date=invoice_row['invoice_date'] 
        )
        
        for item_row in item_rows:
            item = InvoiceItem(
                id=item_row['id'],
                invoice_id=item_row['invoice_id'],
                product_id=item_row['product_id'],
                product_code=item_row['product_code'],
                product_name=item_row['product_name'],
                quantity=item_row['quantity'],
                unit_price=Decimal(str(item_row['unit_price'])),
                total_price=Decimal(str(item_row['total_price']))
            )
            invoice.items.append(item)
        
        return invoice
    
    def get_invoices_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Invoice]:
        """Tarih aralığına göre fişleri getir"""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM invoices 
            WHERE invoice_date BETWEEN ? AND ?
            ORDER BY invoice_date DESC
        """, (start_date, end_date))
        
        invoices = []
        for row in cursor.fetchall():
            invoice = Invoice(
                id=row['id'],
                invoice_number=row['invoice_number'],
                customer_id=row['customer_id'],
                customer_name=row['customer_name'],
                customer_address=row['customer_address'],
                delivery_person=row['delivery_person'],
                receiver_person=row['receiver_person'],
                subtotal=Decimal(str(row['subtotal'])),
                tax_rate=Decimal(str(row['tax_rate'])),
                tax_amount=Decimal(str(row['tax_amount'])),
                total_amount=Decimal(str(row['total_amount'])),
                # DÜZELTME: Artık row['invoice_date'] zaten datetime objesi gelmeli
                invoice_date=row['invoice_date']
            )
            invoices.append(invoice)
        
        conn.close()
        return invoices

    def delete_invoice_by_number(self, invoice_number: str):
        """Fiş numarasını kullanarak bir fişi ve ilgili kalemlerini siler."""
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
            invoice_row = cursor.fetchone()
            
            if not invoice_row:
                raise Exception(f"{invoice_number} numaralı fiş bulunamadı.")
                
            invoice_id = invoice_row['id']
            
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            conn.commit()
            print(f"Fiş başarıyla silindi: {invoice_number} (ID: {invoice_id})")

        except Exception as e:
            conn.rollback() 
            print(f"Fiş silme hatası: {e}")
            raise e 
        finally:
            conn.close()