import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor
import pyodbc
from database import Database
from home import HomePage
from admin_thread import AdminThread
from order_thread import OrderThread
from customer_tab import CustomerTab
from admin_tab import AdminTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sipariş Yönetim Sistemi")
        self.setGeometry(100, 100, 1200, 800)

        # Add database configuration
        self.db_config = (
            "DRIVER={SQL Server};"
            "SERVER=DESKTOP-CRF2JLE\SQLEXPRESS;"  # Replace with your SQL Server name
            "DATABASE=siparisDB;"  # Replace with your database name
            "Trusted_Connection=yes;"  # For Windows Authentication
        )

        self.db = Database()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Ana sayfa sekmesi
        self.home_tab = HomePage(self)
        self.tabs.addTab(self.home_tab, "Ana Sayfa")

        # Admin thread
        self.admin_thread = AdminThread(self.db_config)
        self.admin_thread.order_processed_signal.connect(self.on_order_processed)
        self.admin_thread.log_signal.connect(self.on_log_received)
        self.admin_thread.start()
         # Random bütçeleri başlat
        self.db.initialize_random_budgets()
        # Customer threads
        self.customer_threads = {}


    def open_test_window(self):
        try:
            self.test_window = TestWindow(self.db)
            self.test_window.order_received.connect(self.handle_new_order)
            self.test_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Test penceresi açılırken hata oluştu: {str(e)}")

    def handle_new_order(self, order_data):
        try:
            customer_id = order_data["customer_id"]

            # Create a new thread for the customer
            order_thread = OrderThread(
                customer_id=customer_id,
                is_premium=order_data["is_premium"],
                orders=order_data["orders"],
                db_config=self.db_config  # Pass DB config to thread
            )

            # Connect thread signals
            order_thread.order_signal.connect(self.admin_thread.add_order)
            order_thread.log_signal.connect(self.on_log_received)

            # Start the thread
            self.customer_threads[customer_id] = order_thread
            order_thread.start()

        except Exception as e:
            print(f"Sipariş işlenirken hata: {e}")
            QMessageBox.critical(self, "Hata", f"Sipariş işlenirken hata oluştu: {str(e)}")

    def on_order_processed(self, order_data):
        """Called when an order is processed by the admin thread"""
        try:
            customer_id = order_data["customer_id"]
            if customer_id in self.customer_threads:
                # Clean up the corresponding customer thread
                self.customer_threads[customer_id].quit()
                self.customer_threads[customer_id].wait()
                del self.customer_threads[customer_id]

            # Update the test window
            if hasattr(self, 'test_window'):
                self.test_window.update_orders()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sipariş sonucu işlenirken hata oluştu: {str(e)}")

    def on_log_received(self, log_data):
        """Called when a new log is received"""
        try:
            query_check_customer = "SELECT COUNT(*) FROM Customers WHERE CustomerID = ?"
            customer_count = self.db.fetch_one(query_check_customer, (log_data["customer_id"],))

            if customer_count[0] == 0:
                print(f"Geçersiz CustomerID: {log_data['customer_id']}")
                return

            query = """
                INSERT INTO Logs (CustomerID, OrderID, LogType, LogDate, LogDetails)
                VALUES (?, ?, ?, GETDATE(), ?)
            """
            self.db.execute_query(query, (
                log_data["customer_id"],
                log_data.get("order_id", None),
                log_data["log_type"],
                f"{log_data['result']} - {log_data.get('product', '')} {log_data.get('quantity', '')}"
            ))

            if hasattr(self, 'test_window'):
                self.test_window.admin_tab.load_logs()

        except Exception as e:
            print(f"Log kaydı sırasında hata: {e}")

    def closeEvent(self, event):
        try:
            if hasattr(self, 'admin_thread'):
                self.admin_thread.stop()
                self.admin_thread.wait()

            for thread in self.customer_threads.values():
                thread.quit()
                thread.wait()

            self.db.close()
            event.accept()
        except Exception as e:
            print(f"Uygulama kapatılırken hata: {e}")
            event.accept()


class TestWindow(QWidget):
    order_received = pyqtSignal(dict)

    def __init__(self, database):
        super().__init__()
        self.setWindowTitle("Test Modu - Sipariş Yönetim Sistemi")
        self.setGeometry(150, 150, 1200, 800)

        self.db = database
        self.tabs = QTabWidget()
        
        #Ana layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

         # Sekmelerin arka plan temasını ayarla (Açık/Koyu Gri, Lila ve Mavi Tonları)
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                background-color: #F0F0F0;
                border: 1px solid #CCC;
            }
            QTabBar::tab {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #D1C4E9, stop:1 #BBDEFB
                );
                color: #333;
                padding: 8px;
                border-radius: 8px;
                margin: 3px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9575CD, stop:1 #64B5F6
                );
                color: white;
                border: 1px solid #333;
            }
            """
        )

        self.customer_tabs = []
        for i in range(1, 6):
            customer_tab = CustomerTab(customer_id=i, main_window=self, db=self.db)
            self.customer_tabs.append(customer_tab)
            self.tabs.addTab(customer_tab, f"Müşteri {i}")

        self.admin_tab = AdminTab(self.db)
        self.tabs.addTab(self.admin_tab, "Admin Panel")
        # Ana pencere stili (Modern Tonlar)
        self.setStyleSheet(
            "QWidget {"
            "    background-color: #F5F5F5;"
            "    color: #333;"
            "}"
            "QTableWidget {"
            "    background-color: #FFFFFF;"
            "    gridline-color: #E0E0E0;"
            "    color: #444;"
            "    font-size: 14px;"
            "    border-radius: 8px;"
            "}"
            "QTableWidget::item {"
            "    padding: 6px;"
            "    border: none;"
            "}"
            "QScrollBar:vertical {"
            "    border: none;"
            "    background: #E0E0E0;"
            "    width: 12px;"
            "    margin: 2px;"
            "    border-radius: 6px;"
            "}"
            "QScrollBar::handle:vertical {"
            "    background: qlineargradient("
            "        x1:0, y1:0, x2:1, y2:1,"
            "        stop:0 #9575CD, stop:1 #64B5F6"
            "    );"
            "    min-height: 20px;"
            "    border-radius: 6px;"
            "}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
            "    height: 0px;"
            "}"
            "QPushButton {"
            "    background-color: qlineargradient("
            "        x1:0, y1:0, x2:1, y2:1,"
            "        stop:0 #C5CAE9, stop:1 #BBDEFB"
            "    );"
            "    color: #333;"
            "    padding: 10px 15px;"
            "    border-radius: 8px;"
            "    font-size: 14px;"
            "    border: 1px solid #B0BEC5;"
            "}"
            "QPushButton:hover {"
            "    background-color: qlineargradient("
            "        x1:0, y1:0, x2:1, y2:1,"
            "        stop:0 #90CAF9, stop:1 #64B5F6"
            "    );"
            "    color: white;"
            "    font-weight: bold;"
            "}"
            "QGroupBox {"
            "    border: 1px solid #CCC;"
            "    margin-top: 20px;"
            "    background-color: #FAFAFA;"
            "    border-radius: 8px;"
            "}"
            "QGroupBox::title {"
            "    subcontrol-origin: margin;"
            "    subcontrol-position: top left;"
            "    padding: 0 8px;"
            "    color: #5E35B1;"
            "    font-size: 14px;"
            "}"
        )

        
    def update_orders(self):
        """Update orders for all customer tabs"""
        try:
            for customer_tab in self.customer_tabs:
                customer_tab.update_status()

            if hasattr(self, 'admin_tab'):
                self.admin_tab.update_order_table()

        except Exception as e:
            print(f"Sipariş güncellenirken hata: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
