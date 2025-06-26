# product_dialog.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QSpinBox, QDoubleSpinBox, 
                            QPushButton, QFormLayout)

class ProductDialog(QDialog):
    def __init__(self, parent=None, product_name=None, current_stock=None, current_price=None):
        super().__init__(parent)
        self.setWindowTitle("Ürün Ekle/Güncelle")
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                font-size: 14px;
                color: #1a237e;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton[type="save"] {
                background-color: #4caf50;
            }
            QPushButton[type="save"]:hover {
                background-color: #388e3c;
            }
            QPushButton[type="cancel"] {
                background-color: #f44336;
            }
            QPushButton[type="cancel"]:hover {
                background-color: #d32f2f;
            }
        """)
        self.setup_ui(product_name, current_stock, current_price)

    def setup_ui(self, product_name=None, current_stock=None, current_price=None):
        layout = QFormLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Ürün adı
        self.name_input = QLineEdit()
        if product_name:
            self.name_input.setText(product_name)
            self.name_input.setReadOnly(True)
        layout.addRow("Ürün Adı:", self.name_input)

        # Stok
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)
        if current_stock is not None:
            self.stock_input.setValue(current_stock)
        layout.addRow("Stok:", self.stock_input)

        # Fiyat
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setSuffix(" TL")
        if current_price is not None:
            self.price_input.setValue(current_price)
        layout.addRow("Fiyat:", self.price_input)

        # Butonlar
        button_box = QHBoxLayout()
        
        save_btn = QPushButton("Kaydet")
        save_btn.setProperty("type", "save")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        
        layout.addRow(button_box)
        self.setLayout(layout)

    def get_values(self):
        return {
            'name': self.name_input.text(),
            'stock': self.stock_input.value(),
            'price': self.price_input.value()
        }