from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate

from windows.orders import OrdersWindow

class CustomersWindow(QtWidgets.QMainWindow):
    def __init__(self,menu):
        super().__init__()
        uic.loadUi('windows/customers.ui', self)
        self.model = QSqlRelationalTableModel()
        self.main_menu = menu
        self.model.setTable("customers")
        self.model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.model.setSort(0, Qt.SortOrder.AscendingOrder)
        self.model.select()
        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.le_surname, 1)
        self.mapper.addMapping(self.le_st_name, 2)
        self.mapper.addMapping(self.le_sec_name, 3)
        self.mapper.addMapping(self.le_phone, 4)
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
    def next(self):
        if not self.check():
            self.mapper.toNext()
    def prev(self):
        if not self.check():
            self.mapper.toPrevious()
    def first(self):
        if not self.check():
            self.mapper.toFirst()
    def last(self):
        if not self.check():
            self.mapper.toLast()
    def add(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        self.mapper.setCurrentIndex(row)
        self.le_surname.setFocus()
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
        filter_str = f"customers_phone ILIKE '%{self.le_search.text()}%'"
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
                self.model.select()   
                self.mapper.toFirst()
                return True
        return False
    
          
