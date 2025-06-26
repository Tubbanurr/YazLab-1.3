# admin_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import time
import pyodbc

class AdminThread(QThread):
    order_processed_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(dict)
    stok_guncelleme_sinyali = pyqtSignal(list)  # Yeni eklenen sinyal
    kritik_stok_sinyali = pyqtSignal(str)  # Yeni eklenen sinyal

    def __init__(self, db_config):
        super().__init__()
        self.db_config = db_config
        self.conn = None  # Bağlantıyı burada başlatın
        self.cursor = None  # Cursor'u saklayın
        self.pending_orders = []
        self.is_running = True
        self.kritik_stok_siniri = 10
        self.son_stok_kontrolu = 0
        self.stok_kontrol_araligi = 2  # 2 saniyede bir kontrol

        try:
            self.conn = pyodbc.connect(self.db_config)
            self.cursor = self.conn.cursor()
            print("AdminThread için veritabanı bağlantısı başarılı!")
        except Exception as e:
            print(f"AdminThread: Veritabanı bağlantı hatası: {e}")

    def run(self):
        while self.is_running:
            try:
                # Her işlem için yeni bağlantı
                with pyodbc.connect(self.db_config) as conn:
                    cursor = conn.cursor()
                    
                    # Sadece admin tarafından onaylanmış (İşleniyor) siparişleri al
                    cursor.execute("""
                        SELECT o.OrderID, o.CustomerID, p.ProductName, o.Quantity, 
                            p.Stock, c.CustomerType, o.OrderDate, p.ProductID,
                            o.TotalPrice
                        FROM Orders o WITH (UPDLOCK, ROWLOCK)
                        JOIN Products p ON o.ProductID = p.ProductID
                        JOIN Customers c ON o.CustomerID = c.CustomerID
                        WHERE o.OrderStatus = 'İşleniyor'  -- Sadece onaylanmış siparişler
                        ORDER BY 
                            CASE WHEN c.CustomerType = 'Premium' THEN 1 ELSE 2 END,
                            o.OrderDate ASC
                    """)
                    
                    orders = cursor.fetchall()
                    
                    for order in orders:
                        try:
                            conn.autocommit = False
                            
                            order_id = order[0]
                            customer_id = order[1]
                            product_name = order[2]
                            quantity = order[3]
                            product_id = order[7]
                            
                            # Stok kontrolü (UPDLOCK ile kilit al)
                            cursor.execute("""
                                SELECT Stock
                                FROM Products WITH (UPDLOCK, ROWLOCK)
                                WHERE ProductID = ?
                            """, product_id)
                            
                            actual_stock = cursor.fetchone()[0]
                            
                            if actual_stock >= quantity:
                                # Stok güncelleme
                                cursor.execute("""
                                    UPDATE Products 
                                    SET Stock = Stock - ? 
                                    WHERE ProductID = ? AND Stock >= ?
                                """, (quantity, product_id, quantity))

                                # Siparişi tamamlandı olarak işaretle
                                cursor.execute("""
                                    UPDATE Orders
                                    SET OrderStatus = 'Tamamlandı',
                                        CompletionDate = GETDATE()
                                    WHERE OrderID = ? AND OrderStatus = 'İşleniyor'
                                """, order_id)
                                
                                # Log ekle
                                cursor.execute("""
                                    INSERT INTO Logs (CustomerID, OrderID, LogType, LogDate, LogDetails)
                                    VALUES (?, ?, 'Bilgilendirme', GETDATE(), ?)
                                """, (
                                    customer_id,
                                    order_id,
                                    f"Sipariş tamamlandı - {product_name} ({quantity} adet)"
                                ))
                                
                                conn.commit()
                                
                                # Sinyal gönder
                                self.order_processed_signal.emit({
                                    "customer_id": customer_id,
                                    "product": product_name,
                                    "quantity": quantity,
                                    "status": "Tamamlandı"
                                })
                            else:
                                # Stok yetersiz - siparişi iptal et
                                cursor.execute("""
                                    UPDATE Orders
                                    SET OrderStatus = 'İptal',
                                        CompletionDate = GETDATE()
                                    WHERE OrderID = ? AND OrderStatus = 'İşleniyor'
                                """, order_id)
                                
                                cursor.execute("""
                                    INSERT INTO Logs (CustomerID, OrderID, LogType, LogDate, LogDetails)
                                    VALUES (?, ?, 'Hata', GETDATE(), ?)
                                """, (
                                    customer_id,
                                    order_id,
                                    f"Sipariş iptal edildi - Yetersiz stok ({product_name})"
                                ))
                                
                                conn.commit()
                                
                        except Exception as e:
                            print(f"Sipariş işleme hatası (ID: {order_id}): {e}")
                            conn.rollback()
                        finally:
                            conn.autocommit = True
                                
                    # Stok kontrolü
                    self.check_stock_levels()
                    time.sleep(1)  # CPU yükünü azalt
                    
            except Exception as e:
                print(f"AdminThread ana döngü hatası: {e}")
                time.sleep(1)

    def check_stock(self, conn, cursor, product_name, quantity):
        """Stok kontrolü yapar ve yeterli stok varsa True döner"""
        try:
            # Stok miktarını kontrol et
            cursor.execute("""
                SELECT Stock 
                FROM Products WITH (UPDLOCK) 
                WHERE ProductName = ?
            """, (product_name,))
            
            result = cursor.fetchone()
            if result and result[0] >= quantity:
                return True
            return False

        except Exception as e:
            print(f"Stok kontrol hatası: {e}")
            return False
    
    def check_stock_levels(self):
        """Stok seviyelerini kontrol eden metod"""
        try:
            # Bağlantıyı başlat
            conn = pyodbc.connect(self.db_config)
            cursor = conn.cursor()

            sorgu = """
                SELECT 
                    ProductName,
                    Stock,
                    Price,
                    CASE 
                        WHEN Stock < 10 THEN 'Kritik'
                        WHEN Stock < 20 THEN 'Uyarı'
                        ELSE 'Normal'
                    END as StokDurumu
                FROM Products WITH (NOLOCK)
            """
            cursor.execute(sorgu)
            stok_verisi = []

            for kayit in cursor.fetchall():
                stok_bilgisi = {
                    'urun_adi': kayit[0],
                    'stok': kayit[1],
                    'fiyat': kayit[2],
                    'durum': kayit[3]
                }
                stok_verisi.append(stok_bilgisi)

                # Kritik stok kontrolü
                if kayit[1] < self.kritik_stok_siniri:
                    self.kritik_stok_sinyali.emit(
                        f"Kritik Stok Uyarısı: {kayit[0]} (Stok: {kayit[1]})"
                    )

            # Stok verilerini gönder
            if stok_verisi:  # Boş değilse gönder
                self.stok_guncelleme_sinyali.emit(stok_verisi)

            # Bağlantıyı kapat
            cursor.close()
            conn.close()

        except pyodbc.InterfaceError as e:
            print(f"Veritabanı arayüz hatası (stok kontrol): {e}")
            self.stok_guncelleme_sinyali.emit([])
        except pyodbc.DatabaseError as e:
            print(f"Veritabanı hatası (stok kontrol): {e}")
            self.stok_guncelleme_sinyali.emit([])
        except Exception as e:
            print(f"Beklenmeyen hata (stok kontrol): {e}")
            self.stok_guncelleme_sinyali.emit([])

    def process_order(self, conn, cursor, order):
        """Thread-safe sipariş işleme"""
        try:
            product = order["orders"][0]["product"]
            quantity = order["orders"][0]["quantity"]
            customer_id = order["customer_id"]

            # Transaction başlat
            conn.autocommit = False

            try:
                # Stok kontrolü için kilit al
                cursor.execute("""
                    SELECT Stock 
                    FROM Products WITH (UPDLOCK, ROWLOCK)
                    WHERE ProductName = ?
                """, (product,))
                
                current_stock = cursor.fetchone()
                if current_stock and current_stock[0] >= quantity:
                    # Stoku güncelle
                    cursor.execute("""
                        UPDATE Products 
                        SET Stock = Stock - ? 
                        WHERE ProductName = ? AND Stock >= ?
                    """, (quantity, product, quantity))

                    # Siparişi güncelle
                    cursor.execute("""
                        UPDATE Orders 
                        SET OrderStatus = 'Tamamlandı', 
                            CompletionDate = GETDATE()
                        WHERE CustomerID = ? 
                        AND ProductID = (SELECT ProductID FROM Products WHERE ProductName = ?)
                        AND OrderStatus = 'Bekliyor'
                    """, (customer_id, product))

                    # Log kaydı oluştur
                    log_data = {
                        "customer_id": customer_id,
                        "log_type": "Bilgilendirme",
                        "result": f"Sipariş tamamlandı - {product} ({quantity} adet)"
                    }
                    self.log_signal.emit(log_data)

                    conn.commit()
                    return True
                else:
                    # Stok yetersiz durumu
                    conn.rollback()
                    log_data = {
                        "customer_id": customer_id,
                        "log_type": "Hata",
                        "result": f"Stok yetersiz - {product} (İstenen: {quantity}, Mevcut: {current_stock[0] if current_stock else 0})"
                    }
                    self.log_signal.emit(log_data)
                    return False

            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.autocommit = True

        except Exception as e:
            self.create_error_log(order, f"İşlem Hatası: {str(e)}")
            return False



        

    def calculate_priority_score(self, order):
        """
        Dinamik öncelik skorunu hesaplar:
        ÖncelikSkoru = TemelÖncelikSkoru + (BeklemeSüresi × BeklemeSüresiAğırlığı)
        - Temel Öncelik Skoru: Premium müşteriler için 15, Normal müşteriler için 10
        - Bekleme Süresi Ağırlığı: Her saniye için 0.5 puan
        """
        base_score = 15 if order["is_premium"] else 10
        waiting_time = time.time() - order["timestamp"]  # Saniye cinsinden bekleme süresi
        waiting_weight = 0.5  # Her saniye için 0.5 puan
        
        priority_score = base_score + (waiting_time * waiting_weight)
        return priority_score

    

    def add_order(self, order):
        self.pending_orders.append(order)

    
    def create_success_log(self, order):
        log_data = {
            "customer_id": order["customer_id"],
            "log_type": "Bilgilendirme",
            "customer_type": "Premium" if order["is_premium"] else "Standard",
            "product": order["orders"][0]["product"],
            "quantity": order["orders"][0]["quantity"],
            "timestamp": time.time(),
            "result": "Satın alma başarılı"
        }
        self.log_signal.emit(log_data)

    def create_error_log(self, order, error_message):
        log_data = {
            "customer_id": order["customer_id"],
            "log_type": "Hata",
            "customer_type": "Premium" if order["is_premium"] else "Standard",
            "timestamp": time.time(),
            "result": error_message
        }
        self.log_signal.emit(log_data)

    def stop(self):
        self.is_running = False