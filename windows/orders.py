import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate, QSqlQuery

class OrdersWindow(QtWidgets.QMainWindow):
    def __init__(self, menu,store_id = None):
        super().__init__()
        uic.loadUi('windows/orders.ui', self)
        self.main_menu = menu
        self.store_id = store_id
        self.le_phone.setReadOnly(True)
        self.master_model = QSqlRelationalTableModel()
        self.master_model.setTable("orders")
        self.master_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.master_model.setSort(0, Qt.SortOrder.AscendingOrder)
        self.master_model.setRelation(3, QSqlRelation("stores", "store_id", "store_name"))
        self.master_model.setRelation(2, QSqlRelation("customers", "customer_id", "surname"))
        self.cb_customer.setModel(self.master_model.relationModel(2))
        self.cb_customer.setModelColumn(self.master_model.relationModel(2).fieldIndex("surname"))
        self.cb_store.setModel(self.master_model.relationModel(3))
        self.cb_store.setModelColumn(self.master_model.relationModel(3).fieldIndex("store_name"))
        self.master_mapper = QtWidgets.QDataWidgetMapper()
        self.master_mapper.setModel(self.master_model)
        self.master_mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.master_mapper.addMapping(self.le_id, 0)
        self.master_mapper.addMapping(self.le_date, 1)
        self.master_mapper.addMapping(self.cb_customer, 2)
        self.master_mapper.addMapping(self.cb_store, 3)
        if self.store_id is not None:
            self.master_model.setFilter(f'"store_id" = {self.store_id}')
            self.master_model.select()
            self.master_mapper.setCurrentIndex(0)
            self.master_mapper.toFirst()
        else:
            self.master_model.select()
        self.le_phone.setReadOnly(True)
        self.detail_model = QSqlRelationalTableModel()
        self.detail_model.setTable('"orders compositions"')
        self.detail_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.detail_model.setRelation(2, QSqlRelation("products", "product_id", "product_name"))
        self.tw.setModel(self.detail_model)
        self.tw.setItemDelegate(QSqlRelationalDelegate(self.tw))
        self.tw.hideColumn(0)
        self.tw.hideColumn(3)
        self.detail_model.setHeaderData(1, Qt.Orientation.Horizontal, "Количество")
        self.detail_model.setHeaderData(2, Qt.Orientation.Horizontal, "Товар")
        self.tw.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.master_mapper.toFirst()
        self.update_detail_table()
        self.update_phone()

        self.b_back.clicked.connect(self.return_to_menu)
        self.b_next.clicked.connect(self.next)
        self.b_prev.clicked.connect(self.prev)
        self.b_first.clicked.connect(self.first)
        self.b_last.clicked.connect(self.last)
        self.b_add.clicked.connect(self.add_order)
        self.b_save.clicked.connect(self.save)
        self.b_delete.clicked.connect(self.delete_order)

        self.master_mapper.currentIndexChanged.connect(self.update_detail_table)
        self.master_mapper.currentIndexChanged.connect(self.update_phone)
        self.cb_customer.currentIndexChanged.connect(self.update_phone)

        self.b_otchet.clicked.connect(self.make_report)
        self.btn_add_detail.clicked.connect(self.add_detail)
        self.btn_delete_detail.clicked.connect(self.delete_detail)
        self.le_search.textChanged.connect(self.apply_id_filter)

    def update_detail_table(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            return
        order_id = self.master_model.index(current_row, 0).data()
        if order_id is not None:
            self.detail_model.setFilter(f'"order_id" = {order_id}')
            self.detail_model.select()

    def update_phone(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            self.le_phone.clear()
            return

        idx_cb = self.cb_customer.currentIndex()
        if idx_cb < 0:
            self.le_phone.clear()
            return

    
        rel_model = self.cb_customer.model()
        if rel_model:
            customer_id = rel_model.index(idx_cb, 0).data()
            if customer_id:
                query = QSqlQuery()
                query.prepare("SELECT customers_phone FROM customers WHERE customer_id = ?")
                query.addBindValue(customer_id)
                if query.exec() and query.next():
                    self.le_phone.setText(query.value(0) or "")
                    return
        self.le_phone.clear()

    def next(self):
        if self.detail_model.isDirty():
            self.detail_model.revertAll()
        if self.master_model.isDirty():
            self.master_model.revertAll()
        self.master_mapper.toNext()

    def prev(self):
        if self.detail_model.isDirty():
            self.detail_model.revertAll()
        if self.master_model.isDirty():
            self.master_model.revertAll()
        self.master_mapper.toPrevious()

    def first(self):
        if self.detail_model.isDirty():
            self.detail_model.revertAll()
        if self.master_model.isDirty():
            self.master_model.revertAll()
        self.master_mapper.toFirst()

    def last(self):
        if self.detail_model.isDirty():
            self.detail_model.revertAll()
        if self.master_model.isDirty():
            self.master_model.revertAll()
        self.master_mapper.toLast()

    def add_order(self):
        row = self.master_model.rowCount()
        self.master_model.insertRow(row)
        self.master_model.setData(self.master_model.index(row, 1), QDate.currentDate().toString("yyyy-MM-dd"))
        self.master_mapper.setCurrentIndex(row)


    def delete_order(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите заказ для удаления")
            return
        reply = QtWidgets.QMessageBox.question(self, "Подтверждение",
            "Вы уверены? Удалятся все позиции заказа!",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.master_model.removeRow(current_row)
            if self.master_model.submitAll():
                self.master_model.select()
                self.master_mapper.toFirst()
                QtWidgets.QMessageBox.information(self, "Успех", "Заказ удалён")
            else:
                QtWidgets.QMessageBox.warning(self, "Ошибка",
                    f"Не удалось удалить заказ: {self.master_model.lastError().text()}")
    def save(self):
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                f"Ошибка сохранения состава: {self.detail_model.lastError().text()}")
            return
        self.master_mapper.submit()
        if self.master_model.submitAll():
            self.master_model.select()
            self.master_mapper.toFirst()
            QtWidgets.QMessageBox.information(self, "Успех", "Данные заказа сохранены")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                f"Ошибка сохранения: {self.master_model.lastError().text()}")

    def check_master(self):
        if self.master_model.isDirty():
            current_row = self.master_mapper.currentIndex()
            date_val = self.master_model.index(current_row, 1).data()
            customer_id = self.master_model.index(current_row, 2).data()
            store_id = self.master_model.index(current_row, 3).data()
            order_id = self.master_model.index(current_row, 0).data()
            if (order_id is None or order_id == "" or (not date_val) or customer_id is None or store_id is None or self.le_phone.text()==""):
                self.master_model.revertAll()
                self.master_model.select()
                self.master_mapper.toFirst()
                return True
        return False

    def make_report(self):
        QtWidgets.QMessageBox.information(self, "Отчёт", "Функция отчёта будет реализована позже.")

    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()
    def add_detail(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нет выбранного заказа")
            return
        order_id = self.master_model.index(current_row, 0).data()
        if not order_id:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Сначала сохраните заказ")
            return
        row = self.detail_model.rowCount()
        if not self.detail_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось добавить позицию")
            return
        self.detail_model.setData(self.detail_model.index(row, 3), order_id) 
        self.detail_model.setData(self.detail_model.index(row, 1), 1)
        rel_model = self.detail_model.relationModel(2)
        if rel_model and rel_model.rowCount() > 0:
            first_product_id = rel_model.index(0, 0).data()
            self.detail_model.setData(self.detail_model.index(row, 2), first_product_id)
        self.tw.scrollToBottom()

    def delete_detail(self):

        current_index = self.tw.currentIndex()
        if not current_index.isValid():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите позицию для удаления")
            return
        row = current_index.row()
        self.detail_model.removeRow(row)
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить: {self.detail_model.lastError().text()}")
        else:
            self.detail_model.select() 
    def check_detail(self):
        if self.detail_model.isDirty():
            self.detail_model.revertAll()
            return True
        return False
    def apply_id_filter(self):
        id_str = self.le_search.text().strip()
        if id_str:
            try:
                order_id = int(id_str)
                self.master_model.setFilter(f"order_id = {order_id}")
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "ID заказа – это целое число")
                self.master_model.setFilter("")
        else:
            self.master_model.setFilter("")
    
        self.master_model.select()
        self.master_mapper.setCurrentIndex(0)
        self.update_detail_table()
        self.update_phone()
    