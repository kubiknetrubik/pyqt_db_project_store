from PyQt6 import QtWidgets, uic
from PyQt6.QtSql import QSqlQuery
from windows.adminnav import AdminNav
from windows.managernav import ManagerNav
class AuthWindow(QtWidgets.QMainWindow):
    def __init__(self, main_menu):
        super().__init__()
        uic.loadUi('windows/auth.ui', self)
        self.main_menu = main_menu
        self.b_back.clicked.connect(self.return_to_menu)
        self.b_ok.clicked.connect(self.check_auth)
        self.load_groups()

    def load_groups(self):
        query = QSqlQuery("SELECT login FROM users ORDER BY login")
        self.groups.clear()
        while query.next():
            self.groups.addItem(query.value(0))

    def check_auth(self):
        login = self.groups.currentText()
        password = self.le_password.text()
        query = QSqlQuery()
        query.prepare("SELECT login FROM users WHERE login = ? AND password = ?")
        query.addBindValue(login)
        query.addBindValue(password)
        if query.exec() and query.next():
            role = query.value(0)
            print(f"Авторизация успешна! Роль: {role}")
            if role == "admin":
                print("admin")
                self.hide()
                self.admin_window = AdminNav()
                self.admin_window.move(self.pos())
                self.admin_window.show()
            elif role =="manager":
                self.hide()
                self.manager_window = ManagerNav()
                self.manager_window.move(self.pos())
                self.manager_window.show()
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show() 
        self.close() 