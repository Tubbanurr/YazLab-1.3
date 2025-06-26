from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtCore import *
import random
import time
from customer_tab import CustomerTab
from PyQt5.QtGui import *

class AdminTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.order_table = None
        self.product_table = None
        self.orders = []  # orders listesini başlat
        self.log_list = QListWidget()  # log listesini ekle
        self.init_ui()
        
        # Timer ekle - her 1 saniyede bir güncelleme yapacak
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(1000)  # 1 saniye
    
    def init_ui(self):
        # Ana layout
        layout = QVBoxLayout()

        # Scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QGridLayout()
        content_layout.setSpacing(15)
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        # Üst Panel - Sipariş İşlemleri
        order_operations = QGroupBox("Sipariş İşlemleri")
        order_layout = QVBoxLayout()
        order_layout.setSpacing(10)

        # Buton konteyner
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.approve_selected_button = QPushButton("Seçili Siparişleri Onayla")
        self.approve_all_button = QPushButton("Tüm Siparişleri Onayla")
        self.approve_selected_button.clicked.connect(self.approve_selected_orders)
        self.approve_all_button.clicked.connect(self.approve_all_orders)

        buttons_layout.addWidget(self.approve_selected_button)
        buttons_layout.addWidget(self.approve_all_button)
        order_layout.addLayout(buttons_layout)

        # Sipariş tablosu
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(6)
        self.order_table.setHorizontalHeaderLabels(["Seç", "Müşteri ID", "Ürün", "Adet", "Durum", "Öncelik Skoru"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.order_table.setMinimumHeight(200)  # Minimum yükseklik
        order_layout.addWidget(self.order_table)
        order_operations.setLayout(order_layout)

        # Ürün Yönetimi Paneli
        product_operations = QGroupBox("Ürün Yönetimi")
        product_layout = QVBoxLayout()
        product_layout.setSpacing(10)

        product_buttons = QHBoxLayout()
        add_product_btn = QPushButton("Yeni Ürün Ekle")
        add_product_btn.clicked.connect(self.add_product_dialog)
        product_buttons.addWidget(add_product_btn)
        product_layout.addLayout(product_buttons)

        # Ürün tablosu
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(["Ürün ID", "Ürün Adı", "Stok", "Fiyat", "İşlemler"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.setMinimumHeight(200)  # Minimum yükseklik
        product_layout.addWidget(self.product_table)
        product_operations.setLayout(product_layout)

        # Grafikler Paneli - Küçültülmüş boyutlar
        graphs_panel = QGroupBox("Sistem Analizi")
        graphs_layout = QHBoxLayout()
        graphs_layout.setSpacing(15)

        # Sol grafik (Öncelik) - Küçültülmüş
        left_graph_container = QVBoxLayout()
        left_graph_container.setSpacing(5)
        priority_label = QLabel("Müşteri Öncelik Skorları")
        priority_label.setAlignment(Qt.AlignCenter)
        left_graph_container.addWidget(priority_label)
        
        self.priority_figure = Figure(figsize=(6, 4))  # Küçültülmüş boyut
        self.priority_canvas = FigureCanvas(self.priority_figure)
        self.priority_canvas.setMinimumHeight(250)  # Sabit yükseklik
        left_graph_container.addWidget(self.priority_canvas)

        # Sağ grafikler konteyner
        right_graph_container = QVBoxLayout()
        right_graph_container.setSpacing(10)

        # Stok Bar Grafik - Küçültülmüş
        stock_bar_label = QLabel("Ürün Stok Durumu")
        stock_bar_label.setAlignment(Qt.AlignCenter)
        right_graph_container.addWidget(stock_bar_label)
        
        self.stock_bar_figure = Figure(figsize=(4, 2.5))  # Küçültülmüş boyut
        self.stock_bar_canvas = FigureCanvas(self.stock_bar_figure)
        self.stock_bar_canvas.setMinimumHeight(120)  # Sabit yükseklik
        self.update_stock_bars()
        right_graph_container.addWidget(self.stock_bar_canvas)

        # Stok Pasta Grafik - Küçültülmüş
        stock_pie_label = QLabel("Stok Dağılımı")
        stock_pie_label.setAlignment(Qt.AlignCenter)
        right_graph_container.addWidget(stock_pie_label)
        
        self.stock_pie_figure = Figure(figsize=(4, 2.5))  # Küçültülmüş boyut
        self.stock_pie_canvas = FigureCanvas(self.stock_pie_figure)
        self.stock_pie_canvas.setMinimumHeight(120)  # Sabit yükseklik
        self.update_stock_pie()
        right_graph_container.addWidget(self.stock_pie_canvas)

        graphs_layout.addLayout(left_graph_container, 55)
        graphs_layout.addLayout(right_graph_container, 45)
        graphs_panel.setLayout(graphs_layout)

        # Log Paneli
        log_panel = QGroupBox("Sistem Logları")
        log_layout = QVBoxLayout()
        self.log_list = QListWidget()
        self.log_list.setMinimumHeight(150)  # Minimum yükseklik
        log_layout.addWidget(self.log_list)
        log_panel.setLayout(log_layout)

        # Layout yerleşimi
        content_layout.addWidget(order_operations, 0, 0)
        content_layout.addWidget(product_operations, 0, 1)
        content_layout.addWidget(graphs_panel, 1, 0, 1, 2)
        content_layout.addWidget(log_panel, 2, 0, 1, 2)

        self.setStyleSheet("""
                    QGroupBox {
                        background-color: #FFFFFF;
                        border: 2px solid #E3E8F0;
                        border-radius: 12px;
                        margin-top: 12px;
                        padding: 15px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 8px;
                        color: #2D3748;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton {
                        background-color: #4A5568;
                        color: white;
                        border: none;
                        padding: 10px 15px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #2D3748;
                    }
                    QTableWidget {
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                        background-color: #FFFFFF;
                        gridline-color: #EDF2F7;
                        font-size: 13px;
                    }
                    QTableWidget::item {
                        padding: 8px;
                        border-bottom: 1px solid #EDF2F7;
                    }
                    QTableWidget::item:selected {
                        background-color: #EBF4FF;
                        color: #2D3748;
                    }
                    QHeaderView::section {
                        background-color: #4A5568;
                        color: white;
                        padding: 8px;
                        border: none;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QLabel {
                        color: #2D3748;
                        font-size: 13px;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }
                    QListWidget {
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                        background-color: #FFFFFF;
                        padding: 8px;
                        font-size: 13px;
                    }
                    QListWidget::item {
                        padding: 8px;
                        border-bottom: 1px solid #EDF2F7;
                    }
                    QScrollArea {
                        border: none;
                    }
                    QScrollBar:vertical {
                        border: none;
                        background: #EDF2F7;
                        width: 10px;
                        border-radius: 5px;
                    }
                    QScrollBar::handle:vertical {
                        background: #4A5568;
                        border-radius: 5px;
                        min-height: 20px;
                    }
                    QScrollBar::add-line:vertical,
                    QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    QComboBox {
                        padding: 8px;
                        border: 1px solid #E2E8F0;
                        border-radius: 6px;
                        background-color: #FFFFFF;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox::down-arrow {
                        image: none;
                        border-left: 2px solid #4A5568;
                        border-bottom: 2px solid #4A5568;
                        width: 8px;
                        height: 8px;
                        transform: rotate(45deg);
                        margin-right: 8px;
                    }
                    QSpinBox, QDoubleSpinBox {
                        padding: 8px;
                        border: 1px solid #E2E8F0;
                        border-radius: 6px;
                        background-color: #FFFFFF;
                    }
                    QLineEdit {
                        padding: 8px;
                        border: 1px solid #E2E8F0;
                        border-radius: 6px;
                        background-color: #FFFFFF;
                    }
                """)

        layout.addWidget(scroll_area)
        self.setLayout(layout)

        # Başlangıç verilerini yükle
        self.load_products()
        self.load_orders()
        
    def refresh_data(self):
        """Tüm verileri günceller"""
        self.load_orders()  # Sipariş tablosunu güncelle
        self.update_graphs()  # Grafikleri güncelle
        self.load_logs()    # Logları güncelle

    def update_stock_info(self, stok_verisi):
        """Stok bilgilerini günceller"""
        try:
            # Ürün tablosunu güncelle
            self.load_products()
            
            # Grafikleri güncelle
            self.update_stock_bars()
            self.update_stock_pie()
            self.update_priority_graph()
            
        except Exception as e:
            print(f"Stok bilgileri güncellenirken hata: {e}")

    def handle_order_processed(self, order_data):
        """İşlenen siparişleri yönetir"""
        try:
            # Sipariş tablosunu güncelle
            self.load_orders()
            
            # Stok tablosunu güncelle
            self.load_products()
            
            # Logları güncelle
            self.load_logs()
            
            # Grafikleri güncelle
            self.update_graphs()
            
        except Exception as e:
            print(f"Sipariş işleme güncellemesi sırasında hata: {e}")

    def add_order(self, order):
        """Yeni sipariş ekle ve tabloyu güncelle"""
        try:
            # Siparişi listeye ekle
            self.orders.append(order)
            
            # Siparişi veritabanına ekle
            for order_item in order["orders"]:
                query = """
                    INSERT INTO Orders (CustomerID, ProductID, Quantity, OrderDate, OrderStatus)
                    VALUES (?, (SELECT ProductID FROM Products WHERE ProductName = ?), ?, GETDATE(), 'Bekliyor')
                """
                self.db.execute_query(query, (
                    order["customer_id"],
                    order_item["product"],
                    order_item["quantity"]
                ))

            # Tabloyu güncelle
            self.load_orders()
            
        except Exception as e:
            print(f"Sipariş eklenirken hata: {e}")
            QMessageBox.critical(self, "Hata", f"Sipariş eklenirken hata oluştu: {str(e)}")

    def update_graphs(self):
        self.update_stock_bars()
        self.update_stock_pie()
        self.update_priority_graph()

    def update_stock_bars(self):
        try:
            products = self.db.get_stock_levels()
            names = [p['urun_adi'] for p in products]
            stocks = [max(p['stok'], 0) for p in products]  # Negatif değerleri sıfıra indir

            self.stock_bar_figure.clear()
            ax = self.stock_bar_figure.add_subplot(111)
            ax.bar(names, stocks, color=['green' if s >= 10 else 'red' for s in stocks])
            ax.set_title("Ürünlerin Stok Durumları")
            ax.set_ylabel("Stok Miktarı")
            ax.set_xlabel("Ürünler")
            ax.tick_params(axis='x', rotation=45)

            self.stock_bar_canvas.draw()
        except Exception as e:
            print(f"Stok grafikleri güncellenirken hata: {e}")

    def update_stock_pie(self):
        try:
            products = self.db.get_stock_levels()
            names = [p['urun_adi'] for p in products]
            stocks = [max(p['stok'], 0) for p in products]  # Negatif değerleri sıfıra indir

            if sum(stocks) == 0:
                stocks = [1 for _ in stocks]  # Tüm değerler sıfırsa varsayılan değerler

            self.stock_pie_figure.clear()
            ax = self.stock_pie_figure.add_subplot(111)
            ax.pie(stocks, labels=names, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
            ax.set_title("Stok Dağılımı")

            self.stock_pie_canvas.draw()
        except Exception as e:
            print(f"Pasta grafiği güncellenirken hata: {e}")

    def update_priority_graph(self):
        try:
            customers = self.db.fetch_all("SELECT CustomerID, CustomerType, Budget FROM Customers")
            customer_names = [f"Müşteri {c[0]}" for c in customers]
            priority_scores = [15 if c[1] == 'Premium' else 10 + random.randint(0, 5) for c in customers]

            self.priority_figure.clear()
            ax = self.priority_figure.add_subplot(111)
            ax.bar(customer_names, priority_scores, color=['blue' if "Premium" in n else 'orange' for n in customer_names])
            ax.set_title("Müşteri Öncelik Skorları")
            ax.set_ylabel("Öncelik Skoru")
            ax.set_xlabel("Müşteriler")
            ax.tick_params(axis='x', rotation=45)

            self.priority_canvas.draw()
        except Exception as e:
            print(f"Öncelik grafikleri güncellenirken hata: {e}")

    def load_products(self):
        try:
            # Ürünleri veritabanından çek
            query = "SELECT ProductID, ProductName, Stock, Price FROM Products"
            products = self.db.fetch_all(query)

            self.product_table.setRowCount(len(products))
            for row, product in enumerate(products):
                # Ürün bilgilerini tabloya ekle
                self.product_table.setItem(row, 0, QTableWidgetItem(str(product[0])))
                self.product_table.setItem(row, 1, QTableWidgetItem(product[1]))
                self.product_table.setItem(row, 2, QTableWidgetItem(str(product[2])))
                self.product_table.setItem(row, 3, QTableWidgetItem(str(product[3])))

                # İşlem butonları için widget
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)

                # Stok güncelleme butonu
                update_stock_btn = QPushButton("Stok Güncelle")
                update_stock_btn.setStyleSheet(
                    "QPushButton {"
                    "    background-color: #FDD835;"
                    "    color: black;"
                    "    padding: 5px;"
                    "    border-radius: 6px;"
                    "    font-size: 12px;"
                    "}"
                    "QPushButton:hover {"
                    "    background-color: #FBC02D;"
                    "}"
                )
                update_stock_btn.clicked.connect(lambda _, r=row: self.update_stock_dialog(r))
                actions_layout.addWidget(update_stock_btn)

                # Silme butonu
                delete_btn = QPushButton("Sil")
                delete_btn.setStyleSheet(
                    "QPushButton {"
                    "    background-color: #FF7043;"
                    "    color: white;"
                    "    padding: 5px;"
                    "    border-radius: 6px;"
                    "    font-size: 12px;"
                    "    font-weight: bold;"
                    "}"
                    "QPushButton:hover {"
                    "    background-color: #D84315;"
                    "}"
                )
                delete_btn.clicked.connect(lambda _, r=row: self.delete_product(r))
                actions_layout.addWidget(delete_btn)

                actions_widget.setLayout(actions_layout)
                self.product_table.setCellWidget(row, 4, actions_widget)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürünler yüklenirken hata oluştu: {str(e)}")

    def add_product_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Ürün Ekle")
        layout = QFormLayout()

        # Input alanları
        name_input = QLineEdit()
        stock_input = QSpinBox()
        stock_input.setRange(0, 10000)
        price_input = QDoubleSpinBox()
        price_input.setRange(0, 100000)
        price_input.setDecimals(2)

        layout.addRow("Ürün Adı:", name_input)
        layout.addRow("Stok:", stock_input)
        layout.addRow("Fiyat:", price_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            try:
                # Yeni ürünü veritabanına ekle
                query = """
                INSERT INTO Products (ProductName, Stock, Price)
                VALUES (?, ?, ?)
                """
                self.db.execute_query(query, (
                    name_input.text(),
                    stock_input.value(),
                    price_input.value()
                ))
                self.load_products()  # Tabloyu yenile
                QMessageBox.information(self, "Başarılı", "Ürün başarıyla eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün eklenirken hata oluştu: {str(e)}")

    def update_stock_dialog(self, row):
        product_id = self.product_table.item(row, 0).text()
        current_stock = int(self.product_table.item(row, 2).text())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Stok Güncelle")
        layout = QFormLayout()

        stock_input = QSpinBox()
        stock_input.setRange(0, 10000)
        stock_input.setValue(current_stock)
        layout.addRow("Yeni Stok:", stock_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            try:
                query = "UPDATE Products SET Stock = ? WHERE ProductID = ?"
                self.db.execute_query(query, (stock_input.value(), product_id))
                self.load_products()  # Tabloyu yenile
                QMessageBox.information(self, "Başarılı", "Stok başarıyla güncellendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Stok güncellenirken hata oluştu: {str(e)}")

    def delete_product(self, row):
        product_id = self.product_table.item(row, 0).text()
        product_name = self.product_table.item(row, 1).text()
        
        reply = QMessageBox.question(self, 'Ürün Silme',
                                f'"{product_name}" ürününü silmek istediğinizden emin misiniz?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Önce ürüne ait siparişleri kontrol et
                check_orders_query = """
                    SELECT COUNT(*) 
                    FROM Orders 
                    WHERE ProductID = ?
                """
                result = self.db.fetch_one(check_orders_query, (product_id,))
                
                if result[0] > 0:
                    # Ürüne ait siparişler varsa kullanıcıya sor
                    reply = QMessageBox.question(self, 'Dikkat',
                        'Bu ürüne ait siparişler bulunmaktadır. Tüm siparişler de silinecektir. Devam etmek istiyor musunuz?',
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    
                    if reply == QMessageBox.Yes:
                        # Önce siparişleri sil
                        delete_orders_query = "DELETE FROM Orders WHERE ProductID = ?"
                        self.db.execute_query(delete_orders_query, (product_id,))
                
                # Sonra ürünü sil
                delete_product_query = "DELETE FROM Products WHERE ProductID = ?"
                self.db.execute_query(delete_product_query, (product_id,))
                
                self.load_products()  # Tabloyu yenile
                QMessageBox.information(self, "Başarılı", "Ürün başarıyla silindi!")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün silinirken hata oluştu: {str(e)}")

    
    def approve_selected_orders(self):
        """Seçili siparişleri onaylar."""
        try:
            selected_rows = []
            for row in range(self.order_table.rowCount()):
                if self.order_table.item(row, 0).checkState() == Qt.Checked:
                    selected_rows.append(row)

            if not selected_rows:
                QMessageBox.warning(self, "Uyarı", "Lütfen onaylanacak siparişleri seçin!")
                return

            # Her seçili sipariş için işlem yap
            with self.db.lock:  # Thread güvenliği için kilit kullan
                for row in sorted(selected_rows, reverse=True):
                    customer_id = int(self.order_table.item(row, 1).text())
                    product_name = self.order_table.item(row, 2).text()
                    quantity = int(self.order_table.item(row, 3).text())

                    # Önce bekleyen sipariş var mı kontrol et
                    check_order_query = """
                        SELECT OrderID, OrderStatus
                        FROM Orders
                        WHERE CustomerID = ?
                        AND ProductID = (SELECT ProductID FROM Products WHERE ProductName = ?)
                        AND OrderStatus = 'Bekliyor'
                    """
                    existing_order = self.db.fetch_one(check_order_query, (customer_id, product_name))

                    if not existing_order:
                        continue  # Bekleyen sipariş yoksa devam et

                    # Stok kontrolü
                    stock_query = """
                        SELECT p.Stock,
                            (SELECT ISNULL(SUM(Quantity), 0)
                                FROM Orders 
                                WHERE ProductID = p.ProductID 
                                AND OrderStatus = 'İşleniyor'
                                AND OrderID != ?) as ReservedStock,
                            c.CustomerType
                        FROM Products p
                        CROSS JOIN Customers c
                        WHERE p.ProductName = ? AND c.CustomerID = ?
                    """
                    result = self.db.fetch_one(stock_query, (existing_order[0], product_name, customer_id))
                    
                    if not result:
                        continue

                    current_stock = result[0]
                    reserved_stock = result[1]
                    customer_type = result[2]
                    available_stock = current_stock - reserved_stock

                    if available_stock >= quantity:
                        # Stok yeterli, siparişi onayla
                        self.db.execute_query("""
                            UPDATE Orders 
                            SET OrderStatus = 'İşleniyor'
                            WHERE OrderID = ?
                        """, (existing_order[0],))

                        # Log kaydı
                        self.db.execute_query("""
                            INSERT INTO Logs (CustomerID, LogType, LogDate, LogDetails)
                            VALUES (?, 'Bilgilendirme', GETDATE(), ?)
                        """, (
                            customer_id,
                            f"Sipariş onaylandı - {product_name} ({quantity} adet)"
                        ))
                    else:
                        # Stok yetersiz, siparişi iptal et
                        self.db.execute_query("""
                            UPDATE Orders 
                            SET OrderStatus = 'İptal'
                            WHERE OrderID = ?
                        """, (existing_order[0],))

                        # İptal logu
                        self.db.execute_query("""
                            INSERT INTO Logs (CustomerID, LogType, LogDate, LogDetails)
                            VALUES (?, 'Bilgilendirme', GETDATE(), ?)
                        """, (
                            customer_id,
                            f"Sipariş iptal edildi - Yetersiz stok ({product_name})"
                        ))

            # Tabloları güncelle
            self.load_orders()
            self.load_logs()

            # İşlenen siparişleri yönet
            self.handle_order_processed(order_data={"updated": True})
            
        except Exception as e:
            print(f"Siparişler onaylanırken hata: {e}")
            QMessageBox.critical(self, "Hata", f"Siparişler onaylanırken hata oluştu: {str(e)}")


    def approve_all_orders(self):
        """Tüm siparişleri onaylar."""
        try:
            # Bekleyen tüm siparişleri öncelik sırasına göre al
            query = """
                SELECT o.OrderID, o.CustomerID, p.ProductName, o.Quantity,
                    p.ProductID, p.Stock,
                    (SELECT ISNULL(SUM(o2.Quantity), 0)
                        FROM Orders o2
                        WHERE o2.ProductID = p.ProductID
                        AND o2.OrderStatus = 'İşleniyor'
                        AND o2.OrderID != o.OrderID) as ReservedStock,
                    c.CustomerType
                FROM Orders o
                JOIN Products p ON o.ProductID = p.ProductID
                JOIN Customers c ON o.CustomerID = c.CustomerID
                WHERE o.OrderStatus = 'Bekliyor'
                ORDER BY 
                    CASE WHEN c.CustomerType = 'Premium' THEN 1 ELSE 2 END,
                    o.OrderDate ASC
            """
            orders = self.db.fetch_all(query)

            if not orders:
                QMessageBox.warning(self, "Uyarı", "Onaylanacak sipariş bulunmamaktadır!")
                return

            # Her sipariş için işlem yap
            with self.db.lock:  # Thread güvenliği için kilit kullan
                for order in orders:
                    order_id = order[0]
                    customer_id = order[1]
                    product_name = order[2]
                    quantity = order[3]
                    product_id = order[4]
                    current_stock = order[5]
                    reserved_stock = order[6]
                    customer_type = order[7]
                    
                    # Kullanılabilir stok miktarını hesapla
                    available_stock = current_stock - reserved_stock

                    # Sipariş durumunu tekrar kontrol et
                    check_query = """
                        SELECT OrderStatus
                        FROM Orders
                        WHERE OrderID = ? AND OrderStatus = 'Bekliyor'
                    """
                    order_status = self.db.fetch_one(check_query, (order_id,))
                    
                    if not order_status:
                        continue  # Sipariş durumu değişmişse atla

                    if available_stock >= quantity:
                        # Stok yeterli, siparişi onayla
                        update_query = """
                            UPDATE Orders 
                            SET OrderStatus = 'İşleniyor'
                            WHERE OrderID = ?
                            AND OrderStatus = 'Bekliyor'
                        """
                        self.db.execute_query(update_query, (order_id,))

                        # Log kaydı
                        log_query = """
                            INSERT INTO Logs (CustomerID, LogType, LogDate, LogDetails)
                            VALUES (?, 'Bilgilendirme', GETDATE(), ?)
                        """
                        self.db.execute_query(log_query, (
                            customer_id,
                            f"Sipariş onaylandı - {product_name} ({quantity} adet)"
                        ))
                    else:
                        # Stok yetersiz, siparişi iptal et
                        cancel_query = """
                            UPDATE Orders 
                            SET OrderStatus = 'İptal'
                            WHERE OrderID = ?
                            AND OrderStatus = 'Bekliyor'
                        """
                        self.db.execute_query(cancel_query, (order_id,))

                        # İptal logu
                        log_query = """
                            INSERT INTO Logs (CustomerID, LogType, LogDate, LogDetails)
                            VALUES (?, 'Bilgilendirme', GETDATE(), ?)
                        """
                        self.db.execute_query(log_query, (
                            customer_id,
                            f"Sipariş iptal edildi - Yetersiz stok ({product_name})"
                        ))

            # Kullanıcıya bilgi ver
            QMessageBox.information(self, "Başarılı", "Tüm siparişler işlendi!")

            # Tabloları güncelle
            self.load_orders()
            self.load_logs()

            # İşlenen siparişleri yönet
            self.handle_order_processed(order_data={"updated": True})
            
        except Exception as e:
            print(f"Siparişler onaylanırken hata: {e}")
            QMessageBox.critical(self, "Hata", f"Siparişler onaylanırken hata oluştu: {str(e)}")

    def load_orders(self):
        """Bekleyen siparişleri yükle"""
        try:
            query = """
                WITH UniqueOrders AS (
                    SELECT DISTINCT o.OrderID, o.CustomerID, p.ProductName, o.Quantity, 
                        o.OrderDate, o.OrderStatus, c.CustomerType
                    FROM Orders o
                    JOIN Products p ON o.ProductID = p.ProductID
                    JOIN Customers c ON o.CustomerID = c.CustomerID
                    WHERE o.OrderStatus = 'Bekliyor'
                )
                SELECT * FROM UniqueOrders
                ORDER BY 
                    CASE WHEN CustomerType = 'Premium' THEN 1 ELSE 2 END,
                    OrderDate ASC
            """
            orders = self.db.fetch_all(query)
            
            # Tabloyu temizle
            self.order_table.setRowCount(0)
            
            # Yeni siparişleri ekle
            for row, order in enumerate(orders):
                self.order_table.insertRow(row)
                
                # Checkbox ekle
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox.setCheckState(Qt.Unchecked)
                self.order_table.setItem(row, 0, checkbox)
                
                # Sipariş bilgilerini ekle
                self.order_table.setItem(row, 1, QTableWidgetItem(str(order[1])))  # CustomerID
                self.order_table.setItem(row, 2, QTableWidgetItem(order[2]))       # ProductName
                self.order_table.setItem(row, 3, QTableWidgetItem(str(order[3])))  # Quantity
                self.order_table.setItem(row, 4, QTableWidgetItem(order[5]))       # Status
                
                # Öncelik skorunu hesapla
                is_premium = order[6] == 'Premium'
                order_date = order[4]
                priority_score = self.calculate_priority({
                    "customer_id": order[1],
                    "is_premium": is_premium,
                    "timestamp": order_date.timestamp() if order_date else time.time()
                })
                self.order_table.setItem(row, 5, QTableWidgetItem(f"{priority_score:.2f}"))

                # Premium müşterileri renklendir
                if is_premium:
                    for col in range(6):
                        item = self.order_table.item(row, col)
                        if item:
                            item.setBackground(QColor("#FFE0E0"))

        except Exception as e:
            print(f"Siparişler yüklenirken hata: {e}")
            QMessageBox.critical(self, "Hata", f"Siparişler yüklenirken hata oluştu: {str(e)}")




    def show_test_tabs(self):
        """Test modunda sekmeleri gösterir"""
        # Mevcut tüm sekmeleri kaldır (ana sayfa hariç)
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)
        
        # 5 müşteri sekmesi ekle
        self.customer_tabs = []
        for i in range(1, 6):
            customer_tab = CustomerTab(customer_id=i, main_window=self, db=self.db)
            self.customer_tabs.append(customer_tab)
            self.tabs.addTab(customer_tab, f"Müşteri {i}")
        
        # Admin sekmesini ekle
        self.admin_tab = AdminTab(self.db)
        self.tabs.addTab(self.admin_tab, "Admin Panel")
    
    def load_logs(self):
        try:
            # Logları veritabanından çekerken müşteri tipini de alıyoruz
            query = """
            SELECT l.LogID, l.CustomerID, l.OrderID, l.LogDate, l.LogType, l.LogDetails,
                c.CustomerType
            FROM Logs l
            JOIN Customers c ON l.CustomerID = c.CustomerID
            ORDER BY l.LogDate DESC
            """
            logs = self.db.fetch_all(query)
            
            # Listeyi temizliyoruz
            self.log_list.clear()
            
            # Her log kaydını uygun formatta ekliyoruz
            for log in logs:
                # Müşteri tipi bilgisini ekliyoruz
                customer_type = "(Premium)" if log[6] == 'Premium' else "(Standard)"
                
                # Log kaydını oluşturuyoruz
                log_entry = (
                    f"LogID: {log[0]} - "
                    f"Müşteri {log[1]} {customer_type} - "  # Müşteri tipi eklendi
                    f"OrderID: {log[2]} - "
                    f"Log Türü: {log[4]} - "
                    f"{log[3]} - "  # LogDate
                    f"{log[5]}"  # LogDetails
                )
                
                # Log öğesini oluştur
                log_item = QListWidgetItem(log_entry)
                
                # Premium müşteriler için arka plan rengini ayarla
                if log[6] == 'Premium':
                    log_item.setBackground(QColor("#FFE0E0"))
                
                self.log_list.addItem(log_item)  # Listeye ekliyoruz
                
        except Exception as e:
            print(f"Loglar yüklenirken hata oluştu: {e}")

    def calculate_priority(self, order):
        """
        Dinamik öncelik skorunu hesaplar:
        ÖncelikSkoru = TemelÖncelikSkoru + (BeklemeSüresi × BeklemeSüresiAğırlığı)
        - Temel Öncelik Skoru: Premium müşteriler için 15, Normal müşteriler için 10
        - Bekleme Süresi Ağırlığı: Her saniye için 0.5 puan
        """
        base_score = 15 if order["is_premium"] else 10
        waiting_time = time.time() - order["timestamp"]
        waiting_weight = 0.5
        priority_score = base_score + (waiting_time * waiting_weight)
        return priority_score

    def update_order_table(self):
        """Bekleyen siparişleri tablodan günceller"""
        try:
            # Sadece bekleyen siparişleri getir
            query = """
                SELECT o.OrderID, o.CustomerID, p.ProductName, o.Quantity, o.OrderStatus,
                    CASE WHEN c.CustomerType = 'Premium' THEN 15 ELSE 10 END as PriorityScore
                FROM Orders o
                JOIN Products p ON o.ProductID = p.ProductID
                JOIN Customers c ON o.CustomerID = c.CustomerID
                WHERE o.OrderStatus = 'Bekliyor'
                ORDER BY PriorityScore DESC, o.OrderDate ASC
            """
            orders = self.db.fetch_all(query)
            
            # Tabloyu temizle
            self.order_table.setRowCount(0)
            
            # Yeni siparişleri ekle
            self.order_table.setRowCount(len(orders))
            for row, order in enumerate(orders):
                # Checkbox ekle
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox.setCheckState(Qt.Unchecked)
                self.order_table.setItem(row, 0, checkbox)
                
                # Diğer bilgileri ekle
                self.order_table.setItem(row, 1, QTableWidgetItem(str(order[1])))  # CustomerID
                self.order_table.setItem(row, 2, QTableWidgetItem(order[2]))       # ProductName
                self.order_table.setItem(row, 3, QTableWidgetItem(str(order[3])))  # Quantity
                self.order_table.setItem(row, 4, QTableWidgetItem(order[4]))       # Status
                self.order_table.setItem(row, 5, QTableWidgetItem(str(order[5])))  # PriorityScore
                
                # Premium müşterileri renklendir
                if order[5] == 15:  # Priority Score 15 ise Premium müşteridir
                    for col in range(6):
                        if self.order_table.item(row, col):
                            self.order_table.item(row, col).setBackground(QColor("#FFE0E0"))
                            
        except Exception as e:
            print(f"Sipariş tablosu güncellenirken hata: {e}")
            QMessageBox.critical(self, "Hata", f"Sipariş tablosu güncellenirken hata oluştu: {str(e)}")

    def complete_order(self, conn, cursor, customer_id, product_id, quantity):
        """Siparişi tamamla ve stokları güncelle"""
        try:
            cursor.execute("""
                UPDATE Orders 
                SET OrderStatus = 'Tamamlandı',
                    CompletionDate = GETDATE()
                WHERE CustomerID = ? 
                AND ProductID = ?
                AND OrderStatus = 'İşleniyor'
            """, (customer_id, product_id))

            # Stok ve rezerve stoku güncelle
            cursor.execute("""
                UPDATE Products 
                SET Stock = Stock - ?,
                    ReservedStock = ReservedStock - ?
                WHERE ProductID = ?
            """, (quantity, quantity, product_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Sipariş tamamlama hatası: {e}")
            return False
    def process_order(self, conn, cursor, order):
        """Thread-safe sipariş işleme"""
        try:
            product = order["orders"][0]["product"]
            quantity = order["orders"][0]["quantity"]
            customer_id = order["customer_id"]

            # Transaction başlat
            conn.autocommit = False

            try:
                # UPDLOCK ve ROWLOCK ile stok kontrolü yap
                cursor.execute("""
                    SELECT p.Stock, p.ProductID
                    FROM Products p WITH (UPDLOCK, ROWLOCK)
                    WHERE p.ProductName = ?
                """, product)
                
                result = cursor.fetchone()
                if not result:
                    raise Exception(f"Ürün bulunamadı: {product}")

                current_stock = result[0]
                product_id = result[1]

                # Bekleyen ve işlenen siparişlerin toplam miktarını kontrol et
                cursor.execute("""
                    SELECT ISNULL(SUM(Quantity), 0)
                    FROM Orders
                    WHERE ProductID = ?
                    AND OrderStatus IN ('Bekliyor', 'İşleniyor')
                    AND OrderID != (
                        SELECT TOP 1 OrderID 
                        FROM Orders 
                        WHERE CustomerID = ? 
                        AND ProductID = ? 
                        AND OrderStatus = 'Bekliyor'
                    )
                """, (product_id, customer_id, product_id))
                
                pending_quantity = cursor.fetchone()[0]
                available_stock = current_stock - pending_quantity

                if available_stock >= quantity:
                    # Stok yeterli, siparişi işle
                    cursor.execute("""
                        UPDATE Orders 
                        SET OrderStatus = 'İşleniyor',
                            ProcessStartDate = GETDATE()
                        WHERE CustomerID = ? 
                        AND ProductID = ?
                        AND OrderStatus = 'Bekliyor'
                    """, (customer_id, product_id))

                    # Stok rezervasyonu yap
                    cursor.execute("""
                        UPDATE Products 
                        SET ReservedStock = ReservedStock + ? 
                        WHERE ProductID = ?
                    """, (quantity, product_id))

                    # Log kaydı
                    log_data = {
                        "customer_id": customer_id,
                        "log_type": "Bilgilendirme",
                        "result": f"Sipariş işleme alındı - {product} ({quantity} adet)"
                    }
                    self.log_signal.emit(log_data)

                    conn.commit()
                    return True
                else:
                    # Stok yetersiz
                    cursor.execute("""
                        UPDATE Orders 
                        SET OrderStatus = 'İptal',
                            CompletionDate = GETDATE()
                        WHERE CustomerID = ? 
                        AND ProductID = ?
                        AND OrderStatus = 'Bekliyor'
                    """, (customer_id, product_id))

                    # Log kaydı
                    log_data = {
                        "customer_id": customer_id,
                        "log_type": "Hata",
                        "result": f"Sipariş iptal edildi - Yetersiz stok ({product}). Mevcut: {available_stock}, İstenen: {quantity}"
                    }
                    self.log_signal.emit(log_data)

                    conn.commit()
                    return False

            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.autocommit = True

        except Exception as e:
            error_message = f"İşlem Hatası: {str(e)}"
            print(error_message)
            self.create_error_log(order, error_message)
            return False

