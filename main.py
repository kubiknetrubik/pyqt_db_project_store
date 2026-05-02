import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from windows.auth import AuthWindow
from PyQt6.QtSql import QSqlDatabase
class InfoWindow(QtWidgets.QDialog): 
    def __init__(self):
        super().__init__()
        uic.loadUi('info.ui', self)
        self.b_ok.clicked.connect(self.close) 
class MainMenu(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainMenu, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        if hasattr(self, 'label'):
            pixmap = QPixmap("image.png")
            self.label.setPixmap(pixmap.scaled(360, 240, Qt.AspectRatioMode.KeepAspectRatio))
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.b_auth.clicked.connect(self.open_auth)
        self.b_inf.clicked.connect(self.show_dev_info)
        self.b_quit.clicked.connect(self.close)

    def show_dev_info(self):
        self.info_win = InfoWindow()
        self.info_win.exec()

    def open_auth(self):
        self.hide()
        self.auth_window = AuthWindow(self)
        self.auth_window.move(self.pos())
        self.auth_window.show()
def db_connect():
    db = QSqlDatabase.addDatabase('QPSQL') 
    db.setHostName('localhost') 
    db.setPort(5432) 
    db.setDatabaseName('mydb')
    db.setUserName('postgres')
    db.setPassword('labs')

    if not db.open():
        QtWidgets.QMessageBox.critical(None, "Database Error", 
                                       f"Не удалось подключиться к Docker БД: {db.lastError().text()}")
        return False
    return True
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    if not db_connect():
        sys.exit(1)
    window = MainMenu()
    window.show()
    sys.exit(app.exec())