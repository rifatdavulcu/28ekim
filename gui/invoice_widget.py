"""
Fiş/Sipariş Yönetimi Widget'ı (vFinal - Yüzdelik İndirim, Toplam Düzeltmeleri)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QSpinBox, QTextEdit,
    QGroupBox, QFrame, QHeaderView, QMessageBox,
    QFileDialog, QProgressBar, QCompleter
)
from PySide6.QtCore import Qt, Signal, QStringListModel, QEvent
from PySide6.QtGui import QFont, QPixmap, QDoubleValidator # QDoubleValidator import
from decimal import Decimal, InvalidOperation # InvalidOperation import
import sys
import os
from datetime import datetime

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Invoice, InvoiceItem, Customer, Product
from modules.invoice_manager import InvoiceManager
from utils.pdf_generator import PDFGenerator
try:
    from database import db_manager
except ImportError:
    db_manager = None
    print("UYARI: db_manager modülü invoice_widget içinde import edilemedi.")


class InvoiceWidget(QWidget):
    """Fiş yönetimi widget'ı"""

    invoice_saved = Signal()
    invoice_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoice_manager = InvoiceManager()
        self.pdf_generator = PDFGenerator()
        self.current_invoice = Invoice(items=[])
        """Fiş/Sipariş Yönetimi widget'ı"""
        # Ana layout'u self widget'ına bağla
        main_container_layout = QVBoxLayout(self)
        main_container_layout.setContentsMargins(10, 10, 10, 10)
        main_container_layout.setSpacing(10)
        
        # Ana widget'ı oluştur (QFrame olarak)
        self.main_widget = QFrame(parent=self)
        self.main_widget.setObjectName("invoiceMainWidget")
        self.main_widget.setFrameStyle(QFrame.StyledPanel)
        
        # Ana layout'u main_widget'a bağla
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Ana widget'ı container'a ekle
        main_container_layout.addWidget(self.main_widget)
        
        self.init_ui()

        if hasattr(self, 'delivery_person'): 
            self.delivery_person.setText("Mehmet Ali") # Ayarlardan gelen sabit değer
            self.delivery_person.setEnabled(False) # Düzenlenemez yap
        
        # İndirim alanları için validator ekle
        if hasattr(self, 'discount_input'):
            self.discount_input.setValidator(QDoubleValidator(0, 9999999, 2))
        
        # --- DEĞİŞİKLİK BAŞLANGICI ---
        # eventFilter'ı kaldırıyoruz, QShortcut kullanacağız
        # eventFilter kaldırıldı, QShortcut kullanılıyor
        
        # Yeni satır eklemek için Shift+Enter kısayolu
        from PySide6.QtGui import QShortcut, QKeySequence
        self.new_row_shortcut = QShortcut(QKeySequence("Shift+Return"), self.cart_table)
        self.new_row_shortcut.activated.connect(self.add_new_blank_row)
        
        # (Artık gizli olan) arama kutusunu yine de aktif etmeliyiz
        if hasattr(self, 'product_search'): self.product_search.setEnabled(True) 
        # --- DEĞİŞİKLİK SONU ---

        self.setup_autocomplete()
        self.setup_connections()
        self.load_customers()
        self.update_totals() # Başlangıçta toplamları sıfırla

    # ... (Dosyanızın 52. satırına kadar olan kısım) ...

        # eventFilter kaldırıldı, QShortcut kullanılıyor

    def _extract_product_code(self, text: str) -> str:
        if not text: return ""
        parts = text.split(' - '); code = parts[0].strip(); return code

    def setup_autocomplete(self):
        """Autocomplete ayarları"""
        if not hasattr(self, 'product_search'): return
        self.completer = QCompleter(self); self.completer.setCaseSensitivity(Qt.CaseInsensitive); self.completer.setFilterMode(Qt.MatchContains); self.completer.setMaxVisibleItems(15)
        self.product_model = QStringListModel(self); self.completer.setModel(self.product_model); self.product_search.setCompleter(self.completer)

    def init_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout'u temizle ve yeniden ayarla
        for i in reversed(range(self.main_layout.count())): 
            item = self.main_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Alt layout'ları da temizle
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            self.main_layout.takeAt(i)
        
        # Başlık
        title_label = QLabel("🧾 Fiş/Sipariş Yönetimi", parent=self.main_widget)
        title_label.setObjectName("titleLabel")  # CSS için
        title_label.setFont(QFont("Roboto", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title_label)
        
        # İçerik bölümü
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Panel sıralaması değişti: Önce müşteri (sağda), sonra ürün (solda)
        customer_panel = self.create_right_panel()  # Müşteri panel (1 birim)
        content_layout.addWidget(customer_panel, 1)
        
        products_panel = self.create_left_panel()   # Ürün panel (2 birim)
        content_layout.addWidget(products_panel, 2)
        
        self.main_layout.addLayout(content_layout)
        
        # Buton paneli
        button_panel = self.create_button_panel()
        self.main_layout.addWidget(button_panel)
        
        # Spacer ekleyerek alt boşluk bırak
        self.main_layout.addStretch()

    def create_left_panel(self):
        """Ürün Arama/Sepet panelini oluştur (SAĞDA)"""
        panel = QFrame(parent=self.main_widget)
        panel.setObjectName("productsPanel")
        panel.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Arama Grubu
        search_group = QGroupBox("🔍 Ürün Arama", parent=panel)
        search_group.setObjectName("searchGroup")
        search_layout = QVBoxLayout(search_group)
        
        self.product_search = QLineEdit(parent=search_group)
        self.product_search.setPlaceholderText("Önce müşteri seçin veya girin...")
        self.product_search.setMinimumHeight(30)  # Yükseklik artırıldı
        search_layout.addWidget(self.product_search)
        
        layout.addWidget(search_group)
        
        # Sepet Grubu
        cart_group = QGroupBox("🛒 Sepet", parent=panel)
        cart_group.setObjectName("cartGroup")
        cart_layout = QVBoxLayout(cart_group)
        
        self.cart_table = QTableWidget(parent=cart_group)
        self.cart_table.setObjectName("cartTable")
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(["Kod", "Ürün Adı", "Miktar", "Birim Fiyat", "Toplam", "İşlem"])
        
        # Sütun genişlikleri ayarlandı
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Kod
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)          # Ürün Adı
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Miktar
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Birim Fiyat
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Toplam
        self.cart_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)           # İşlem
        self.cart_table.setColumnWidth(5, 40)  # İşlem sütunu 40px
        
        # Diğer tablo ayarları
        self.cart_table.setAlternatingRowColors(True)  # Alternatif satır renkleri
        self.cart_table.setShowGrid(True)              # Grid çizgileri
        self.cart_table.setGridStyle(Qt.SolidLine)     # Düz grid çizgisi
        
        cart_layout.addWidget(self.cart_table)
        layout.addWidget(cart_group)
        
        return panel

    # --- BU FONKSİYON DEĞİŞTİ (Yüzdelik İndirim alanı eklendi) ---
    def create_right_panel(self):
        """Müşteri bilgileri panelini oluştur"""
        panel = QFrame(parent=self.main_widget)
        panel.setObjectName("customerPanel")
        panel.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Müşteri Bilgileri Grubu
        customer_group = QGroupBox("👤 Müşteri Bilgileri", parent=panel)
        customer_group.setObjectName("customerGroup")
        customer_layout = QVBoxLayout(customer_group)
        customer_layout.setSpacing(15)
        
        # Grid Panel - Müşteri Bilgileri
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Müşteri Combobox
        customer_label = QLabel("Müşteri:", parent=panel)
        customer_label.setObjectName("fieldLabel")
        
        self.customer_selector = QComboBox(parent=panel)
        self.customer_selector.setObjectName("customerSelector")
        self.customer_selector.setPlaceholderText("Müşteri Seçiniz")
        self.customer_selector.setMinimumWidth(200)
        self.customer_selector.setMinimumHeight(30)
        self.customer_selector.currentIndexChanged.connect(self.on_customer_selected_index)
        self.update_customer_selector()
        
        grid.addWidget(customer_label, 0, 0)
        grid.addWidget(self.customer_selector, 0, 1)

        # Teslim Alan Kişi
        receiver_label = QLabel("Teslim Alan:", parent=customer_group)
        receiver_label.setObjectName("fieldLabel")
        
        self.receiver_person = QLineEdit(parent=customer_group)
        self.receiver_person.setObjectName("receiverPerson")
        self.receiver_person.setPlaceholderText("Teslim alan kişinin adı")
        self.receiver_person.setMinimumHeight(30)
        
        grid.addWidget(receiver_label, 1, 0)
        grid.addWidget(self.receiver_person, 1, 1)
        
        # Grid'i grubun layout'una ekle
        customer_layout.addLayout(grid)
        layout.addWidget(customer_group)
        
        # Özet Panel
        summary_group = QGroupBox("💰 Özet Bilgiler", parent=panel)
        summary_group.setObjectName("summaryGroup")
        summary_layout = QGridLayout(summary_group)
        summary_layout.setSpacing(15)
        
        # Özet etiketleri (hepsi sağa hizalı)
        tax_rate_title = QLabel("KDV Oranı:", parent=summary_group)
        tax_rate_title.setObjectName("summaryLabel")
        tax_rate_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.tax_rate_label = QLabel("20%", parent=summary_group)
        self.tax_rate_label.setObjectName("summaryValue")
        self.tax_rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        summary_layout.addWidget(tax_rate_title, 0, 0)
        summary_layout.addWidget(self.tax_rate_label, 0, 1)
        
        subtotal_title = QLabel("KDV Hariç:", parent=summary_group)
        subtotal_title.setObjectName("summaryLabel")
        subtotal_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.subtotal_label = QLabel("0,00 ₺", parent=summary_group)
        self.subtotal_label.setObjectName("summaryValue")
        self.subtotal_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        summary_layout.addWidget(subtotal_title, 1, 0)
        summary_layout.addWidget(self.subtotal_label, 1, 1)

        # İndirim Tipi ve Tutarı
        discount_type_label = QLabel("İndirim Tipi:", parent=summary_group)
        discount_type_label.setObjectName("summaryLabel")
        discount_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        discount_type_layout = QHBoxLayout()
        self.discount_type_combo = QComboBox(parent=summary_group)
        self.discount_type_combo.addItems(["%", "TL"])
        self.discount_type_combo.setMaximumWidth(60)
        
        self.discount_input = QLineEdit(parent=summary_group)
        self.discount_input.setPlaceholderText("0.00")
        self.discount_input.setText("0.00")
        self.discount_input.setAlignment(Qt.AlignRight)
        
        discount_type_layout.addWidget(self.discount_type_combo)
        discount_type_layout.addWidget(self.discount_input)
        
        summary_layout.addWidget(discount_type_label, 2, 0)
        summary_layout.addLayout(discount_type_layout, 2, 1)
        
        tax_title = QLabel("KDV:", parent=summary_group)
        tax_title.setObjectName("summaryLabel")
        tax_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.tax_label = QLabel("0,00 ₺", parent=summary_group)
        self.tax_label.setObjectName("summaryValue")
        self.tax_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        summary_layout.addWidget(tax_title, 3, 0)
        summary_layout.addWidget(self.tax_label, 3, 1)
        
        total_title = QLabel("TOPLAM:", parent=summary_group)
        total_title.setObjectName("totalLabel")
        total_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_title.setFont(QFont("Roboto", 14, QFont.Bold))
        
        self.total_label = QLabel("0,00 ₺", parent=summary_group)
        self.total_label.setObjectName("totalValue")
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.total_label.setFont(QFont("Roboto", 14, QFont.Bold))
        
        summary_layout.addWidget(total_title, 4, 0)
        summary_layout.addWidget(self.total_label, 4, 1)
        
        # Sütunların eşit genişlikte olmasını sağla
        summary_layout.setColumnStretch(0, 1)
        summary_layout.setColumnStretch(1, 1)
        
        layout.addWidget(summary_group)
        layout.addStretch()  # Alt boşluk için spacer
        
        return panel
    
    # ... (Fonksiyonun geri kalanı)
    #         # TOPLAM
        summary_layout.addWidget(QLabel("TOPLAM:"), 3, 0, Qt.AlignRight); self.total_label = QLabel("0,00 ₺"); self.total_label.setFont(QFont("Roboto", 14, QFont.Bold)); self.total_label.setStyleSheet("color: #1976d2;"); summary_layout.addWidget(self.total_label, 3, 1, Qt.AlignRight)

        summary_layout.setColumnStretch(0, 1); summary_layout.setColumnStretch(1, 1)
        layout.addWidget(summary_group)
        return panel

    def create_button_panel(self):
        """Alt buton panelini oluştur"""
        panel = QFrame(parent=self.main_widget)
        panel.setObjectName("buttonPanel")
        panel.setFrameStyle(QFrame.StyledPanel)
        
        layout = QHBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Yeni Fiş Butonu
        self.new_invoice_btn = QPushButton("🆕 Yeni Fiş", parent=panel)
        self.new_invoice_btn.setObjectName("new_invoice_btn")
        layout.addWidget(self.new_invoice_btn)
        
        # Kaydet Butonu
        self.save_btn = QPushButton("💾 Kaydet", parent=panel)
        self.save_btn.setObjectName("save_btn")
        layout.addWidget(self.save_btn)
        
        # PDF Butonu
        self.pdf_btn = QPushButton("📄 PDF Oluştur", parent=panel)
        self.pdf_btn.setObjectName("pdf_btn")
        layout.addWidget(self.pdf_btn)
        
        # Yazdır Butonu
        self.print_btn = QPushButton("🖨️ Yazdır", parent=panel)
        self.print_btn.setObjectName("print_btn")
        layout.addWidget(self.print_btn)
        
        # Sağa doğru boşluk
        layout.addStretch()
        
        return panel

    def setup_connections(self):
        self.new_invoice_btn.clicked.connect(self.new_invoice); self.save_btn.clicked.connect(self.save_invoice); self.pdf_btn.clicked.connect(self.generate_pdf); self.print_btn.clicked.connect(self.print_invoice)
        if hasattr(self, 'customer_selector'): 
            self.customer_selector.currentIndexChanged.connect(self.on_customer_selected_index)
        if hasattr(self, 'customer_name'):
            self.customer_name.textChanged.connect(self.on_customer_name_changed)
        if hasattr(self, 'discount_input'): self.discount_input.editingFinished.connect(self.on_discount_changed)
        if hasattr(self, 'discount_type_combo'): self.discount_type_combo.currentIndexChanged.connect(self.on_discount_changed)

    def load_customers(self):
        """Müşteri listesini yükle (customer_selector için)"""
        if not hasattr(self, 'customer_selector') or not hasattr(self, 'invoice_manager'): return
        try:
            customers = self.invoice_manager.get_all_customers()
            self.customer_selector.blockSignals(True)
            current_selection_data = self.customer_selector.currentData()
            
            self.customer_selector.clear()
            self.customer_selector.addItem("Müşteri Seç...", userData=None)
            restored_index = 0
            
            for i, customer in enumerate(customers or []):  # None kontrolü
                if customer and hasattr(customer, 'name') and hasattr(customer, 'id'):
                    self.customer_selector.addItem(customer.name, customer)
                    if (current_selection_data and 
                        hasattr(current_selection_data, 'id') and 
                        customer.id == current_selection_data.id):
                        restored_index = i + 1
            
            self.customer_selector.setCurrentIndex(restored_index)
            self.customer_selector.blockSignals(False)
            print(f"DEBUG: Müşteriler yüklendi. Seçili index: {restored_index}")
            
        except Exception as e:
            print(f"Müşteriler yüklenemedi: {e}")
            if hasattr(self, 'customer_selector'):
                self.customer_selector.blockSignals(False)

    def on_discount_changed(self):
        """İndirim (%) veya (TL) alanı düzenlemesi bittiğinde."""
        print("DEBUG: İndirim alanı değişti (editingFinished veya Combo Changed)")
        if not hasattr(self, 'discount_input') or not hasattr(self, 'discount_type_combo'): return
        
        discount_type = self.discount_type_combo.currentText()
        
        try:
            discount_text = self.discount_input.text().replace(',', '.').strip()
            discount_value = Decimal(discount_text if discount_text else '0.0')

            if discount_type == "%":
                # Yüzde 0-100 arasında olmalı
                if not (Decimal('0') <= discount_value <= Decimal('100')):
                    discount_value = max(Decimal('0'), min(Decimal('100'), discount_value)) # Sınırlara çek
                    QMessageBox.warning(self, "Uyarı", "İndirim yüzdesi 0 ile 100 arasında olmalıdır.")
            else: # "TL"
                # Sadece pozitif olmalı
                if discount_value < Decimal('0'):
                    discount_value = Decimal('0.0')
                    QMessageBox.warning(self, "Uyarı", "İndirim tutarı negatif olamaz.")
            
            self.discount_input.blockSignals(True)
            self.discount_input.setText(f"{discount_value:.2f}") # Formatla
            self.discount_input.blockSignals(False)

        except InvalidOperation:
            self.discount_input.blockSignals(True); self.discount_input.setText("0.00"); self.discount_input.blockSignals(False)
            QMessageBox.warning(self, "Uyarı", "Geçersiz indirim formatı.")
        except Exception as e:
            print(f"İndirim formatlama hatası: {e}"); self.discount_input.blockSignals(True); self.discount_input.setText("0.00"); self.discount_input.blockSignals(False)
        
        self.update_totals() # Toplamları yeniden hesapla

    def update_product_suggestions(self, text):
        if not hasattr(self, 'product_model'): return
        if len(text) < 2: self.product_model.setStringList([]); return
        try: products = self.invoice_manager.search_products(text); suggestions = [f"{p.code} - {p.name}" for p in products]; self.product_model.setStringList(suggestions)
        except Exception as e: print(f"Ürün önerileri alınırken hata: {e}"); self.product_model.setStringList([])

    
    # --- BU FONKSİYON GÜNCELLENDİ (Toplam Hesaplama Düzeltmesi) ---
    def add_product_by_code(self, product_code):
        """Ürün koduna göre sepete ekle"""
        print(f"DEBUG: add_product_by_code: '{product_code}'")
        product_code = product_code.strip();
        if not product_code: print("DEBUG: Ürün kodu boş."); return;
        try: product = self.invoice_manager.get_product_by_code(product_code)
        except Exception as e: QMessageBox.critical(self, "Veritabanı Hatası", f"Ürün aranırken hata: {e}"); print(f"DEBUG: get_product_by_code Hata: {e}"); return
        if not product: print(f"DEBUG: Ürün DB'de yok: '{product_code}'"); QMessageBox.warning(self, "Uyarı", f"Ürün bulunamadı: {product_code}"); return
        print(f"DEBUG: Ürün bulundu: ID={product.id}, Ad={product.name}, Fiyat={product.unit_price}")

        if self.current_invoice.items is None: self.current_invoice.items = []
        existing_item = next((item for item in self.current_invoice.items if item and item.product_code == product_code), None)

        if existing_item:
            print(f"DEBUG: Miktar artırılıyor. Eski Miktar={existing_item.quantity}, Fiyat={existing_item.unit_price}")
            existing_item.quantity = (existing_item.quantity or 0) + 1
            unit_price = existing_item.unit_price or Decimal('0.0')
            # DOĞRU HESAPLAMA:
            existing_item.total_price = Decimal(existing_item.quantity) * unit_price
            print(f"DEBUG: Yeni Miktar={existing_item.quantity}, Yeni Toplam Fiyat={existing_item.total_price}")
        else:
            print(f"DEBUG: Yeni ürün ekleniyor.")
            unit_price = Decimal(str(product.unit_price or '0.0')) # Fiyatı Decimal yap
            quantity = 1
            # DOĞRU HESAPLAMA:
            total_price = Decimal(quantity) * unit_price
            new_item = InvoiceItem(product_id=product.id, product_code=product.code, product_name=product.name, quantity=quantity, unit_price=unit_price, total_price=total_price)
            print(f"DEBUG: Yeni item: Miktar={new_item.quantity}, Fiyat={new_item.unit_price}, Toplam={new_item.total_price}")
            self.current_invoice.items.append(new_item)

        print(f"DEBUG: Sepet boyutu: {len(self.current_invoice.items)}")
        self.update_cart_table(); self.update_totals() # Önce tablo, sonra toplamlar

    def update_cart_table(self):
        print("DEBUG: update_cart_table")
        if not hasattr(self, 'cart_table'): return
        self.cart_table.blockSignals(True);
        try: self.cart_table.itemChanged.disconnect(self.on_cart_item_changed)
        except: pass

        item_count = len(self.current_invoice.items or [])
        self.cart_table.setRowCount(item_count)
        print(f"DEBUG: Tablo satır: {item_count}")
        if item_count > 0:
            for row, item in enumerate(self.current_invoice.items or []):
                if item is None: continue
                # --- YENİ: OTOMATİK TAMAMLAMALI KOD HÜCRESİ (Sütun 0) ---
                code_editor = QLineEdit(item.product_code or "")
                code_editor.setCompleter(self.completer) # Mevcut tamamlayıcıyı bağla
                # Sinyaller:
                code_editor.textChanged.connect(self.update_product_suggestions) # Önerileri güncelle
                code_editor.editingFinished.connect(
                    lambda r=row, c=0, editor=code_editor: self._on_cell_editor_finished(r, c, editor.text())
                )
                self.cart_table.setCellWidget(row, 0, code_editor)

                # --- YENİ: OTOMATİK TAMAMLAMALI AD HÜCRESİ (Sütun 1) ---
                name_editor = QLineEdit(item.product_name or "")
                name_editor.setCompleter(self.completer) # Mevcut tamamlayıcıyı bağla
                # Sinyaller:
                name_editor.textChanged.connect(self.update_product_suggestions) # Önerileri güncelle
                name_editor.editingFinished.connect(
                    lambda r=row, c=1, editor=name_editor: self._on_cell_editor_finished(r, c, editor.text())
                )
                self.cart_table.setCellWidget(row, 1, name_editor)

                # --- MİKTAR (Sütun 2 - Değişiklik yok) ---
                quantity_spin = QSpinBox(); quantity_spin.setRange(1, 999); quantity_spin.setValue(item.quantity or 1); 
                quantity_spin.valueChanged.connect(lambda val, r=row: self.update_item_quantity(r, val)); 
                self.cart_table.setCellWidget(row, 2, quantity_spin)

                # --- BİRİM FİYAT (Sütun 3 - Değişiklik yok, QTableWidgetItem kullan) ---
                price_item = QTableWidgetItem(f"{item.unit_price or Decimal('0.0'):.2f}"); 
                price_item.setFlags(price_item.flags() | Qt.ItemIsEditable); 
                self.cart_table.setItem(row, 3, price_item)

                # --- TOPLAM (Sütun 4 - Değişiklik yok) ---
                total_item = QTableWidgetItem(f"{item.total_price or Decimal('0.0'):.2f} ₺"); 
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable); 
                self.cart_table.setItem(row, 4, total_item)
                
                # --- SİL (Sütun 5 - Değişiklik yok) ---
                delete_btn = QPushButton("🗑️"); delete_btn.setMaximumWidth(30); 
                delete_btn.clicked.connect(lambda checked, r=row: self.remove_item_from_cart(r)); 
                self.cart_table.setCellWidget(row, 5, delete_btn)

        # Sinyali tekrar bağla
        self.cart_table.itemChanged.connect(self.on_cart_item_changed)
        self.cart_table.blockSignals(False)
        print("DEBUG: update_cart_table bitti.")


# Bu fonksiyonu update_cart_table'ın hemen sonrasına ekleyin
    
    def _on_cell_editor_finished(self, row, column, text):
        """Hücredeki (QLineEdit) düzenleme bittiğinde (Enter'a basıldığında) tetiklenir."""
        if self.cart_table.signalsBlocked(): return
        if not self.current_invoice or not self.current_invoice.items or row >= len(self.current_invoice.items): return

        item = self.current_invoice.items[row]
        if item is None: return
        
        text = text.strip()
        print(f"DEBUG: Hücre (Widget) düzenlemesi bitti: Satır={row}, Sütun={column}, Metin='{text}'")

        if column == 0: # KOD hücresi
            if item.product_code == text: return # Değişiklik yok
            
            # Kod değişti, ürünü bul ve tüm satırı güncelle
            product_code = self._extract_product_code(text)
            if product_code:
                try:
                    product = self.invoice_manager.get_product_by_code(product_code)
                    if product:
                        print(f"DEBUG: Ürün bulundu: {product.name}, Fiyat: {product.unit_price}")
                        item.product_id = product.id
                        item.product_code = product.code
                        item.product_name = product.name
                        item.unit_price = Decimal(str(product.unit_price or '0.0'))
                        item.quantity = 1 # Varsayılan miktar
                        item.total_price = Decimal(item.quantity) * item.unit_price
                        
                        self.update_cart_table() # Tüm tabloyu yenile (en kolayı)
                        self.update_totals()
                    else:
                        print(f"DEBUG: Ürün bulunamadı: {product_code}")
                        item.product_code = text.upper() # Sadece kodu güncelle
                        item.product_name = "ÜRÜN BULUNAMADI"
                        self.update_cart_table()
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Ürün aranırken hata: {e}")
            
        elif column == 1: # AD hücresi
            if item.product_name == text: return # Değişiklik yok
            
            # Ad değişti, ürünü bul (kodunu al)
            product_code = self._extract_product_code(text)
            if product_code:
                # Eğer öneriden seçtiyse (örn: "KOD - Ad"), kodu işle
                self._on_cell_editor_finished(row, 0, product_code)
            else:
                # Sadece adı manuel değiştirdiyse
                item.product_name = text
                # (Sadece adı güncellemek için tabloyu yenilemeye gerek yok, ama editör kaybolur)
                print(f"DEBUG: Sadece ad güncellendi: {text}")

    def add_new_blank_row(self):
        """Sepete yeni bir boş ('KOD GİRİN') satır ekler."""
        if not self.cart_table.isEnabled():
             QMessageBox.warning(self, "Uyarı", "Lütfen önce bir müşteri seçin.")
             return

        print("DEBUG: Shift+Enter - Yeni boş satır ekleniyor.")
        new_item = InvoiceItem(product_code="KOD GİRİN", product_name="Ürün Adı", quantity=1, unit_price=Decimal('0.0'), total_price=Decimal('0.0'))
        if self.current_invoice.items is None: self.current_invoice.items = []
        
        self.current_invoice.items.append(new_item)
        
        self.update_cart_table()
        
        new_row_index = self.cart_table.rowCount() - 1
        if new_row_index >= 0:
            # Yeni eklenen satırdaki "Kod" hücresine odaklan
            self.cart_table.setCurrentCell(new_row_index, 0)
            editor = self.cart_table.cellWidget(new_row_index, 0)
            if editor:
                editor.setFocus()
                editor.selectAll()

    # (update_item_quantity fonksiyonu aynı kalır)
    

    # --- BU FONKSİYON GÜNCELLENDİ (Toplam Hesaplama Düzeltmesi) ---
    def update_item_quantity(self, row, quantity):
        print(f"DEBUG: Miktar değişti: Satır={row}, Yeni Miktar={quantity}")
        if self.current_invoice.items and row < len(self.current_invoice.items):
            item = self.current_invoice.items[row]
            if item is None: return
            if quantity <= 0: self.remove_item_from_cart(row); return
            
            # 1. Miktar güncelleniyor
            item.quantity = quantity; 
            unit_price = item.unit_price or Decimal('0.0')
            
            # 2. DOĞRU HESAPLAMA: Miktar * Birim Fiyat
            item.total_price = Decimal(item.quantity) * unit_price
            
            print(f"DEBUG: Miktar güncellendi: Fiyat={unit_price}, Toplam={item.total_price}")
            
            # 3. Tablodaki "Toplam" hücresi güncelleniyor
            self.cart_table.blockSignals(True); 
            total_item_widget = self.cart_table.item(row, 4)
            total_text = f"{item.total_price:.2f} ₺"
            print(f"DEBUG: Tablo Toplam hücresi ({row}, 4) güncelleniyor: '{total_text}'")
            if total_item_widget: total_item_widget.setText(total_text)
            else: total_item_widget = QTableWidgetItem(total_text); total_item_widget.setFlags(total_item_widget.flags() & ~Qt.ItemIsEditable); self.cart_table.setItem(row, 4, total_item_widget)
            self.cart_table.blockSignals(False);
            
            # 4. Fişin Genel Toplamı güncelleniyor
            self.update_totals() # Toplamları güncelle

    # --- BU FONKSİYON GÜNCELLENDİ (Toplam Hesaplama Düzeltmesi) ---
    def on_cart_item_changed(self, item_widget):
        """Birim Fiyat (Sütun 3) hücresi değiştiğinde"""
        if not item_widget: return
        row = item_widget.row()
        column = item_widget.column()
        if self.cart_table.signalsBlocked(): return

        # --- DEĞİŞİKLİK: Sadece Sütun 3'ü (Birim Fiyat) dinle ---
        # Sütun 0 ve 1 artık QLineEdit widget'larıdır ve bu sinyali tetiklememelidir.
        if column not in (3,): 
            # print(f"DEBUG: on_cart_item_changed - Sütun {column} dikkate alınmıyor.")
            return

        # None kontrolü ve index kontrolü daha güvenli
        if not self.current_invoice or not self.current_invoice.items or row >= len(self.current_invoice.items) or self.current_invoice.items[row] is None:
             print(f"UYARI: on_cart_item_changed - Geçersiz satır indexi veya item: {row}")
             return
        invoice_item = self.current_invoice.items[row]
        new_text = item_widget.text()
        print(f"DEBUG: Hücre (Item) değişti: Satır={row}, Sütun={column}, Değer='{new_text}'")

        # --- DEĞİŞİKLİK: Sütun 0 ve 1 mantığı kaldırıldı ---
        
        if column == 3: # SÜTUN 3 (Birim Fiyat)
            try: # <<< TRY BAŞLIYOR
                new_price_text = new_text.replace(',', '.').replace('₺', '').replace('TL', '').strip()
                new_price = Decimal('0.0') if not new_price_text else Decimal(new_price_text)
                print(f"DEBUG: Fiyat güncellendi: {new_price}")

                invoice_item.unit_price = new_price
                quantity = invoice_item.quantity or 1 # None kontrolü
                invoice_item.total_price = Decimal(quantity) * invoice_item.unit_price # Decimal ile çarpım
                print(f"DEBUG: Fiyat değişimi sonrası: Miktar={quantity}, Toplam={invoice_item.total_price}")

                # Toplam hücresini güncelle
                self.cart_table.blockSignals(True)
                total_item_widget = self.cart_table.item(row, 4)
                total_text = f"{invoice_item.total_price:.2f} ₺"
                print(f"DEBUG: Tablo Toplam hücresi ({row}, 4) güncelleniyor: '{total_text}'")
                if total_item_widget:
                    total_item_widget.setText(total_text)
                else:
                    total_item_widget = QTableWidgetItem(total_text)
                    total_item_widget.setFlags(total_item_widget.flags() & ~Qt.ItemIsEditable)
                    self.cart_table.setItem(row, 4, total_item_widget)

                # Fiyat hücresini de formatla (kullanıcı 25 yazdıysa 25.00 olsun)
                # item_widget'ı değiştirmek için doğru referansı kullan
                price_item_widget = self.cart_table.item(row, column)
                if price_item_widget:
                     price_item_widget.setText(f"{invoice_item.unit_price:.2f}")

                self.cart_table.blockSignals(False)
                self.update_totals() # Toplamları güncelle

            except InvalidOperation: # <<< İLK EXCEPT
                 QMessageBox.warning(self, "Uyarı", f"Geçersiz fiyat formatı! Lütfen sayısal bir değer girin.")
                 print("DEBUG: Geçersiz fiyat formatı.")
                 # --- GİRİNTİ DÜZELTİLDİ ---
                 self.cart_table.blockSignals(True)
                 # Güvenlik kontrolleri eklendi
                 if self.current_invoice and self.current_invoice.items and row < len(self.current_invoice.items) and self.current_invoice.items[row]:
                      # item_widget yerine doğru referansı kullan
                      price_item_widget = self.cart_table.item(row, column)
                      if price_item_widget:
                           price_item_widget.setText(f"{self.current_invoice.items[row].unit_price or Decimal('0.0'):.2f}")
                 self.cart_table.blockSignals(False)
                 # --- GİRİNTİ SONU ---
            except Exception as e: # <<< İKİNCİ EXCEPT
                QMessageBox.warning(self, "Hata", f"Fiyat güncellenirken beklenmedik hata: {e}")
                print(f"DEBUG: Fiyat güncelleme hatası: {e}")
                # --- GİRİNTİ DÜZELTİLDİ ---
                self.cart_table.blockSignals(True)
                # Güvenlik kontrolleri eklendi
                if self.current_invoice and self.current_invoice.items and row < len(self.current_invoice.items) and self.current_invoice.items[row]:
                     # item_widget yerine doğru referansı kullan
                     price_item_widget = self.cart_table.item(row, column)
                     if price_item_widget:
                          price_item_widget.setText(f"{self.current_invoice.items[row].unit_price or Decimal('0.0'):.2f}")
                self.cart_table.blockSignals(False)
                # --- GİRİNTİ SONU ---
            # <<< EXCEPT BLOKLARI BİTİYOR
        # <<< ELIF COLUMN == 3 BİTİYOR

    def remove_item_from_cart(self, row):
        print(f"DEBUG: Ürün siliniyor: Satır={row}")
        if self.current_invoice.items and row < len(self.current_invoice.items):
             if self.current_invoice.items[row] is not None: del self.current_invoice.items[row]; self.update_cart_table(); self.update_totals()
             else: print(f"UYARI: Satır {row} zaten None."); self.update_cart_table()

    # --- BU FONKSİYON DEĞİŞTİ (Yüzdelik indirim hesaplaması) ---
    def update_totals(self):
        """Toplamları güncelle (Yüzdelik veya TL İndirim dahil)"""
        # ... (Ara toplam hesaplaması aynı kalır) ...
        subtotal = sum(Decimal(str(item.total_price or '0.0')) for item in (self.current_invoice.items or []) if item)

        # --- İndirim Hesaplaması (Dinamik Tip) ---
        discount_amount = Decimal('0.0')
        discount_value_for_debug = Decimal('0.0')
        discount_type_for_debug = "%"

        if hasattr(self, 'discount_input') and hasattr(self, 'discount_type_combo'):
            discount_type = self.discount_type_combo.currentText()
            discount_type_for_debug = discount_type
            try:
                discount_text = self.discount_input.text().replace(',', '.').strip()
                discount_value = Decimal(discount_text if discount_text else '0.0')
                discount_value_for_debug = discount_value

                if discount_type == "%":
                    # Yüzde 0-100 arasında olmalı
                    discount_percent = max(Decimal('0'), min(Decimal('100'), discount_value))
                    discount_amount = (subtotal * discount_percent) / Decimal('100')
                
                else: # "TL"
                    # Tutar subtotal'dan büyük olamaz (eksi bakiye önlemi)
                    discount_amount = max(Decimal('0'), min(subtotal, discount_value))
                    if discount_value > subtotal and subtotal > 0:
                         print("UYARI: İndirim tutarı ara toplamdan büyük, ara toplama eşitlendi.")
                         # Opsiyonel: Kullanıcıyı uyarmak için değeri düzeltebilirsiniz
                         # self.discount_input.setText(f"{discount_amount:.2f}")

            except (InvalidOperation, Exception) as e: 
                print(f"HATA: İndirim hesaplanamadı: {e}")
                discount_amount = Decimal('0.0')

        # İndirim tutarını iki ondalık basamağa yuvarla
        discount_amount = discount_amount.quantize(Decimal("0.01"))
        # --- İndirim Hesaplaması Sonu ---

        discounted_subtotal = subtotal - discount_amount
        tax_amount = discounted_subtotal * Decimal('0.20') # KDV indirimli tutardan
        total = discounted_subtotal + tax_amount

        # Hesaplanan değerleri Invoice objesine yaz
        if self.current_invoice: # None kontrolü
            self.current_invoice.subtotal = subtotal
            # Bu satır en önemlisi (PDF ve DB bunu kullanır)
            if hasattr(self.current_invoice, 'discount_amount'): self.current_invoice.discount_amount = discount_amount 
            self.current_invoice.tax_amount = tax_amount
            self.current_invoice.total_amount = total

        # Etiketleri güncelle
        if hasattr(self, 'subtotal_label'): self.subtotal_label.setText(f"{subtotal:.2f} ₺")
        if hasattr(self, 'tax_label'): self.tax_label.setText(f"{tax_amount:.2f} ₺")
        if hasattr(self, 'total_label'): self.total_label.setText(f"{total:.2f} ₺")
        print(f"DEBUG: Toplamlar güncellendi: Ara={subtotal}, Tip={discount_type_for_debug}, Değer={discount_value_for_debug}, İnd. Tutar={discount_amount}, KDV={tax_amount}, Toplam={total}")


    def update_customer_selector(self):
        """Müşteri seçiciyi güncelle"""
        if not hasattr(self, 'customer_selector') or not hasattr(self, 'invoice_manager'): return
        try:
            customers = self.invoice_manager.get_all_customers()
            self.customer_selector.blockSignals(True)
            current_selection_data = self.customer_selector.currentData()
            
            self.customer_selector.clear()
            self.customer_selector.addItem("Müşteri Seç...", userData=None)
            restored_index = 0
            
            for i, customer in enumerate(customers or []):  # None kontrolü
                if customer and hasattr(customer, 'name') and hasattr(customer, 'id'):
                    self.customer_selector.addItem(customer.name, customer)
                    if (current_selection_data and 
                        hasattr(current_selection_data, 'id') and 
                        customer.id == current_selection_data.id):
                        restored_index = i + 1
            
            self.customer_selector.setCurrentIndex(restored_index)
            self.customer_selector.blockSignals(False)
            print(f"DEBUG: Müşteriler yüklendi. Seçili index: {restored_index}")
            
        except Exception as e:
            print(f"Müşteriler yüklenemedi: {e}")
            if hasattr(self, 'customer_selector'):
                self.customer_selector.blockSignals(False)

    def on_customer_selected_index(self, index):
        """Müşteri ComboBox'ından seçim yapıldığında (Tabloyu etkinleştirir)"""
        if not all(hasattr(self, attr) for attr in ['customer_selector', 'customer_name', 'customer_address', 'cart_table']): return
        customer_data = self.customer_selector.itemData(index); is_valid_customer_selected = False; print(f"DEBUG: ComboBox index değişti: {index}")
        
        if customer_data and isinstance(customer_data, Customer):
            print(f"DEBUG: Müşteri seçildi: {customer_data.name}")
            self.customer_name.blockSignals(True); self.customer_name.setText(customer_data.name); self.customer_name.blockSignals(False)
            if hasattr(self, 'customer_address'):
                self.customer_address.setPlainText(customer_data.address or ""); 
            is_valid_customer_selected = True
        else:
            print("DEBUG: 'Müşteri Seç...' seçildi.")
            self.customer_name.blockSignals(True); self.customer_name.clear(); self.customer_name.blockSignals(False)
            if hasattr(self, 'customer_address'):
                self.customer_address.clear(); 
            is_valid_customer_selected = False
            
        # --- DEĞİŞİKLİK BURADA ---
        # Artık arama kutusu yerine doğrudan sepet tablosunu etkinleştiriyoruz.
        print(f"DEBUG: Sepet tablosu aktif mi: {is_valid_customer_selected}")
        self.cart_table.setEnabled(is_valid_customer_selected)
        if not is_valid_customer_selected:
             # Müşteri yoksa sepeti temizle
             if self.current_invoice: self.current_invoice.items = []
             self.update_cart_table()
             self.update_totals()
        # --- DEĞİŞİKLİK SONU ---

    def on_customer_name_changed(self, text):
        """Müşteri Adı alanına manuel yazı yazıldığında tetiklenir (Tabloyu etkinleştirir)"""
        if not all(hasattr(self, attr) for attr in ['customer_selector', 'customer_name', 'cart_table']): return
        current_combo_index = self.customer_selector.currentIndex(); customer_data_from_combo = self.customer_selector.itemData(current_combo_index); entered_name = text.strip(); print(f"DEBUG: Müşteri Adı değişti: '{entered_name}'")
        
        if customer_data_from_combo and isinstance(customer_data_from_combo, Customer) and customer_data_from_combo.name != entered_name:
            if entered_name: 
                print(f"DEBUG: Manuel isim ComboBox ile farklı, ComboBox sıfırlanıyor.")
                self.customer_selector.blockSignals(True)
                self.customer_selector.setCurrentIndex(0)
                self.customer_selector.blockSignals(False)
                if hasattr(self, 'customer_address'): 
                    self.customer_address.clear()
        
        is_valid_customer_typed = bool(entered_name)
        
        # --- DEĞİŞİKLİK BURADA ---
        # Artık arama kutusu yerine doğrudan sepet tablosunu etkinleştiriyoruz.
        self.cart_table.setEnabled(is_valid_customer_typed)
        
        if not is_valid_customer_typed and current_combo_index == 0:
             # Müşteri alanı boşaldıysa ve combo da seçili değilse sepeti temizle
             if self.current_invoice: self.current_invoice.items = []
             self.update_cart_table()
             self.update_totals()
        # --- DEĞİŞİKLİK SONU ---
    def new_invoice(self):
        """Yeni fiş oluştur (İndirim sıfırlama eklendi)"""
        if self.current_invoice and hasattr(self.current_invoice, 'items'): self.current_invoice.items = []
        else: self.current_invoice = Invoice(items=[])
        if hasattr(self, 'cart_table'): self.cart_table.setRowCount(0)
        if hasattr(self, 'product_search'): self.product_search.clear()
        if hasattr(self, 'customer_name'): self.customer_name.clear()
        if hasattr(self, 'customer_address'): self.customer_address.clear()
        if hasattr(self, 'delivery_person'): self.delivery_person.setText("Mehmet Ali")
        if hasattr(self, 'receiver_person'): self.receiver_person.clear()
        if hasattr(self, 'customer_selector'): self.customer_selector.setCurrentIndex(0)
        if hasattr(self, 'discount_input'):
            self.discount_input.blockSignals(True); self.discount_input.setText("0.00"); self.discount_input.blockSignals(False)
        # YENİ EKLENEN SATIR:
        if hasattr(self, 'discount_type_combo'):
            self.discount_type_combo.blockSignals(True); self.discount_type_combo.setCurrentIndex(0); self.discount_type_combo.blockSignals(False) # Default '%'
        
        self.update_totals() # Toplamları sıfırla

    def save_invoice(self):
        """Fişi kaydet (İndirim dahil)"""
        if not hasattr(self, 'current_invoice') or not self.current_invoice: self.current_invoice = Invoice(items=[])
        if self.current_invoice.items is None: self.current_invoice.items = []
        self.current_invoice.items = [i for i in self.current_invoice.items if i and i.product_code != "KOD GİRİN"]
        if not self.current_invoice.items: QMessageBox.warning(self, "Uyarı", "Sepette geçerli ürün bulunmuyor!"); return
        customer_name = self.customer_name.text().strip() if hasattr(self, 'customer_name') else ""
        if not customer_name: QMessageBox.warning(self, "Uyarı", "Müşteri adı gerekli!"); return
        # Kaydetmeden önce son kez toplamları ve indirimi hesapla/güncelle
        self.update_totals() # Bu satır kritik
        self.current_invoice.customer_name = customer_name
        self.current_invoice.customer_address = self.customer_address.toPlainText().strip() if hasattr(self, 'customer_address') else ""
        self.current_invoice.delivery_person = self.delivery_person.text().strip() if hasattr(self, 'delivery_person') else "Mehmet Ali"
        self.current_invoice.receiver_person = self.receiver_person.text().strip() if hasattr(self, 'receiver_person') else ""
        self.current_invoice.invoice_date = datetime.now()
        # İndirim, tax_amount vs. update_totals içinde current_invoice'a yazıldı

        try: 
            self.save_customer_info()
            # Müşteri listesini güncelle
            self.load_customers()
        except Exception as cust_e: QMessageBox.critical(self, "Müşteri Kayıt Hatası", f"Müşteri kaydedilirken/güncellenirken hata oluştu: {cust_e}"); return
        try:
            saved_invoice = self.invoice_manager.save_invoice(self.current_invoice)
            reply = QMessageBox.question(self, "PDF Oluştur", "Fiş kaydedildi!\nPDF oluşturulsun mu?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                file_path, _ = QFileDialog.getSaveFileName(self, "PDF Kaydet", f"fis_{saved_invoice.invoice_number}.pdf", "PDF (*.pdf)")
                if file_path:
                    try: self.pdf_generator.generate_invoice_pdf(saved_invoice, file_path); QMessageBox.information(self, "Başarılı", f"PDF oluşturuldu:\n{file_path}")
                    except Exception as e: QMessageBox.warning(self, "Uyarı", f"PDF oluşturulamadı: {str(e)}")
            self.invoice_saved.emit(); self.new_invoice()
        except Exception as e: QMessageBox.critical(self, "Fiş Kayıt Hatası", f"Fiş kaydedilemedi: {str(e)}"); print(f"Detaylı fiş kaydetme hatası: {e}")

    def save_customer_info(self):
        """Müşteri bilgilerini kaydet/güncelle (Tel/Eposta yok)"""
        if not all(hasattr(self, attr) for attr in ['customer_name', 'customer_address', 'invoice_manager']): return
        customer_name = self.customer_name.text().strip();
        if not customer_name: return
        customer_address = self.customer_address.toPlainText().strip()
        try: existing_customer = self.invoice_manager.get_customer_by_name(customer_name)
        except Exception as e: print(f"HATA: Müşteri aranırken: {e}"); raise
        if not existing_customer:
            print(f"DEBUG: Yeni müşteri '{customer_name}' ekleniyor.")
            new_customer = Customer(name=customer_name, address=customer_address)
            try: self.invoice_manager.save_customer(new_customer)
            except Exception as e: print(f"HATA: Yeni müşteri kaydedilemedi: {e}"); raise
        elif hasattr(existing_customer, 'address') and existing_customer.address != customer_address:
             print(f"DEBUG: Müşteri '{customer_name}' adresi güncelleniyor.")
             if hasattr(self.invoice_manager, 'update_customer_address'):
                 try: self.invoice_manager.update_customer_address(existing_customer.id, customer_address)
                 except Exception as e: print(f"HATA: Adres güncellenemedi: {e}"); raise
             else: print("UYARI: InvoiceManager'da 'update_customer_address' yok.")

    def generate_pdf(self):
        """PDF oluştur"""
        if not hasattr(self, 'current_invoice') or not self.current_invoice or not self.current_invoice.items: pdf_items = []
        else: pdf_items = [i for i in self.current_invoice.items if i and i.product_code != "KOD GİRİN"]
        if not pdf_items: QMessageBox.warning(self, "Uyarı", "Sepette geçerli ürün yok!"); return
        # PDF için kullanılacak fiş objesi (dikkatli kullan, referans)
        pdf_invoice = self.current_invoice; pdf_invoice.items = pdf_items
        pdf_invoice.customer_name = self.customer_name.text().strip() if hasattr(self, 'customer_name') else ""
        pdf_invoice.customer_address = self.customer_address.toPlainText().strip() if hasattr(self, 'customer_address') else ""
        pdf_invoice.delivery_person = self.delivery_person.text().strip() if hasattr(self, 'delivery_person') else "Mehmet Ali"
        pdf_invoice.receiver_person = self.receiver_person.text().strip() if hasattr(self, 'receiver_person') else ""
        if not pdf_invoice.invoice_number: pdf_invoice.invoice_number = "TASLAK"
        # İndirim vs. save_invoice'dan önce update_totals ile zaten ayarlanmış olmalı
        file_path, _ = QFileDialog.getSaveFileName(self, "PDF Kaydet", f"fis_{pdf_invoice.invoice_number}.pdf", "PDF (*.pdf)")
        if file_path:
            try: self.pdf_generator.generate_invoice_pdf(pdf_invoice, file_path); QMessageBox.information(self, "Başarılı", f"PDF oluşturuldu:\n{file_path}")
            except Exception as e: QMessageBox.critical(self, "Hata", f"PDF oluşturulamadı: {str(e)}")

    def print_invoice(self):
        """Fişi yazdır"""
        QMessageBox.information(self, "Bilgi", "Yazdırma özelliği yakında eklenecek!")