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
        try:
            rows = query_rows("""
                SELECT
                    p.product_name,
                    COALESCE(SUM(oc.quantity), 0) AS total_quantity,
                    COUNT(DISTINCT oc.order_id) AS orders_count,
                    COALESCE(SUM(oc.quantity * p.price), 0) AS total_amount
                FROM products p
                LEFT JOIN "orders compositions" oc ON oc.product_id = p.product_id
                GROUP BY p.product_id, p.product_name
                ORDER BY total_quantity DESC, p.product_name
            """)
        except RuntimeError as error:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(error))
            return

        self.report_window = show_report(
            self,
            "Статистика по покупке продуктов",
            ["Товар", "Куплено шт.", "Заказов", "Сумма"],
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
                return True
        return False
