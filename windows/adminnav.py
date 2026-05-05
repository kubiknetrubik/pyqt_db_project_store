from PyQt6 import QtWidgets, uic
from PyQt6.QtSql import QSqlQuery
from windows.products import ProductsWindow
from windows.categories import CategoriesWindow
from windows.customers import CustomersWindow
from windows.orders import OrdersWindow
from windows.shippers import ShippersWindow
from windows.storages import StoragesWindow
from windows.stores import StoresWindow
class AdminNav(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('windows/adminnav.ui', self)
        self.b_products.clicked.connect(self.goproducts)
        self.b_categories.clicked.connect(self.gocategories)
        self.b_customers.clicked.connect(self.gocustomers)
        self.b_orders.clicked.connect(self.goorders)
        self.b_shippers.clicked.connect(self.goshippers)
        self.b_storages.clicked.connect(self.gostorages)
        self.b_stores.clicked.connect(self.gostores)
        self.b_back.clicked.connect(self.close)
    def goproducts(self):
        self.hide()
        self.products_window = ProductsWindow(self)
        self.products_window.move(self.pos())
        self.products_window.show()
    def gocategories(self):
        self.hide()
        self.categories_window = CategoriesWindow(self)
        self.categories_window.move(self.pos())
        self.categories_window.show()
    def gocustomers(self):
        self.hide()
        self.customers_window = CustomersWindow(self)
        self.customers_window.move(self.pos())
        self.customers_window.show()
    def goorders(self):
        self.hide()
        self.orders_window = OrdersWindow(self)
        self.orders_window.move(self.pos())
        self.orders_window.show()
    def goshippers(self):
        self.hide()
        self.shippers_window = ShippersWindow(self)
        self.shippers_window.move(self.pos())
        self.shippers_window.show()
    def gostorages(self):
        self.hide()
        self.storages_window = StoragesWindow(self)
        self.storages_window.move(self.pos())
        self.storages_window.show()
    def gostores(self):
        self.hide()
        self.stores_window = StoresWindow(self)
        self.stores_window.move(self.pos())
        self.stores_window.show()
