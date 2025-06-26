from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QLinearGradient
from helpers.StyleHelper import StyleHelper
from database import Database
from customer_page import CustomerPage
from admin_login_page import AdminLoginPage
from register_page import RegisterPage

class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.database = self.main_window.db  # Ana pencereden veritabanı bağlantısını al
        self.init_ui()

    def init_ui(self):
        # Pencereyi ekranın merkezine konumlandır ve tam ekran yap
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)

        # Arka plan ve tasarım
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#F3F4F6"))
        gradient.setColorAt(1, QColor("#FFFFFF"))
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(self.backgroundRole(), gradient)
        self.setPalette(palette)

        # İçeriği ortala
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)

        # Logo ve başlık
        logo_label = QLabel("🛒")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 72px; margin-bottom: 20px;")
        center_layout.addWidget(logo_label)

        title_label = QLabel("Sipariş Sistemi")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 36px; color: #1E3A8A; font-weight: bold; margin-bottom: 40px;")
        center_layout.addWidget(title_label)

        # Giriş formu için container
        form_container = QWidget()
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(20)
        
        # Test modu butonu
        test_button = QPushButton("Test Modu")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 20px;
                min-width: 300px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        test_button.clicked.connect(self.activate_test_mode)
        form_layout.addWidget(test_button, 0, Qt.AlignCenter)

        # Kullanıcı adı ve şifre giriş alanları
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        self.username_input.setFixedWidth(300)
        StyleHelper.set_input_style(self.username_input)
        form_layout.addWidget(self.username_input, 0, Qt.AlignCenter)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(300)
        StyleHelper.set_input_style(self.password_input)
        form_layout.addWidget(self.password_input, 0, Qt.AlignCenter)

        # Giriş yap butonu
        login_button = QPushButton("Giriş Yap")
        login_button.setFixedWidth(300)
        StyleHelper.set_button_style(login_button)
        login_button.clicked.connect(self.login)
        form_layout.addWidget(login_button, 0, Qt.AlignCenter)

        # Alt butonlar
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignCenter)

        buttons = [
            ("Admin Girişi", self.open_admin_login),
            ("Kayıt Ol", self.open_register_page)
        ]

        for text, func in buttons:
            button = QPushButton(text)
            StyleHelper.set_button_style(button)
            button.setFixedSize(200, 60)
            button.setFont(QFont("Arial", 14))
            button.clicked.connect(func)
            buttons_layout.addWidget(button)

        form_layout.addLayout(buttons_layout)
        form_container.setLayout(form_layout)
        center_layout.addWidget(form_container)

        center_widget.setLayout(center_layout)
        layout.addWidget(center_widget)
        self.setLayout(layout)

    def activate_test_mode(self):
        """Test modunu aktifleştirir"""
        try:
            if hasattr(self.main_window, 'open_test_window'):
                self.main_window.open_test_window()
            else:
                raise AttributeError("Test modu fonksiyonu bulunamadı")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Test modu başlatılırken bir hata oluştu: {str(e)}")

    # Diğer metodlar aynı kalacak (login, open_customer_page, vb.)
            

    def login(self):
        try:
            username = self.username_input.text()
            password = self.password_input.text()
    
            if not username or not password:
                QMessageBox.warning(self, "Hata", "Kullanıcı adı ve şifre boş bırakılamaz!")
                return
    
            if self.database.check_customer_credentials(username, password):
                self.open_customer_page()
            else:
                QMessageBox.warning(self, "Hata", "Geçersiz kullanıcı adı veya şifre!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş yaparken bir hata oluştu: {e}")
            print(f"Giriş sırasında hata: {e}")

    def open_customer_page(self):
        try:
            customer_data = self.database.get_customer_data(self.username_input.text())
            if customer_data:
                self.customer_page = CustomerPage(customer_data["CustomerID"])
                self.customer_page.show()
                self.hide()
            else:
                QMessageBox.warning(self, "Hata", "Müşteri bilgileri bulunamadı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Müşteri sayfasına geçişte bir hata oluştu: {e}")
            print(f"Müşteri sayfasına geçiş sırasında hata: {e}")

    def open_register_page(self):
        try:
            self.register_page = RegisterPage(self.database, self)
            self.register_page.show()
            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sayfası açılırken bir hata oluştu: {e}")
            print(f"Kayıt sayfası açılırken hata: {e}")

    def open_admin_login(self):
        try:
            self.admin_login_page = AdminLoginPage(self.database)
            self.admin_login_page.show()
            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Admin giriş sayfası açılırken bir hata oluştu: {e}")
            print(f"Admin giriş sayfası açılırken hata: {e}")

    