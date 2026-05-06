from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import (
    QSqlQuery,
    QSqlQueryModel,
    QSqlRelation,
    QSqlRelationalDelegate,
    QSqlRelationalTableModel,
)

from windows.report_window import model_rows, show_report


class ProductSelectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор товара")
        self.resize(650, 420)
        self.selected_product_id = None

        self.le_search = QtWidgets.QLineEdit(self)
        self.le_search.setPlaceholderText("Поиск по названию товара")

        self.model = QSqlQueryModel(self)
        self.table = QtWidgets.QTableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.b_select = QtWidgets.QPushButton("Выбрать", self)
        self.b_cancel = QtWidgets.QPushButton("Отмена", self)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.b_select)
        buttons.addWidget(self.b_cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.le_search)
        layout.addWidget(self.table)
        layout.addLayout(buttons)

        self.le_search.textChanged.connect(self.reload_products)
        self.table.doubleClicked.connect(self.accept_selected)
        self.b_select.clicked.connect(self.accept_selected)
        self.b_cancel.clicked.connect(self.reject)
        self.reload_products()

    def reload_products(self):
        search_text = self.le_search.text().strip().replace("'", "''")
        where = ""
        if search_text:
            where = f"WHERE p.product_name ILIKE '%{search_text}%'"
        self.model.setQuery(f"""
            SELECT
                p.product_id AS "Код",
                p.product_name AS "Товар",
                p.price AS "Цена",
                c.category_name AS "Категория"
            FROM products p
            LEFT JOIN categories c ON c.category_id = p.category_id
            {where}
            ORDER BY p.product_name
        """)
        self.table.hideColumn(0)

    def accept_selected(self):
        index = self.table.currentIndex()
        if not index.isValid():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите товар")
            return
        self.selected_product_id = self.model.index(index.row(), 0).data()
        self.accept()


class OrdersWindow(QtWidgets.QMainWindow):
    def __init__(self, menu=None, store_id=None, customer_id=None):
        super().__init__()
        if isinstance(menu, int) and store_id is None:
            store_id = menu
            menu = None

        uic.loadUi("windows/orders.ui", self)
        self.main_menu = menu
        self.store_id = int(store_id) if store_id is not None else None
        self.customer_id = int(customer_id) if customer_id is not None else None
        self._changing_filter = False
        self.show_all_orders = False

        self.le_id.setReadOnly(True)
        self.le_phone.setReadOnly(True)

        self.master_model = QSqlRelationalTableModel(self)
        self.master_model.setTable("orders")
        self.master_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.master_model.setSort(1, Qt.SortOrder.DescendingOrder)
        self.master_model.setRelation(2, QSqlRelation("customers", "customer_id", "surname"))
        self.master_model.setRelation(3, QSqlRelation("stores", "store_id", "store_name"))

        self.master_mapper = QtWidgets.QDataWidgetMapper(self)
        self.master_mapper.setModel(self.master_model)
        self.master_mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.master_mapper.addMapping(self.le_id, 0)
        self.master_mapper.addMapping(self.le_date, 1)
        self.master_mapper.addMapping(self.cb_customer, 2)
        self.master_mapper.addMapping(self.cb_store, 3)

        self.cb_customer.setModel(self.master_model.relationModel(2))
        self.cb_customer.setModelColumn(self.master_model.relationModel(2).fieldIndex("surname"))
        self.cb_store.setModel(self.master_model.relationModel(3))
        self.cb_store.setModelColumn(self.master_model.relationModel(3).fieldIndex("store_name"))
        if self.customer_id is not None:
            self.cb_customer.setEnabled(False)
        if self.store_id is not None:
            self.cb_store.setEnabled(False)

        self.detail_model = QSqlRelationalTableModel(self)
        self.detail_model.setTable('"orders compositions"')
        self.detail_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self.detail_model.setRelation(2, QSqlRelation("products", "product_id", "product_name"))
        self.detail_model.setHeaderData(1, Qt.Orientation.Horizontal, "Количество")
        self.detail_model.setHeaderData(2, Qt.Orientation.Horizontal, "Название")

        self.tw.setModel(self.detail_model)
        self.tw.setItemDelegate(QSqlRelationalDelegate(self.tw))
        self.tw.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tw.hideColumn(0)
        self.tw.hideColumn(3)

        self.orders_limit_label = QtWidgets.QLabel(self.centralwidget)
        self.orders_limit_label.setGeometry(30, 340, 260, 22)
        self.orders_limit_label.show()
        self.b_toggle_orders_limit = QtWidgets.QPushButton(self.centralwidget)
        self.b_toggle_orders_limit.setGeometry(30, 365, 180, 28)
        self.b_toggle_orders_limit.show()

        self.apply_order_filter(keep_current=False)

        self.b_back.clicked.connect(self.return_to_menu)
        self.b_next.clicked.connect(self.next)
        self.b_prev.clicked.connect(self.prev)
        self.b_first.clicked.connect(self.first)
        self.b_last.clicked.connect(self.last)
        self.b_add.clicked.connect(self.add_order)
        self.b_save.clicked.connect(self.save)
        if hasattr(self, "b_save_2"):
            self.b_save_2.clicked.connect(self.save)
        self.b_delete.clicked.connect(self.delete_order)
        self.b_otchet.clicked.connect(self.make_report)
        self.btn_add_detail.clicked.connect(self.add_detail)
        self.btn_delete_detail.clicked.connect(self.delete_detail)
        self.le_search.textChanged.connect(self.apply_order_filter)
        self.b_toggle_orders_limit.clicked.connect(self.toggle_orders_limit)

        self.master_mapper.currentIndexChanged.connect(self.update_detail_table)
        self.master_mapper.currentIndexChanged.connect(self.update_phone)
        self.cb_customer.currentIndexChanged.connect(self.update_phone)

    def build_base_filter_parts(self):
        parts = []
        if self.store_id is not None:
            parts.append(f'"orders"."store_id" = {self.store_id}')
        if self.customer_id is not None:
            parts.append(f'"orders"."customer_id" = {self.customer_id}')

        search_text = self.le_search.text().strip()
        if search_text:
            escaped = search_text.replace("'", "''")
            if search_text.isdigit():
                parts.append(
                    f'("orders"."order_id" = {int(search_text)} OR "orders"."customer_id" IN '
                    f"(SELECT customer_id FROM customers WHERE surname ILIKE '%{escaped}%'))"
                )
            else:
                parts.append(
                    f'"orders"."customer_id" IN '
                    f"(SELECT customer_id FROM customers WHERE surname ILIKE '%{escaped}%')"
                )
        return parts

    def build_order_filter(self):
        parts = self.build_base_filter_parts()
        if not self.show_all_orders:
            sub_parts = [part.replace('"orders".', "") for part in parts]
            sub_filter = ""
            if sub_parts:
                sub_filter = "WHERE " + " AND ".join(sub_parts)
            parts.append(
                '"orders"."order_id" IN ('
                f'SELECT order_id FROM orders {sub_filter} '
                'ORDER BY order_date DESC, order_id DESC LIMIT 10)'
            )
        return " AND ".join(parts)

    def apply_order_filter(self, keep_current=True):
        if self._changing_filter:
            return

        self._changing_filter = True
        current_id = None
        current_row = self.master_mapper.currentIndex()
        if keep_current and current_row >= 0:
            current_id = self.master_model.index(current_row, 0).data()

        self.master_model.setFilter(self.build_order_filter())
        self.master_model.select()

        target_row = 0
        if current_id is not None:
            for row in range(self.master_model.rowCount()):
                if self.master_model.index(row, 0).data() == current_id:
                    target_row = row
                    break

        if self.master_model.rowCount() > 0:
            self.master_mapper.setCurrentIndex(target_row)
        else:
            self.master_mapper.setCurrentIndex(-1)

        self.update_detail_table()
        self.update_phone()
        self.update_orders_limit_text()
        self._changing_filter = False

    def update_orders_limit_text(self):
        count = self.master_model.rowCount()
        if self.show_all_orders:
            self.orders_limit_label.setText(f"Показаны все заказы: {count}")
            self.b_toggle_orders_limit.setText("Показать 10 последних")
        else:
            self.orders_limit_label.setText(f"Показаны последние заказы: {count} из 10")
            self.b_toggle_orders_limit.setText("Показать все заказы")

    def toggle_orders_limit(self):
        self.show_all_orders = not self.show_all_orders
        self.apply_order_filter()

    def update_detail_table(self):
        current_row = self.master_mapper.currentIndex()
        order_id = None
        if current_row >= 0:
            order_id = self.master_model.index(current_row, 0).data()

        if order_id:
            self.detail_model.setFilter(f'"order_id" = {order_id}')
        else:
            self.detail_model.setFilter('"order_id" = -1')

        self.detail_model.select()
        self.tw.hideColumn(0)
        self.tw.hideColumn(3)

    def update_phone(self):
        customer_id = self.current_customer_id()
        if not customer_id:
            self.le_phone.clear()
            return

        query = QSqlQuery()
        query.prepare("SELECT customers_phone FROM customers WHERE customer_id = ?")
        query.addBindValue(customer_id)
        if query.exec() and query.next():
            self.le_phone.setText(query.value(0) or "")
        else:
            self.le_phone.clear()

    def current_customer_id(self):
        rel_model = self.cb_customer.model()
        index = self.cb_customer.currentIndex()
        if rel_model is None or index < 0:
            return None
        return rel_model.index(index, 0).data()

    def next_order_id(self):
        query = QSqlQuery()
        if query.exec("SELECT COALESCE(MAX(order_id), 0) + 1 FROM orders") and query.next():
            return query.value(0)
        return None

    def revert_unsaved_changes(self):
        self.master_mapper.revert()
        detail_was_dirty = self.detail_model.isDirty()
        master_was_dirty = self.master_model.isDirty()

        if detail_was_dirty:
            self.detail_model.revertAll()
        if master_was_dirty:
            self.master_model.revertAll()
            self.apply_order_filter(keep_current=False)
        else:
            self.update_detail_table()
            self.update_phone()

    def next(self):
        self.revert_unsaved_changes()
        self.master_mapper.toNext()

    def prev(self):
        self.revert_unsaved_changes()
        self.master_mapper.toPrevious()

    def first(self):
        self.revert_unsaved_changes()
        self.master_mapper.toFirst()

    def last(self):
        self.revert_unsaved_changes()
        self.master_mapper.toLast()

    def add_order(self):
        self.revert_unsaved_changes()
        row = self.master_model.rowCount()
        if not self.master_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Error", self.master_model.lastError().text())
            return

        order_id = self.next_order_id()
        if order_id is not None:
            self.master_model.setData(self.master_model.index(row, 0), order_id)
        self.master_model.setData(self.master_model.index(row, 1), QDate.currentDate().toString("yyyy-MM-dd"))
        if self.customer_id is not None:
            self.master_model.setData(self.master_model.index(row, 2), self.customer_id)
        if self.store_id is not None:
            self.master_model.setData(self.master_model.index(row, 3), self.store_id)
        self.master_mapper.setCurrentIndex(row)
        self.le_date.setFocus()

    def delete_order(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Error", "Select an order to delete.")
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm",
            "Delete this order and all its rows?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        self.detail_model.revertAll()
        self.master_model.removeRow(current_row)
        self.detail_model.setFilter('"order_id" = -1')
        self.detail_model.select()

    def save(self):
        current_row = self.master_mapper.currentIndex()
        current_id = None
        if current_row >= 0:
            current_id = self.master_model.index(current_row, 0).data()
        self.master_mapper.submit()
        if not self.master_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Error", self.master_model.lastError().text())
            return

        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Error", self.detail_model.lastError().text())
            return

        self.apply_order_filter()
        if current_id is not None:
            self.set_current_order_by_id(current_id)
        QtWidgets.QMessageBox.information(self, "Saved", "Order data saved.")

    def set_current_order_by_id(self, order_id):
        for row in range(self.master_model.rowCount()):
            if self.master_model.index(row, 0).data() == order_id:
                self.master_mapper.setCurrentIndex(row)
                return True
        return False

    def add_detail(self):
        current_row = self.master_mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Error", "Select an order first.")
            return

        order_id = self.master_model.index(current_row, 0).data()
        if not order_id:
            QtWidgets.QMessageBox.warning(self, "Error", "Save the order before adding products.")
            return

        dialog = ProductSelectDialog(self)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        row = self.detail_model.rowCount()
        if not self.detail_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Error", self.detail_model.lastError().text())
            return

        self.detail_model.setData(self.detail_model.index(row, 3), order_id)
        self.detail_model.setData(self.detail_model.index(row, 1), 1)
        self.detail_model.setData(self.detail_model.index(row, 2), dialog.selected_product_id)
        self.tw.scrollToBottom()

    def delete_detail(self):
        current_index = self.tw.currentIndex()
        if not current_index.isValid():
            QtWidgets.QMessageBox.warning(self, "Error", "Select a product row to delete.")
            return
        self.detail_model.removeRow(current_index.row())
        self.tw.clearSelection()

    def make_report(self):
        columns = [
            (0, "№ заказа"),
            (1, "Дата"),
            (2, "Покупатель"),
            (3, "Магазин"),
        ]
        self.report_window = show_report(
            self,
            "Отчёт по заказам",
            [title for _, title in columns],
            model_rows(self.master_model, columns),
        )

    def return_to_menu(self):
        self.revert_unsaved_changes()
        if self.main_menu is not None:
            self.main_menu.move(self.pos())
            self.main_menu.show()
        self.close()
