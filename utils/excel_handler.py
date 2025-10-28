"""
Excel işleme modülü
"""
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import os

from database.models import Invoice
from database import db_manager


class ExcelHandler:
    """Excel işleme sınıfı"""
    
    def __init__(self):
        self.db = db_manager
    
    def export_report_to_excel(self, file_path: str, start_date: datetime, 
                                 end_date: datetime, report_type: str):
        """Raporu Excel dosyasına aktar"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                
                if report_type == "Satış Raporu":
                    self._export_sales_report(writer, start_date, end_date)
                elif report_type == "Ürün Analizi":
                    self._export_product_analysis(writer, start_date, end_date)
                elif report_type == "Müşteri Analizi":
                    self._export_customer_analysis(writer, start_date, end_date)
                elif report_type == "Günlük Özet":
                    self._export_daily_summary(writer, start_date, end_date)
                elif report_type == "Aylık Özet":
                    self._export_monthly_summary(writer, start_date.year)
                else:
                    # Genel rapor - tüm verileri ekle
                    self._export_sales_report(writer, start_date, end_date)
                    self._export_product_analysis(writer, start_date, end_date)
                    self._export_customer_analysis(writer, start_date, end_date)
                
        except Exception as e:
            raise Exception(f"Excel dosyası oluşturulamadı: {str(e)}")
    
    def _export_sales_report(self, writer, start_date: datetime, end_date: datetime):
        """Satış raporunu Excel'e aktar"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                invoice_number,
                invoice_date,
                customer_name,
                customer_address,
                delivery_person,
                receiver_person,
                subtotal,
                tax_amount,
                total_amount
            FROM invoices 
            WHERE invoice_date BETWEEN ? AND ?
            ORDER BY invoice_date DESC
        """, (start_date, end_date))
        
        sales_data = []
        for row in cursor.fetchall():
            sales_data.append({
                'Fiş No': row['invoice_number'],
                'Tarih': row['invoice_date'],
                'Müşteri': row['customer_name'],
                'Adres': row['customer_address'],
                'Teslim Eden': row['delivery_person'],
                'Teslim Alan': row['receiver_person'],
                'Ara Toplam': row['subtotal'],
                'KDV': row['tax_amount'],
                'Toplam': row['total_amount']
            })
        
        conn.close()
        
        df = pd.DataFrame(sales_data)
        df.to_excel(writer, sheet_name='Satış Raporu', index=False)
    
    def _export_product_analysis(self, writer, start_date: datetime, end_date: datetime):
        """Ürün analizini Excel'e aktar"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ii.product_code,
                ii.product_name,
                SUM(ii.quantity) as total_quantity,
                SUM(ii.total_price) as total_amount,
                AVG(ii.unit_price) as avg_price,
                COUNT(DISTINCT i.id) as invoice_count
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.invoice_date BETWEEN ? AND ?
            GROUP BY ii.product_code, ii.product_name
            ORDER BY total_amount DESC
        """, (start_date, end_date))
        
        product_data = []
        for row in cursor.fetchall():
            product_data.append({
                'Ürün Kodu': row['product_code'],
                'Ürün Adı': row['product_name'],
                'Satılan Miktar': row['total_quantity'],
                'Toplam Tutar': row['total_amount'],
                'Ortalama Fiyat': row['avg_price'],
                'Fiş Sayısı': row['invoice_count']
            })
        
        conn.close()
        
        df = pd.DataFrame(product_data)
        df.to_excel(writer, sheet_name='Ürün Analizi', index=False)
    
    def _export_customer_analysis(self, writer, start_date: datetime, end_date: datetime):
        """Müşteri analizini Excel'e aktar"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                customer_name,
                customer_address,
                COUNT(*) as invoice_count,
                SUM(total_amount) as total_amount,
                AVG(total_amount) as avg_amount,
                MIN(invoice_date) as first_purchase,
                MAX(invoice_date) as last_purchase
            FROM invoices 
            WHERE invoice_date BETWEEN ? AND ?
            GROUP BY customer_name, customer_address
            ORDER BY total_amount DESC
        """, (start_date, end_date))
        
        customer_data = []
        for row in cursor.fetchall():
            customer_data.append({
                'Müşteri Adı': row['customer_name'],
                'Adres': row['customer_address'],
                'Fiş Sayısı': row['invoice_count'],
                'Toplam Tutar': row['total_amount'],
                'Ortalama Tutar': row['avg_amount'],
                'İlk Alış': row['first_purchase'],
                'Son Alış': row['last_purchase']
            })
        
        conn.close()
        
        df = pd.DataFrame(customer_data)
        df.to_excel(writer, sheet_name='Müşteri Analizi', index=False)
    
    def _export_daily_summary(self, writer, start_date: datetime, end_date: datetime):
        """Günlük özeti Excel'e aktar"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(invoice_date) as sale_date,
                COUNT(*) as invoice_count,
                SUM(total_amount) as daily_revenue,
                AVG(total_amount) as avg_invoice_amount
            FROM invoices 
            WHERE invoice_date BETWEEN ? AND ?
            GROUP BY DATE(invoice_date)
            ORDER BY sale_date
        """, (start_date, end_date))
        
        daily_data = []
        for row in cursor.fetchall():
            daily_data.append({
                'Tarih': row['sale_date'],
                'Fiş Sayısı': row['invoice_count'],
                'Günlük Ciro': row['daily_revenue'],
                'Ortalama Fiş': row['avg_invoice_amount']
            })
        
        conn.close()
        
        df = pd.DataFrame(daily_data)
        df.to_excel(writer, sheet_name='Günlük Özet', index=False)
    
    def _export_monthly_summary(self, writer, year: int):
        """Aylık özeti Excel'e aktar"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%m', invoice_date) as month,
                COUNT(*) as invoice_count,
                SUM(total_amount) as monthly_revenue,
                AVG(total_amount) as avg_invoice_amount
            FROM invoices 
            WHERE strftime('%Y', invoice_date) = ?
            GROUP BY strftime('%m', invoice_date)
            ORDER BY month
        """, (str(year),))
        
        monthly_data = []
        month_names = {
            '01': 'Ocak', '02': 'Şubat', '03': 'Mart', '04': 'Nisan',
            '05': 'Mayıs', '06': 'Haziran', '07': 'Temmuz', '08': 'Ağustos',
            '09': 'Eylül', '10': 'Ekim', '11': 'Kasım', '12': 'Aralık'
        }
        
        for row in cursor.fetchall():
            monthly_data.append({
                'Ay': month_names.get(row['month'], row['month']),
                'Fiş Sayısı': row['invoice_count'],
                'Aylık Ciro': row['monthly_revenue'],
                'Ortalama Fiş': row['avg_invoice_amount']
            })
        
        conn.close()
        
        df = pd.DataFrame(monthly_data)
        df.to_excel(writer, sheet_name='Aylık Özet', index=False)
    
    def export_invoice_details_to_excel(self, invoice: Invoice, file_path: str):
        """Fiş detaylarını Excel'e aktar"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                
                # Fiş bilgileri
                invoice_info = {
                    'Bilgi': ['Fiş No', 'Tarih', 'Müşteri', 'Adres', 'Teslim Eden', 'Teslim Alan'],
                    'Değer': [
                        invoice.invoice_number,
                        invoice.invoice_date.strftime('%d.%m.%Y %H:%M'),
                        invoice.customer_name,
                        invoice.customer_address,
                        invoice.delivery_person,
                        invoice.receiver_person
                    ]
                }
                
                df_info = pd.DataFrame(invoice_info)
                df_info.to_excel(writer, sheet_name='Fiş Bilgileri', index=False)
                
                # Ürün detayları
                product_data = []
                for item in invoice.items:
                    product_data.append({
                        'Kod': item.product_code,
                        'Ürün Adı': item.product_name,
                        'Miktar': item.quantity,
                        'Birim Fiyat': float(item.unit_price),
                        'Toplam': float(item.total_price)
                    })
                
                df_products = pd.DataFrame(product_data)
                df_products.to_excel(writer, sheet_name='Ürün Detayları', index=False)
                
                # Özet bilgiler
                summary_data = {
                    'Özet': ['Ara Toplam', 'KDV (%20)', 'TOPLAM'],
                    'Tutar': [
                        float(invoice.subtotal),
                        float(invoice.tax_amount),
                        float(invoice.total_amount)
                    ]
                }
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Özet', index=False)
                
        except Exception as e:
            raise Exception(f"Excel dosyası oluşturulamadı: {str(e)}")
    
    def create_template_file(self, template_type: str, file_path: str):
        """Şablon dosyası oluştur"""
        try:
            if template_type == "products":
                # DataImporter'daki değişiklikle uyumlu hale getirildi
                template_data = {
                    'code': ['PRD001', 'PRD002', 'PRD003'],
                    'name': ['Örnek Ürün 1', 'Örnek Ürün 2', 'Örnek Ürün 3']
                }
            elif template_type == "customers":
                template_data = {
                    'name': ['Örnek Müşteri 1', 'Örnek Müşteri 2', 'Örnek Müşteri 3'],
                    'address': ['Adres 1', 'Adres 2', 'Adres 3'],
                    'phone': ['05551234567', '05559876543', '05555555555'],
                    'email': ['musteri1@email.com', 'musteri2@email.com', 'musteri3@email.com'],
                    'tax_number': ['1234567890', '0987654321', '5555555555']
                }
            else:
                raise ValueError("Geçersiz şablon türü")
            
            df = pd.DataFrame(template_data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            
        except Exception as e:
            raise Exception(f"Şablon dosyası oluşturulamadı: {str(e)}")