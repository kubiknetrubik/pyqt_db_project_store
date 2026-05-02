from PyQt6 import QtWidgets, uic
from PyQt6.QtSql import QSqlQuery
class ManagerNav(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('windows/managernav.ui', self)
        store_id, ok = QtWidgets.QInputDialog.getInt(
            self, 
            "ID магазина", 
            "Введите ваш store_id (число):", 
            1, 1, 100
        )
        if not ok:
            self.close()
            return
        self.store_id = store_id
        self.b_customers.clicked.connect(self.gocustomers)
        self.b_orders.clicked.connect(self.goorders)
        self.b_back.clicked.connect(self.close)
    def gocustomers():
        print("gocustomers")
    def goorders():
        print("goorders")