from math import log
from shutil import move
import sys
import sqlite3
import db
import utils

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox,
    QVBoxLayout, QWidget, QStackedWidget, QFileDialog, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QSpinBox, QComboBox, QTextEdit, QFormLayout, QGridLayout, QLayout, QFrame, QListWidget, QListWidgetItem,
    QListView, QAbstractItemView, QHeaderView, QButtonGroup, QScrollArea, QTabWidget, QDialog
)


from PyQt6.QtGui import QPixmap, QDesktopServices, QPixmap, QPainter
from PyQt6.QtCore import QUrl, Qt

import pandas as pd
import csv
import openpyxl

def init_base_stylesheet():
    return """
        QWidget {
            background-color: white;
            color: black;
            font-size: 14px;
            font-family: Calibri, sans-serif;
        }
        QPushButton {
            background-color: orange;
            border: none;
            color: black;
            outline: none;
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #FFB02E;
        }
        QPushButton:pressed {
            background-color: #FFB02E;
        }
        QPushButton:focus {
            background-color: #FFB02E;
        }
        QPushButton:checked {
            background-color: #FFB02E;
        }
        QPushButton#destructive_button {
            background-color: transparent;
            color: red;
        }
        QPushButton#destructive_button:hover {
            background-color: white;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #888;
            border-radius: 5px;
        }
        QComboBox {
            padding: 5px;
            border: 1px solid #888;
            border-radius: 5px;
        }
        QTableWidget {
            background-color: white;
            color: white;
            font-size: 14px;
        }
        QAbstractItemView {
            background: white;
            outline: none;
            border-radius: 5px;
            color: black;
        }
        QAbstractItemView::item {
            padding: 5px;
            outline: none;
            color: black;
            background-color: transparent;
        }
        QAbstractItemView::item:selected {
            background-color: #FFB02E;
            color: black;
        }
        QScrollBar {
            border: none;
            outline: none;
        }
        QScrollBar:horizontal {
            background-color: gray;
            height: 10px;
            border-radius: 5px;
        }
        QScrollBar:vertical {
            background-color: gray;
            width: 10px;
            border-radius: 5px;
        }
        QSpinBox {
            padding: 5px;
            border: 1px solid #888;
            border-radius: 5px;
        }
        QPushButton#delete_button {
            background-color: red;
            border: none;
            color: white;
            outline: none;
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton#delete_button:hover {
            background-color: #FF0000;
        }
        QPushButton#delete_button:pressed {
            background-color: #FF0000;
        }
        QPushButton#delete_button:focus {
            background-color: #FF0000;
        }
        QPushButton#delete_button:checked {
            background-color: #FF0000;
        }
    """

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учета данных о производстве одежды")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(init_base_stylesheet())
        utils.center_window(self)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.create_data_tab(), "Учет данных")
        self.tabs.addTab(self.create_category_tab(), "Категории")

        self.category_names = []

        self.load_categories()
        self.load_data_to_table()


    def create_data_tab(self):
        """Вкладка для учета данных"""
        tab = QWidget()
        layout = QVBoxLayout()

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Артикул", "Наименование", "Категория", "Размер", "Дата", "Количество", "Цена", "Закуп. цена"
        ])
        self.header = self.table.horizontalHeader()
        for i in range(8):
            self.header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # Подключение обработчика двойного клика
        self.table.cellDoubleClicked.connect(self.open_edit_dialog)

        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Обновить список")
        refresh_button.clicked.connect(self.load_data_to_table)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("Экспорт в .xlsx/.csv")
        export_button.clicked.connect(self.export_data)
        button_layout.addWidget(export_button)

        import_button = QPushButton("Импорт из .xlsx/.csv")
        import_button.clicked.connect(self.import_data)
        button_layout.addWidget(import_button)

        layout.addLayout(button_layout)

        form_layout = QFormLayout()
        self.inputs = {
            "Артикул": QLineEdit(),
            "Наименование": QLineEdit(),
            "Категория": QComboBox(),
            "Размер": QLineEdit(),
            "Дата": QLineEdit(),
            "Количество": QLineEdit(),
            "Цена": QLineEdit(),
            "Закуп. цена": QLineEdit()
        }

        for label, input_field in self.inputs.items():
            form_layout.addRow(QLabel(label.capitalize()), input_field)

        add_button = QPushButton("Добавить запись")
        add_button.clicked.connect(self.add_record)

        form_container = QVBoxLayout()
        form_container.addLayout(form_layout)
        form_container.addWidget(add_button)

        layout.addLayout(form_container)
        tab.setLayout(layout)
        return tab

    def open_edit_dialog(self, row):
        """Открывает диалоговое окно для редактирования записи"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование записи")
        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()

        data = {}
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            data[header] = self.table.item(row, col).text() if self.table.item(row, col) else ""

        self.edit_inputs = {}
        for field, value in data.items():
            if field == "Категория":
                input_field = QComboBox()
                input_field.addItems(self.category_names)
                input_field.setCurrentText(value)
                self.edit_inputs[field] = input_field
                form_layout.addRow(QLabel(field), input_field)
                continue
            input_field = QLineEdit(value)
            self.edit_inputs[field] = input_field
            form_layout.addRow(QLabel(field), input_field)

        layout.addLayout(form_layout)

        # Кнопки сохранения и удаления
        button_layout = QHBoxLayout()
        
        delete_button = QPushButton("Удалить")
        delete_button.setObjectName("delete_button")
        delete_button.clicked.connect(lambda: self.delete_record(dialog, row))
        button_layout.addWidget(delete_button)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_changes(dialog, row))
        button_layout.addWidget(save_button)

      

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def save_changes(self, dialog, row):
        """Сохранение изменений в базе данных и обновление таблицы"""
        COLUMN_MAPPING = {
            "Артикул": "articul",
            "Наименование": "name",
            "Категория": "category",
            "Размер": "size",
            "Дата": "date_added",
            "Количество": "quantity",
            "Цена": "price",
            "Закуп. цена": "cost"
        }
        try:
            updated_data = {field: input_field.text() if field != "Категория" else input_field.currentText() for field, input_field in self.edit_inputs.items()}
            articul = self.table.item(row, 0).text()

            # Обновление базы данных
            for column_name, new_value in updated_data.items():
                db_column = COLUMN_MAPPING[column_name]  # Преобразование имени
                db.execute_query(
                    f"UPDATE clothing_items SET {db_column} = ? WHERE articul = ?",
                    (new_value, articul)
                )

            for col, (field, value) in enumerate(updated_data.items()):
                self.table.setItem(row, col, QTableWidgetItem(value))

            QMessageBox.information(self, "Успех", "Изменения успешно сохранены.")
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {e}")

    def delete_record(self, dialog, row):
        """Удаление записи из базы данных и таблицы"""
        try:
            articul = self.table.item(row, 0).text()  # Уникальный идентификатор
            confirm = QMessageBox.question(
                self,
                "Подтверждение удаления",
                "Вы уверены, что хотите удалить эту запись?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                db.execute_query("DELETE FROM clothing_items WHERE articul=?", (articul,))

                self.table.removeRow(row)

                QMessageBox.information(self, "Успех", "Запись успешно удалена.")
                dialog.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {e}")

    def export_data(self):
        """Экспорт данных из таблицы в файл."""
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if path:
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            df = pd.DataFrame(data, columns=["Артикул", "Наименование", "Категория", "Размер", "Дата", "Количество", "Цена", "Закуп. цена"])

            try:
                if path.endswith('.xlsx'):
                    df.to_excel(path, index=False)
                elif path.endswith('.csv'):
                    df.to_csv(path, index=False)
                QMessageBox.information(self, "Успех", "Данные успешно экспортированы.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать данные: {e}")

    def import_data(self):
        """Импорт данных из CSV или Excel"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "CSV (*.csv);;Excel (*.xlsx)")
        if not file_path:
            return

        imported_data = []
        try:
            if file_path.endswith(".csv"):
                with open(file_path, mode="r", encoding="utf-8") as file:
                    reader = csv.reader(file)
                    next(reader)  # Пропустить заголовок
                    imported_data = list(reader)
            elif file_path.endswith(".xlsx"):
                workbook = openpyxl.load_workbook(file_path)
                sheet = workbook.active
                for row in sheet.iter_rows(min_row=2, values_only=True):  # Пропустить заголовок
                    imported_data.append(row)

            for record in imported_data:
                try:
                    db.execute_query(
                        "INSERT INTO clothing_items (articul, name, category, size, date_added, quantity, price, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", record
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать запись c артикулом: {record[0]}")

            QMessageBox.information(self, "Успех", "Данные успешно импортированы!")
            self.load_data_to_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать данные: {e}")

    def create_category_tab(self):
        """Вкладка для управления категориями"""
        tab = QWidget()
        layout = QVBoxLayout()

        self.category_table = QTableWidget(0, 1)
        self.category_table.setHorizontalHeaderLabels(["Название"])
        self.header = self.category_table.horizontalHeader()
        self.header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.category_table)

        refresh_button = QPushButton("Обновить список категорий")
        refresh_button.clicked.connect(self.load_categories)
        layout.addWidget(refresh_button)

        form_layout = QFormLayout()
        self.category_input = QLineEdit()
        form_layout.addRow(QLabel("Название категории"), self.category_input)

        add_button = QPushButton("Добавить категорию")
        add_button.clicked.connect(self.add_category)

        form_container = QVBoxLayout()
        form_container.addLayout(form_layout)
        form_container.addWidget(add_button)

        layout.addLayout(form_container)
        tab.setLayout(layout)
        return tab

    def load_data_to_table(self):
        """Загружает данные из базы в таблицу."""
        query = "SELECT articul, name, category, size, date_added, quantity, price, cost FROM clothing_items"
        records = db.fetch_all(query)
        self.table.setRowCount(len(records))

        for row_index, row_data in enumerate(records):
            for column_index, value in enumerate(row_data):
                self.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def add_record(self):
        """Добавляет новую запись в базу данных."""
        values = [
            self.inputs["Артикул"].text(),
            self.inputs["Наименование"].text(),
            self.inputs["Категория"].currentText(),
            self.inputs["Размер"].text(),
            self.inputs["Дата"].text(),
            self.inputs["Количество"].text(),
            self.inputs["Цена"].text(),
            self.inputs["Закуп. цена"].text(),
        ]

        # Валидация
        if not all(values):
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены!")
            return

        try:
            values[5] = int(values[5]) 
            values[6] = float(values[6])  
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество и цена должны быть числовыми значениями!")
            return

        query = """
        INSERT INTO clothing_items (articul, name, category, size, date_added, quantity, price, cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            db.execute_query(query, values)
            self.load_data_to_table()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")

    def clear_inputs(self):
        """Очищает поля ввода после добавления записи."""
        for input_field in self.inputs.values():
            if isinstance(input_field, QComboBox):
                input_field.setCurrentIndex(0)
            else:
                input_field.clear()

    def load_categories(self):
        """Загружает категории из базы данных."""
        query = "SELECT name FROM categories"
        categories = db.fetch_all(query)
        self.category_names = [cat[0] for cat in categories]
        self.category_table.setRowCount(len(categories))
        for row_index, cat in enumerate(categories):
            self.category_table.setItem(row_index, 0, QTableWidgetItem(cat[0]))

        # Обновление выпадающего списка категорий
        self.inputs["Категория"].clear()
        self.inputs["Категория"].addItems([cat_name[0] for cat_name in categories])

    def add_category(self):
        """Добавляет новую категорию в базу данных."""
        category_name = self.category_input.text().strip()

        if not category_name:
            QMessageBox.warning(self, "Ошибка", "Название категории не может быть пустым!")
            return

        query = "INSERT INTO categories (name) VALUES (?)"
        try:
            db.execute_query(query, (category_name,))
            self.load_categories()
            self.category_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить категорию: {e}")

    def logout(self):
        self.close()
        self.auth_window = AuthWindow()
        self.auth_window.show()

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = db.create_connection()
        self.setFixedSize(400, 200)
        utils.center_window(self)
        self.setWindowTitle("Авторизация")

        self.setStyleSheet(
            init_base_stylesheet()
            + """
            #submit_button {
                background-color: orange;
            }

            #submit_button:hover {  
                background-color: #FF8C00;
            }

            #submit_button:pressed {
                background-color: #FF8C00;
            }
            #switch_button {
                background-color: white;
                color: black;
            }
            """
        )

        self.setContentsMargins(5, 5, 5, 5)

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(LoginFormWidget(self.conn, self))
        self.stack.addWidget(RegisterFormWidget(self.conn, self))
        
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def switch_window(self, number):
        self.stack.setCurrentIndex(number)
        if (self.stack.currentIndex() == 0):
            self.setWindowTitle("Авторизация")
        else:
            self.setWindowTitle("Регистрация")

class LoginFormWidget(QWidget):
    def __init__(self, conn, parent):
        super().__init__()
        self.conn = conn
        self.db_cursor = conn.cursor()
        self.setFixedSize(400, 200)
        self.parent = parent
        self.setWindowTitle("Аунтификация")

        form_layout = QFormLayout()
        fields_layout = QGridLayout()

        username_label = QLabel('Логин')
        self.username_input = QLineEdit()
        
        password_label = QLabel('Пароль')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)


        submit_button = QPushButton('Войти')
        submit_button.clicked.connect(self.login)

        submit_button.setObjectName("submit_button")

        open_register_button = QPushButton('Создать аккаунт')
        open_register_button.clicked.connect(self.open_register_window)

        open_register_button.setObjectName("switch_button")

        fields_layout.addWidget(username_label, 0, 0)
        fields_layout.addWidget(self.username_input, 0, 1)
        fields_layout.addWidget(password_label, 1, 0)
        fields_layout.addWidget(self.password_input, 1, 1)

        fields_layout.addWidget(submit_button, 2, 0, 1, 2)
        fields_layout.addWidget(open_register_button, 3, 0, 1, 2)
      

        form_layout.setLayout(1, QFormLayout.ItemRole.SpanningRole, fields_layout)
        self.setLayout(form_layout)


    def login(self):
        """Обработка авторизации."""
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        
        self.db_cursor.execute("""
        SELECT id, username FROM users WHERE username = ? AND password = ?
        """, (username, password))
        user = self.db_cursor.fetchone()

        if user:
            QMessageBox.information(self, "Успех", f"Добро пожаловать, {username}!")
            self.open_main_window(user)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль.")

   
    def open_main_window(self, user):
        """Открытие основного окна после авторизации."""
        self.parent.close()
        self.main = MainApp()
        self.main.show()

    def open_register_window(self):
        self.parent.switch_window(1)


class RegisterFormWidget(QWidget):
    def __init__(self, conn, parent):
        super().__init__()
        self.conn = conn
        self.parent = parent
        self.setFixedSize(400, 200)
        self.db_cursor = conn.cursor()
        self.setWindowTitle("Регистрация")

        form_layout = QFormLayout()
        fields_layout = QGridLayout()

        username_label = QLabel('Имя пользователя')
        self.username_input = QLineEdit()
        
        password_label = QLabel('Пароль')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
   
        submit_button = QPushButton('Создать аккаунт')
        submit_button.clicked.connect(self.register)

        submit_button.setObjectName("submit_button")

        open_login_button = QPushButton('Войти')
        open_login_button.clicked.connect(self.open_login_window)

        open_login_button.setObjectName("switch_button")

        fields_layout.addWidget(username_label, 0, 0)
        fields_layout.addWidget(self.username_input, 0, 1)
        fields_layout.addWidget(password_label, 1, 0)
        fields_layout.addWidget(self.password_input, 1, 1)

        fields_layout.addWidget(submit_button, 3, 0, 1, 2)
        fields_layout.addWidget(open_login_button, 4, 0, 1, 2)

        form_layout.setLayout(1, QFormLayout.ItemRole.SpanningRole, fields_layout)

        self.setLayout(form_layout)

    def register(self):
        """Обработка регистрации."""
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        self.db_cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if self.db_cursor.fetchone():
            QMessageBox.warning(self, "Ошибка", "Имя пользователя уже занято.")
            return

        self.db_cursor.execute("""
        INSERT INTO users (username, password) VALUES (?, ?)
        """, (username, password))
        self.conn.commit()
        self.username_input.clear()
        self.password_input.clear()
        self.open_login_window()
        QMessageBox.information(self, "Успех", "Регистрация успешно завершена!")

  

    def open_login_window(self):
        self.parent.switch_window(0)

app = QApplication(sys.argv)
db.initialize_database()
# db.seed_database()
auth_window = AuthWindow()
auth_window.show()
sys.exit(app.exec())