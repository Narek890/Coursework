from calendar import c
from unicodedata import category
from numpy import delete
import pandas as pd
import csv
import openpyxl
from math import log
from shutil import move
import sys
import sqlite3
import db
from style import base_styles
import utils
import consts

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox,
    QVBoxLayout, QWidget, QStackedWidget, QFileDialog, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QSpinBox, QComboBox, QTextEdit, QFormLayout, QGridLayout, QLayout, QFrame, QListWidget, QListWidgetItem,
    QListView, QAbstractItemView, QHeaderView, QButtonGroup, QScrollArea, QTabWidget, QDialog, QDateEdit
)

from PyQt6.QtGui import QPixmap, QDesktopServices, QPixmap, QPainter
from PyQt6.QtCore import QUrl, Qt, QDate


class User:
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

class SizesComboBox(QComboBox):
    def __init__(self, value=None):
        super().__init__()
        self.addItems(consts.cloth_sizes)

        if value:
            str_value = str(value)
            self.setCurrentIndex(self.findText(str_value))

class CategoriesComboBox(QComboBox):
    def __init__(self, value=None, parent=None):
        super().__init__(parent)
        try:
            conn = db.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories")
            categories = cursor.fetchall()
            for category in categories:
                self.addItem(category[1], category[0])
            
            if value:
                str_value = str(value)
                found = self.findText(str_value)
                if found != -1:
                    self.setCurrentIndex(found)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", "Не удалось получить данные о категориях")
            return
    

class MaterialsComboBox(QComboBox):
    def __init__(self, value=None):
        super().__init__()
        try:
            conn = db.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM materials")
            materials = cursor.fetchall()
            for material in materials:
                self.addItem(material[1], material[0])
            
            if value:
                str_value = str(value)
                self.setCurrentIndex(self.findText(str_value))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", "Не удалось получить данные о материалах")
            return


class MainApp(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        if self.user.role == "admin":        
            self.setWindowTitle("Система учета данных о производстве одежды")
        elif self.user.role == "employee":
            self.setWindowTitle("Система анализа данных о производстве одежды")
        else:
            self.setWindowTitle("Магазин")

        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(base_styles)
        utils.center_window(self)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        tab_title = "Учёт данных"
        if self.user.role == 'employee':
            tab_title = "Анализ данных"
        elif self.user.role == 'user':
            tab_title = "Товары магазина"

        exit_button = QPushButton("Выход")
        exit_button.setFixedHeight(40)
        exit_button.clicked.connect(self.logout)
        exit_button.setObjectName("destructive_button")
        self.tabs.setCornerWidget(exit_button)
        self.tabs.addTab(self.create_data_tab(), tab_title)
        if self.user.role != 'user':
            self.tabs.addTab(self.create_category_tab(), "Категории")
            self.tabs.addTab(self.create_material_tab(), "Материалы")
            if self.user.role == "admin":
                self.tabs.addTab(self.create_employees_tab(), "Сотрудники")

        self.tabs.currentChanged.connect(self.handle_tab_change)
        self.category_names = []


    def handle_tab_change(self, index):
        if index == 0:
            self.load_data_to_table()
            
    def create_data_tab(self):
        """Вкладка для учета данных"""
        tab = QWidget(self)
        
        self.articule_input = QLineEdit()
        self.name_input = QLineEdit()
        self.category_combobox = CategoriesComboBox()
        self.size_input = SizesComboBox()
        self.material_combobox = MaterialsComboBox()
        self.date_input = QDateEdit()
        self.quantity_input = QLineEdit()
        self.price_input = QLineEdit()
        self.cost_input = QLineEdit()

        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setCalendarPopup(True)
        calendar = self.date_input.calendarWidget()
        calendar.setMinimumSize(300, 200) 

        self.inputs_map = {
            "Артикул": self.articule_input,
            "Наименование": self.name_input,
            "Категория": self.category_combobox,
            "Размер": self.size_input,
            "Материал": self.material_combobox,
            "Дата": self.date_input,
            "Количество": self.quantity_input,
            "Цена": self.price_input,
            "Закуп. цена": self.cost_input
        }
        layout = QVBoxLayout()

        header_labels = [
           "ID", "Артикул", "Наименование", "Категория", "Размер", "Материал", "Дата", "Количество", "Цена", "Закуп. цена"
        ]
        self.table = QTableWidget(0, len(header_labels))
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(header_labels)
        self.header = self.table.horizontalHeader()

        self.table.setColumnHidden(0, True)

        for i in range(len(header_labels)):
            self.header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        if self.user.role == 'admin':
            self.table.cellDoubleClicked.connect(self.open_edit_dialog)

        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Обновить список")
        refresh_button.clicked.connect(self.load_data_to_table)
        button_layout.addWidget(refresh_button)
        
        if self.user.role != 'user':
            export_button = QPushButton("Экспорт в .xlsx/.csv")
            export_button.clicked.connect(self.export_data)
            button_layout.addWidget(export_button)
            
            if self.user.role == 'admin': 
                import_button = QPushButton("Импорт из .xlsx/.csv")
                import_button.clicked.connect(self.import_data)
                button_layout.addWidget(import_button)

        layout.addLayout(button_layout)

        if self.user.role == 'admin':
            form_layout = QFormLayout()

            for label, input_field in self.inputs_map.items():
                form_layout.addRow(QLabel(label.capitalize()), input_field)

            add_button = QPushButton("Добавить запись")
            add_button.clicked.connect(self.add_record)

            form_container = QVBoxLayout()
            form_container.addLayout(form_layout)
            form_container.addWidget(add_button)

            layout.addLayout(form_container)
        tab.setLayout(layout)
        
        self.load_data_to_table()

        return tab

    def open_edit_dialog(self, row, column):
        """Открывает диалоговое окно для редактирования записи"""
        cloth_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = QDialog(self)
        dialog.setFixedSize(400, 400)
        dialog.setWindowTitle("Редактирование записи")
        layout = QVBoxLayout(dialog)

        try:
            conn = db.create_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT articul, clothing_items.name, categories.name, size, materials.name, 
                    date_added, quantity, price, cost
                FROM clothing_items
                LEFT JOIN categories ON clothing_items.category_id = categories.id
                LEFT JOIN materials ON clothing_items.material_id = materials.id
                WHERE clothing_items.id = ?
                """,
                (cloth_id,)
            )
            cloth = cursor.fetchone()
            if not cloth:
                raise ValueError("Не найдена запись с таким ID")
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            QMessageBox.critical(self, "Ошибка", "Не удалось получить данные о товаре")
            return

        form_layout = QFormLayout()

        auticule_input = QLineEdit(cloth[0])
        name_input = QLineEdit(cloth[1])        
        category_combobox = CategoriesComboBox(cloth[2])
        size_input = SizesComboBox(cloth[3])
        material_input = MaterialsComboBox(cloth[4])
        date_input = QDateEdit(QDate.fromString(cloth[5], "yyyy-MM-dd"))
        quantity_input = QLineEdit(str(cloth[6]))
        price_input = QLineEdit(str(cloth[7]))
        cost_input = QLineEdit(str(cloth[8]))

        date_input.setCalendarPopup(True)
        calendar = date_input.calendarWidget()

        calendar.setMinimumSize(300, 200) 
        date_input.setDate(QDate.currentDate())
        date_input.setDisplayFormat("yyyy-MM-dd")

        form_layout.addRow(QLabel("Артикул"), auticule_input)
        form_layout.addRow(QLabel("Наименование"), name_input)
        form_layout.addRow(QLabel("Категория"), category_combobox)
        form_layout.addRow(QLabel("Размер"), size_input)
        form_layout.addRow(QLabel("Материал"), material_input)
        form_layout.addRow(QLabel("Дата"), date_input)
        form_layout.addRow(QLabel("Количество"), quantity_input)
        form_layout.addRow(QLabel("Цена"), price_input)
        form_layout.addRow(QLabel("Закуп. цена"), cost_input)

        local_inputs = [
            auticule_input,
            name_input,
            category_combobox,
            size_input,
            material_input,
            date_input,
            quantity_input,
            price_input,
            cost_input
        ]

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()

        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(lambda: self.delete_record(dialog, row))
        delete_button.setObjectName("destructive_button")
        button_layout.addWidget(delete_button)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_changes(dialog, row, local_inputs))
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def save_changes(self, dialog, row, fields: list[QLineEdit | QComboBox]):
        """Сохранение изменений в базе данных и обновление таблицы"""
        try:
            cloth_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            db.execute_query(
                "UPDATE clothing_items SET articul = ?, name = ?, category_id = ?, size = ?, material_id = ?, date_added = ?, quantity = ?, price = ?, cost = ? WHERE id = ?",
                (
                    fields[0].text(),
                    fields[1].text(),
                    fields[2].currentData(),
                    fields[3].currentText(),
                    fields[4].currentData(),
                    fields[5].date().toString("yyyy-MM-dd"),
                    fields[6].text(),
                    fields[7].text(),
                    fields[8].text(),
                    cloth_id
                )
            )
            self.load_data_to_table()

            QMessageBox.information(self, "Успех", "Изменения успешно сохранены.")
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {e}")

    def delete_record(self, dialog, row):
        """Удаление записи из базы данных и таблицы"""
        try:
            cloth_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) 
            confirm = QMessageBox.question(
                self,
                "Подтверждение удаления",
                "Вы уверены, что хотите удалить эту запись?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                db.execute_query("DELETE FROM clothing_items WHERE id = ?", (cloth_id,))

                self.table.removeRow(row)

                QMessageBox.information(self, "Успех", "Запись успешно удалена.")
                dialog.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {e}")

    def load_data_to_table(self):
        """Загружает данные из базы в таблицу."""
        query = "SELECT clothing_items.id, articul, clothing_items.name, categories.name, size, materials.name, date_added, quantity, price, cost FROM clothing_items LEFT JOIN categories on categories.id = category_id LEFT JOIN materials on materials.id = material_id"
        records = db.fetch_all(query)
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(records))
        self.table.setColumnCount(10)
        
        for row_index, row_data in enumerate(records):
            for column_index, value in enumerate(row_data):
                if column_index == 0:
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                else:
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    
                self.table.setItem(row_index, column_index, item)
        self.table.setSortingEnabled(True)
    def add_record(self):
        """Добавляет новую запись в базу данных."""
        artucul = self.articule_input.text()
        name = self.name_input.text()
        category_id = self.category_combobox.currentData()
        size = self.size_input.currentText()
        material = self.material_combobox.currentData()
        date_added = self.date_input.text()
        quantity = self.quantity_input.text()
        price = self.price_input.text()
        cost = self.cost_input.text()
        
        values = [artucul, name, category_id, size, material, date_added, quantity, price, cost]
        if not all(values):
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены!")
            return
        
        try:
            quantity = int(quantity)
            price = float(price)
            cost = float(cost)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество и цена должны быть числовыми значениями!")
            return

        query = """
        INSERT INTO clothing_items (articul, name, category_id, size, material_id, date_added, quantity, price, cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            db.execute_query(query, values)
            self.clear_inputs()
            self.load_data_to_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")

    def clear_inputs(self):
        """Очищает поля ввода после добавления записи."""
        for input_field in self.inputs_map.values():
            if isinstance(input_field, QComboBox):
                input_field.setCurrentIndex(0)
            else:
                input_field.clear()

    def export_data(self):
        """Экспорт данных из таблицы в файл."""
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if path:
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount() - 1):
                    item = self.table.item(row, col + 1)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            df = pd.DataFrame(data, columns=["Артикул", "Наименование", "Категория", "Размер", "Материал", "Дата", "Количество", "Цена", "Закуп. цена"])

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
                    next(reader) 
                    imported_data = list(reader)
            elif file_path.endswith(".xlsx"):
                workbook = openpyxl.load_workbook(file_path)
                sheet = workbook.active
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    imported_data.append(row)

            for record in imported_data:
                articul = record[0]
                name = record[1]
                category = record[2]
                size = record[3]
                material = record[4]
                date_added = record[5]
                quantity = record[6]
                price = record[7]
                cost = record[8]
            
                conn = db.create_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
                category_id = cursor.fetchone()[0]
                category = category_id

                cursor.execute("SELECT id FROM materials WHERE name = ?", (material,))
                material_id = cursor.fetchone()[0]
                material = material_id

                record = (articul, name, category, size, material, date_added, quantity, price, cost)
                print(record)
                try:
                    db.execute_query("INSERT INTO clothing_items (articul, name, category_id, size, material_id, date_added, quantity, price, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", record)
                except Exception as e:
                    print(e)
                    QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать запись c артикулом: {record[0]}")

            QMessageBox.information(self, "Успех", "Данные успешно импортированы!")
            self.load_data_to_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать данные: {e}")

    def create_category_tab(self):
        """Вкладка для управления категориями"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Таблица категорий
        self.category_table = QTableWidget(0, 1)
        self.category_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.category_table.setHorizontalHeaderLabels(["Название"])
        self.category_table.setSortingEnabled(True)
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.category_table.itemDoubleClicked.connect(self.open_category_dialog)
        layout.addWidget(self.category_table)

        # Кнопка обновления списка категорий
        refresh_button = QPushButton("Обновить список категорий")
        refresh_button.clicked.connect(self.load_categories)
        layout.addWidget(refresh_button)

        # Форма добавления новой категории (для администратора)
        if self.user.role == "admin":
            form_container = QVBoxLayout()
            form_layout = QFormLayout()
            self.category_input = QLineEdit()
            form_layout.addRow(QLabel("Название категории"), self.category_input)

            add_button = QPushButton("Добавить категорию")
            add_button.clicked.connect(self.add_category)
            form_container.addWidget(add_button)

            form_container.addLayout(form_layout)
            layout.addLayout(form_container)

        tab.setLayout(layout)
        self.load_categories()
        return tab

    def load_categories(self):
        """Загружает список категорий в таблицу."""
        query = "SELECT id, name FROM categories"
        try:
            categories = db.fetch_all(query)
            if self.user.role == "admin":
                self.category_combobox.clear()
                for category_id, name in categories:
                    self.category_combobox.addItem(name, category_id)
            self.category_table.setRowCount(len(categories))
            for row_index, (category_id, name) in enumerate(categories):
                item = QTableWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, category_id)
                self.category_table.setItem(row_index, 0, item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список категорий: {e}")

    def add_category(self):
        """Добавляет новую категорию."""
        category_name = self.category_input.text().strip()
        if not category_name:
            QMessageBox.warning(self, "Ошибка", "Название категории не может быть пустым!")
            return

        query = "INSERT INTO categories (name) VALUES (?)"
        try:
            db.execute_query(query, (category_name,))
            QMessageBox.information(self, "Успех", "Категория успешно добавлена!")
            self.category_input.clear()
            self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить категорию: {e}")

    def open_category_dialog(self, item):
        """Открывает диалоговое окно для редактирования/удаления категории."""
        category_id = item.data(Qt.ItemDataRole.UserRole)
        category_name = item.text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать категорию")
        dialog.setModal(True)
        dialog.resize(300, 150)

        layout = QVBoxLayout(dialog)

        # Поле для изменения названия
        name_input = QLineEdit(category_name)
        layout.addWidget(QLabel("Название категории:"))
        layout.addWidget(name_input)

        # Кнопки сохранения и удаления
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        delete_button = QPushButton("Удалить")
        delete_button.setObjectName("destructive_button")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        layout.addLayout(buttons_layout)

    
        def save_changes():
            new_name = name_input.text().strip()
            if not new_name:
                QMessageBox.warning(dialog, "Ошибка", "Название категории не может быть пустым!")
                return
            query = "UPDATE categories SET name = ? WHERE id = ?"
            try:
                db.execute_query(query, (new_name, category_id))
                QMessageBox.information(dialog, "Успех", "Категория успешно обновлена!")
                self.load_categories()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить категорию: {e}")

        def delete_category():
            confirm = QMessageBox.question(
                dialog, "Удаление категории",
                "Вы уверены, что хотите удалить эту категорию?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                query = "DELETE FROM categories WHERE id = ?"
                try:
                    db.execute_query(query, (category_id,))
                    QMessageBox.information(dialog, "Успех", "Категория успешно удалена!")
                    self.load_categories()
                    dialog.accept()
                except Exception as e:
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось удалить категорию: {e}")

        # Привязка кнопок к действиям
        save_button.clicked.connect(save_changes)
        delete_button.clicked.connect(delete_category)

        dialog.exec()

    def create_material_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.material_table = QTableWidget(0, 1)
        self.material_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.material_table.setHorizontalHeaderLabels(["Название"])
        self.material_table.setSortingEnabled(True)
        self.material_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.material_table.itemDoubleClicked.connect(self.open_material_dialog)
        layout.addWidget(self.material_table)

        refresh_button = QPushButton("Обновить список материалов")
        refresh_button.clicked.connect(self.load_materials)
        layout.addWidget(refresh_button)

        if self.user.role == "admin":
            form_container = QVBoxLayout()
            form_layout = QFormLayout()
            self.material_input = QLineEdit()

            add_button = QPushButton("Добавить материал")
            add_button.clicked.connect(self.add_material)

            form_container.addWidget(add_button)
            form_layout.addRow(QLabel("Название материала"), self.material_input)
            form_container.addLayout(form_layout)
            layout.addLayout(form_container)

        tab.setLayout(layout)
        self.load_materials()
        return tab

    def load_materials(self):
        """Загружает список материалов в таблицу."""
        query = "SELECT id, name FROM materials"
        try:
            materials = db.fetch_all(query) 
            if self.user.role == "admin":
                self.material_combobox.clear()
                for material_id, name in materials:
                    self.material_combobox.addItem(name, material_id)
                    
            self.material_table.setRowCount(len(materials))
            for row_index, (material_id, name) in enumerate(materials):
                item = QTableWidgetItem(name)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, material_id) 
                self.material_table.setItem(row_index, 0, item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список материалов: {e}")

    def add_material(self):
        """Добавляет новый материал."""
        material_name = self.material_input.text().strip()
        if not material_name:
            QMessageBox.warning(self, "Ошибка", "Название материала не может быть пустым!")
            return

        query = "INSERT INTO materials (name) VALUES (?)"
        try:
            db.execute_query(query, (material_name,))
            QMessageBox.information(self, "Успех", "Материал успешно добавлен!")
            self.material_input.clear()
            self.load_materials()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить материал: {e}")

    def open_material_dialog(self, item):
        """Открывает диалоговое окно для редактирования/удаления материала."""
        material_id = item.data(Qt.ItemDataRole.UserRole)
        material_name = item.text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать материал")
        dialog.setModal(True)
        dialog.resize(300, 150)

        layout = QVBoxLayout(dialog)

        name_input = QLineEdit(material_name)
        layout.addWidget(QLabel("Название материала:"))
        layout.addWidget(name_input)

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        delete_button = QPushButton("Удалить")
        delete_button.setObjectName("destructive_button")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(delete_button)
        layout.addLayout(buttons_layout)

        def save_changes():
            new_name = name_input.text().strip()
            if not new_name:
                QMessageBox.warning(dialog, "Ошибка", "Название материала не может быть пустым!")
                return
            query = "UPDATE materials SET name = ? WHERE id = ?"
            try:
                db.execute_query(query, (new_name, material_id))
                QMessageBox.information(dialog, "Успех", "Материал успешно обновлён!")
                self.load_materials()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить материал: {e}")

        def delete_material():
            confirm = QMessageBox.question(
                dialog, "Удаление материала",
                "Вы уверены, что хотите удалить этот материал?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                query = "DELETE FROM materials WHERE id = ?"
                try:
                    db.execute_query(query, (material_id,))
                    QMessageBox.information(dialog, "Успех", "Материал успешно удалён!")
                    self.load_materials()
                    dialog.accept()
                except Exception as e:
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось удалить материал: {e}")

        save_button.clicked.connect(save_changes)
        delete_button.clicked.connect(delete_material)

        dialog.exec()

    def create_employees_tab(self):
        tab = QWidget()

        # Основной макет вкладки
        main_layout = QVBoxLayout(tab)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        
        self.users_table = QTableWidget(0, 2)
        self.users_table.setHorizontalHeaderLabels(["Логин", "Роль"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        main_layout.addWidget(QLabel("Список сотрудников:"))
        main_layout.addWidget(self.users_table)

        form_container = QWidget()
        form_container.setFixedWidth(400)
        form_layout = QVBoxLayout(form_container)

        label = QLabel("Регистрация сотрудника")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        form_layout.addWidget(label)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form_inputs = QFormLayout()
        form_inputs.addRow(QLabel("Логин"), self.username_input)
        form_inputs.addRow(QLabel("Пароль"), self.password_input)
        form_layout.addLayout(form_inputs)

        register_button = QPushButton("Зарегистрировать")
        register_button.clicked.connect(self.register_employee)
        form_layout.addWidget(register_button)

        main_layout.addWidget(form_container, alignment=Qt.AlignmentFlag.AlignCenter)

        self.load_users_table()

        return tab

    def register_employee(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        query = "INSERT INTO users (username, password, role) VALUES (?, ?, 'employee')"
        try:
            db.execute_query(query, (username, password))
            QMessageBox.information(self, "Успех", "Регистрация успешно завершена!")
            self.username_input.clear()
            self.password_input.clear()

            self.load_users_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось зарегистрировать пользователя: {e}")

    def load_users_table(self):
        """Загружает список пользователей в таблицу."""
        query = "SELECT username, role FROM users"
        self.users_table.setSortingEnabled(False)
        self.users_table.clearContents()
        self.users_table.setRowCount(0)

        try:
            users = db.fetch_all(query)
            self.users_table.setRowCount(len(users))
            for row_index, (username, role) in enumerate(users):
                self.users_table.setItem(row_index, 0, QTableWidgetItem(username))
                self.users_table.setItem(row_index, 1, QTableWidgetItem(role))

            self.users_table.setSortingEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список пользователей: {e}")



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
            base_styles
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
        SELECT id, username, role FROM users WHERE username = ? AND password = ?
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
        user_obj = User(user[0], user[1], user[2])
        self.main = MainApp(user_obj)
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
        self.setWindowTitle("Регистрация пользователя")

        form_layout = QFormLayout()
        fields_layout = QGridLayout()

        username_label = QLabel('Логин')
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
db.seed_database()
auth_window = AuthWindow()
auth_window.show()
sys.exit(app.exec())