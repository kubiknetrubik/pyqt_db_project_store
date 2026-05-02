from PyQt6 import QtWidgets, uic
from PyQt6.QtSql import QSqlQuery
from windows.products import ProductsWindow
from windows.categories import CategoriesWindow
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
        print("gocustomers")
    def goorders(self):
        print("goorders")
    def goshippers(self):
        print("goshippers")
    def gostorages(self):
        print("gostorages")
    def gostores(self):
        print("gostores")
