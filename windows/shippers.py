import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate, QSqlQuery

class ShippersWindow(QtWidgets.QMainWindow):
    def __init__(self, menu):
        super().__init__()
        uic.loadUi('windows/shippers.ui', self)
        self.main_menu = menu
        self.master_model = QSqlRelationalTableModel()
        self.master_model.setTable("shippers")
        self.master_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.master_model.setSort(0, Qt.SortOrder.AscendingOrder) 
        self.master_model.select()
        self.master_mapper = QtWidgets.QDataWidgetMapper()
        self.master_mapper.setModel(self.master_model)
        self.master_mapper.addMapping(self.le_name, 1)  
        self.master_mapper.addMapping(self.le_phone, 2)  
        self.master_mapper.toFirst()
        self.detail_model = QSqlRelationalTableModel()
        self.detail_model.setTable("products")
        self.detail_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.detail_model.setRelation(3, QSqlRelation("categories", "category_id", "category_name"))
        self.detail_model.setRelation(5, QSqlRelation("storages", "storage_id", "storage_address"))
        self.tw.setModel(self.detail_model)
        self.tw.setItemDelegate(QSqlRelationalDelegate(self.tw))
        self.tw.hideColumn(0) 
        self.tw.hideColumn(4) 
        self.detail_model.setHeaderData(1, Qt.Orientation.Horizontal, "Название")
        self.detail_model.setHeaderData(2, Qt.Orientation.Horizontal, "Цена")
        self.detail_model.setHeaderData(3, Qt.Orientation.Horizontal, "Категория")
        self.detail_model.setHeaderData(5, Qt.Orientation.Horizontal, "Склад")
        self.tw.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.master_mapper.toFirst()
        self.update_detail_table()

        self.b_back.clicked.connect(self.return_to_menu)
        self.b_next.clicked.connect(self.next)
        self.b_prev.clicked.connect(self.prev)
        self.b_first.clicked.connect(self.first)
        self.b_last.clicked.connect(self.last)
        self.b_add.clicked.connect(self.add_shipper)
        self.b_delete.clicked.connect(self.delete_shipper)
        self.b_save.clicked.connect(self.save)
        if hasattr(self, "b_save_2"):
            self.b_save_2.clicked.connect(self.save)
        self.b_add_detail.clicked.connect(self.add_detail)
        self.b_delete_detail.clicked.connect(self.delete_detail)
        self.le_search.textChanged.connect(self.apply_search)
        self.master_mapper.currentIndexChanged.connect(self.update_detail_table)

    def find_master_row_by_id(self, shipper_id):
        for row in range(self.master_model.rowCount()):
            if self.master_model.index(row, 0).data() == shipper_id:
                return row
        return -1

    def restore_master_row(self, current_id=None, fallback_row=0):
        target_row = self.find_master_row_by_id(current_id) if current_id is not None else -1
        if target_row < 0 and self.master_model.rowCount() > 0:
            target_row = min(max(fallback_row, 0), self.master_model.rowCount() - 1)
        if target_row >= 0:
            self.master_mapper.setCurrentIndex(target_row)
        else:
            self.master_mapper.setCurrentIndex(-1)
        self.update_detail_table()

    def apply_search(self):
        current_row = self.master_mapper.currentIndex()
        current_id = None
        if current_row >= 0:
            current_id = self.master_model.index(current_row, 0).data()
        search_text = self.le_search.text().strip().replace("'", "''")
        self.master_model.setFilter(f"shipper_name ILIKE '%{search_text}%'" if search_text else "")
        self.master_model.select()
        self.restore_master_row(current_id, current_row)

    def update_detail_table(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            self.detail_model.setFilter("shipper_id = -1")
            self.detail_model.select()
            return
        shipper_id = self.master_model.index(current_row, 0).data()
        if shipper_id is not None:
            self.detail_model.setFilter(f"shipper_id = {shipper_id}")
            self.detail_model.select()

    def next(self):
        if not self.check_master():
            self.master_mapper.toNext()

    def prev(self):
        if not self.check_master():
            self.master_mapper.toPrevious()

    def first(self):
        if not self.check_master():
            self.master_mapper.toFirst()

    def last(self):
        if not self.check_master():
            self.master_mapper.toLast()

    def add_shipper(self):
        row = self.master_model.rowCount()
        if not self.master_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось добавить поставщика: {self.master_model.lastError().text()}")
            return
        self.master_mapper.setCurrentIndex(row)
        self.le_name.setFocus()
        self.detail_model.setFilter("shipper_id = -1")
        self.detail_model.select()

    def delete_shipper(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите поставщика для удаления")
            return

        if not self.master_model.removeRow(current_row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить поставщика: {self.master_model.lastError().text()}")
            return
        if self.master_model.submitAll():
            self.master_model.select()
            self.restore_master_row(fallback_row=current_row)
            QtWidgets.QMessageBox.information(self, "Успех", "Поставщик удалён")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                f"Не удалось удалить: {self.master_model.lastError().text()}")

    def save(self):
        current_row = self.master_mapper.currentIndex()
        current_id = None
        if current_row >= 0:
            current_id = self.master_model.index(current_row, 0).data()
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                f"Ошибка сохранения товаров: {self.detail_model.lastError().text()}")
            return
        self.master_mapper.submit()
        if self.master_model.submitAll():
            self.master_model.select()
            self.restore_master_row(current_id, self.master_model.rowCount() - 1)
            QtWidgets.QMessageBox.information(self, "Успех", "Данные поставщика сохранены")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                f"Ошибка сохранения: {self.master_model.lastError().text()}")

    def check_master(self):
        if self.master_model.isDirty():
            current_row = self.master_mapper.currentIndex()
            name_val = self.master_model.index(current_row, 1).data()
            shipper_id = self.master_model.index(current_row, 0).data()
            if (shipper_id is None or shipper_id <= 0) and (not name_val or name_val.strip() == ""):
                self.master_model.revertAll()
                self.master_model.select()
                self.restore_master_row(fallback_row=current_row)
                return True
        return False
    def add_detail(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нет выбранного поставщика")
            return
        shipper_id = self.master_model.index(current_row, 0).data()
        if not shipper_id:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Сначала сохраните поставщика")
            return
        row = self.detail_model.rowCount()
        if not self.detail_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось добавить товар")
            return
        self.detail_model.setData(self.detail_model.index(row, 4), shipper_id) 
        self.detail_model.setData(self.detail_model.index(row, 2), 0.0) 
        rel_cat = self.detail_model.relationModel(3)
        if rel_cat and rel_cat.rowCount() > 0:
            first_cat = rel_cat.index(0, 0).data()
            self.detail_model.setData(self.detail_model.index(row, 3), first_cat)
        rel_sto = self.detail_model.relationModel(5)
        if rel_sto and rel_sto.rowCount() > 0:
            first_sto = rel_sto.index(0, 0).data()
            self.detail_model.setData(self.detail_model.index(row, 5), first_sto)
        self.tw.scrollToBottom()

    def delete_detail(self):
        current_index = self.tw.currentIndex()
        if not current_index.isValid():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите товар для удаления")
            return
        row = current_index.row()
        if not self.detail_model.removeRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить товар: {self.detail_model.lastError().text()}")
            return
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить: {self.detail_model.lastError().text()}")
        else:
            self.detail_model.select()
    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()
