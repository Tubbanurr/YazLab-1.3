from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont
import time

class CustomerTab(QWidget):
    admin_signal = pyqtSignal(dict)
    def __init__(self, customer_id, main_window, db):
        super().__init__()
        self.customer_id = customer_id
        self.main_window = main_window
        self.db = db  # Veritabanı bağlantısı
        self.is_premium = customer_id % 2 == 0  # Örnek: Çift ID'ler premium
        self.orders = []
        self.timer_countdown = 20  # 2 dakika geri sayım
        self.timer = QTimer(self)  # Geri sayım timer'ı

        # UI
        self.layout = QVBoxLayout(self)

        # Önceki Siparişler Butonu
        self.previous_orders_button = QPushButton("Önceki Siparişler")
        self.previous_orders_button.clicked.connect(self.load_previous_orders)
        self.layout.addWidget(self.previous_orders_button)

        # Müşteri bilgi etiketi
        self.info_label = QLabel(f"Müşteri {customer_id} {'(Premium)' if self.is_premium else '(Normal)'}")
        self.info_label.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.info_label)

        # Bütçe etiketi
        self.budget_label = QLabel("Bütçe: 0 TL")
        self.layout.addWidget(self.budget_label)

        # Ürün seçim combobox'ı
        self.product_combo = QComboBox(self)
        self.product_combo.addItems(self.get_product_names())
        self.layout.addWidget(self.product_combo)

        # Miktar giriş alanı
        self.quantity_input = QLineEdit(self)
        self.quantity_input.setPlaceholderText("Adet")
        self.layout.addWidget(self.quantity_input)

        # Sepete ekle butonu
        self.add_to_cart_button = QPushButton("Sepete Ekle")
        self.add_to_cart_button.clicked.connect(self.add_to_cart)
        self.layout.addWidget(self.add_to_cart_button)

        # Sipariş ver butonu
        self.place_order_button = QPushButton("Sipariş Ver")
        self.place_order_button.clicked.connect(self.place_order)
        self.place_order_button.setEnabled(False)
        self.layout.addWidget(self.place_order_button)

        # Sepet etiketi
        self.cart_label = QLabel("Sepet: Boş")
        self.layout.addWidget(self.cart_label)

        # İlerleme çubuğu
        self.status_progress = QProgressBar(self)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(False)
        self.status_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #aaa; 
                border-radius: 5px; 
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #B39DDB, stop:1 #64B5F6);
            }
        """)
        self.layout.addWidget(self.status_progress)

        # Durum mesajı
        self.status_message = QLabel("Durum: Beklenmiyor")
        self.layout.addWidget(self.status_message)

        # Durum güncelleme zamanlayıcısı
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

        # Sayaç için yeni timer
        self.cart_timer = QTimer(self)
        self.cart_timer.timeout.connect(self.update_cart_timer)

        self.remaining_time = 0  # Sayaç başlangıçta sıfır olacak
        self.timer_label = QLabel("Süre: 02:00")
        self.timer_label.setFont(QFont("Arial", 12))  # Daha küçük font
        self.timer_label.setAlignment(Qt.AlignCenter)  # Ortalanmış metin
        self.timer_label.setStyleSheet("""
            background-color: #E8EAF6;  /* Hafif mor renk */
            border: 2px solid #8E24AA;  /* Mor kenar çizgisi */
            border-radius: 10px;  /* Kenarları yuvarlak yapar */
            padding: 5px;  /* İçeriye biraz boşluk ekler */
            color: #512DA8;  /* Mor renkli yazı */
        """)
        self.layout.addWidget(self.timer_label)
        self.timer_label.hide()  # Başlangıçta gizle

        self.load_customer_data()  # Müşteri bilgilerini yükle

    def load_previous_orders(self):
        """Müşterinin önceki siparişlerini yükler ve gösterir."""
        try:
            query = """
            SELECT p.ProductName, o.Quantity, o.TotalPrice, o.OrderDate, o.OrderStatus
            FROM Orders o
            JOIN Products p ON o.ProductID = p.ProductID
            WHERE o.CustomerID = ?
            ORDER BY o.OrderDate DESC
            """
            previous_orders = self.db.fetch_all(query, (self.customer_id,))

            if not previous_orders:
                QMessageBox.information(self, "Bilgi", "Bu müşteri için önceki sipariş bulunamadı.")
                return

            orders_window = QDialog(self)
            orders_window.setWindowTitle("Önceki Siparişler")
            layout = QVBoxLayout()

            orders_table = QTableWidget()
            orders_table.setColumnCount(5)
            orders_table.setHorizontalHeaderLabels(["Ürün", "Adet", "Toplam Fiyat", "Tarih", "Durum"])
            orders_table.setRowCount(len(previous_orders))

            for row, order in enumerate(previous_orders):
                for col, value in enumerate(order):
                    orders_table.setItem(row, col, QTableWidgetItem(str(value)))

            layout.addWidget(orders_table)
            orders_window.setLayout(layout)
            orders_window.setStyleSheet(
                "QTableWidget {"
                "    border: 1px solid #CCC;"
                "    font-size: 14px;"
                "    background-color: #F9F9F9;"
                "    gridline-color: #CCC;"
                "}"
                "QTableWidget::item {"
                "    padding: 4px;"
                "}"
            )
            orders_window.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Önceki siparişler yüklenirken bir hata oluştu: {e}")


    def load_customer_data(self):
        """Müşteri bilgilerini veritabanından al ve UI'yi güncelle"""
        query = "SELECT CustomerName, Budget, CustomerType FROM Customers WHERE CustomerID = ?"
        result = self.db.fetch_one(query, (self.customer_id,))
        if result:
            customer_name, budget, customer_type = result
            self.info_label.setText(f"{customer_name} ({'Premium' if customer_type == 'Premium' else 'Normal'})")
            self.budget_label.setText(f"Bütçe: {budget} TL")
            self.budget = budget  # Müşterinin bütçesini kaydet

    def log_order_error(self, error_message):
        """Hata mesajı log kaydını oluşturur"""
        query = """
        INSERT INTO Logs (CustomerID, LogType, LogDetails, LogDate)
        VALUES (?, 'Hata', ?, GETDATE())
        """
        self.db.execute_query(query, (self.customer_id, error_message))
    def get_product_price(self, product_name):
        """Veritabanından ürün fiyatını al"""
        query = "SELECT Price FROM Products WHERE ProductName = ?"
        result = self.db.fetch_one(query, (product_name,))
        if result:
            return result[0]
        return 0  # Eğer ürün bulunamazsa 0 döner

    def countdown(self):
        """Geri sayımı gerçekleştirir ve süre dolarsa sepete sıfırlama işlemi yapar."""
        self.timer_countdown -= 1
        if self.timer_countdown <= 0:
            self.clear_cart()
            self.status_message.setText("Süre doldu, sepet temizlendi.")
            self.timer.stop()  # Timer'ı durdur
        else:
            # Durumu güncelle
            self.status_message.setText(f"Süre: {self.timer_countdown} saniye kaldı.")

    

    def clear_cart(self):
        """Sepeti temizler."""
        self.orders.clear()
        self.cart_label.setText("Sepet: Boş")
        self.place_order_button.setEnabled(False)
        
    def update_status(self):
        """Sipariş durumunu güncelle"""
        try:
            if self.orders:
                # Veritabanından sipariş durumunu kontrol et
                query = """
                    SELECT OrderStatus, DATEDIFF(SECOND, OrderDate, GETDATE()) as WaitingTime
                    FROM Orders
                    WHERE CustomerID = ? AND OrderStatus != 'Tamamlandı'
                    ORDER BY OrderDate DESC
                """
                result = self.db.fetch_all(query, (self.customer_id,))

                if result:
                    status = result[0][0]
                    waiting_time = result[0][1] if result[0][1] is not None else 0

                    # Duruma göre ilerleme çubuğu ve mesaj
                    if status == 'Bekliyor':
                        self.status_progress.setValue(30)
                        self.status_message.setText(f"Müşteri {self.customer_id} siparişi bekliyor")

                    elif status == 'İşleniyor':
                        self.status_progress.setValue(70)
                        self.status_message.setText(f"Müşteri {self.customer_id}'in siparişi işleniyor")

                    elif status == 'Tamamlandı':
                        self.status_progress.setValue(100)
                        self.status_message.setText(f"Müşteri {self.customer_id} siparişi tamamlandı")

                    else:
                        self.status_progress.setValue(0)
                        self.status_message.setText("Durum bilinmiyor")
                else:
                    self.status_progress.setValue(0)
                    self.status_message.setText("Durum: Beklenmiyor")

            # Sepet durumunu güncelle
            if self.orders:
                products = [f"{order['product']} ({order['quantity']} adet)" for order in self.orders]
                self.cart_label.setText(f"Sepet: {', '.join(products)}")
            else:
                self.cart_label.setText("Sepet: Boş")

        except Exception as e:
            print(f"Durum güncellenirken hata: {e}")

    def get_product_names(self):
        """Veritabanından ürün adlarını çeker."""
        try:
            return [product["ProductName"] for product in self.db.get_all_products()]
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Ürünler yüklenirken bir hata oluştu: {e}")
            return []

    def add_to_cart(self):
        """Ürün sepete eklenir ve sayaç başlar."""
        product = self.product_combo.currentText()
        quantity = self.quantity_input.text()

        if not product or not quantity.isdigit():
            QMessageBox.warning(self, "Hata", "Geçerli bir ürün ve miktar girin!")
            return

        quantity = int(quantity)

        # 5'ten fazla ürün seçimini arayüz kısmında sınırla
        if quantity > 5:
            self.quantity_input.setText("5")
            QMessageBox.warning(self, "Hata", "Bir üründen en fazla 5 adet seçebilirsiniz!")
            return

        # Stok kontrolü
        try:
            query = "SELECT Stock FROM Products WHERE ProductName = ?"
            result = self.db.fetch_one(query, (product,))
            if result is None:
                QMessageBox.warning(self, "Hata", "Seçilen ürün veritabanında bulunamadı!")
                return

            current_stock = result[0]
            if current_stock < quantity:
                # Hata mesajı göster
                QMessageBox.warning(self, "Stok Yetersiz", f"{product} için yeterli stok bulunmamaktadır. Mevcut stok: {current_stock}")

                # Hata logunu kaydet
                self.db.execute_query("""
                    INSERT INTO Logs (CustomerID, LogType, LogDate, LogDetails)
                    VALUES (?, 'Hata', GETDATE(), ?)
                """, (self.customer_id, f"Stok yetersiz - Ürün: {product}, İstenen: {quantity}, Mevcut: {current_stock}"))

                return

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Stok kontrolü sırasında bir hata oluştu: {e}")
            return

        # Stok yeterli ise sepete ekle
        self.orders.append({"product": product, "quantity": quantity, "status": "Bekliyor"})
        self.cart_label.setText(f"Sepet: {product} - {quantity} adet")
        self.place_order_button.setEnabled(True)

        # Başlangıç durumu ve çubuğu ayarla
        self.status_progress.setValue(30)
        self.status_message.setText("Durum: Bekliyor")

        # Sayaç başlat
        self.remaining_time = 120  # 2 dakika
        self.cart_timer.start(1000)  # Her saniye sayar
        self.timer_label.show()  # Sayaç görünür hale gelir


    def place_order(self):
        """Siparişi veritabanına ekler"""
        try:
            if not self.orders:
                QMessageBox.warning(self, "Uyarı", "Sepetiniz boş!")
                return
            
            # Toplam tutarı hesapla
            total_amount = sum(
                order["quantity"] * self.db.get_product_price(order["product"])
                for order in self.orders
            )
            
            # Müşterinin mevcut bütçesini kontrol et
            query = "SELECT Budget FROM Customers WHERE CustomerID = ?"
            current_budget = self.db.fetch_one(query, (self.customer_id,))[0]
            
            if current_budget < total_amount:
                QMessageBox.warning(self, "Yetersiz Bakiye", 
                                f"Toplam tutar ({total_amount:.2f} TL) bakiyenizden ({current_budget:.2f} TL) fazla!")
                return

            # Siparişleri ekle ve bütçeyi güncelle
            with self.db.lock:  # Thread güvenliği için kilit kullan
                for order in self.orders:
                    # Önce aynı üründen bekleyen sipariş var mı kontrol et
                    check_query = """
                        SELECT OrderID 
                        FROM Orders 
                        WHERE CustomerID = ? 
                        AND ProductID = (SELECT ProductID FROM Products WHERE ProductName = ?)
                        AND OrderStatus = 'Bekliyor'
                    """
                    existing_order = self.db.fetch_one(check_query, (self.customer_id, order["product"]))
                    
                    if existing_order:
                        # Var olan siparişi güncelle
                        update_query = """
                            UPDATE Orders 
                            SET Quantity = Quantity + ?
                            WHERE OrderID = ?
                        """
                        self.db.execute_query(update_query, (order["quantity"], existing_order[0]))
                    else:
                        # Yeni sipariş ekle
                        insert_query = """
                            INSERT INTO Orders (CustomerID, ProductID, Quantity, OrderDate, OrderStatus)
                            VALUES (?, (SELECT ProductID FROM Products WHERE ProductName = ?), ?, GETDATE(), 'Bekliyor')
                        """
                        self.db.execute_query(insert_query, (self.customer_id, order["product"], order["quantity"]))

                # Bütçeyi güncelle
                update_budget_query = """
                    UPDATE Customers 
                    SET Budget = Budget - ? 
                    WHERE CustomerID = ?
                """
                self.db.execute_query(update_budget_query, (total_amount, self.customer_id))

            # Bütçe göstergesini güncelle
            self.budget = current_budget - total_amount
            self.budget_label.setText(f"Bütçe: {self.budget:.2f} TL")

            # Siparişi başarıyla ekledikten sonra
            QMessageBox.information(self, "Başarılı", f"Siparişiniz alındı! Kalan bakiye: {self.budget:.2f} TL")
            self.orders.clear()  # Sepeti temizle
            self.cart_label.setText("Sepet: Boş")
            self.admin_signal.emit({"customer_id": self.customer_id, "orders": self.orders})
            
        except Exception as e:
            print(f"Sipariş eklenirken hata: {e}")
            QMessageBox.critical(self, "Hata", f"Sipariş eklenirken hata oluştu: {str(e)}")


    def update_cart_timer(self):
        """Sepet için sayaç geri sayımını güncelle."""
        self.remaining_time -= 1

        if self.remaining_time <= 0:
            # Süre dolarsa sepete eklenen ürünleri sıfırla
            self.orders.clear()
            self.cart_label.setText("Sepet: Boş")
            self.place_order_button.setEnabled(False)
            self.timer_label.hide()  # Sayaç gizlenir
            self.cart_timer.stop()  # Timer durdurulur
            self.status_progress.setValue(0)
            self.status_message.setText("Durum: Süre Bitti")
        else:
            # Geriye kalan süreyi formatla (örneğin: 01:45)
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.timer_label.setText(f"Süre: {minutes:02}:{seconds:02}")