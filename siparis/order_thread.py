# order_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import time
import pyodbc

class OrderThread(QThread):
    order_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(dict)

    def __init__(self, customer_id, is_premium, orders, db_config):
        super().__init__()
        self.customer_id = customer_id
        self.is_premium = is_premium
        self.orders = orders
        self.db_config = db_config
        self.start_time = time.time()

    def run(self):
        try:
            # Her thread kendi bağlantısını oluşturmalı
            conn = pyodbc.connect(self.db_config)
            cursor = conn.cursor()

            order_data = {
                "customer_id": self.customer_id,
                "is_premium": self.is_premium,
                "orders": self.orders,
                "timestamp": self.start_time,
                "priority_score": self.calculate_priority()
            }
            
            # Sipariş sinyali gönder
            self.order_signal.emit(order_data)
            
            # Log kaydı oluştur
            log_data = {
                "customer_id": self.customer_id,
                "log_type": "Bilgilendirme",
                "customer_type": "Premium" if self.is_premium else "Standard",
                "product": self.orders[0]["product"],
                "quantity": self.orders[0]["quantity"],
                "timestamp": time.time(),
                "result": "Sipariş işleme alındı"
            }
            self.log_signal.emit(log_data)
            
            # İşlem tamamlandıktan sonra bağlantıyı kapat
            cursor.close()
            conn.close()
            
        except Exception as e:
            # Hata durumunda log kaydı
            error_log = {
                "customer_id": self.customer_id,
                "log_type": "Hata",
                "customer_type": "Premium" if self.is_premium else "Standard",
                "timestamp": time.time(),
                "result": f"Hata: {str(e)}"
            }
            self.log_signal.emit(error_log)


    def calculate_priority(self):
        base_score = 15 if self.is_premium else 10
        waiting_time = time.time() - self.start_time
        return base_score + (waiting_time * 0.5)