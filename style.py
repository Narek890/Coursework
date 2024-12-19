base_styles = """
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
        QTabWidget::pane {
            border: none;
        }
        QTabWidget::tab-bar {
            border: none;
        }
        QTabWidget::tab {
            background-color: #FFB02E;
            border: none;
            color: black;
            outline: none;
            padding: 5px;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
        }
        QTabWidget::tab:selected {
            background-color: #FFB02E;
            color: black;
        }
        QCalendarWidget { font-size: 12px; }
        QDateEdit {
            padding: 5px;
            border: 1px solid #888;
            border-radius: 5px;
        }
    """