from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate

from windows.report_window import query_rows, show_report

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
        self.b_otchet_1.clicked.connect(self.report_products_by_price)
        self.b_otchet_2.clicked.connect(self.report_products_ordered_year)
        self.b_otchet_3.clicked.connect(self.report_product_purchase_stats)
        self.rb_1.toggled.connect(lambda: self.filter_by_shipper("Рога и Копыта"))
        self.rb_2.toggled.connect(lambda: self.filter_by_shipper("ТрансЛогистик"))

    def find_row_by_id(self, product_id):
        for row in range(self.model.rowCount()):
            if self.model.index(row, 0).data() == product_id:
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
        if not self.model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось добавить товар: {self.model.lastError().text()}")
            return
        self.mapper.setCurrentIndex(row)
        self.le_name.setFocus()
    def delete(self):
        current_row = self.mapper.currentIndex()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите товар для удаления")
            return
        if not self.model.removeRow(current_row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить товар: {self.model.lastError().text()}")
            return
        if not self.model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить товар: {self.model.lastError().text()}")
            return
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
        filter_str = f"product_name ILIKE '%{search_text}%'"
        self.model.setFilter(filter_str)
        self.model.select()
        self.restore_row(current_id, current_row)
    def filter_by_shipper(self, shipper_name):
        if self.sender().isChecked():
            current_row = self.mapper.currentIndex()
            current_id = None
            if current_row >= 0:
                current_id = self.model.index(current_row, 0).data()
            filter_str = f"shipper_name = '{shipper_name}'"
            self.model.setFilter(filter_str)
            self.model.select()
            self.restore_row(current_id, current_row)
    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()
    def report_products_by_price(self):
        try:
            rows = query_rows("""
                SELECT
                    p.product_name,
                    p.price,
                    c.category_name,
                    s.shipper_name,
                    st.storage_address
                FROM products p
                LEFT JOIN categories c ON c.category_id = p.category_id
                LEFT JOIN shippers s ON s.shipper_id = p.shipper_id
                LEFT JOIN storages st ON st.storage_id = p.storage_id
                ORDER BY p.price ASC, p.product_name
            """)
        except RuntimeError as error:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(error))
            return

        self.report_window = show_report(
            self,
            "Товары по возрастанию цены",
            ["Товар", "Цена", "Категория", "Поставщик", "Склад"],
            rows,
        )

    def report_products_ordered_year(self):
        try:
            rows = query_rows("""
                SELECT
                    p.product_name,
                    c.category_name,
                    s.shipper_name,
                    st.storage_address
                FROM products p
                JOIN "orders compositions" oc ON oc.product_id = p.product_id
                JOIN orders o ON o.order_id = oc.order_id
                LEFT JOIN categories c ON c.category_id = p.category_id
                LEFT JOIN shippers s ON s.shipper_id = p.shipper_id
                LEFT JOIN storages st ON st.storage_id = p.storage_id
                WHERE o.order_date >= CURRENT_DATE - INTERVAL '1 year'
                  AND o.order_date <= CURRENT_DATE
                GROUP BY p.product_id, p.product_name, c.category_name, s.shipper_name, st.storage_address
                ORDER BY p.product_name
            """)
        except RuntimeError as error:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(error))
            return

        self.report_window = show_report(
            self,
            "Товары, заказанные в течение года",
            ["Товар", "Категория", "Поставщик", "Склад"],
            rows,
        )

    def report_product_purchase_stats(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Параметры отчёта")
        scope_combo = QtWidgets.QComboBox(dialog)
        scope_combo.addItems(["За последний год", "Все заказы"])
        group_combo = QtWidgets.QComboBox(dialog)
        group_combo.addItems(["По товарам", "По категориям"])
        ok_button = QtWidgets.QPushButton("Сформировать", dialog)
        cancel_button = QtWidgets.QPushButton("Отмена", dialog)

        form = QtWidgets.QFormLayout()
        form.addRow("Период", scope_combo)
        form.addRow("Группировка", group_combo)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addLayout(form)
        layout.addLayout(buttons)
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        year_only = scope_combo.currentIndex() == 0
        group_by_category = group_combo.currentIndex() == 1
        sales_where = ""
        period_title = "за последний год" if year_only else "по всем заказам"
        if year_only:
            sales_where = """
                WHERE o.order_date >= CURRENT_DATE - INTERVAL '1 year'
                  AND o.order_date <= CURRENT_DATE
            """

        if group_by_category:
            select_sql = """
                COALESCE(c.category_name, 'Без категории') AS group_name,
                COALESCE(SUM(sales.quantity), 0) AS total_quantity,
                COUNT(DISTINCT sales.order_id) AS orders_count,
                COALESCE(SUM(sales.quantity * p.price), 0) AS total_amount
            """
            group_sql = "GROUP BY c.category_id, c.category_name"
            order_sql = "ORDER BY total_quantity DESC, group_name"
            headers = ["Категория", "Куплено шт.", "Заказов", "Сумма"]
            title = f"Статистика покупки продуктов по категориям, {period_title}"
        else:
            select_sql = """
                p.product_name,
                COALESCE(c.category_name, 'Без категории') AS category_name,
                COALESCE(SUM(sales.quantity), 0) AS total_quantity,
                COUNT(DISTINCT sales.order_id) AS orders_count,
                COALESCE(SUM(sales.quantity * p.price), 0) AS total_amount
            """
            group_sql = "GROUP BY p.product_id, p.product_name, c.category_name"
            order_sql = "ORDER BY total_quantity DESC, p.product_name"
            headers = ["Товар", "Категория", "Куплено шт.", "Заказов", "Сумма"]
            title = f"Статистика покупки продуктов по товарам, {period_title}"

        try:
            rows = query_rows(f"""
                SELECT
                    {select_sql}
                FROM products p
                LEFT JOIN categories c ON c.category_id = p.category_id
                LEFT JOIN (
                    SELECT oc.product_id, oc.quantity, oc.order_id
                    FROM "orders compositions" oc
                    JOIN orders o ON o.order_id = oc.order_id
                    {sales_where}
                ) sales ON sales.product_id = p.product_id
                {group_sql}
                {order_sql}
            """)
        except RuntimeError as error:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(error))
            return

        self.report_window = show_report(
            self,
            title,
            headers,
            rows,
        )
    def check(self):
        if self.model.isDirty():
            current_row = self.mapper.currentIndex()
            name_val = self.model.index(current_row, 1).data()
            price = self.model.index(current_row, 2).data() 
            category = self.model.index(current_row, 3).data() 
            shipper = self.model.index(current_row, 4).data() 
            storage = self.model.index(current_row, 5).data() 
            if not name_val or name_val.strip() == "" or price =="" or category == "" or shipper == "" or storage == "":
                self.model.revertAll()
                self.model.select()
                self.restore_row(fallback_row=current_row)
                return True
        return False
