"""
Raporlama ve Analiz Widget'ı
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QGroupBox, QFrame, QHeaderView,
    QMessageBox, QFileDialog, QTabWidget, QProgressBar
)
from PySide6.QtCore import Qt, QDate, Signal
from datetime import datetime, timedelta
import sys
import os
from PySide6.QtGui import QFont

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Invoice
from modules.report_generator import ReportGenerator

# --- YENİ EKLENEN IMPORT (HATA DÜZELTMESİ) ---
from modules.data_importer import DataImporter
# ---------------------------------------------


class ReportsWidget(QWidget):
    """Raporlama ve Analiz Widget'ı"""
    
    # Signal'lar
    report_generated = Signal(str)  # Rapor oluşturulduğunda
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_generator = ReportGenerator()
        
        # --- YENİ EKLENEN NESNE (HATA DÜZELTMESİ) ---
        # Excel'e aktarmak için doğru sınıfı (DataImporter) oluştur
        self.data_importer = DataImporter()
        # ---------------------------------------------
        
        self.current_report_data = None
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title_label = QLabel("📊 Raporlama ve Analiz")
        title_label.setFont(QFont("Roboto", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Ana içerik alanı
        content_layout = QHBoxLayout()
        
        # Sol panel - Filtreler ve kontroller
        left_panel = self.create_filter_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Sağ panel - Rapor sonuçları
        right_panel = self.create_report_panel()
        content_layout.addWidget(right_panel, 2)
        
        layout.addLayout(content_layout)
    
    def create_filter_panel(self):
        """Filtre paneli oluştur"""
        group = QGroupBox("📋 Rapor Filtreleri")
        group.setFont(QFont("Roboto", 12, QFont.Weight.Bold))
        layout = QVBoxLayout(group)
        
        # Tarih aralığı
        date_layout = QGridLayout()
        
        date_layout.addWidget(QLabel("Başlangıç Tarihi:"), 0, 0)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date, 0, 1)
        
        date_layout.addWidget(QLabel("Bitiş Tarihi:"), 1, 0)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date, 1, 1)
        
        layout.addLayout(date_layout)
        
        # Rapor türü
        layout.addWidget(QLabel("Rapor Türü:"))
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Günlük Satış Raporu",
            "Aylık Satış Raporu", 
            "Ürün Bazlı Rapor",
            "Müşteri Bazlı Rapor"
        ])
        layout.addWidget(self.report_type)
        
        # Butonlar
        button_layout = QVBoxLayout()
        
        self.generate_btn = QPushButton("📊 Rapor Oluştur")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        button_layout.addWidget(self.generate_btn)
        
        self.excel_btn = QPushButton("📄 Excel'e Aktar")
        self.excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.excel_btn)
        
        self.pdf_btn = QPushButton("📄 PDF Oluştur")
        self.pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        button_layout.addWidget(self.pdf_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return group
    
    def create_report_panel(self):
        """Rapor paneli oluştur"""
        group = QGroupBox("📈 Rapor Sonuçları")
        group.setFont(QFont("Roboto", 12, QFont.Weight.Bold))
        layout = QVBoxLayout(group)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Rapor tab'ı
        self.report_tab = self.create_report_tab()
        self.tab_widget.addTab(self.report_tab, "📊 Rapor")
        
        # Grafik tab'ı
        self.chart_tab = self.create_chart_tab()
        self.tab_widget.addTab(self.chart_tab, "📈 Grafik")
        
        layout.addWidget(self.tab_widget)
        
        return group
    
    def create_report_tab(self):
        """Rapor tab'ı oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Rapor tablosu
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Tarih", "Fiş No", "Müşteri", "Ürün", "Miktar", "Tutar"
        ])
        
        # Tablo ayarları
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.report_table)
        
        # Özet bilgiler
        summary_layout = QHBoxLayout()
        
        self.total_label = QLabel("Toplam: 0 ₺")
        self.total_label.setFont(QFont("Roboto", 12, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #27ae60;")
        summary_layout.addWidget(self.total_label)
        
        self.count_label = QLabel("Fiş Sayısı: 0")
        self.count_label.setFont(QFont("Roboto", 12, QFont.Weight.Bold))
        self.count_label.setStyleSheet("color: #3498db;")
        summary_layout.addWidget(self.count_label)
        
        layout.addLayout(summary_layout)
        
        return widget
    
    def create_chart_tab(self):
        """Grafik tab'ı oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grafik butonları
        button_layout = QHBoxLayout()
        
        daily_btn = QPushButton("📅 Günlük Satışlar")
        daily_btn.clicked.connect(self.show_daily_sales_chart)
        button_layout.addWidget(daily_btn)
        
        monthly_btn = QPushButton("📆 Aylık Satışlar")
        monthly_btn.clicked.connect(self.show_monthly_sales_chart)
        button_layout.addWidget(monthly_btn)
        
        product_btn = QPushButton("📦 Ürün Satışları")
        product_btn.clicked.connect(self.show_product_sales_chart)
        button_layout.addWidget(product_btn)
        
        layout.addLayout(button_layout)
        
        # Grafik alanı
        self.chart_label = QLabel("Grafik burada görüntülenecek\nButonlara tıklayarak grafikleri görüntüleyebilirsiniz")
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                color: #666;
            }
        """)
        layout.addWidget(self.chart_label)
        
        return widget
    
    def setup_connections(self):
        """Signal-slot bağlantılarını kur"""
        # Rapor butonları
        self.generate_btn.clicked.connect(self.generate_report)
        self.excel_btn.clicked.connect(self.export_to_excel)
        self.pdf_btn.clicked.connect(self.export_to_pdf)
        
        # Tarih değişiklikleri
        self.start_date.dateChanged.connect(self.on_date_changed)
        self.end_date.dateChanged.connect(self.on_date_changed)
    
    def on_date_changed(self):
        """Tarih değiştiğinde"""
        # Otomatik rapor güncelleme (isteğe bağlı)
        pass
    
    def generate_report(self):
        """Rapor oluştur"""
        try:
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()
            report_type = self.report_type.currentText()
            
            # Rapor verilerini al
            if "Günlük" in report_type:
                self.current_report_data = self.report_generator.get_daily_sales(start_date, end_date)
            elif "Aylık" in report_type:
                self.current_report_data = self.report_generator.get_monthly_sales(start_date.year)
            elif "Ürün" in report_type:
                self.current_report_data = self.report_generator.get_product_analysis(start_date, end_date)
            elif "Müşteri" in report_type:
                self.current_report_data = self.report_generator.get_customer_analysis(start_date, end_date)
            else:
                self.current_report_data = []

            # Tabloyu güncelle
            self.update_report_table()
            
            # Signal gönder
            self.report_generated.emit(f"{report_type} oluşturuldu")
            
            QMessageBox.information(self, "Başarılı", f"{report_type} başarıyla oluşturuldu!")
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Rapor oluşturulamadı: {str(e)}")
            print(f"Rapor oluşturma hatası: {e}") # Debug için
    
    def update_report_table(self):
        """Rapor tablosunu güncelle"""
        if not self.current_report_data:
            self.report_table.setRowCount(0)
            self.total_label.setText("Toplam Tutar: 0.00 ₺")
            self.count_label.setText("Toplam Satır: 0")
            return
        
        # Tabloyu temizle
        self.report_table.setRowCount(0)
        
        # Verileri ekle
        total_amount = 0
        row_count = 0
        
        # Rapor türüne göre tabloyu doldur
        report_type = self.report_type.currentText()

        # Sütun başlıklarını rapora göre ayarla
        if "Ürün" in report_type:
            headers = ["Kod", "Ürün Adı", "Toplam Miktar", "Toplam Tutar", "Ort. Fiyat", ""]
        elif "Müşteri" in report_type:
            headers = ["Müşteri Adı", "Fiş Sayısı", "Toplam Tutar", "Ort. Fiş Tutarı", "", ""]
        elif "Günlük" in report_type:
            headers = ["Tarih", "Fiş Sayısı", "Günlük Ciro", "", "", ""]
        elif "Aylık" in report_type:
            headers = ["Ay", "Fiş Sayısı", "Aylık Ciro", "", "", ""]
        else:
            headers = ["Tarih", "Fiş No", "Müşteri", "Ürün", "Miktar", "Tutar"]
        
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)


        for item in self.current_report_data:
            row = self.report_table.rowCount()
            self.report_table.insertRow(row)
            
            # Rapor türüne göre satırları doldur
            if "Ürün" in report_type:
                self.report_table.setItem(row, 0, QTableWidgetItem(item.get('code', '')))
                self.report_table.setItem(row, 1, QTableWidgetItem(item.get('name', '')))
                self.report_table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', 0))))
                self.report_table.setItem(row, 3, QTableWidgetItem(f"{item.get('total', 0):.2f} ₺"))
                self.report_table.setItem(row, 4, QTableWidgetItem(f"{item.get('avg_price', 0):.2f} ₺"))
                total_amount += item.get('total', 0)
            elif "Müşteri" in report_type:
                self.report_table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))
                self.report_table.setItem(row, 1, QTableWidgetItem(str(item.get('invoice_count', 0))))
                self.report_table.setItem(row, 2, QTableWidgetItem(f"{item.get('total_amount', 0):.2f} ₺"))
                self.report_table.setItem(row, 3, QTableWidgetItem(f"{item.get('avg_amount', 0):.2f} ₺"))
                total_amount += item.get('total_amount', 0)
            elif "Günlük" in report_type:
                self.report_table.setItem(row, 0, QTableWidgetItem(str(item.get('date', ''))))
                self.report_table.setItem(row, 1, QTableWidgetItem(str(item.get('invoice_count', 0))))
                self.report_table.setItem(row, 2, QTableWidgetItem(f"{item.get('revenue', 0):.2f} ₺"))
                total_amount += item.get('revenue', 0)
            elif "Aylık" in report_type:
                self.report_table.setItem(row, 0, QTableWidgetItem(str(item.get('month', ''))))
                self.report_table.setItem(row, 1, QTableWidgetItem(str(item.get('invoice_count', 0))))
                self.report_table.setItem(row, 2, QTableWidgetItem(f"{item.get('revenue', 0):.2f} ₺"))
                total_amount += item.get('revenue', 0)
            
            row_count += 1
        
        # Özet bilgileri güncelle
        self.total_label.setText(f"Toplam Tutar: {total_amount:.2f} ₺")
        self.count_label.setText(f"Toplam Satır: {row_count}")
    
    def show_daily_sales_chart(self):
        """Günlük satış grafiği göster"""
        try:
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()
            
            chart_data = self.report_generator.get_daily_sales_data(start_date, end_date)
            
            self.chart_label.setText(f"📅 Günlük Satış Grafiği\n\n{chart_data}")
            
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Grafik oluşturulamadı: {str(e)}")
    
    def show_monthly_sales_chart(self):
        """Aylık satış grafiği göster"""
        try:
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()
            
            # Report generator'daki fonksiyonunuz start/end date bekliyordu, 
            # ancak verdiğiniz kodda (report_generator.py) sadece 'year' alıyor.
            # Şimdilik start_date'in yılını alıyorum.
            chart_data = self.report_generator.get_monthly_sales_data(start_date, end_date)
            
            self.chart_label.setText(f"📆 Aylık Satış Grafiği\n\n{chart_data}")
            
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Grafik oluşturulamadı: {str(e)}")
    
    def show_product_sales_chart(self):
        """Ürün satış grafiği göster"""
        try:
            chart_data = self.report_generator.get_product_sales_data()
            
            self.chart_label.setText(f"📦 Ürün Satış Grafiği\n\n{chart_data}")
            
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Grafik oluşturulamadı: {str(e)}")
    

    # --- BU FONKSİYON TAMAMEN DEĞİŞTİ (HATA DÜZELTMESİ) ---
    def export_to_excel(self):
        """
        Fişleri tarih aralığına göre Excel'e aktarır.
        Not: Bu fonksiyon 'Geçmiş Fişler'i aktarır, mevcut tabloyu değil.
        """
        try:
            # 1. Kullanıcıdan tarih aralığını al (Python formatında)
            start_date_py = self.start_date.date().toPython()
            end_date_py = self.end_date.date().toPython()

            # 2. DataImporter'ın beklediği string formatına (ISO) çevir
            #    DataImporter'daki sorgu 'BETWEEN ? AND ?' olduğu için 
            #    tarihleri doğrudan ISO formatında string olarak gönderebiliriz.
            start_date_str = start_date_py.isoformat()
            end_date_str = end_date_py.isoformat()
            
            # 3. Dosya kaydetme diyaloğunu aç
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Excel Fiş Raporu Kaydet", 
                f"fis_raporu_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                # 4. DataImporter'daki DOĞRU fonksiyonu çağır
                print(f"DEBUG: export_invoices çağrılıyor. Path: {file_path}, Start: {start_date_str}, End: {end_date_str}")
                self.data_importer.export_invoices(
                    file_path=file_path, 
                    start_date=start_date_str, 
                    end_date=end_date_str
                )
                QMessageBox.information(self, "Başarılı", f"Fiş raporu Excel'e aktarıldı:\n{file_path}")
                    
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Excel dosyası oluşturulamadı!\nHata: {str(e)}")
            print(f"Excel aktarım hatası: {e}") # Debug için
    # --- DEĞİŞİKLİK SONU ---

    
    def export_to_pdf(self):
        """PDF oluştur"""
        if not self.current_report_data:
            QMessageBox.warning(self, "Uyarı", "Önce rapor oluşturun!")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "PDF Dosyası Kaydet", 
                f"rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Dosyaları (*.pdf)"
            )
            
            if file_path:
                # PDF oluşturma mantığını ReportGenerator'a devret
                
                # Rapor verisini 'generate_report_pdf'nin beklediği formata sok
                report_data_dict = {
                    'type': self.report_type.currentText(),
                    'start_date': self.start_date.date().toString("dd.MM.yyyy"),
                    'end_date': self.end_date.date().toString("dd.MM.yyyy"),
                    'stats': {
                         'total_revenue': sum(item.get('total', item.get('total_amount', item.get('revenue', 0))) for item in self.current_report_data),
                         'total_invoices': len(self.current_report_data),
                         # Bu veriler 'report_generator.py' içinden daha doğru hesaplanmalı
                         'avg_invoice_amount': 0, 
                         'top_product': 'N/A' 
                    },
                    'details': self.current_report_data
                }
                
                # report_generator.py dosyanızda 'generate_report_pdf' fonksiyonu yoksa bu satır hata verir
                self.report_generator.generate_report_pdf(report_data_dict, file_path)
                QMessageBox.information(self, "Başarılı", f"Rapor PDF olarak kaydedildi:\n{file_path}")
                
        except AttributeError as ae:
             if 'generate_report_pdf' in str(ae):
                 QMessageBox.warning(self, "Hata", "PDF oluşturma fonksiyonu (generate_report_pdf) 'report_generator.py' içinde bulunamadı.")
             else:
                 QMessageBox.warning(self, "Hata", f"PDF oluşturma başarısız: {str(ae)}")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"PDF oluşturma başarısız: {str(e)}")
    
    def refresh_data(self):
        """Verileri yenile"""
        # Mevcut raporu yeniden oluştur
        if self.current_report_data:
            self.generate_report()