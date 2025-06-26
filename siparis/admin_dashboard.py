from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QLineEdit, QFormLayout, QMessageBox, QInputDialog, QDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class AdminDashboard(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Admin Paneli")
        self.setGeometry(300, 100, 800, 600)

        layout = QVBoxLayout()

        title_label = QLabel("Admin Paneli")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Ürün Yönetimi
        products_label = QLabel("Ürün Yönetimi")
        products_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(products_label)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)  # 4 columns + 1 for 'Stok Güncelle' and 'Ürün Sil'
        self.products_table.setHorizontalHeaderLabels(["Ürün Adı", "Stok", "Fiyat", "Stok Güncelle", "Ürün Sil"])
        self.load_products()
        layout.addWidget(self.products_table)

        # Ürün işlemleri
        product_buttons = QHBoxLayout()
        add_product_button = QPushButton("Ürün Ekle")
        add_product_button.clicked.connect(self.open_add_product_dialog)
        product_buttons.addWidget(add_product_button)
        layout.addLayout(product_buttons)

        # Log Yönetimi
        logs_label = QLabel("İşlem Logları")
        logs_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(logs_label)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(4)
        self.logs_table.setHorizontalHeaderLabels(["Log ID", "Müşteri ID", "Tür", "Detay"])
        self.load_logs()
        layout.addWidget(self.logs_table)

        self.setLayout(layout)

    def load_products(self):
        # Veritabanından ürünleri alıyoruz
        products = self.database.get_all_products()
        self.products_table.setRowCount(len(products))
        
        # Ürünleri tabloya ekliyoruz
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(product["ProductName"]))
            self.products_table.setItem(row, 1, QTableWidgetItem(str(product["Stock"])))
            self.products_table.setItem(row, 2, QTableWidgetItem(f"{product['Price']} TL"))
            
            # Her satıra "Stok Güncelle" butonu ekliyoruz
            update_button = QPushButton("Stok Güncelle")
            update_button.clicked.connect(lambda checked, row=row: self.update_stock_for_product(row))
            self.products_table.setCellWidget(row, 3, update_button)
            
            # Her satıra "Ürün Sil" butonu ekliyoruz
            delete_button = QPushButton("Ürün Sil")
            delete_button.clicked.connect(lambda checked, row=row: self.delete_product(row))
            self.products_table.setCellWidget(row, 4, delete_button)

    def load_logs(self):
        logs = self.database.get_all_logs()
        self.logs_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.logs_table.setItem(row, 0, QTableWidgetItem(str(log["LogID"])))
            self.logs_table.setItem(row, 1, QTableWidgetItem(str(log["CustomerID"])))
            self.logs_table.setItem(row, 2, QTableWidgetItem(log["LogType"]))
            self.logs_table.setItem(row, 3, QTableWidgetItem(log["LogDetails"]))

    def open_add_product_dialog(self):
        self.add_product_dialog = AddProductDialog(self)
        self.add_product_dialog.show()

    def save_product(self, product_name, stock, price):
        try:
            self.database.add_product(product_name, stock, price)
            QMessageBox.information(self, "Başarılı", "Ürün başarıyla eklendi!")
            self.load_products()  # Ürün listesi güncellenir
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Ürün eklenirken hata oluştu: {e}")

    # admin_dashboard.py içinde update_stock_for_product metodunu güncelle
    def update_stock_for_product(self, row):
        product_name = self.products_table.item(row, 0).text()
        stock = self.products_table.item(row, 1).text()

        new_stock, ok = QInputDialog.getInt(self, "Stok Güncelle", 
                                        "Yeni stok miktarını girin:", 
                                        int(stock))

        if ok:
            try:
                self.database.update_product_stock(product_name, new_stock)
                QMessageBox.information(self, "Başarılı", "Stok başarıyla güncellendi!")
                self.load_products()
                
                # Müşteri panelini güncellemek için sinyal gönder
                if hasattr(self.parent(), 'update_signal'):
                    self.parent().update_signal.emit()
                    
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Stok güncellenirken hata oluştu: {e}")
    def delete_product(self, row):
        product_name = self.products_table.item(row, 0).text()  # Ürün adı
        try:
            self.database.delete_product(product_name)
            QMessageBox.information(self, "Başarılı", "Ürün başarıyla silindi!")
            self.load_products()  # Ürünler tekrar yükleniyor
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Ürün silinirken hata oluştu: {e}")



class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ürün Ekle")
        self.setGeometry(500, 200, 400, 250)

        layout = QFormLayout(self)

        self.product_name_input = QLineEdit(self)
        self.stock_input = QLineEdit(self)
        self.price_input = QLineEdit(self)

        layout.addRow("Ürün Adı:", self.product_name_input)
        layout.addRow("Stok Miktarı:", self.stock_input)
        layout.addRow("Fiyat:", self.price_input)

        add_button = QPushButton("Ekle", self)
        add_button.clicked.connect(self.save_product)
        layout.addWidget(add_button)

        self.setLayout(layout)

    def save_product(self):
        product_name = self.product_name_input.text()
        stock = self.stock_input.text()
        price = self.price_input.text()

        # Geçerlilik kontrolleri
        if product_name and stock.isdigit() and price.replace('.', '', 1).isdigit():
            stock = int(stock)
            price = float(price)
            self.parent().save_product(product_name, stock, price)  # AdminDashboard'a bağlanıyoruz
            self.close()
        else:
            QMessageBox.warning(self, "Hata", "Geçersiz giriş! Lütfen tüm alanları doğru şekilde doldurun.")
