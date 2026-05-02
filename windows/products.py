from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate

class ProductsWindow(QtWidgets.QMainWindow):
    def __init__(self,menu):
        super().__init__()
        uic.loadUi('windows/products.ui', self)
        self.model = QSqlRelationalTableModel()
        self.main_menu = menu
        self.model.setTable("products")
        self.model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.model.setRelation(3, QSqlRelation("categories", "category_id", "category_name"))
        self.model.setRelation(4, QSqlRelation("shippers", "shipper_id", "shipper_name"))
        self.model.setRelation(5, QSqlRelation("storages", "storage_id", "storage_address"))
        self.model.setSort(0, Qt.SortOrder.AscendingOrder)
        self.model.select()
        self.cb_category.setModel(self.model.relationModel(3))
        self.cb_category.setModelColumn(self.model.relationModel(3).fieldIndex("category_name"))
        self.cb_shipper.setModel(self.model.relationModel(4))
        self.cb_shipper.setModelColumn(self.model.relationModel(4).fieldIndex("shipper_name"))
        self.cb_storage.setModel(self.model.relationModel(5))
        self.cb_storage.setModelColumn(self.model.relationModel(5).fieldIndex("storage_address"))
        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.le_name, 1)
        self.mapper.addMapping(self.le_price, 2)
        self.mapper.addMapping(self.cb_category, 3)
        self.mapper.addMapping(self.cb_shipper, 4)
        self.mapper.addMapping(self.cb_storage, 5)
        self.mapper.toFirst()
        self.b_back.clicked.connect(self.return_to_menu)
        self.b_next.clicked.connect(self.next)
        self.b_prev.clicked.connect(self.prev)
        self.b_first.clicked.connect(self.first)
        self.b_last.clicked.connect(self.last)
        self.b_add.clicked.connect(self.add)
        self.b_save.clicked.connect(self.save)
        self.b_delete.clicked.connect(self.delete)
        self.le_search.textChanged.connect(self.apply_search)
        self.rb_1.toggled.connect(lambda: self.filter_by_shipper("Рога и Копыта"))
        self.rb_2.toggled.connect(lambda: self.filter_by_shipper("ТрансЛогистик"))
    def next(self):
        self.check()
        self.mapper.toNext()
    def prev(self):
        self.check()
        self.mapper.toPrevious()
    def first(self):
        self.check()
        self.mapper.toFirst()
    def last(self):
        self.check()
        self.mapper.toLast()
    def add(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        self.mapper.setCurrentIndex(row)
        self.le_name.setFocus()
    def delete(self):
        current_row = self.mapper.currentIndex()
        self.model.removeRow(current_row)
        self.model.submitAll()
        self.model.select()
        self.mapper.toFirst()
    def save(self):
        self.mapper.submit()
        if self.model.submitAll():
            QtWidgets.QMessageBox.information(self, "Успех", "Данные сохранены!")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения: {self.model.lastError().text()}")
    def apply_search(self):
        filter_str = f"product_name ILIKE '%{self.le_search.text()}%'"
        self.model.setFilter(filter_str)
        self.model.select()
        self.mapper.toFirst()
    def filter_by_shipper(self, shipper_name):
        if self.sender().isChecked():
            filter_str = f"shipper_name = '{shipper_name}'"
            self.model.setFilter(filter_str)
            self.model.select()
            self.mapper.toFirst()
    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()
    def check(self):
        if self.model.isDirty():
            current_row = self.mapper.currentIndex()
            name_val = self.model.index(current_row, 1).data() 
            if not name_val or name_val.strip() == "":
                self.model.revertAll()
                return True
        return False