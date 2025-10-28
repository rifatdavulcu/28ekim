"""
Rapor oluşturma modülü
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from database.models import Invoice, InvoiceItem
from database import db_manager


class ReportGenerator:
    """Rapor oluşturma sınıfı"""
    
    def __init__(self):
        self.db = db_manager
    
    def get_sales_report(self, start_date: datetime, end_date: datetime) -> List[Invoice]:
        """Satış raporu oluştur"""
        conn = self.db.get_connection()
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
                invoice_date=datetime.fromisoformat(row['invoice_date'])
            )
            invoices.append(invoice)
        
        conn.close()
        return invoices
    
    def get_product_analysis(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Ürün analizi oluştur"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ii.product_code,
                ii.product_name,
                SUM(ii.quantity) as total_quantity,
                SUM(ii.total_price) as total_amount,
                AVG(ii.unit_price) as avg_price
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.invoice_date BETWEEN ? AND ?
            GROUP BY ii.product_code, ii.product_name
            ORDER BY total_amount DESC
        """, (start_date, end_date))
        
        products = []
        for row in cursor.fetchall():
            product_data = {
                'code': row['product_code'],
                'name': row['product_name'],
                'quantity': row['total_quantity'],
                'total': Decimal(str(row['total_amount'])),
                'avg_price': Decimal(str(row['avg_price']))
            }
            products.append(product_data)
        
        conn.close()
        return products
    
    def get_customer_analysis(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Müşteri analizi oluştur"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                customer_name,
                COUNT(*) as invoice_count,
                SUM(total_amount) as total_amount,
                AVG(total_amount) as avg_amount
            FROM invoices 
            WHERE invoice_date BETWEEN ? AND ?
            GROUP BY customer_name
            ORDER BY total_amount DESC
        """, (start_date, end_date))
        
        customers = []
        for row in cursor.fetchall():
            customer_data = {
                'name': row['customer_name'],
                'invoice_count': row['invoice_count'],
                'total_amount': Decimal(str(row['total_amount'])),
                'avg_amount': Decimal(str(row['avg_amount']))
            }
            customers.append(customer_data)
        
        conn.close()
        return customers
    
    def get_summary_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Özet istatistikler"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Temel istatistikler
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_invoice_amount
            FROM invoices 
            WHERE invoice_date BETWEEN ? AND ?
        """, (start_date, end_date))
        
        stats_row = cursor.fetchone()
        
        # En çok satan ürün
        cursor.execute("""
            SELECT 
                ii.product_name,
                SUM(ii.quantity) as total_quantity
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.invoice_date BETWEEN ? AND ?
            GROUP BY ii.product_code, ii.product_name
            ORDER BY total_quantity DESC
            LIMIT 1
        """, (start_date, end_date))
        
        top_product_row = cursor.fetchone()
        
        conn.close()
        
        stats = {
            'total_invoices': stats_row['total_invoices'] or 0,
            'total_revenue': Decimal(str(stats_row['total_revenue'] or 0)),
            'avg_invoice_amount': Decimal(str(stats_row['avg_invoice_amount'] or 0)),
            'top_product': top_product_row['product_name'] if top_product_row else 'Ürün Yok',
            'top_product_quantity': top_product_row['total_quantity'] if top_product_row else 0
        }
        
        return stats
    
    def get_daily_sales(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Günlük satış verileri"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(invoice_date) as sale_date,
                COUNT(*) as invoice_count,
                SUM(total_amount) as daily_revenue
            FROM invoices 
            WHERE invoice_date BETWEEN ? AND ?
            GROUP BY DATE(invoice_date)
            ORDER BY sale_date
        """, (start_date, end_date))
        
        daily_data = []
        for row in cursor.fetchall():
            day_data = {
                'date': datetime.fromisoformat(row['sale_date']).date(),
                'invoice_count': row['invoice_count'],
                'revenue': Decimal(str(row['daily_revenue']))
            }
            daily_data.append(day_data)
        
        conn.close()
        return daily_data
    
    def get_monthly_sales(self, year: int) -> List[Dict[str, Any]]:
        """Aylık satış verileri"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%m', invoice_date) as month,
                COUNT(*) as invoice_count,
                SUM(total_amount) as monthly_revenue
            FROM invoices 
            WHERE strftime('%Y', invoice_date) = ?
            GROUP BY strftime('%m', invoice_date)
            ORDER BY month
        """, (str(year),))
        
        monthly_data = []
        for row in cursor.fetchall():
            month_data = {
                'month': int(row['month']),
                'invoice_count': row['invoice_count'],
                'revenue': Decimal(str(row['monthly_revenue']))
            }
            monthly_data.append(month_data)
        
        conn.close()
        return monthly_data
    
    def get_product_sales_trend(self, product_code: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Ürün satış trendi"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(i.invoice_date) as sale_date,
                SUM(ii.quantity) as daily_quantity,
                SUM(ii.total_price) as daily_revenue
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE ii.product_code = ? 
            AND i.invoice_date BETWEEN ? AND ?
            GROUP BY DATE(i.invoice_date)
            ORDER BY sale_date
        """, (product_code, start_date, end_date))
        
        trend_data = []
        for row in cursor.fetchall():
            trend_item = {
                'date': datetime.fromisoformat(row['sale_date']).date(),
                'quantity': row['daily_quantity'],
                'revenue': Decimal(str(row['daily_revenue']))
            }
            trend_data.append(trend_item)
        
    def get_daily_sales_data(self, start_date: datetime, end_date: datetime) -> str:
        """Günlük satış grafik verileri"""
        daily_data = self.get_daily_sales(start_date, end_date)
        
        if not daily_data:
            return "Veri bulunamadı"
        
        result = "Günlük Satış Verileri:\n"
        for data in daily_data[-7:]:  # Son 7 gün
            result += f"{data['date']}: {data['invoice_count']} fiş, {data['revenue']:.2f} ₺\n"
        
        return result
    
    def get_monthly_sales_data(self, start_date: datetime, end_date: datetime) -> str:
        """Aylık satış grafik verileri"""
        current_year = datetime.now().year
        monthly_data = self.get_monthly_sales(current_year)
        
        if not monthly_data:
            return "Veri bulunamadı"
        
        result = "Aylık Satış Verileri:\n"
        for data in monthly_data:
            result += f"{data['month']}. Ay: {data['invoice_count']} fiş, {data['revenue']:.2f} ₺\n"
        
        return result
    
    def get_product_sales_data(self) -> str:
        """Ürün satış grafik verileri"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        products = self.get_product_analysis(start_date, end_date)
        
        if not products:
            return "Veri bulunamadı"
        
        result = "En Çok Satan Ürünler:\n"
        for i, product in enumerate(products[:5], 1):  # İlk 5 ürün
            result += f"{i}. {product['name']}: {product['quantity']} adet, {product['total']:.2f} ₺\n"
        
        return result
