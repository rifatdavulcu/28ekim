"""
Geçmiş Fişler Widget'ı (Excel Export Düzeltildi)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QDateEdit, QTextEdit,
    QGroupBox, QFrame, QHeaderView, QMessageBox,
    QFileDialog, QProgressBar, QTabWidget
)
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QFont
from datetime import datetime, timedelta
import sys 
import os

from decimal import Decimal

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Invoice
from modules.invoice_manager import InvoiceManager
from utils.pdf_generator import PDFGenerator
# --- YENİ EKLENEN IMPORT (Excel Export için) ---
from modules.data_importer import DataImporter
# ---------------------------------------------


class InvoiceHistoryWidget(QWidget):
    """Geçmiş fişler widget'ı"""

    def __init__(self):
        super().__init__()
        self.invoice_manager = InvoiceManager()
        self.pdf_generator = PDFGenerator()

        self.init_ui()
        self.setup_connections()

        # Otomatik yenileme timer'ı
        self.refresh_timer = QTimer(self) # Parent eklendi
        # Lambda fonksiyonunu show_message olmadan çağırmak için düzeltme
        self.refresh_timer.timeout.connect(lambda: self.load_invoices(show_message=False))
        self.refresh_timer.start(30000)  # 30 saniyede bir yenile

        # Başlangıçta fişleri yükle
        self.load_invoices(show_message=False)


    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Başlık
        title_label = QLabel("📋 Geçmiş Fişler")
        title_label.setFont(QFont("Roboto", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Filtre paneli
        filter_panel = self.create_filter_panel()
        layout.addWidget(filter_panel)

        # Fiş listesi
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(9) # Sil butonu için 9 sütun
        self.invoice_table.setHorizontalHeaderLabels([
            "Fiş No", "Tarih", "Müşteri", "Ara Toplam", "KDV", "Toplam",
            "Görüntüle", "PDF", "Sil"
        ])
        self.invoice_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Sütun genişliklerini ayarla (Opsiyonel ama daha iyi görünüm için)
        self.invoice_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Fiş No
        self.invoice_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Tarih
        self.invoice_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)        # Müşteri
        self.invoice_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Ara Toplam
        self.invoice_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # KDV
        self.invoice_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Toplam
        self.invoice_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # Görüntüle
        self.invoice_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents) # PDF
        self.invoice_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents) # Sil
        # Seçim modunu ayarla (Tüm satırı seç)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoice_table.setSelectionMode(QTableWidget.SingleSelection) # Tek satır seçimi
        self.invoice_table.setEditTriggers(QTableWidget.NoEditTriggers) # Düzenlemeyi kapat
        layout.addWidget(self.invoice_table)

        # Alt butonlar
        button_panel = self.create_button_panel()
        layout.addWidget(button_panel)

    def create_filter_panel(self):
        """Filtre panelini oluştur"""
        panel = QFrame(); panel.setFrameStyle(QFrame.StyledPanel); panel.setStyleSheet("QFrame { background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; }")
        layout = QHBoxLayout(panel); layout.setSpacing(10)
        layout.addWidget(QLabel("Başlangıç:"))
        self.start_date = QDateEdit(); self.start_date.setDate(QDate.currentDate().addDays(-30)); self.start_date.setCalendarPopup(True); layout.addWidget(self.start_date)
        layout.addWidget(QLabel("Bitiş:"))
        self.end_date = QDateEdit(); self.end_date.setDate(QDate.currentDate()); self.end_date.setCalendarPopup(True); layout.addWidget(self.end_date)
        layout.addWidget(QLabel("Müşteri:"))
        self.customer_filter = QLineEdit(); self.customer_filter.setPlaceholderText("Müşteri adı ara..."); layout.addWidget(self.customer_filter)
        self.filter_btn = QPushButton("🔍 Filtrele"); self.filter_btn.setStyleSheet("QPushButton { background-color: #2196f3; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #1976d2; }"); layout.addWidget(self.filter_btn)
        return panel

    def create_button_panel(self):
        """Buton panelini oluştur"""
        panel = QFrame(); layout = QHBoxLayout(panel); layout.setSpacing(10)
        self.pdf_btn = QPushButton("📄 PDF Oluştur"); self.pdf_btn.setStyleSheet("QPushButton { background-color: #ff9800; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #f57c00; }"); layout.addWidget(self.pdf_btn)
        self.excel_btn = QPushButton("📈 Excel'e Aktar"); self.excel_btn.setStyleSheet("QPushButton { background-color: #4caf50; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #45a049; }"); layout.addWidget(self.excel_btn)
        self.refresh_btn = QPushButton("🔄 Yenile"); self.refresh_btn.setStyleSheet("QPushButton { background-color: #9c27b0; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #7b1fa2; }"); layout.addWidget(self.refresh_btn)
        layout.addStretch(); return panel

    def setup_connections(self):
        """Sinyal bağlantılarını kur"""
        self.filter_btn.clicked.connect(self.filter_invoices)
        self.pdf_btn.clicked.connect(self.generate_selected_pdf) # Seçili olanı PDF yapacak
        self.excel_btn.clicked.connect(self.export_to_excel) # Hatalı fonksiyonu çağırıyordu, düzeltildi
        self.refresh_btn.clicked.connect(lambda: self.load_invoices(show_message=True)) # Yenile butonu mesaj göstersin
        self.customer_filter.textChanged.connect(self.filter_invoices) # Yazarken filtrele

    def load_invoices(self, show_message=True):
        """Fişleri yükle"""
        print("DEBUG: load_invoices çağrıldı.") # Debug
        try:
            start_date = self.start_date.date().toPython()
            end_date_obj = self.end_date.date().toPython()
            # Bitiş gününü dahil etmek için sonraki günün başlangıcını al
            end_date = end_date_obj + timedelta(days=1)

            # Başlangıç ve bitiş aynıysa veya başlangıç bitişten sonraysa mantıksız olur,
            # başlangıcı 30 gün geriye alabiliriz veya kullanıcıyı uyarabiliriz.
            # Şimdilik başlangıcı 30 gün geri alalım.
            if start_date >= end_date_obj:
                 start_date = end_date_obj - timedelta(days=30)
                 self.start_date.setDate(QDate(start_date.year, start_date.month, start_date.day)) # UI'yı da güncelle
                 if show_message:
                     QMessageBox.information(self, "Bilgi", "Başlangıç tarihi bitiş tarihinden sonra olamaz. Son 30 gün gösteriliyor.")


            print(f"DEBUG: Fişler yükleniyor: {start_date} - {end_date_obj}") # Debug
            invoices = self.invoice_manager.get_invoices_by_date_range(start_date, end_date) # Manager'a doğru tarihleri gönder

            if not invoices:
                if show_message:
                    QMessageBox.information(self, "Bilgi", "Seçilen tarih aralığında fiş bulunamadı!")
                self.invoice_table.setRowCount(0) # Tabloyu temizle
                return

            self.populate_invoice_table(invoices)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Fişler yüklenemedi!\nHata: {str(e)}")
            print(f"DEBUG: Fiş yükleme hatası: {e}") # Debug

    def populate_invoice_table(self, invoices):
        """Fiş tablosunu doldur"""
        self.invoice_table.setRowCount(0) # Önce temizle
        self.invoice_table.setRowCount(len(invoices))
        print(f"DEBUG: Tablo dolduruluyor: {len(invoices)} fiş.") # Debug

        for row, invoice in enumerate(invoices):
             # invoice None veya eksik attribute kontrolü
            if not invoice or not hasattr(invoice, 'invoice_number'):
                print(f"UYARI: Satır {row} için geçersiz fiş verisi.")
                continue

            # Fiş No
            item_num = QTableWidgetItem(invoice.invoice_number)
            self.invoice_table.setItem(row, 0, item_num)
            # Tarih
            date_str = invoice.invoice_date.strftime("%d.%m.%Y %H:%M") if hasattr(invoice, 'invoice_date') and invoice.invoice_date else "N/A"
            item_date = QTableWidgetItem(date_str)
            self.invoice_table.setItem(row, 1, item_date)
            # Müşteri
            item_cust = QTableWidgetItem(invoice.customer_name or "")
            self.invoice_table.setItem(row, 2, item_cust)
            # Ara Toplam
            item_sub = QTableWidgetItem(f"{invoice.subtotal or 0:.2f} TL"); item_sub.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.invoice_table.setItem(row, 3, item_sub)
            # KDV
            item_tax = QTableWidgetItem(f"{invoice.tax_amount or 0:.2f} TL"); item_tax.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.invoice_table.setItem(row, 4, item_tax)
            # Toplam
            item_total = QTableWidgetItem(f"{invoice.total_amount or 0:.2f} TL"); item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_total.setFont(QFont("Roboto", 10, QFont.Weight.Bold)) # Toplamı kalın yap
            self.invoice_table.setItem(row, 5, item_total)

            # Görüntüle butonu
            view_btn = QPushButton("👁️"); view_btn.setToolTip("Fiş Detaylarını Görüntüle")
            view_btn.clicked.connect(lambda checked, inv=invoice: self.view_invoice(inv))
            self.invoice_table.setCellWidget(row, 6, view_btn)
            # PDF butonu
            pdf_btn = QPushButton("📄"); pdf_btn.setToolTip("Bu Fişi PDF Olarak Kaydet")
            pdf_btn.clicked.connect(lambda checked, inv=invoice: self.generate_single_invoice_pdf(inv)) # Ayrı fonksiyon
            self.invoice_table.setCellWidget(row, 7, pdf_btn)
            # Sil butonu
            delete_btn = QPushButton("❌"); delete_btn.setToolTip("Bu Fişi Sil")
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white; border:none; border-radius: 3px;")
            delete_btn.clicked.connect(lambda checked, num=invoice.invoice_number: self.confirm_delete_invoice(num))
            self.invoice_table.setCellWidget(row, 8, delete_btn)

        # Tablonun içeriğe göre boyutlanmasını sağla (ilk iki sütun için)
        # self.invoice_table.resizeColumnsToContents()
        print("DEBUG: Tablo dolduruldu.") # Debug


    def filter_invoices(self):
        """Fişleri filtrele"""
        print("DEBUG: filter_invoices çağrıldı.") # Debug
        try:
            start_date = self.start_date.date().toPython()
            end_date_obj = self.end_date.date().toPython()
            end_date = end_date_obj + timedelta(days=1) # Bitiş gününü dahil et

            if start_date >= end_date_obj:
                 # Mantıksız tarih aralığı, belki ilk yüklemedeki gibi davranmalı?
                 # Şimdilik filtrelemeden çıkalım veya kullanıcıyı uyaralım.
                 print("DEBUG: Geçersiz tarih aralığı, filtreleme yapılmadı.")
                 # self.load_invoices(show_message=False) # Ya da varsayılan aralığı yükle
                 return

            customer_filter = self.customer_filter.text().strip()
            print(f"DEBUG: Filtreleme: {start_date} - {end_date_obj}, Müşteri: '{customer_filter}'") # Debug

            invoices = self.invoice_manager.get_invoices_by_date_range(start_date, end_date)

            # Müşteri filtresi uygula (büyük/küçük harf duyarsız)
            if customer_filter:
                invoices = [inv for inv in invoices if inv and hasattr(inv, 'customer_name') and inv.customer_name and customer_filter.lower() in inv.customer_name.lower()]
                print(f"DEBUG: Müşteri filtresi sonrası kalan fiş sayısı: {len(invoices)}") # Debug

            self.populate_invoice_table(invoices)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Filtreleme hatası!\nHata: {str(e)}")
            print(f"DEBUG: Filtreleme hatası: {e}") # Debug

    def confirm_delete_invoice(self, invoice_number):
        """Fişi silmeden önce kullanıcıdan onay al"""
        msg_box = QMessageBox(self); msg_box.setWindowTitle("Silme Onayı"); msg_box.setText(f"<b>{invoice_number}</b> numaralı fişi kalıcı olarak silmek istediğinizden emin misiniz?"); msg_box.setInformativeText("Bu işlem geri alınamaz."); msg_box.setIcon(QMessageBox.Warning); msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No); msg_box.setDefaultButton(QMessageBox.No)
        ret = msg_box.exec()
        if ret == QMessageBox.Yes:
            self.delete_invoice(invoice_number)

    def delete_invoice(self, invoice_number):
        """Fişi veritabanından sil"""
        try:
            # InvoiceManager'da bu isimde bir metod olduğunu varsayıyoruz
            if hasattr(self.invoice_manager, 'delete_invoice_by_number'):
                self.invoice_manager.delete_invoice_by_number(invoice_number)
                QMessageBox.information(self, "Başarılı", f"{invoice_number} numaralı fiş başarıyla silindi.")
                self.load_invoices(show_message=False) # Tabloyu yenile
            else:
                 QMessageBox.critical(self, "Hata", "InvoiceManager'da 'delete_invoice_by_number' metodu bulunamadı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Fiş silinirken bir hata oluştu:\n{str(e)}")

    def view_invoice(self, invoice):
        """Fişi görüntüle"""
        try:
            full_invoice = self.invoice_manager.get_invoice_by_number(invoice.invoice_number)
            if full_invoice:
                self.show_invoice_details(full_invoice)
            else:
                QMessageBox.warning(self, "Uyarı", "Fiş detayları bulunamadı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Fiş görüntülenemedi!\nHata: {str(e)}")

    def show_invoice_details(self, invoice):
        """Fiş detaylarını bir dialogda göster"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout # QHBoxLayout eklendi
        dialog = QDialog(self); dialog.setWindowTitle(f"Fiş Detayları - {invoice.invoice_number}"); dialog.setModal(True); dialog.resize(600, 500)
        layout = QVBoxLayout(dialog)
        details_text = f"""
FİŞ DETAYLARI
═══════════════════════════════════════════════════════════════
Fiş No: {invoice.invoice_number}
Tarih: {invoice.invoice_date.strftime('%d.%m.%Y %H:%M') if hasattr(invoice, 'invoice_date') and invoice.invoice_date else "N/A"}
Müşteri: {invoice.customer_name or ""}
Adres: {invoice.customer_address or 'Belirtilmemiş'}
Teslim Eden: {invoice.delivery_person or 'Belirtilmemiş'}
Teslim Alan: {invoice.receiver_person or 'Belirtilmemiş'}

ÜRÜN LİSTESİ
═══════════════════════════════════════════════════════════════
"""
        if invoice.items: # None kontrolü
            for item in invoice.items:
                 if item: # item None kontrolü
                     details_text += f"""
Kod: {item.product_code or ""}
Ürün: {item.product_name or ""}
Miktar: {item.quantity or 0}
Birim Fiyat: {item.unit_price or 0:.2f} TL
Toplam: {item.total_price or 0:.2f} TL
───────────────────────────────────────────────────────────────
"""
        discount_amount = getattr(invoice, 'discount_amount', Decimal('0.0')) or Decimal('0.0')
        details_text += f"""

FİYAT ÖZETİ
═══════════════════════════════════════════════════════════════
Ara Toplam: {invoice.subtotal or 0:.2f} TL
"""
        if discount_amount > 0:
             details_text += f"İndirim: -{discount_amount:.2f} TL\n"
        details_text += f"""KDV (%20): {invoice.tax_amount or 0:.2f} TL
TOPLAM: {invoice.total_amount or 0:.2f} TL
"""
        text_edit = QTextEdit(); text_edit.setPlainText(details_text); text_edit.setReadOnly(True); layout.addWidget(text_edit)
        button_layout = QHBoxLayout() # QHBoxLayout kullanıldı
        pdf_btn = QPushButton("📄 PDF Oluştur"); pdf_btn.clicked.connect(lambda: self.generate_single_invoice_pdf(invoice)); button_layout.addWidget(pdf_btn)
        close_btn = QPushButton("❌ Kapat"); close_btn.clicked.connect(dialog.close); button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        dialog.exec()

    def generate_single_invoice_pdf(self, invoice):
        """Tek bir fiş için PDF oluştur (dialog içinden çağrılır)"""
        try:
            # Önce tam fiş detaylarını (item'lar dahil) aldığından emin ol
            full_invoice = self.invoice_manager.get_invoice_by_number(invoice.invoice_number)
            if not full_invoice:
                 QMessageBox.warning(self, "Uyarı", "PDF oluşturulacak fiş detayları bulunamadı!")
                 return

            file_path, _ = QFileDialog.getSaveFileName(self, "PDF Kaydet", f"fis_{full_invoice.invoice_number}.pdf", "PDF Dosyaları (*.pdf)")
            if file_path:
                self.pdf_generator.generate_invoice_pdf(full_invoice, file_path)
                QMessageBox.information(self, "Başarılı", f"PDF oluşturuldu!\nDosya: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturulamadı!\nHata: {str(e)}")

    def generate_selected_pdf(self):
        """Seçili fiş için PDF oluştur (ana ekrandaki buton)"""
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Uyarı", "Lütfen PDF oluşturmak için tablodan bir fiş seçin!")
            return
        if len(selected_rows) > 1:
             QMessageBox.warning(self, "Uyarı", "Lütfen sadece bir fiş seçin.")
             return

        selected_row_index = selected_rows[0].row()
        invoice_number_item = self.invoice_table.item(selected_row_index, 0) # Fiş No sütunu

        if not invoice_number_item:
             QMessageBox.warning(self, "Uyarı", "Seçili satırdan fiş numarası alınamadı.")
             return

        invoice_number = invoice_number_item.text()
        print(f"DEBUG: Seçili fiş PDF'i oluşturulacak: {invoice_number}") # Debug

        try:
            # Tam fiş bilgilerini al
            full_invoice = self.invoice_manager.get_invoice_by_number(invoice_number)
            if full_invoice:
                self.generate_single_invoice_pdf(full_invoice) # PDF oluşturma fonksiyonunu çağır
            else:
                QMessageBox.warning(self, "Uyarı", f"'{invoice_number}' numaralı fiş detayları bulunamadı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Fiş detayları alınırken hata oluştu!\nHata: {str(e)}")


    # --- BU FONKSİYON TAMAMEN DEĞİŞTİ (Excel Export Düzeltildi) ---
    def export_to_excel(self):
        """Excel'e aktar (DÜZELTİLDİ - DataImporter kullanılıyor)"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Excel Kaydet", f"fisler_{datetime.now().strftime('%Y%m%d')}.xlsx", "Excel Dosyaları (*.xlsx)"
            )

            if file_path:
                # --- DOĞRU SINIFI KULLAN ---
                # excel_handler = ExcelHandler() # YANLIŞ
                data_importer = DataImporter() # DOĞRU

                # --- TARİHLERİ DOĞRU FORMATTA (ISO STRING) AL ---
                start_date_py = self.start_date.date().toPython()
                end_date_py = self.end_date.date().toPython()
                # DataImporter.export_invoices BETWEEN kullandığı için +1 gün GEREKMEZ
                start_date_str = start_date_py.isoformat()
                end_date_str = end_date_py.isoformat()
                # --------------------------------------------------

                print(f"DEBUG (History): export_invoices çağrılıyor. Path: {file_path}, Start: {start_date_str}, End: {end_date_str}") # Debug

                # --- DOĞRU FONKSİYONU ÇAĞIR ---
                data_importer.export_invoices(
                    file_path=file_path,
                    start_date=start_date_str,
                    end_date=end_date_str
                )
                # -----------------------------

                QMessageBox.information(self, "Başarılı", f"Excel dosyası oluşturuldu!\nDosya: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel dosyası oluşturulamadı!\nHata: {str(e)}")
            print(f"DEBUG (History Excel Export): Hata: {e}") # Debug
    # --- DEĞİŞİKLİK SONU ---