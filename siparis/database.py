import pyodbc
from PyQt5.QtWidgets import QMessageBox
import threading

class Database:
    def __init__(self):
        try:
            self.db_config = (
                "DRIVER={SQL Server};"
                "SERVER=DESKTOP-CRF2JLE\SQLEXPRESS;"  # Sunucu adını kontrol edin
                "DATABASE=siparisDB;"  # Veritabanı adını kontrol edin
                "Trusted_Connection=yes;"  # Windows kimlik doğrulamasını kullanıyorsanız
            )
            # Create the connection first
            self.conn = pyodbc.connect(self.db_config)
            # Then create the cursor
            self.cursor = self.conn.cursor()
            self.lock = threading.Lock()  # Thread güvenliği için kilit
            print("Veritabanı bağlantısı başarılı!")  # Bağlantının başarılı olduğunu göstermek için
        except pyodbc.InterfaceError as e:
            print(f"Veritabanı arayüz hatası: {e}")
            raise
        except pyodbc.DatabaseError as e:
            print(f"Veritabanı hatası: {e}")
            raise
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            raise
      # Stok takibi için yeni metodlar

    def initialize_random_budgets(self):
        """Tüm müşterilere random bütçe atar (500-3000 TL arası)"""
        try:
            query = """
                UPDATE Customers
                SET Budget = ABS(CHECKSUM(NEWID()) % 2501 + 500)
            """
            self.execute_query(query)
            return True
        except Exception as e:
            print(f"Bütçe atama hatası: {e}")
            return False

    def get_customer_budget(self, customer_id):
        """Müşterinin mevcut bütçesini getirir"""
        try:
            query = "SELECT Budget FROM Customers WHERE CustomerID = ?"
            result = self.fetch_one(query, (customer_id,))
            return result[0] if result else 0
        except Exception as e:
            print(f"Bütçe sorgulama hatası: {e}")
            return 0

    def update_customer_budget(self, customer_id, amount):
        """Müşteri bütçesini günceller"""
        try:
            query = """
                UPDATE Customers 
                SET Budget = Budget - ? 
                WHERE CustomerID = ?
            """
            self.execute_query(query, (amount, customer_id))
            return True
        except Exception as e:
            print(f"Bütçe güncelleme hatası: {e}")
            return False
    def get_product_price(self, product_name):
        """Ürün fiyatını getirir"""
        try:
            query = "SELECT Price FROM Products WHERE ProductName = ?"
            result = self.fetch_one(query, (product_name,))
            if result:
                return result[0]
            return 0  # Ürün bulunamazsa 0 döndür
        except Exception as e:
            print(f"Ürün fiyatı alınırken hata: {e}")
            return 0
        
    def get_stock_levels(self):
        """Tüm ürünlerin stok seviyelerini getirir"""
        try:
            query = """
                SELECT 
                    ProductName,
                    Stock,
                    Price,
                    CASE 
                        WHEN Stock < 10 THEN 'Kritik'
                        WHEN Stock < 20 THEN 'Uyarı'
                        ELSE 'Normal'
                    END as StokDurumu
                FROM Products
            """
            result = self.fetch_all(query)
            return [{
                'urun_adi': row[0],
                'stok': row[1],
                'fiyat': row[2],
                'durum': row[3]
            } for row in result]
        except Exception as e:
            print(f"Stok seviyeleri alınırken hata: {e}")
            return []

    def update_stock(self, product_name, new_stock):
        """Ürün stoğunu günceller"""
        try:
            query = """
                UPDATE Products 
                SET Stock = ?,
                    LastUpdateDate = GETDATE()
                WHERE ProductName = ?
            """
            self.execute_query(query, (new_stock, product_name))
            return True
        except Exception as e:
            print(f"Stok güncellenirken hata: {e}")
            return False

    def get_critical_stock_products(self, threshold=10):
        """Kritik stok seviyesindeki ürünleri getirir"""
        try:
            query = """
                SELECT ProductName, Stock, Price
                FROM Products
                WHERE Stock <= ?
                ORDER BY Stock ASC
            """
            result = self.fetch_all(query, (threshold,))
            return [{
                'urun_adi': row[0],
                'stok': row[1],
                'fiyat': row[2]
            } for row in result]
        except Exception as e:
            print(f"Kritik stok ürünleri alınırken hata: {e}")
            return []

    def check_stock_availability(self, product_name, quantity):
        """Ürün stoğunun yeterli olup olmadığını kontrol eder"""
        try:
            query = "SELECT Stock FROM Products WHERE ProductName = ?"
            result = self.fetch_one(query, (product_name,))
            if result and result[0] >= quantity:
                return True
            return False
        except Exception as e:
            print(f"Stok kontrolü yapılırken hata: {e}")
            return False

    def log_stock_update(self, product_name, old_stock, new_stock, update_type):
        """Stok güncellemelerini loglar"""
        try:
            query = """
                INSERT INTO Logs (ProductID, LogType, LogDate, LogDetails)
                VALUES (
                    (SELECT ProductID FROM Products WHERE ProductName = ?),
                    'Stok Güncelleme',
                    GETDATE(),
                    ?
                )
            """
            log_details = f"{update_type}: {product_name} - Eski Stok: {old_stock}, Yeni Stok: {new_stock}"
            self.execute_query(query, (product_name, log_details))
            return True
        except Exception as e:
            print(f"Stok güncelleme logu oluşturulurken hata: {e}")
            return False

    def get_stock_history(self, product_name):
        """Ürünün stok geçmişini getirir"""
        try:
            query = """
                SELECT LogDate, LogDetails
                FROM Logs
                WHERE ProductID = (SELECT ProductID FROM Products WHERE ProductName = ?)
                    AND LogType = 'Stok Güncelleme'
                ORDER BY LogDate DESC
            """
            result = self.fetch_all(query, (product_name,))
            return [{
                'tarih': row[0],
                'detay': row[1]
            } for row in result]
        except Exception as e:
            print(f"Stok geçmişi alınırken hata: {e}")
            return []

    def update_stock_with_log(self, product_name, new_stock, update_type="Manuel Güncelleme"):
        """Stok güncelleme ve loglama işlemini birlikte yapar"""
        try:
            # Mevcut stok miktarını al
            query = "SELECT Stock FROM Products WHERE ProductName = ?"
            current_stock = self.fetch_one(query, (product_name,))
            
            if current_stock is None:
                raise ValueError(f"Ürün bulunamadı: {product_name}")

            old_stock = current_stock[0]

            # Stok güncelleme
            if self.update_stock(product_name, new_stock):
                # Log oluştur
                self.log_stock_update(product_name, old_stock, new_stock, update_type)
                return True
            return False
        except Exception as e:
            print(f"Stok güncelleme ve loglama işlemi sırasında hata: {e}")
            return False

    def get_low_stock_alerts(self):
        """Düşük stok uyarılarını getirir"""
        try:
            query = """
                SELECT 
                    ProductName,
                    Stock,
                    CASE 
                        WHEN Stock = 0 THEN 'Stok Tükendi'
                        WHEN Stock < 10 THEN 'Kritik Stok'
                        WHEN Stock < 20 THEN 'Düşük Stok'
                    END as AlertType
                FROM Products
                WHERE Stock < 20
                ORDER BY Stock ASC
            """
            result = self.fetch_all(query)
            return [{
                'urun_adi': row[0],
                'stok': row[1],
                'uyari_tipi': row[2]
            } for row in result]
        except Exception as e:
            print(f"Stok uyarıları alınırken hata: {e}")
            return []
        
    def execute_query(self, query, params=None):
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            try:
                # SELECT veya OUTPUT sonuçlarını kontrol et
                results = cursor.fetchall()
                self.conn.commit()
                return results
            except:
                # SELECT veya OUTPUT yoksa
                self.conn.commit()
                return None
                
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def get_all_products(self):
        try:
            query = "SELECT ProductName, Stock, Price FROM Products"
            result = self.fetch_all(query)
            return [{"ProductName": row[0], "Stock": row[1], "Price": row[2]} for row in result]
        except Exception as e:
            print(f"Ürünleri getirirken hata oluştu: {e}")
            return []

    def reduce_stock(self, product_name, quantity):
        """Stok azaltma işlemini thread-safe hale getirir."""
        with self.lock:  # Kilit kullanımı
            try:
                # Stok kontrolü
                self.cursor.execute("SELECT Stock FROM Products WHERE ProductName = ?", (product_name,))
                current_stock = self.cursor.fetchone()
                if current_stock and current_stock[0] >= quantity:
                    # Stoku güncelle
                    self.cursor.execute("UPDATE Products SET Stock = Stock - ? WHERE ProductName = ?", (quantity, product_name))
                    self.conn.commit()
                    return True
                return False
            except Exception as e:
                self.conn.rollback()
                raise e
            
    def fetch_all(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    def check_customer_credentials(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        return user is not None

    def get_customer_data(self, username):
        query = "SELECT CustomerID, Username, CustomerName, CustomerType FROM Customers WHERE Username = ?"
        result = self.fetch_all(query, (username,))
        if result:
            return {
                "CustomerID": result[0][0],
                "Username": result[0][1],
                "CustomerName": result[0][2],
                "CustomerType": result[0][3]
            }
        return None

    def close(self):
        self.cursor.close()
        self.conn.close()

    def add_customer(self, username, password, name, customer_type, budget):
        query = """
        INSERT INTO Customers (Username, Password, CustomerName, CustomerType, Budget)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            # Veritabanına ekleme işlemi
            self.execute_query(query, (username, password, name, customer_type, budget))
            return True
        except Exception as e:
            print(f"Hata: {e}")  # Hata ayıklama için
            return False
        
    def add_product(self, product_name, stock, price):
        try:
            query = """
            INSERT INTO Products (ProductName, Stock, Price)
            VALUES (?, ?, ?)
            """
            self.execute_query(query, (product_name, stock, price))
        except Exception as e:
            print(f"Ürün eklerken hata oluştu: {e}")
            raise
    
    def check_admin_credentials(self, username, password):
        try:
            query = "SELECT * FROM Admins WHERE Username = ? AND Password = ?"
            result = self.fetch_all(query, (username, password))
            return len(result) > 0  # Eğer sonuç dönerse, giriş bilgileri doğru
        except Exception as e:
            print(f"Admin giriş kontrolü sırasında hata: {e}")
            return False
    
    
    def update_product_stock(self, product_name, new_stock):
        try:
            query = """
            UPDATE Products 
            SET Stock = ? 
            WHERE ProductName = ?
            """
            self.execute_query(query, (new_stock, product_name))
        except Exception as e:
            print(f"Stok güncellenirken hata oluştu: {e}")
            raise
    def delete_product(self, product_name):
        try:
            # Ürünle ilişkili logları güncelleme (product_id'yi NULL yapma)
            query = """
            UPDATE Logs 
            SET ProductID = NULL 
            WHERE ProductID = (SELECT ProductID FROM Products WHERE ProductName = ?)
            """
            self.execute_query(query, (product_name,))

            # Ürünü silme işlemi
            query = """
            DELETE FROM Products 
            WHERE ProductName = ?
            """
            self.execute_query(query, (product_name,))

            QMessageBox.information(None, "Başarılı", "Ürün başarıyla silindi!")

        except Exception as e:
            # Hata mesajını ekrana bastırmak için, hata daha ayrıntılı olarak yazdırılabilir
            print(f"Ürün silinirken hata oluştu: {e}")
            QMessageBox.warning(None, "Hata", f"Ürün silinirken hata oluştu: {e}")
        QMessageBox.warning(self, "Hata", f"Ürün silinirken hata oluştu: {e}")


    def get_all_logs(self):
        query = "SELECT LogID, CustomerID, LogType, LogDetails FROM Logs"
        result = self.fetch_all(query)
        return [{"LogID": row[0], "CustomerID": row[1], "LogType": row[2], "LogDetails": row[3]} for row in result]

    def insert_order(self, customer_id, orders):
        """Siparişi veritabanına ekler."""
        try:
            for order in orders:
                product_name = order["product"]
                quantity = order["quantity"]
                # Ürün bilgilerini almak için query
                query = """
                    SELECT ProductID FROM Products WHERE ProductName = ?
                """
                result = self.fetch_all(query, (product_name,))
                
                if not result:
                    raise ValueError(f"Ürün bulunamadı: {product_name}")
                
                product_id = result[0][0]
                
                # Siparişi eklemek için query
                insert_query = """
                    INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderDate, OrderStatus)
                    VALUES (?, ?, ?, ?, GETDATE(), 'Bekliyor')
                """
                total_price = self.calculate_total_price(product_id, quantity)  # Bu fonksiyon siparişin toplam fiyatını hesaplar
                self.execute_query(insert_query, (customer_id, product_id, quantity, total_price))
                
        except Exception as e:
            print(f"Sipariş eklenirken hata: {e}")
            raise

    def calculate_total_price(self, product_id, quantity):
        """Ürünün toplam fiyatını hesaplar"""
        try:
            # Ürün fiyatını almak için query
            query = "SELECT Price FROM Products WHERE ProductID = ?"
            result = self.fetch_all(query, (product_id,))
            
            if not result:
                raise ValueError("Ürün fiyatı bulunamadı.")
            
            price = result[0][0]  # Ürün fiyatı
            total_price = price * quantity  # Toplam fiyat
            return total_price
        except Exception as e:
            print(f"Fiyat hesaplama hatası: {e}")
            raise
    def fetch_one(self, query, params=None):
        """Bir satır veri döndürür"""
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchone()
    
    def get_product_names(self):
        """Veritabanından ürün adlarını çeker."""
        try:
            # Ürünleri veritabanından çekme işlemi
            return [product["ProductName"] for product in self.db.fetch_all("SELECT ProductName FROM Products")]
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Ürünler yüklenirken bir hata oluştu: {e}")
            return []
