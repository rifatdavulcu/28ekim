"""
Ana pencere ve navigasyon yönetimi
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QMenuBar, QStatusBar, QToolBar,
    QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence, QAction

from .invoice_widget import InvoiceWidget
from .reports_widget import ReportsWidget
from .settings_widget import SettingsWidget
from .invoice_history_widget import InvoiceHistoryWidget


class MainWindow(QMainWindow):
    """Ana pencere sınıfı"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forklift Yedek Parça Satış ve Yönetim Sistemi")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Merkezi widget ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Ana layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # UI bileşenlerini oluştur
        self.create_menu_bar()
        self.create_toolbar()
        self.create_content_area()
        self.create_status_bar()
        
        # Stil uygula
        self.apply_styles()
        
        # İlk sayfayı göster
        self.show_invoice_page()
    
    def create_menu_bar(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")
        
        # Yeni fiş
        new_invoice_action = QAction("Yeni Fiş", self)
        new_invoice_action.setShortcut(QKeySequence.New)
        new_invoice_action.triggered.connect(self.show_invoice_page)
        file_menu.addAction(new_invoice_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")
        
        # Yeni Fiş
        invoice_action = QAction("Yeni Fiş", self)
        invoice_action.triggered.connect(self.show_invoice_page)
        view_menu.addAction(invoice_action)
        
        # Geçmiş Fişler
        history_action = QAction("Geçmiş Fişler", self)
        history_action.triggered.connect(self.show_invoice_history_page)
        view_menu.addAction(history_action)
        
        # Raporlar
        reports_action = QAction("Raporlar", self)
        reports_action.triggered.connect(self.show_reports_page)
        view_menu.addAction(reports_action)
        
        # Ayarlar
        settings_action = QAction("Ayarlar", self)
        settings_action.triggered.connect(self.show_settings_page)
        view_menu.addAction(settings_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")
        
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Araç çubuğunu oluştur"""
        toolbar = QToolBar("Ana Araçlar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Fişler butonu
        invoice_action = QAction("🧾 Yeni Fiş", self)
        invoice_action.triggered.connect(self.show_invoice_page)
        toolbar.addAction(invoice_action)
        
        # Geçmiş fişler butonu
        history_action = QAction("📋 Geçmiş Fişler", self)
        history_action.triggered.connect(self.show_invoice_history_page)
        toolbar.addAction(history_action)
        
        # Raporlar butonu
        reports_action = QAction("📊 Raporlar", self)
        reports_action.triggered.connect(self.show_reports_page)
        toolbar.addAction(reports_action)
        
        # Ayarlar butonu
        settings_action = QAction("⚙️ Ayarlar", self)
        settings_action.triggered.connect(self.show_settings_page)
        toolbar.addAction(settings_action)
        
        self.addToolBar(toolbar)
    
    def create_content_area(self):
        """İçerik alanını oluştur"""
        # Stacked widget - sayfalar arası geçiş için
        self.stacked_widget = QStackedWidget()
        
        # Sayfa widget'larını oluştur
        self.invoice_widget = InvoiceWidget()
        self.invoice_history_widget = InvoiceHistoryWidget()
        self.reports_widget = ReportsWidget()
        self.settings_widget = SettingsWidget()
        
        # Sayfaları stacked widget'a ekle
        self.stacked_widget.addWidget(self.invoice_widget)
        self.stacked_widget.addWidget(self.invoice_history_widget)
        self.stacked_widget.addWidget(self.reports_widget)
        self.stacked_widget.addWidget(self.settings_widget)
        
        # Ana layout'a ekle
        self.main_layout.addWidget(self.stacked_widget)
        
        # Signal bağlantıları
        self.setup_signal_connections()
    
    def setup_signal_connections(self):
        """Signal bağlantılarını kur"""
        # Fiş kaydedildiğinde raporları güncelle
        self.invoice_widget.invoice_saved.connect(self.on_invoice_saved)
        
        # Fiş güncellendiğinde raporları güncelle
        self.invoice_widget.invoice_updated.connect(self.on_invoice_updated)
    
    def on_invoice_saved(self):
        """Fiş kaydedildiğinde çağrılır"""
        # Raporları yenile
        if hasattr(self, 'reports_widget'):
            self.reports_widget.refresh_data()
        
        # Durum çubuğunu güncelle
        self.status_bar.showMessage("Fiş kaydedildi - Raporlar güncellendi")
    
    def on_invoice_updated(self):
        """Fiş güncellendiğinde çağrılır"""
        # Raporları yenile
        if hasattr(self, 'reports_widget'):
            self.reports_widget.refresh_data()
        
        # Durum çubuğunu güncelle
        self.status_bar.showMessage("Fiş güncellendi - Raporlar güncellendi")
    
    def create_status_bar(self):
        """Durum çubuğunu oluştur"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Durum mesajı
        self.status_bar.showMessage("Sistem hazır")
        
        # Sağ tarafta bilgi etiketi
        self.info_label = QLabel("Forklift Yedek Parça Sistemi v1.0")
        self.status_bar.addPermanentWidget(self.info_label)
    
    def apply_styles(self):
        """Uygulama stillerini uygula"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QToolBar {
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
            padding: 5px;
        }
        
        QToolBar QAction {
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
        }
        
        QToolBar QAction:hover {
            background-color: #e3f2fd;
        }
        
        QStatusBar {
            background-color: #ffffff;
            border-top: 1px solid #e0e0e0;
        }
        
        QMenuBar {
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
        }
        
        QMenuBar::item {
            padding: 8px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #e3f2fd;
        }
        """
        self.setStyleSheet(style)
    
    def show_invoice_page(self):
        """Yeni fiş sayfasını göster"""
        self.stacked_widget.setCurrentWidget(self.invoice_widget)
        self.status_bar.showMessage("Yeni fiş oluşturma sayfası")
    
    def show_invoice_history_page(self):
        """Geçmiş fişler sayfasını göster"""
        self.stacked_widget.setCurrentWidget(self.invoice_history_widget)
        self.status_bar.showMessage("Geçmiş fişler sayfası")
    
    def show_reports_page(self):
        """Raporlar sayfasını göster"""
        self.stacked_widget.setCurrentWidget(self.reports_widget)
        self.status_bar.showMessage("Raporlar ve analiz sayfası")
    
    def show_settings_page(self):
        """Ayarlar sayfasını göster"""
        self.stacked_widget.setCurrentWidget(self.settings_widget)
        self.status_bar.showMessage("Sistem ayarları sayfası")
    
    def show_about(self):
        """Hakkında dialog'unu göster"""
        from PySide6.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "Hakkında",
            """
            <h3>Forklift Yedek Parça Satış ve Yönetim Sistemi</h3>
            <p><b>Sürüm:</b> 1.0.0</p>
            <p><b>Geliştirici:</b> Forklift Systems</p>
            <p>Modern Python masaüstü uygulaması olarak geliştirilmiş 
            forklift yedek parça satış ve yönetim sistemi.</p>
            <p><b>Teknolojiler:</b><br>
            • PySide6 (Qt6)<br>
            • SQLite<br>
            • ReportLab (PDF)<br>
            • pandas (Excel)</p>
            """
        )