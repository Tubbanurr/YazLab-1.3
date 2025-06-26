class StyleHelper:
    @staticmethod
    def set_button_style(button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #1E3A8A;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)

    @staticmethod
    def set_input_style(input_field):
        input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 5px;
                padding: 8px;
                background-color: #F3F4F6;
                color: #374151;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #06B6D4;
            }
        """)
