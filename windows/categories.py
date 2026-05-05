from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate

class CategoriesWindow(QtWidgets.QMainWindow):
    def __init__(self, menu):
        super().__init__()
        uic.loadUi('windows/categories.ui', self)
        self.main_menu = menu
        self.master_model = QSqlRelationalTableModel()
        self.master_model.setTable("categories")
        self.master_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.master_model.setSort(0, Qt.SortOrder.AscendingOrder)
        self.master_model.select()
        self.master_mapper = QtWidgets.QDataWidgetMapper()
        self.master_mapper.setModel(self.master_model)
        self.master_mapper.addMapping(self.le_name, 1) 
        self.master_mapper.toFirst()

        self.detail_model = QSqlRelationalTableModel()
        self.detail_model.setTable("products")
        self.detail_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnFieldChange)
        self.detail_model.setRelation(4, QSqlRelation("shippers", "shipper_id", "shipper_name"))
        self.detail_model.setRelation(5, QSqlRelation("storages", "storage_id", "storage_address"))

        self.tw.setModel(self.detail_model)
        self.tw.setItemDelegate(QSqlRelationalDelegate(self.tw))
        self.tw.hideColumn(0)
        self.tw.hideColumn(3) 
        self.detail_model.setHeaderData(1, Qt.Orientation.Horizontal, "Название")
        self.detail_model.setHeaderData(2, Qt.Orientation.Horizontal, "Цена")
        self.detail_model.setHeaderData(4, Qt.Orientation.Horizontal, "Поставщик")
        self.detail_model.setHeaderData(5, Qt.Orientation.Horizontal, "Склад")
        self.tw.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.update_detail_table()
        self.b_back.clicked.connect(self.return_to_menu)
        self.b_next.clicked.connect(self.next)
        self.b_prev.clicked.connect(self.prev)
        self.b_first.clicked.connect(self.first)
        self.b_last.clicked.connect(self.last)
        self.b_add.clicked.connect(self.add)
        self.b_save.clicked.connect(self.save)
        self.b_delete.clicked.connect(self.delete)
    def update_detail_table(self):
        current_master_row = self.master_mapper.currentIndex()
        category_id = self.master_model.index(current_master_row, 0).data()
        self.detail_model.setFilter(f"category_id = {category_id}")
        self.detail_model.select()
    def next(self):
        if not self.check():
            self.master_mapper.toNext()
            self.update_detail_table()
    def prev(self):
        if not self.check():
            self.master_mapper.toPrevious()
            self.update_detail_table()
    def first(self):
        if not self.check():
            self.master_mapper.toFirst()
            self.update_detail_table()
    def last(self):
        if not self.check():
            self.master_mapper.toLast()
            self.update_detail_table()
    def add(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        self.mapper.setCurrentIndex(row)
        self.le_name.setFocus()
        self.update_detail_table()
    def delete(self):
        current_row = self.mapper.currentIndex()
        self.model.removeRow(current_row)
        self.model.submitAll()
        self.model.select()
        self.mapper.toFirst()
        self.update_detail_table()
    def save(self):
        self.master_mapper.submit()
        if self.master_model.submitAll():
            QtWidgets.QMessageBox.information(self, "Успех", "Данные сохранены!")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения: {self.model.lastError().text()}")
    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()
    def check(self):
        if self.master_model.isDirty():
            current_row = self.master_mapper.currentIndex()
            name_val = self.master_model.index(current_row,0).data() 
            if not name_val or name_val.strip() == "":
                self.master_model.revertAll()
                self.model.select()   
                self.mapper.toFirst()
                return True
        return False
    