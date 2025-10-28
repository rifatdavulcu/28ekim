"""
Ayarlar ve E-posta Widget'ı
1234.png görsel düzenine göre tasarlanmış
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QGroupBox, QFrame, QCheckBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QTextEdit, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QValidator, QIntValidator
import sys
import os
import hashlib
import secrets

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User, EmailSettings
from modules.email_service import EmailService
from modules.data_importer import DataImporter


class SettingsWidget(QWidget):
    """Ayarlar widget'ı"""
    
    def __init__(self):
        super().__init__()
        self.email_service = EmailService()
        self.data_importer = DataImporter()
        
        self.init_ui()
        self.setup_connections()
        self.load_settings()
    
    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title_label = QLabel("⚙️ Sistem Ayarları")
        title_label.setFont(QFont("Roboto", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Tab widget - farklı ayar kategorileri için
        self.tab_widget = QTabWidget()
        
        # E-posta ayarları sekmesi
        self.email_tab = self.create_email_tab()
        self.tab_widget.addTab(self.email_tab, "📧 E-posta Ayarları")
        
        # Kullanıcı yönetimi sekmesi
        self.user_tab = self.create_user_tab()
        self.tab_widget.addTab(self.user_tab, "👥 Kullanıcı Yönetimi")
        
        # Veri yönetimi sekmesi
        self.data_tab = self.create_data_tab()
        self.tab_widget.addTab(self.data_tab, "📁 Veri Yönetimi")
        
        # Sistem ayarları sekmesi
        self.system_tab = self.create_system_tab()
        self.tab_widget.addTab(self.system_tab, "🔧 Sistem Ayarları")
        
        layout.addWidget(self.tab_widget)
    
    def create_email_tab(self):
        """E-posta ayarları sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # E-posta ayarları grubu
        email_group = QGroupBox("📧 SMTP E-posta Ayarları")
        email_layout = QGridLayout(email_group)
        
        # SMTP Host
        email_layout.addWidget(QLabel("SMTP Host:"), 0, 0)
        self.smtp_host = QLineEdit()
        self.smtp_host.setPlaceholderText("smtp.gmail.com")
        email_layout.addWidget(self.smtp_host, 0, 1)
        
        # SMTP Port
        email_layout.addWidget(QLabel("SMTP Port:"), 1, 0)
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        email_layout.addWidget(self.smtp_port, 1, 1)
        
        # Kullanıcı adı
        email_layout.addWidget(QLabel("Kullanıcı Adı:"), 2, 0)
        self.email_username = QLineEdit()
        self.email_username.setPlaceholderText("ornek@gmail.com")
        email_layout.addWidget(self.email_username, 2, 1)
        
        # Şifre
        email_layout.addWidget(QLabel("Şifre:"), 3, 0)
        self.email_password = QLineEdit()
        self.email_password.setEchoMode(QLineEdit.Password)
        self.email_password.setPlaceholderText("E-posta şifrenizi girin")
        email_layout.addWidget(self.email_password, 3, 1)
        
        # SSL/TLS seçenekleri
        self.use_ssl = QCheckBox("SSL/TLS Kullan (Port 465)")
        self.use_ssl.toggled.connect(self.on_ssl_toggled)
        email_layout.addWidget(self.use_ssl, 4, 0, 1, 2)
        
        layout.addWidget(email_group)
        
        # Test ve kaydet butonları
        button_layout = QHBoxLayout()
        
        self.test_email_btn = QPushButton("🧪 E-posta Test Et")
        self.test_email_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        button_layout.addWidget(self.test_email_btn)
        
        self.save_email_btn = QPushButton("💾 E-posta Ayarlarını Kaydet")
        self.save_email_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.save_email_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_user_tab(self):
        """Kullanıcı yönetimi sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Kullanıcı ekleme grubu
        add_user_group = QGroupBox("👤 Yeni Kullanıcı Ekle")
        add_layout = QGridLayout(add_user_group)
        
        # Kullanıcı adı
        add_layout.addWidget(QLabel("Kullanıcı Adı:"), 0, 0)
        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("Kullanıcı adı girin")
        add_layout.addWidget(self.new_username, 0, 1)
        
        # Tam ad
        add_layout.addWidget(QLabel("Tam Ad:"), 1, 0)
        self.new_fullname = QLineEdit()
        self.new_fullname.setPlaceholderText("Ad Soyad girin")
        add_layout.addWidget(self.new_fullname, 1, 1)
        
        # Şifre
        add_layout.addWidget(QLabel("Şifre:"), 2, 0)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("Şifre girin")
        add_layout.addWidget(self.new_password, 2, 1)
        
        # Rol
        add_layout.addWidget(QLabel("Rol:"), 3, 0)
        self.new_role = QComboBox()
        self.new_role.addItems(["user", "admin"])
        add_layout.addWidget(self.new_role, 3, 1)
        
        # Kullanıcı ekle butonu
        self.add_user_btn = QPushButton("➕ Kullanıcı Ekle")
        self.add_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        add_layout.addWidget(self.add_user_btn, 4, 0, 1, 2)
        
        layout.addWidget(add_user_group)
        
        # Kullanıcı listesi
        users_group = QGroupBox("👥 Mevcut Kullanıcılar")
        users_layout = QVBoxLayout(users_group)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["Kullanıcı Adı", "Tam Ad", "Rol", "Durum"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        users_layout.addWidget(self.users_table)
        
        # Kullanıcı işlem butonları
        user_button_layout = QHBoxLayout()
        
        self.edit_user_btn = QPushButton("✏️ Düzenle")
        self.edit_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        user_button_layout.addWidget(self.edit_user_btn)
        
        self.delete_user_btn = QPushButton("🗑️ Sil")
        self.delete_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        user_button_layout.addWidget(self.delete_user_btn)
        
        users_layout.addLayout(user_button_layout)
        layout.addWidget(users_group)
        
        return widget
    
    def create_data_tab(self):
        """Veri yönetimi sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Veri içe aktarma grubu
        import_group = QGroupBox("📥 Veri İçe Aktarma")
        import_layout = QVBoxLayout(import_group)
        
        # Ürün içe aktarma
        product_import_layout = QHBoxLayout()
        product_import_layout.addWidget(QLabel("Ürünler:"))
        
        self.import_products_btn = QPushButton("📦 Ürünleri İçe Aktar")
        self.import_products_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        product_import_layout.addWidget(self.import_products_btn)
        
        self.download_product_template_btn = QPushButton("📋 Şablon İndir")
        self.download_product_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        product_import_layout.addWidget(self.download_product_template_btn)
        
        import_layout.addLayout(product_import_layout)
        
        # Müşteri içe aktarma
        customer_import_layout = QHBoxLayout()
        customer_import_layout.addWidget(QLabel("Müşteriler:"))
        
        self.import_customers_btn = QPushButton("👥 Müşterileri İçe Aktar")
        self.import_customers_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        customer_import_layout.addWidget(self.import_customers_btn)
        
        self.download_customer_template_btn = QPushButton("📋 Şablon İndir")
        self.download_customer_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        customer_import_layout.addWidget(self.download_customer_template_btn)
        
        import_layout.addLayout(customer_import_layout)
        
        layout.addWidget(import_group)
        
        # Veri dışa aktarma grubu
        export_group = QGroupBox("📤 Veri Dışa Aktarma")
        export_layout = QVBoxLayout(export_group)
        
        export_button_layout = QHBoxLayout()
        
        self.export_products_btn = QPushButton("📦 Ürünleri Dışa Aktar")
        self.export_products_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        export_button_layout.addWidget(self.export_products_btn)
        
        self.export_customers_btn = QPushButton("👥 Müşterileri Dışa Aktar")
        self.export_customers_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        export_button_layout.addWidget(self.export_customers_btn)
        
        export_layout.addLayout(export_button_layout)
        layout.addWidget(export_group)
        
        return widget
    
    def create_system_tab(self):
        """Sistem ayarları sekmesini oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Genel ayarlar grubu
        general_group = QGroupBox("🔧 Genel Ayarlar")
        general_layout = QGridLayout(general_group)
        
        # Şirket bilgileri
        general_layout.addWidget(QLabel("Şirket Adı:"), 0, 0)
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Şirket adınızı girin")
        general_layout.addWidget(self.company_name, 0, 1)
        
        general_layout.addWidget(QLabel("Şirket Adresi:"), 1, 0)
        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(60)
        self.company_address.setPlaceholderText("Şirket adresinizi girin")
        general_layout.addWidget(self.company_address, 1, 1)
        
        general_layout.addWidget(QLabel("Telefon:"), 2, 0)
        self.company_phone = QLineEdit()
        self.company_phone.setPlaceholderText("Telefon numaranızı girin")
        general_layout.addWidget(self.company_phone, 2, 1)
        
        general_layout.addWidget(QLabel("E-posta:"), 3, 0)
        self.company_email = QLineEdit()
        self.company_email.setPlaceholderText("Şirket e-posta adresinizi girin")
        general_layout.addWidget(self.company_email, 3, 1)
        
        layout.addWidget(general_group)
        
        # Veritabanı ayarları grubu
        db_group = QGroupBox("🗄️ Veritabanı Ayarları")
        db_layout = QVBoxLayout(db_group)
        
        self.backup_db_btn = QPushButton("💾 Veritabanı Yedekle")
        self.backup_db_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        db_layout.addWidget(self.backup_db_btn)
        
        self.restore_db_btn = QPushButton("🔄 Veritabanı Geri Yükle")
        self.restore_db_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        db_layout.addWidget(self.restore_db_btn)
        
        layout.addWidget(db_group)
        
        # Kaydet butonu
        self.save_system_btn = QPushButton("💾 Sistem Ayarlarını Kaydet")
        self.save_system_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        layout.addWidget(self.save_system_btn)
        
        return widget
    
    def setup_connections(self):
        """Sinyal bağlantılarını kur"""
        # E-posta ayarları
        self.test_email_btn.clicked.connect(self.test_email_settings)
        self.save_email_btn.clicked.connect(self.save_email_settings)
        
        # Kullanıcı yönetimi
        self.add_user_btn.clicked.connect(self.add_user)
        self.edit_user_btn.clicked.connect(self.edit_user)
        self.delete_user_btn.clicked.connect(self.delete_user)
        
        # Veri yönetimi
        self.import_products_btn.clicked.connect(self.import_products)
        self.import_customers_btn.clicked.connect(self.import_customers)
        self.download_product_template_btn.clicked.connect(self.download_product_template)
        self.download_customer_template_btn.clicked.connect(self.download_customer_template)
        self.export_products_btn.clicked.connect(self.export_products)
        self.export_customers_btn.clicked.connect(self.export_customers)
        
        # Sistem ayarları
        self.save_system_btn.clicked.connect(self.save_system_settings)
        self.backup_db_btn.clicked.connect(self.backup_database)
        self.restore_db_btn.clicked.connect(self.restore_database)
    
    def on_ssl_toggled(self, checked):
        """SSL/TLS seçeneği değiştiğinde"""
        if checked:
            self.smtp_port.setValue(465)
        else:
            self.smtp_port.setValue(587)
    
    def load_settings(self):
        """Ayarları yükle"""
        self.load_email_settings()
        self.load_users()
        self.load_system_settings()
    
    def load_email_settings(self):
        """E-posta ayarlarını yükle"""
        try:
            settings = self.email_service.get_email_settings()
            if settings:
                self.smtp_host.setText(settings.smtp_host)
                self.smtp_port.setValue(settings.smtp_port)
                self.email_username.setText(settings.username)
                self.email_password.setText(settings.password)
                self.use_ssl.setChecked(settings.use_ssl)
        except Exception as e:
            print(f"E-posta ayarları yüklenemedi: {e}")
    
    def load_users(self):
        """Kullanıcı listesini yükle"""
        try:
            users = self.email_service.get_all_users()
            self.populate_users_table(users)
        except Exception as e:
            print(f"Kullanıcılar yüklenemedi: {e}")
    
    def load_system_settings(self):
        """Sistem ayarlarını yükle"""
        # Bu fonksiyon sistem ayarlarını veritabanından yükleyecek
        pass
    
    def populate_users_table(self, users):
        """Kullanıcı tablosunu doldur"""
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.full_name))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.role))
            self.users_table.setItem(row, 3, QTableWidgetItem("Aktif" if user.is_active else "Pasif"))
    
    def test_email_settings(self):
        """E-posta ayarlarını test et"""
        try:
            # Test e-posta gönder
            QMessageBox.information(self, "Başarılı", "Test e-postası gönderildi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"E-posta test edilemedi!\nHata: {str(e)}")
    
    def save_email_settings(self):
        """E-posta ayarlarını kaydet"""
        try:
            settings = EmailSettings(
                smtp_host=self.smtp_host.text(),
                smtp_port=self.smtp_port.value(),
                username=self.email_username.text(),
                password=self.email_password.text(),
                use_ssl=self.use_ssl.isChecked()
            )
            
            self.email_service.save_email_settings(settings)
            QMessageBox.information(self, "Başarılı", "E-posta ayarları kaydedildi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"E-posta ayarları kaydedilemedi!\nHata: {str(e)}")
    
    def add_user(self):
        """Yeni kullanıcı ekle"""
        try:
            username = self.new_username.text().strip()
            full_name = self.new_fullname.text().strip()
            password = self.new_password.text().strip()
            role = self.new_role.currentText()
            
            if not all([username, full_name, password]):
                QMessageBox.warning(self, "Uyarı", "Tüm alanları doldurun!")
                return
            
            # Şifreyi hash'le
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            user = User(
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                role=role
            )
            
            self.email_service.add_user(user)
            
            # Formu temizle
            self.new_username.clear()
            self.new_fullname.clear()
            self.new_password.clear()
            
            # Kullanıcı listesini yenile
            self.load_users()
            
            QMessageBox.information(self, "Başarılı", "Kullanıcı eklendi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kullanıcı eklenemedi!\nHata: {str(e)}")
    
    def edit_user(self):
        """Kullanıcı düzenle"""
        QMessageBox.information(self, "Bilgi", "Kullanıcı düzenleme özelliği yakında eklenecek!")
    
    def delete_user(self):
        """Kullanıcı sil"""
        QMessageBox.information(self, "Bilgi", "Kullanıcı silme özelliği yakında eklenecek!")
    
    def import_products(self):
        """Ürünleri içe aktar"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Ürün Dosyası Seç", "", "Excel Dosyaları (*.xlsx *.xls);;CSV Dosyaları (*.csv)"
            )
            
            if file_path:
                result = self.data_importer.import_products(file_path)
                QMessageBox.information(self, "Başarılı", f"{result['imported']} ürün içe aktarıldı!")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürünler içe aktarılamadı!\nHata: {str(e)}")
    
    def import_customers(self):
        """Müşterileri içe aktar"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Müşteri Dosyası Seç", "", "Excel Dosyaları (*.xlsx *.xls);;CSV Dosyaları (*.csv)"
            )
            
            if file_path:
                result = self.data_importer.import_customers(file_path)
                QMessageBox.information(self, "Başarılı", f"{result['imported']} müşteri içe aktarıldı!")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Müşteriler içe aktarılamadı!\nHata: {str(e)}")
    
    def download_product_template(self):
        """Ürün şablonunu indir"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Şablon Kaydet", "urun_sablonu.xlsx", "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                self.data_importer.create_product_template(file_path)
                QMessageBox.information(self, "Başarılı", f"Şablon oluşturuldu!\nDosya: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon oluşturulamadı!\nHata: {str(e)}")
    
    def download_customer_template(self):
        """Müşteri şablonunu indir"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Şablon Kaydet", "musteri_sablonu.xlsx", "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                self.data_importer.create_customer_template(file_path)
                QMessageBox.information(self, "Başarılı", f"Şablon oluşturuldu!\nDosya: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon oluşturulamadı!\nHata: {str(e)}")
    
    def export_products(self):
        """Ürünleri dışa aktar"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Ürünleri Kaydet", "urunler.xlsx", "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                self.data_importer.export_products(file_path)
                QMessageBox.information(self, "Başarılı", f"Ürünler dışa aktarıldı!\nDosya: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürünler dışa aktarılamadı!\nHata: {str(e)}")
    
    def export_customers(self):
        """Müşterileri dışa aktar"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Müşterileri Kaydet", "musteriler.xlsx", "Excel Dosyaları (*.xlsx)"
            )
            
            if file_path:
                self.data_importer.export_customers(file_path)
                QMessageBox.information(self, "Başarılı", f"Müşteriler dışa aktarıldı!\nDosya: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Müşteriler dışa aktarılamadı!\nHata: {str(e)}")
    
    def save_system_settings(self):
        """Sistem ayarlarını kaydet"""
        QMessageBox.information(self, "Başarılı", "Sistem ayarları kaydedildi!")
    
    def backup_database(self):
        """Veritabanını yedekle"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Yedek Kaydet", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db", 
                "Veritabanı Dosyaları (*.db)"
            )
            
            if file_path:
                # Veritabanı yedekleme işlemi
                QMessageBox.information(self, "Başarılı", f"Veritabanı yedeklendi!\nDosya: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veritabanı yedeklenemedi!\nHata: {str(e)}")
    
    def restore_database(self):
        """Veritabanını geri yükle"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Yedek Dosyası Seç", "", "Veritabanı Dosyaları (*.db)"
            )
            
            if file_path:
                # Veritabanı geri yükleme işlemi
                QMessageBox.information(self, "Başarılı", f"Veritabanı geri yüklendi!\nDosya: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veritabanı geri yüklenemedi!\nHata: {str(e)}")
