"""
Forklift Yedek Parça Satış ve Yönetim Sistemi
Ana uygulama giriş noktası
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QIcon, QFont # QFont import edildi

# --- YENİ İMPORT ---
import os.path
# --- YENİ İMPORT BİTTİ ---

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- YENİ LOGLAMA KODU ---
LOG_FILE_PATH = os.path.join(os.path.expanduser("~"), "forklift_app_log.txt")

def write_log(message):
    """Log dosyasına bir satır yazar"""
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception as e:
        print(f"Log yazılamadı: {e}") 
# --- YENİ LOGLAMA KODU BİTTİ ---


def main():
    """Ana uygulama fonksiyonu"""
    
    # Log dosyasını temizle ve başlat
    if os.path.exists(LOG_FILE_PATH):
        os.remove(LOG_FILE_PATH)
    write_log("Uygulama başlatıldı.")
    
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Turkish_Turkey.1254')
        except:
            pass
    
    app = QApplication(sys.argv)
    app.setApplicationName("Forklift Yedek Parça Sistemi")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Forklift Systems")
    
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    write_log("Font yükleme işlemi başlıyor...")
    
    # Roboto fontunu yükle
    font_path = resource_path("fonts/Roboto-Medium.ttf")
    write_log(f"Aranan font dosyası: fonts/Roboto-Medium.ttf")
    write_log(f"resource_path fonksiyonunun bulduğu tam yol: {font_path}")
    
    # Önce Medium versiyonunu yükle
    font_id = QFontDatabase.addApplicationFont(font_path)
    
    # Sonra Bold versiyonunu da yükle
    bold_font_path = resource_path("fonts/Roboto-Bold.ttf")
    bold_font_id = QFontDatabase.addApplicationFont(bold_font_path)
    write_log(f"Bold font için resource_path: {bold_font_path}")
    
    GLOBAL_FONT_NAME = "Arial" # Varsayılan

    if font_id != -1 and bold_font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            GLOBAL_FONT_NAME = font_families[0]
            write_log(f"SONUÇ: Font başarıyla yüklendi. Kodda kullanılacak ad: '{GLOBAL_FONT_NAME}'")
            
            # --- KRİTİK DÜZELTME: GLOBAL FONT ATAMASI ---
            # Fontun tüm uygulamada kullanılması için ayarla
            default_font = QFont(GLOBAL_FONT_NAME, 10)
            default_font.setStyleStrategy(QFont.PreferAntialias)
            
            # Uygulama genelinde font ayarları
            app.setFont(default_font)
            
            # Özel font stillerini QFontDatabase'e kaydet
            QFontDatabase.addApplicationFont(resource_path("fonts/Roboto-Bold.ttf"))
            
            write_log(f"SONUÇ: Uygulama fontu '{GLOBAL_FONT_NAME}' olarak ayarlandı.")
            # --- GLOBAL FONT ATAMASI SONU ---
        else:
            write_log("SONUÇ: Font yüklendi ama AİLE ADI BULUNAMADI. Arial kullanılacak.")
    else:
        write_log(f"SONUÇ: QFontDatabase.addApplicationFont BAŞARISIZ OLDU. Font yüklenemedi. (Hata: {font_path})")
    
    # Stil dosyasını yükle
    style_file = resource_path("assets/styles/main.qss")
    write_log(f"Stil dosyası yükleniyor: {style_file}")
    
    try:
        with open(style_file, 'r', encoding='utf-8') as f:
            style_sheet = f.read()
            app.setStyleSheet(style_sheet)
            write_log("Stil dosyası başarıyla yüklendi.")
    except Exception as e:
        write_log(f"Stil dosyası yüklenemedi: {e}")
    
    write_log("Ana pencere (MainWindow) oluşturuluyor...")
    window = MainWindow()
    window.show()
    write_log("Uygulama çalışıyor (exec).")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
