from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt
from helpers.StyleHelper import StyleHelper

import random  # Rastgele sayı üretmek için

class RegisterPage(QWidget):
    def __init__(self, database, home_page):
        super().__init__()
        self.database = database
        self.home_page = home_page
        self.init_ui()
        self.showFullScreen()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)

        title_label = QLabel("Müşteri Kayıt")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 36px; color: #1E3A8A; font-weight: bold; margin-bottom: 40px;")
        layout.addWidget(title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        StyleHelper.set_input_style(self.username_input)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        StyleHelper.set_input_style(self.password_input)
        layout.addWidget(self.password_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ad Soyad")
        StyleHelper.set_input_style(self.name_input)
        layout.addWidget(self.name_input)

        register_button = QPushButton("Kayıt Ol")
        StyleHelper.set_button_style(register_button)
        register_button.clicked.connect(self.register)
        layout.addWidget(register_button)

        layout.addStretch()
        self.setLayout(layout)

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        name = self.name_input.text()
        customer_type = "Standart"
        
        # Bütçe için rastgele bir değer oluştur
        initial_budget = random.randint(500, 3000)  

        if self.database.add_customer(username, password, name, customer_type, initial_budget):
            QMessageBox.information(self, "Başarılı", "Kayıt başarıyla tamamlandı!")
            self.close()
            self.home_page.show()
        else:
            QMessageBox.warning(self, "Hata", "Kayıt sırasında bir hata oluştu!")

