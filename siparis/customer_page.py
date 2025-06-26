from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient
from database import Database

class CustomerPage(QWidget):
    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowState(Qt.WindowMaximized)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Arka plan gradyanı
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#E8EAF6"))
        gradient.setColorAt(1, QColor("#FFFFFF"))
        palette = self.palette()
        palette.setBrush(QPalette.Window, gradient)
        self.setPalette(palette)

        # Müşteri Bilgileri
        self.customer_data = self.get_customer_data()
        info_layout = QHBoxLayout()
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #FFFFFF; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);")
        info_layout.addWidget(self.create_info_section("Müşteri Adı", self.customer_data["CustomerName"]))
        info_layout.addWidget(self.create_info_section("Müşteri ID", str(self.customer_data["CustomerID"])))
        info_layout.addWidget(self.create_info_section("Bütçe", f"{self.customer_data['Budget']} TL"))
        info_layout.addWidget(self.create_info_section("Müşteri Tipi", self.customer_data["CustomerType"]))
        info_widget.setLayout(info_layout)
        main_layout.addWidget(info_widget)

        # Sipariş Oluşturma Formu
        order_layout = QVBoxLayout()
        order_widget = QWidget()
        order_widget.setStyleSheet("background-color: #FFFFFF; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);")
        
        order_title = QLabel("Sipariş Oluştur")
        order_title.setFont(QFont("Arial", 18, QFont.Bold))
        order_title.setStyleSheet("color: #3F51B5; margin-bottom: 15px;")
        order_layout.addWidget(order_title)

        self.product_combo = QComboBox()
        self.fill_product_combo()
        self.product_combo.setStyleSheet("padding: 10px; font-size: 14px; border: 1px solid #C5CAE9; border-radius: 5px;")
        order_layout.addWidget(self.product_combo)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 5)
        self.quantity_spin.setStyleSheet("padding: 10px; font-size: 14px; border: 1px solid #C5CAE9; border-radius: 5px;")
        order_layout.addWidget(self.quantity_spin)

        order_button = QPushButton("Sipariş Ver")
        order_button.setStyleSheet("""
            QPushButton {
                background-color: #3F51B5;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5C6BC0;
            }
        """)
        order_button.clicked.connect(self.place_order)
        order_layout.addWidget(order_button)

        order_widget.setLayout(order_layout)
        main_layout.addWidget(order_widget)

        # Sipariş Geçmişi
        history_title = QLabel("Sipariş Geçmişi")
        history_title.setFont(QFont("Arial", 18, QFont.Bold))
        history_title.setStyleSheet("color: #3F51B5; margin-top: 20px; margin-bottom: 10px;")
        main_layout.addWidget(history_title)

        self.order_table = QTableWidget()
        self.order_table.setColumnCount(5)
        self.order_table.setHorizontalHeaderLabels(["Sipariş ID", "Ürün", "Miktar", "Toplam Fiyat", "Durum"])
        self.order_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border-radius: 15px;
                padding: 10px;
            }
            QHeaderView::section {
                background-color: #C5CAE9;
                padding: 5px;
                border: 1px solid #7986CB;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fill_order_table()
        main_layout.addWidget(self.order_table)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(main_layout)
        scroll_area.setWidget(scroll_content)

        main_scroll_layout = QVBoxLayout(self)
        main_scroll_layout.addWidget(scroll_area)
        self.setLayout(main_scroll_layout)


    def get_customer_data(self):
        query = "SELECT CustomerID, CustomerName, Budget, CustomerType FROM Customers WHERE CustomerID = ?"
        result = self.db.fetch_all(query, (self.customer_id,))
        if result:
            return {
                "CustomerID": result[0][0],
                "CustomerName": result[0][1],
                "Budget": result[0][2],
                "CustomerType": result[0][3]
            }
        return None

    def create_info_section(self, title, value):
        widget = QWidget()
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        value_label = QLabel(str(value))
        value_label.setFont(QFont("Arial", 14))
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        widget.setLayout(layout)
        return widget

    def fill_product_combo(self):
        query = "SELECT ProductName FROM Products"
        products = self.db.fetch_all(query)
        self.product_combo.addItems([product[0] for product in products])

    def place_order(self):
        try:
            product_name = self.product_combo.currentText()
            quantity = self.quantity_spin.value()
            
            # Ürün bilgilerini al
            query = "SELECT ProductID, Price, Stock FROM Products WHERE ProductName = ?"
            product = self.db.fetch_all(query, (product_name,))[0]
            
            product_id = product[0]
            price = product[1]
            stock = product[2]
            total_price = price * quantity

            # Stok kontrolü
            if stock < quantity:
                self.create_log(None, "Hata", f"Yetersiz stok: {product_name} - İstenen: {quantity}, Mevcut: {stock}")
                QMessageBox.warning(self, "Uyarı", "Yetersiz stok!")
                return

            # Bütçe kontrolü
            if self.customer_data["Budget"] < total_price:
                self.create_log(None, "Hata", f"Yetersiz bütçe: Gerekli: {total_price}TL, Mevcut: {self.customer_data['Budget']}TL")
                QMessageBox.warning(self, "Uyarı", "Yetersiz bütçe!")
                return

            # Siparişi oluştur
            order_query = """
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderDate, OrderStatus)
                OUTPUT INSERTED.OrderID
                VALUES (?, ?, ?, ?, GETDATE(), 'Bekliyor')
            """
            order_id = self.db.execute_query(order_query, 
                (self.customer_id, product_id, quantity, total_price))

            # Stok güncelle
            update_stock_query = "UPDATE Products SET Stock = Stock - ? WHERE ProductID = ?"
            self.db.execute_query(update_stock_query, (quantity, product_id))

            # Müşteri bilgilerini güncelle
            self.update_customer_stats(total_price)

            # Başarılı işlem logu
            log_details = f"""
                Ürün: {product_name}
                Miktar: {quantity}
                Toplam Fiyat: {total_price}TL
                Müşteri Türü: {self.customer_data['CustomerType']}
            """
            self.create_log(order_id, "Bilgilendirme", f"Satın alma başarılı. {log_details}")

            # Müşteri verilerini yenile
            self.customer_data = self.get_customer_data()
            
            # Tabloyu güncelle
            self.fill_order_table()

            QMessageBox.information(self, "Başarılı", "Sipariş başarıyla oluşturuldu!")

        except Exception as e:
            self.create_log(None, "Hata", f"Sipariş oluşturma hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", "Sipariş oluşturulurken bir hata oluştu!")

    def fill_order_table(self):
        query = """
            SELECT o.OrderID, p.ProductName, o.Quantity, o.TotalPrice, o.OrderStatus
            FROM Orders o
            JOIN Products p ON o.ProductID = p.ProductID
            WHERE o.CustomerID = ?
            ORDER BY o.OrderDate DESC
        """
        orders = self.db.fetch_all(query, (self.customer_id,))
        
        self.order_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            for col, value in enumerate(order):
                self.order_table.setItem(row, col, QTableWidgetItem(str(value)))

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

    def create_log(self, order_id, log_type, log_details):
        """Log kaydı oluşturma"""
        query = """
            INSERT INTO Logs (CustomerID, OrderID, LogDate, LogType, LogDetails)
            VALUES (?, ?, GETDATE(), ?, ?)
        """
        self.db.execute_query(query, (self.customer_id, order_id, log_type, log_details))

    def update_customer_stats(self, total_price):
        """Müşteri istatistiklerini güncelleme"""
        query = """
            UPDATE Customers 
            SET Budget = Budget - ?,
                TotalSpent = TotalSpent + ?
            WHERE CustomerID = ?
        """
        self.db.execute_query(query, (total_price, total_price, self.customer_id))

    def place_order(self):
        product_name = self.product_combo.currentText()
        quantity = self.quantity_spin.value()
        
        # Ürün bilgilerini al
        query = "SELECT ProductID, Price, Stock FROM Products WHERE ProductName = ?"
        product = self.db.fetch_all(query, (product_name,))[0]
        product_id = product[0]
        price = product[1]
        stock = product[2]
        
        total_price = price * quantity

        try:
            # Stok kontrolü
            if stock < quantity:
                self.create_log(None, "Hata", f"Yetersiz stok: {product_name} - İstenen: {quantity}, Mevcut: {stock}")
                QMessageBox.warning(self, "Uyarı", "Yetersiz stok!")
                return

            # Bütçe kontrolü
            if self.customer_data["Budget"] < total_price:
                self.create_log(None, "Hata", f"Yetersiz bütçe: Gerekli: {total_price}TL, Mevcut: {self.customer_data['Budget']}TL")
                QMessageBox.warning(self, "Uyarı", "Yetersiz bütçe!")
                return

            # Siparişi oluştur
            order_query = """
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderDate, OrderStatus)
                OUTPUT INSERTED.OrderID
                VALUES (?, ?, ?, ?, GETDATE(), 'Bekliyor')
            """
            order_id = self.db.execute_query(order_query, 
                (self.customer_id, product_id, quantity, total_price))

            # Stok güncelle
            update_stock_query = "UPDATE Products SET Stock = Stock - ? WHERE ProductID = ?"
            self.db.execute_query(update_stock_query, (quantity, product_id))

            # Müşteri bilgilerini güncelle
            self.update_customer_stats(total_price)

            # Başarılı işlem logu
            log_details = f"""
                Ürün: {product_name}
                Miktar: {quantity}
                Toplam Fiyat: {total_price}TL
                Müşteri Türü: {self.customer_data['CustomerType']}
            """
            self.create_log(order_id, "Bilgilendirme", f"Satın alma başarılı. {log_details}")

            # Müşteri verilerini yenile
            self.customer_data = self.get_customer_data()
            
            # Tabloyu güncelle
            self.fill_order_table()

            QMessageBox.information(self, "Başarılı", "Sipariş başarıyla oluşturuldu!")

        except Exception as e:
            self.create_log(None, "Hata", f"Sipariş oluşturma hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", "Sipariş oluşturulurken bir hata oluştu!")

    def fill_order_table(self):
        query = """
            SELECT 
                o.OrderID, 
                p.ProductName, 
                o.Quantity, 
                o.TotalPrice, 
                o.OrderStatus,
                o.OrderDate
            FROM Orders o
            JOIN Products p ON o.ProductID = p.ProductID
            WHERE o.CustomerID = ?
            ORDER BY o.OrderDate DESC
        """
        orders = self.db.fetch_all(query, (self.customer_id,))
        
        self.order_table.setColumnCount(6)
        self.order_table.setHorizontalHeaderLabels([
            "Sipariş ID", "Ürün", "Miktar", "Toplam Fiyat", "Durum", "Sipariş Tarihi"
        ])
        
        self.order_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            for col, value in enumerate(order):
                item = QTableWidgetItem(str(value))
                # Duruma göre renklendirme
                if col == 4:  # OrderStatus kolonu
                    if value == 'Bekliyor':
                        item.setBackground(QColor('#FFF3CD'))
                    elif value == 'İşleniyor':
                        item.setBackground(QColor('#CCE5FF'))
                    elif value == 'Tamamlandı':
                        item.setBackground(QColor('#D4EDDA'))
                self.order_table.setItem(row, col, item)
