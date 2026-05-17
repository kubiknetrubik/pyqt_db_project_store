from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate

from windows.report_window import query_rows, show_report

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
        self.b_otchet.clicked.connect(self.make_report)
        self.le_search.textChanged.connect(self.apply_search)

    def find_master_row_by_id(self, category_id):
        for row in range(self.master_model.rowCount()):
            if self.master_model.index(row, 0).data() == category_id:
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
        if search_text:
            self.master_model.setFilter(f"category_name ILIKE '%{search_text}%'")
        else:
            self.master_model.setFilter("")
        self.master_model.select()

        self.restore_master_row(current_id, current_row)

    def update_detail_table(self):
        current_master_row = self.master_mapper.currentIndex()
        if current_master_row < 0:
            self.detail_model.setFilter("category_id = -1")
            self.detail_model.select()
            return
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
        row = self.master_model.rowCount()
        self.master_model.insertRow(row)
        self.master_mapper.setCurrentIndex(row)
        self.le_name.setFocus()
        self.update_detail_table()
    def delete(self):
        current_row = self.master_mapper.currentIndex()
        self.master_model.removeRow(current_row)
        self.master_model.submitAll()
        self.master_model.select()
        self.restore_master_row(fallback_row=current_row)
    def save(self):
        current_row = self.master_mapper.currentIndex()
        current_id = None
        if current_row >= 0:
            current_id = self.master_model.index(current_row, 0).data()
        self.master_mapper.submit()
        if self.master_model.submitAll():
            self.master_model.select()
            self.restore_master_row(current_id, self.master_model.rowCount() - 1)
            QtWidgets.QMessageBox.information(self, "Успех", "Данные сохранены!")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения: {self.master_model.lastError().text()}")
    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()
    def make_report(self):
        try:
            rows = query_rows("""
                SELECT
                    c.category_name,
                    COUNT(p.product_id) AS products_count,
                    COALESCE(SUM(p.price), 0) AS total_price,
                    COALESCE(AVG(p.price), 0) AS average_price
                FROM categories c
                LEFT JOIN products p ON p.category_id = c.category_id
                GROUP BY c.category_id, c.category_name
                ORDER BY total_price DESC, c.category_name
            """)
        except RuntimeError as error:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(error))
            return

        self.report_window = show_report(
            self,
            "Стоимость категорий",
            ["Категория", "Товаров", "Общая стоимость", "Средняя цена"],
            rows,
        )
    def check(self):
        if self.master_model.isDirty():
            current_row = self.master_mapper.currentIndex()
            name_val = self.master_model.index(current_row,1).data()
            if not name_val or name_val.strip() == "":
                self.master_model.revertAll()
                self.master_model.select()
                self.restore_master_row(fallback_row=current_row)
                return True
        return False
    
