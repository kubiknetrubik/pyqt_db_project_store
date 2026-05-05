import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlRelationalTableModel, QSqlRelation, QSqlRelationalDelegate, QSqlQuery

class OrdersWindow(QtWidgets.QMainWindow):
    def __init__(self, menu, store_id=None):
        super().__init__()
        uic.loadUi('windows/orders2.ui', self)   # предполагается, что в orders.ui есть:
                                                # - tw_orders (QTableView для списка заказов)
                                                # - tw (QTableView для состава заказа)
                                                # - остальные поля (le_search, b_back и т.д.)
        self.main_menu = menu
        self.store_id = store_id

        # ---- Модель для заказов (мастер) ----
        self.orders_model = QSqlRelationalTableModel()
        self.orders_model.setTable("orders")
        self.orders_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnFieldChange)
        self.orders_model.setSort(0, Qt.SortOrder.AscendingOrder)
        self.orders_model.setRelation(2, QSqlRelation("customers", "customer_id", "surname"))
        self.orders_model.setRelation(3, QSqlRelation("stores", "store_id", "store_name"))

        # Фильтр по магазину (если задан)
        if self.store_id is not None:
            self.orders_model.setFilter(f"store_id = {self.store_id}")
        self.orders_model.select()

        # Настраиваем таблицу заказов
        self.tw_orders.setModel(self.orders_model)
        self.tw_orders.setItemDelegate(QSqlRelationalDelegate(self.tw_orders))
        # Скрываем колонки с внешними ключами (customer_id, store_id), оставляем отображаемые
        self.tw_orders.hideColumn(0)   # order_id (можно оставить видимым, по желанию)
        self.tw_orders.hideColumn(2)   # customer_id (заменяется на surname)
        self.tw_orders.hideColumn(3)   # store_id (заменяется на store_name)
        # Настройка заголовков для видимых колонок
        self.orders_model.setHeaderData(1, Qt.Orientation.Horizontal, "Дата заказа")
        # Колонка 2 стала surname, колонка 3 стала store_name – они отобразятся автоматически

        # Растягиваем колонки
        self.tw_orders.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        # ---- Модель для состава заказа (детали) ----
        self.detail_model = QSqlRelationalTableModel()
        self.detail_model.setTable('"orders compositions"')
        self.detail_model.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnFieldChange)
        self.detail_model.setRelation(2, QSqlRelation("products", "product_id", "product_name"))

        self.tw.setModel(self.detail_model)
        self.tw.setItemDelegate(QSqlRelationalDelegate(self.tw))
        self.tw.hideColumn(0)   # compos_id
        self.tw.hideColumn(3)   # order_id (используется для фильтрации)
        self.detail_model.setHeaderData(1, Qt.Orientation.Horizontal, "Количество")
        self.detail_model.setHeaderData(2, Qt.Orientation.Horizontal, "Товар")
        self.tw.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        # При выборе строки в таблице заказов обновляем состав
        self.tw_orders.clicked.connect(self.on_order_selected)

        # --- Кнопки управления (оставляем как есть, но адаптируем) ---
        self.b_back.clicked.connect(self.return_to_menu)
        self.b_add.clicked.connect(self.add_order)
        self.b_delete.clicked.connect(self.delete_order)
        self.b_save.clicked.connect(self.save)  # не обязателен при OnFieldChange, но можно оставить
        self.b_add_detail.clicked.connect(self.add_detail)
        self.b_delete_detail.clicked.connect(self.delete_detail)

        self.le_search.textChanged.connect(self.apply_id_filter)
        self.b_otchet.clicked.connect(self.make_report)

        # Если есть кнопки навигации (b_next, b_prev и т.д.), их можно удалить или скрыть,
        # так как навигация теперь через таблицу.

        # Дополнительно: при инициализации, если есть заказы, выделяем первый и загружаем его состав
        if self.orders_model.rowCount() > 0:
            first_index = self.orders_model.index(0, 0)
            self.tw_orders.setCurrentIndex(first_index)
            self.on_order_selected(first_index)

    def on_order_selected(self, index):
        """При выборе заказа загружаем его состав"""
        order_id = self.orders_model.index(index.row(), 0).data()
        if order_id:
            self.detail_model.setFilter(f'"order_id" = {order_id}')
            self.detail_model.select()
            # Дополнительно можно обновить поле телефона, если оно есть в UI
            self.update_phone(order_id)

    def update_phone(self, order_id):
        """Заполняет поле телефона по order_id (если у вас есть такое поле)"""
        if not hasattr(self, 'le_phone'):
            return
        query = QSqlQuery()
        query.prepare("""
            SELECT c.customers_phone 
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.order_id = ?
        """)
        query.addBindValue(order_id)
        if query.exec() and query.next():
            self.le_phone.setText(query.value(0) or "")
        else:
            self.le_phone.clear()

    def add_order(self):
        """Добавляет новый заказ"""
        row = self.orders_model.rowCount()
        if not self.orders_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось добавить заказ")
            return
        # Устанавливаем дату по умолчанию (текущая)
        self.orders_model.setData(self.orders_model.index(row, 1), QDate.currentDate().toString("yyyy-MM-dd"))
        # Если задан store_id, подставляем его автоматически
        if self.store_id is not None:
            self.orders_model.setData(self.orders_model.index(row, 3), self.store_id)
        # Прокручиваем таблицу к новой строке
        self.tw_orders.scrollToBottom()
        # Начинаем редактирование даты или покупателя (по желанию)
        self.tw_orders.edit(self.orders_model.index(row, 1))

    def delete_order(self):
        """Удаляет текущий выбранный заказ"""
        current = self.tw_orders.currentIndex()
        if not current.isValid():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите заказ для удаления")
            return
        reply = QtWidgets.QMessageBox.question(self, "Подтверждение",
            "Удалить заказ? Все позиции состава также будут удалены!",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.orders_model.removeRow(current.row())
            if not self.orders_model.submitAll():
                QtWidgets.QMessageBox.warning(self, "Ошибка", 
                    f"Не удалось удалить: {self.orders_model.lastError().text()}")
            else:
                # После удаления обновляем состав (если удалён последний заказ)
                self.detail_model.setFilter("order_id = -1")
                self.detail_model.select()

    def save(self):
        """Принудительное сохранение (если стратегия не OnFieldChange)"""
        if not self.orders_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка", 
                f"Ошибка сохранения заказов: {self.orders_model.lastError().text()}")
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка", 
                f"Ошибка сохранения состава: {self.detail_model.lastError().text()}")

    def add_detail(self):
        """Добавляет позицию в состав текущего заказа"""
        current = self.tw_orders.currentIndex()
        if not current.isValid():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Сначала выберите заказ")
            return
        order_id = self.orders_model.index(current.row(), 0).data()
        if not order_id:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось определить заказ")
            return
        row = self.detail_model.rowCount()
        if not self.detail_model.insertRow(row):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось добавить позицию")
            return
        self.detail_model.setData(self.detail_model.index(row, 3), order_id)  # order_id
        self.detail_model.setData(self.detail_model.index(row, 1), 1)         # количество по умолчанию
        # Устанавливаем первый товар из списка (если есть)
        rel_model = self.detail_model.relationModel(2)
        if rel_model and rel_model.rowCount() > 0:
            first_product_id = rel_model.index(0, 0).data()
            self.detail_model.setData(self.detail_model.index(row, 2), first_product_id)
        self.tw.scrollToBottom()

    def delete_detail(self):
        """Удаляет выбранную позицию из состава"""
        current = self.tw.currentIndex()
        if not current.isValid():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите позицию для удаления")
            return
        row = current.row()
        self.detail_model.removeRow(row)
        if not self.detail_model.submitAll():
            QtWidgets.QMessageBox.warning(self, "Ошибка", 
                f"Не удалось удалить: {self.detail_model.lastError().text()}")
        else:
            self.detail_model.select()

    def apply_id_filter(self):
        """Поиск заказа по ID"""
        id_str = self.le_search.text().strip()
        if id_str:
            try:
                order_id = int(id_str)
                self.orders_model.setFilter(f"order_id = {order_id}")
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите число (ID заказа)")
                return
        else:
            self.orders_model.setFilter("")
        self.orders_model.select()
        # После фильтрации выделяем первый заказ (если есть)
        if self.orders_model.rowCount() > 0:
            first_idx = self.orders_model.index(0, 0)
            self.tw_orders.setCurrentIndex(first_idx)
            self.on_order_selected(first_idx)
        else:
            self.detail_model.setFilter("order_id = -1")
            self.detail_model.select()
            if hasattr(self, 'le_phone'):
                self.le_phone.clear()

    def make_report(self):
        QtWidgets.QMessageBox.information(self, "Отчёт", "Функция отчёта будет реализована позже.")

    def return_to_menu(self):
        self.main_menu.move(self.pos())
        self.main_menu.show()
        self.close()