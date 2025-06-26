from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from admin_dashboard import AdminDashboard

class AdminLoginPage(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Admin Girişi")
        self.setGeometry(100, 100, 800, 600)  # Ana panel boyutlarıyla aynı
        layout = QVBoxLayout()
        layout.setSpacing(20)

        title_label = QLabel("Admin Girişi")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_button = QPushButton("Giriş Yap")
        login_button.clicked.connect(self.check_login)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def check_login(self):
        try:
            username = self.username_input.text()
            password = self.password_input.text()      
            if not username or not password:
                QMessageBox.warning(self, "Hata", "Kullanıcı adı ve şifre boş bırakılamaz!")
                return     
            if self.database.check_admin_credentials(username, password):
                QMessageBox.information(self, "Başarılı", "Giriş başarılı!")
                self.open_admin_dashboard()
            else:
                QMessageBox.warning(self, "Hata", "Geçersiz kullanıcı adı veya şifre!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş işlemi sırasında bir hata oluştu: {e}")
            print(f"Giriş işlemi sırasında hata: {e}")


    def open_admin_dashboard(self):
        try:
            self.admin_dashboard = AdminDashboard(self.database)
            self.admin_dashboard.show()  # Admin panelini göster
            self.hide()  # Giriş penceresini gizle
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Admin paneli yüklenirken bir hata oluştu: {e}")
            print(f"Admin paneli yüklenirken hata: {e}")
