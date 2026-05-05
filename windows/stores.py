import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate, QSqlQuery

class StoresWindow(QtWidgets.QMainWindow):
    def __init__(self, menu):
        super().__init__()
        uic.loadUi('windows/stores.ui', self)  # ваш файл .ui для магазинов
        self.main_menu = menu
        self.master_model = QSqlRelationalTableModel()
        self.master_model.setTable("stores")
        self.master_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.master_model.setSort(0, Qt.SortOrder.AscendingOrder)
        self.master_model.select()
        self.master_mapper = QtWidgets.QDataWidgetMapper()
        self.master_mapper.setModel(self.master_model)
        self.master_mapper.addMapping(self.le_name, 1)    
        self.master_mapper.addMapping(self.le_address, 2) 
        self.master_mapper.toFirst()
        self.detail_model = QSqlRelationalTableModel()
        self.detail_model.setTable("orders")
        self.detail_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.detail_model.setRelation(2, QSqlRelation("customers", "customer_id", "surname"))
        self.tw.setModel(self.detail_model)
        self.tw.setItemDelegate(QSqlRelationalDelegate(self.tw))
        self.tw.hideColumn(3)
        self.detail_model.setHeaderData(0, Qt.Orientation.Horizontal, "№ заказа")
        self.detail_model.setHeaderData(1, Qt.Orientation.Horizontal, "Дата заказа")
        self.detail_model.setHeaderData(2, Qt.Orientation.Horizontal, "Покупатель")
        self.tw.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.master_mapper.toFirst()
        self.update_detail_table()
        self.b_back.clicked.connect(self.return_to_menu)
        self.b_next.clicked.connect(self.next)
        self.b_prev.clicked.connect(self.prev)
        self.b_first.clicked.connect(self.first)
        self.b_last.clicked.connect(self.last)
        self.b_add.clicked.connect(self.add_store)
        self.b_delete.clicked.connect(self.delete_store)
        self.b_save.clicked.connect(self.save)
        self.b_add_detail.clicked.connect(self.add_detail)
        self.b_delete_detail.clicked.connect(self.delete_detail)
        self.master_mapper.currentIndexChanged.connect(self.update_detail_table)

    def update_detail_table(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            return
        store_id = self.master_model.index(current_row, 0).data()
        if store_id is not None and store_id > 0:
            self.detail_model.setFilter(f"store_id = {store_id}")
        else:
            self.detail_model.setFilter("store_id = -1")
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

    def add_store(self):
        row = self.master_model.rowCount()
        self.master_model.insertRow(row)
        self.master_mapper.setCurrentIndex(row)
        self.le_name.setFocus()
        self.detail_model.setFilter("store_id = -1")
        self.detail_model.select()

    def delete_store(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите магазин для удаления")
            return
        reply = QtWidgets.QMessageBox.question(self, "Подтверждение",
            "Удалить магазин? Все его заказы также будут удалены!",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.master_model.removeRow(current_row)
            if self.master_model.submitAll():
                self.master_model.select()
                self.master_mapper.toFirst()
                QtWidgets.QMessageBox.information(self, "Успех", "Магазин удалён")
            else:
                QtWidgets.QMessageBox.warning(self, "Ошибка",
                    f"Не удалось удалить: {self.master_model.lastError().text()}")

    def save(self):
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                f"Ошибка сохранения заказов: {self.detail_model.lastError().text()}")
            return
        self.master_mapper.submit()
        if self.master_model.submitAll():
            self.master_model.select()
            self.master_mapper.toFirst()
            QtWidgets.QMessageBox.information(self, "Успех", "Данные магазина сохранены")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                f"Ошибка сохранения: {self.master_model.lastError().text()}")

    def check_master(self):
        if self.master_model.isDirty():
            current_row = self.master_mapper.currentIndex()
            if current_row < 0:
                return False
            name_val = self.master_model.index(current_row, 1).data()
            store_id = self.master_model.index(current_row, 0).data()
            if (store_id is None or store_id <= 0) and (not name_val or name_val.strip() == ""):
                self.master_model.revertAll()
                self.master_model.select()
                self.master_mapper.toFirst()
                return True
        return False

    def add_detail(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нет выбранного магазина")
            return
        store_id = self.master_model.index(current_row, 0).data()
        if not store_id or store_id <= 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Сначала сохраните магазин")
            return
        row = self.detail_model.rowCount()
        if not self.detail_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось добавить заказ")
            return
        self.detail_model.setData(self.detail_model.index(row, 3), store_id)
        self.detail_model.setData(self.detail_model.index(row, 1), QDate.currentDate().toString("yyyy-MM-dd"))
        rel_cust = self.detail_model.relationModel(2)
        if rel_cust and rel_cust.rowCount() > 0:
            first_customer_id = rel_cust.index(0, 0).data()
            self.detail_model.setData(self.detail_model.index(row, 2), first_customer_id)
        self.tw.scrollToBottom()

    def delete_detail(self):
        current_index = self.tw.currentIndex()
        if not current_index.isValid():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите заказ для удаления")
            return
        row = current_index.row()
        self.detail_model.removeRow(row)
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить: {self.detail_model.lastError().text()}")
        else:
            self.detail_model.select()

    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()