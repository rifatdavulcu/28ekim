"""
Veritabanı modelleri (Güncellenmiş)
"""
from dataclasses import dataclass, field # field eklendi
from datetime import datetime
from typing import List, Optional
from decimal import Decimal


@dataclass
class Customer:
    """Müşteri modeli"""
    id: Optional[int] = None
    name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    tax_number: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Product:
    """Ürün modeli (Eksik alanlar eklendi)"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    # --- YENİ EKLENEN ALANLAR (Varsayılan değerlerle) ---
    description: str = ""
    unit_price: Decimal = field(default_factory=lambda: Decimal('0.00')) # Varsayılan 0.00
    category: str = ""
    brand: str = ""
    # --- YENİ ALANLAR SONU ---
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class InvoiceItem:
    """Fiş kalemi modeli"""
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    product_id: Optional[int] = None
    product_code: str = ""
    product_name: str = ""
    quantity: int = 0
    unit_price: Decimal = field(default_factory=lambda: Decimal('0.00')) # Varsayılan 0.00
    total_price: Decimal = field(default_factory=lambda: Decimal('0.00')) # Varsayılan 0.00


@dataclass
class Invoice:
    """Fiş modeli"""
    id: Optional[int] = None
    invoice_number: str = ""
    customer_id: Optional[int] = None
    customer_name: str = ""
    customer_address: str = ""
    delivery_person: str = ""
    receiver_person: str = ""
    subtotal: Decimal = field(default_factory=lambda: Decimal('0.00')) # Varsayılan 0.00
    discount_amount: Decimal = field(default_factory=lambda: Decimal('0.00')) # İndirim tutarı
    tax_rate: Decimal = field(default_factory=lambda: Decimal('0.20')) # Varsayılan 0.20
    tax_amount: Decimal = field(default_factory=lambda: Decimal('0.00')) # Varsayılan 0.00
    total_amount: Decimal = field(default_factory=lambda: Decimal('0.00')) # Varsayılan 0.00
    invoice_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    items: List[InvoiceItem] = field(default_factory=list) # Varsayılan boş liste
    # __post_init__ kaldırıldı, field(default_factory=list) daha iyi


@dataclass
class User:
    """Kullanıcı modeli"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = "user"
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class EmailSettings:
    """E-posta ayarları modeli"""
    id: Optional[int] = None
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    use_ssl: bool = True
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None