from PyQt6 import QtWidgets, uic
from PyQt6.QtSql import QSqlQuery
from windows.customers import CustomersWindow
from windows.orders import OrdersWindow
class ManagerNav(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('windows/managernav.ui', self)
        self.b_customers.clicked.connect(self.gocustomers)
        self.b_orders.clicked.connect(self.goorders)
        self.b_back.clicked.connect(self.close)
    def gocustomers(self):
        self.hide()
        self.customers_window = CustomersWindow(self)
        self.customers_window.move(self.pos())
        self.customers_window.show()
    def goorders(self):
        self.orders_win = OrdersWindow(self)
        self.orders_win.show()
        self.hide()