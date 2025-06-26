from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, 
    QMessageBox, QLineEdit, QHBoxLayout, QListWidget
)
from PyQt5.QtCore import Qt
from database import Database

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Penceresi - Sipariş Sistemi")
        self.setGeometry(100, 100, 1200, 800)
        
        # Ana widget ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Database bağlantısı
        self.db = Database()
        
        # Tab widget'ı oluştur
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Müşteri sekmelerini oluştur
        for i in range(1, 6):
            customer_tab = self.create_customer_tab(i)
            self.tabs.addTab(customer_tab, f"Müşteri {i}")
        
        # Admin sekmesini oluştur
        admin_tab = self.create_admin_tab()
        self.tabs.addTab(admin_tab, "Admin")

    def create_customer_tab(self, customer_id):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Müşteri bilgileri
        info_label = QLabel(f"Müşteri ID: {customer_id}")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(info_label)
        
        # Premium durumu
        is_premium = customer_id % 2 == 0  # Çift sayılı ID'ler premium
        status_label = QLabel(f"Müşteri Tipi: {'Premium' if is_premium else 'Normal'}")
        status_label.setStyleSheet("color: #1E3A8A;")
        layout.addWidget(status_label)
        
        # Sipariş formu
        form_layout = QVBoxLayout()
        
        # Ürün seçimi
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("Ürün Adı")
        self.product_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        form_layout.addWidget(self.product_input)
        
        # Miktar girişi
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Miktar")
        self.quantity_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        form_layout.addWidget(self.quantity_input)
        
        # Sipariş butonu
        order_button = QPushButton("Sipariş Ver")
        order_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        form_layout.addWidget(order_button)
        
        layout.addLayout(form_layout)
        
        # Sipariş geçmişi tablosu
        history_label = QLabel("Sipariş Geçmişi")
        history_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Ürün", "Miktar", "Tarih", "Durum"])
        layout.addWidget(self.history_table)
        
        tab.setLayout(layout)
        return tab

    def create_admin_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Admin panel başlığı
        title = QLabel("Admin Kontrol Paneli")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Sipariş tablosu
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(5)
        self.order_table.setHorizontalHeaderLabels(["Müşteri ID", "Ürün", "Miktar", "Tarih", "Durum"])
        layout.addWidget(self.order_table)
        
        # Butonlar
        buttons_layout = QHBoxLayout()
        
        approve_button = QPushButton("Seçili Siparişleri Onayla")
        approve_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(approve_button)
        
        reject_button = QPushButton("Seçili Siparişleri Reddet")
        reject_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        buttons_layout.addWidget(reject_button)
        
        layout.addLayout(buttons_layout)
        
        # Log alanı
        log_label = QLabel("İşlem Logları")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(log_label)
        
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)
        
        tab.setLayout(layout)
        return tab