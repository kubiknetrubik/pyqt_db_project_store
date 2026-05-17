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
        self.b_orders.clicked.connect(self.open_orders)

    def find_row_by_id(self, customer_id):
        for row in range(self.model.rowCount()):
            if self.model.index(row, 0).data() == customer_id:
                return row
        return -1

    def restore_row(self, current_id=None, fallback_row=0):
        target_row = self.find_row_by_id(current_id) if current_id is not None else -1
        if target_row < 0 and self.model.rowCount() > 0:
            target_row = min(max(fallback_row, 0), self.model.rowCount() - 1)
        if target_row >= 0:
            self.mapper.setCurrentIndex(target_row)
        else:
            self.mapper.setCurrentIndex(-1)

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
        self.restore_row(fallback_row=current_row)
    def save(self):
        current_row = self.mapper.currentIndex()
        current_id = None
        if current_row >= 0:
            current_id = self.model.index(current_row, 0).data()
        self.mapper.submit()
        if self.model.submitAll():
            self.model.select()
            self.restore_row(current_id, self.model.rowCount() - 1)
            QtWidgets.QMessageBox.information(self, "Успех", "Данные сохранены!")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения: {self.model.lastError().text()}")
    def apply_search(self):
        current_row = self.mapper.currentIndex()
        current_id = None
        if current_row >= 0:
            current_id = self.model.index(current_row, 0).data()
        search_text = self.le_search.text().strip().replace("'", "''")
        filter_str = f"customers_phone ILIKE '%{search_text}%'"
        self.model.setFilter(filter_str)
        self.model.select()
        self.restore_row(current_id, current_row)
    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()
    def open_orders(self):
        if self.model.isDirty():
            self.model.revertAll()
            self.model.select()

        current_row = self.mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите покупателя")
            return

        customer_id = self.model.index(current_row, 0).data()
        if not customer_id:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Сначала сохраните покупателя")
            return

        store_id = getattr(self.main_menu, "store_id", None)

        self.hide()
        self.orders_window = OrdersWindow(self, store_id=store_id, customer_id=customer_id)
        self.orders_window.move(self.pos())
        self.orders_window.show()
    def check(self):
        if self.model.isDirty():
            current_row = self.mapper.currentIndex()
            name_val = self.model.index(current_row, 1).data() 
            if not name_val or name_val.strip() == "":
                self.model.revertAll()
                self.model.select()   
                self.restore_row(fallback_row=current_row)
                return True
        return False
    
          
