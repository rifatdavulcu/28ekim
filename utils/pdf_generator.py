"""
PDF oluşturma modülü (PyInstaller UYUMLU)
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
import sys # sys import edildi
from datetime import datetime
from decimal import Decimal

# Türkçe fontları (TTF) kaydetmek için gereken modüller
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Invoice


# --- PYINSTALLER İÇİN YARDIMCI FONKSİYON ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller geçici bir yol oluşturur ve bunu _MEIPASS'e atar
        base_path = sys._MEIPASS
    except Exception:
        # PyInstaller ile çalışmıyorken (geliştirme ortamı)
        # Bu dosyanın (pdf_generator.py) olduğu yerin bir üst klasörüne (forkpy/) git
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)
# --- YARDIMCI FONKSİYON SONU ---

# --- FONT YOLU GÜNCELLENDİ ---
# Artık 'fonts' klasörünün doğrudan ana dizinde (base_path) olduğunu varsayıyoruz
ROBOTO_NORMAL_PATH = resource_path(os.path.join("fonts", "Roboto-Medium.ttf"))
ROBOTO_BOLD_PATH = resource_path(os.path.join("fonts", "Roboto-Bold.ttf"))
# --- GÜNCELLEME SONU ---


class PDFGenerator:
    """PDF oluşturma sınıfı"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Özel stilleri tanımla ve Türkçe (Roboto) fontları kaydet"""
        try:
            pdfmetrics.registerFont(TTFont('Roboto-Medium', ROBOTO_NORMAL_PATH))
            pdfmetrics.registerFont(TTFont('Roboto-Bold', ROBOTO_BOLD_PATH))
            pdfmetrics.registerFontFamily('Roboto', normal='Roboto-Medium', bold='Roboto-Bold')
            self.base_font = 'Roboto-Medium'
            self.base_font_bold = 'Roboto-Bold'
            print("DEBUG: Roboto fontları projeden başarıyla yüklendi.")
        except Exception as e:
            print(f"!!! KRİTİK HATA: Roboto fontları yüklenemedi!")
            print(f"   Aranan yol (Normal): {ROBOTO_NORMAL_PATH}")
            print(f"   Hata: {e}")
            self.base_font = 'Helvetica'
            self.base_font_bold = 'Helvetica-Bold'
        
        self.styles.add(ParagraphStyle(name='CustomTitle', parent=self.styles['Heading1'], fontName=self.base_font_bold, fontSize=18, spaceAfter=30, alignment=TA_CENTER, textColor=colors.darkblue))
        self.styles.add(ParagraphStyle(name='CustomHeading', parent=self.styles['Heading2'], fontName=self.base_font_bold, fontSize=14, spaceAfter=12, textColor=colors.darkblue))
        self.styles.add(ParagraphStyle(name='CustomNormal', parent=self.styles['Normal'], fontName=self.base_font, fontSize=10, spaceAfter=6))
 
    # ... (Dosyanızın 81. satırına kadar olan kısım) ...

    def generate_invoice_pdf(self, invoice: Invoice, file_path: str):
        """Fiş PDF'i oluştur (İndirim ve Kurumsal Başlık dahil - Metin Kaydırmalı)"""
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        story = []

        # --- 1. KURUMSAL BAŞLIK EKLENDİ ---
        try:
            company_name = "World Worklift İTH. İHR. SAN. VE TİC. LTD. ŞTİ."
            address_line = "İ.O.S.B Mah. Giyim Sanatkarları Sosyal Tesis Sok. Giyim Sanatkarları Ticaret Merkezi Sosyal Tesisi No: 1/1 Kapı No: B001 Başakşehir/İstanbul"
            phone = "Tel: 0212 549 34 02"
            email_web = "info@worldforklift.com.tr | www.worldforklift.com.tr"

            # Başlık için özel stiller
            styleH = ParagraphStyle(name='HeaderTitle', parent=self.styles['Normal'], fontName=self.base_font_bold, fontSize=11, alignment=TA_LEFT)
            styleN_small = ParagraphStyle(name='HeaderNormal', parent=self.styles['Normal'], fontName=self.base_font, fontSize=8, alignment=TA_LEFT, leading=10)

            # İçeriği bir listeye topla
            header_content = [
                Paragraph(company_name, styleH),
                Spacer(1, 4), # İsim ve adres arası boşluk
                Paragraph(address_line, styleN_small),
                Paragraph(phone, styleN_small),
                Paragraph(email_web, styleN_small)
            ]
            
            # Tüm başlık içeriğini tek hücreli bir tabloya koy
            header_table = Table([[header_content]], colWidths=[16*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(header_table)
            
            # Başlık ve ana içerik arasına ayırıcı çizgi ekle
            story.append(Table(Table([[None]]), colWidths=[16*cm], rowHeights=[0.5*cm], style=TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 1, colors.black)
            ])))
            story.append(Spacer(1, 5)) # Çizgiden sonra boşluk
            
        except Exception as e:
            print(f"HATA: PDF başlığı oluşturulamadı: {e}")
            # Başlık olmasa da PDF oluşturmaya devam et
        # --- KURUMSAL BAŞLIK SONU ---

        
        title = Paragraph("SİPARİŞ FİŞİ", self.styles['CustomTitle'])
        story.append(title); story.append(Spacer(1, 20))

        # Fiş bilgileri (Tarih sağa hizalı)
        invoice_info_data = [
            [f"Fiş No: {invoice.invoice_number}", f"TARİH: {invoice.invoice_date.strftime('%d.%m.%Y') if hasattr(invoice, 'invoice_date') and invoice.invoice_date else datetime.now().strftime('%d.%m.%Y')}"]
        ]
        invoice_table = Table(invoice_info_data, colWidths=[8*cm, 8*cm])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_bold),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(invoice_table)

        # Müşteri bilgileri (Adres için Paragraph kullanılıyor)
        customer_info = [
            ['Sayın :', invoice.customer_name],
            ['Adresi :', Paragraph(invoice.customer_address.replace('\n', '<br/>') or '', self.styles['CustomNormal'])],
        ]
        customer_table = Table(customer_info, colWidths=[2*cm, 14*cm])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), self.base_font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(customer_table); story.append(Spacer(1, 12))


        # --- 2. ÜRÜN LİSTESİ GÜNCELLENDİ (Metin Kaydırma) ---
        table_data = [['MİKTARI', 'KODU', 'MALZEME ADI', 'BİRİM FİYATI', 'TUTARI']]
        
        # Ürün adı için özel stil (Paragraf olarak kaydırma yapabilmesi için)
        # Tablo stilindeki 9pt font boyutuna uyumlu
        product_text_style = ParagraphStyle(
            name='ProductStyle', 
            parent=self.styles['Normal'], 
            fontName=self.base_font, 
            fontSize=9,
            leading=11 # Satır yüksekliği
        )

        if invoice.items:
            for item in invoice.items:
                 if item and hasattr(item, 'product_code'):
                     table_data.append([
                         item.quantity or 1,
                         item.product_code or '',
                         # DEĞİŞİKLİK: Ürün adını Paragraph objesi olarak ekle
                         Paragraph(item.product_name or '', product_text_style), 
                         f"{item.unit_price or Decimal('0.0'):.2f} TL",
                         f"{item.total_price or Decimal('0.0'):.2f} TL"
                     ])
                     
        min_rows = 10
        for _ in range(max(0, min_rows - len(table_data) + 1)):
             table_data.append(['', '', '', '', ''])
             
        products_table = Table(table_data, colWidths=[2*cm, 3*cm, 6*cm, 2.5*cm, 2.5*cm])
        products_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E0E0E0")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.base_font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            # DEĞİŞİKLİK: Dikey hizalamayı 'ÜST' olarak ayarla
            ('VALIGN', (0, 1), (-1, -1), 'TOP'), 
        ]))
        story.append(products_table); story.append(Spacer(1, 20))
        # --- ÜRÜN LİSTESİ GÜNCELLENDİ SONU ---


        # Toplam bilgileri (İndirim dahil)
        totals_data = [['Ara Toplam:', f"{invoice.subtotal or Decimal('0.0'):.2f} TL"]]
        discount_amount = getattr(invoice, 'discount_amount', Decimal('0.0')) or Decimal('0.0')
        if discount_amount > 0:
            totals_data.append(['İndirim:', f"-{discount_amount:.2f} TL"])

        totals_data.extend([
            ['KDV (%20):', f"{invoice.tax_amount or Decimal('0.0'):.2f} TL"],
            ['TOPLAM:', f"{invoice.total_amount or Decimal('0.0'):.2f} TL"]
        ])

        totals_table = Table(totals_data, colWidths=[13*cm, 3*cm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_bold),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.darkblue),
        ]))
        if discount_amount > 0:
             totals_table.setStyle(TableStyle([('TEXTCOLOR', (0, 1), (-1, 1), colors.red)]))
        
        story.append(totals_table); story.append(Spacer(1, 30))

        # Teslimat Bilgileri
        delivery_info_data = [
             [f"Teslim Eden: {invoice.delivery_person or '_______________________'}", 
              f"Teslim Alan: {invoice.receiver_person or '_______________________'}"]
        ]
        delivery_table = Table(delivery_info_data, colWidths=[8*cm, 8*cm])
        delivery_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ]))
        story.append(delivery_table)
        
        # PDF'i oluştur
        try:
             doc.build(story)
             print("DEBUG: PDF (Kurumsal Başlıklı) başarıyla oluşturuldu.")
        except Exception as build_e:
             print(f"HATA: PDF build sırasında hata: {build_e}")
             raise

# ... (Dosyanızın geri kalanı) ...

    def generate_report_pdf(self, report_data: dict, file_path: str):
        # ... (Bu fonksiyon indirimden etkilenmez, aynı kalabilir) ...
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        story = []
        title = Paragraph("SATIŞ RAPORU", self.styles['CustomTitle'])
        story.append(title); story.append(Spacer(1, 20))
        report_info = [['Rapor Türü:', report_data.get('type', 'Genel Rapor')], ['Başlangıç Tarihi:', report_data.get('start_date', '')], ['Bitiş Tarihi:', report_data.get('end_date', '')], ['Oluşturulma Tarihi:', datetime.now().strftime('%d.%m.%Y %H:%M')]]
        info_table = Table(report_info, colWidths=[4*cm, 8*cm]); info_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), self.base_font), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (0, -1), self.base_font_bold), ('FONTSIZE', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)])); story.append(info_table); story.append(Spacer(1, 20))
        if 'stats' in report_data:
            stats_title = Paragraph("ÖZET İSTATİSTİKLER", self.styles['CustomHeading']); story.append(stats_title)
            stats = report_data['stats']
            stats_data = [['Toplam Fiş Sayısı:', str(stats.get('total_invoices', 0))], ['Toplam Ciro:', f"{stats.get('total_revenue', 0):.2f} TL"], ['Ortalama Fiş Tutarı:', f"{stats.get('avg_invoice_amount', 0):.2f} TL"], ['En Çok Satan Ürün:', stats.get('top_product', 'Ürün Yok')]]
            stats_table = Table(stats_data, colWidths=[6*cm, 4*cm]); stats_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), self.base_font), ('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONTNAME', (0, 0), (0, -1), self.base_font_bold), ('FONTSIZE', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey)])); story.append(stats_table); story.append(Spacer(1, 20))
        if 'details' in report_data:
            details_title = Paragraph("DETAYLI VERİLER", self.styles['CustomHeading']); story.append(details_title)
            # Rapor detaylarını tablo olarak eklemek için kod buraya eklenebilir.
        try:
             doc.build(story)
             print("DEBUG: Rapor PDF başarıyla oluşturuldu.")
        except Exception as build_e:
             print(f"HATA: Rapor PDF build sırasında hata: {build_e}")
             raise

    # add_header_footer (Kullanılmıyor gibi görünüyor, şimdilik dokunmuyoruz)