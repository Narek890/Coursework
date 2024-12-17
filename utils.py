from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QGuiApplication

def center_window(self):
    screen = QGuiApplication.primaryScreen()
    if not screen:
        QMessageBox.critical(self, "Ошибка", "Невозможно получить экран. Пожалуйста, закройте окно и попробуйте еще раз.")
        return
    rect = screen.availableGeometry()
    self.move((rect.width() - self.width()) // 2, (rect.height() - self.height()) // 2 )