from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

from windows.report_window import query_rows, show_report


class AnalyticNav(QtWidgets.QMainWindow):
    def __init__(self, menu=None):
        super().__init__()
        self.main_menu = menu
        self.setWindowTitle("Аналитика")
        self.resize(800, 600)

        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)

        title = QtWidgets.QLabel("Аналитика", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")

        self.b_orders = QtWidgets.QPushButton("Отчёт по заказам", self)
        self.b_categories = QtWidgets.QPushButton("Стоимость категорий", self)
        self.b_products_price = QtWidgets.QPushButton("Товары по возрастанию цены", self)
        self.b_products_year = QtWidgets.QPushButton("Товары, заказанные в течение года", self)
        self.b_products_stats = QtWidgets.QPushButton("Статистика по покупке продуктов", self)
        self.b_exit = QtWidgets.QPushButton("Выйти", self)

        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addSpacing(12)
        layout.addWidget(self.b_orders)
        layout.addWidget(self.b_categories)
        layout.addWidget(self.b_products_price)
        layout.addWidget(self.b_products_year)
        layout.addWidget(self.b_products_stats)
        layout.addStretch()
        layout.addWidget(self.b_exit)

        self.b_orders.clicked.connect(self.report_orders)
        self.b_categories.clicked.connect(self.report_categories)
        self.b_products_price.clicked.connect(self.report_products_by_price)
        self.b_products_year.clicked.connect(self.report_products_ordered_year)
        self.b_products_stats.clicked.connect(self.report_product_purchase_stats)
        self.b_exit.clicked.connect(QtWidgets.QApplication.quit)

    def show_report_or_error(self, title, headers, sql):
        try:
            rows = query_rows(sql)
        except RuntimeError as error:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.report_window = show_report(self, title, headers, rows)

    def report_orders(self):
        self.show_report_or_error(
            "Отчёт по заказам",
            ["№ заказа", "Дата", "Покупатель", "Магазин"],
            """
            SELECT
                o.order_id,
                o.order_date,
                c.surname,
                s.store_name
            FROM orders o
            LEFT JOIN customers c ON c.customer_id = o.customer_id
            LEFT JOIN stores s ON s.store_id = o.store_id
            ORDER BY o.order_id
            """,
        )

    def report_categories(self):
        self.show_report_or_error(
            "Стоимость категорий",
            ["Категория", "Товаров", "Общая стоимость", "Средняя цена"],
            """
            SELECT
                c.category_name,
                COUNT(p.product_id) AS products_count,
                COALESCE(SUM(p.price), 0) AS total_price,
                COALESCE(AVG(p.price), 0) AS average_price
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.category_id
            GROUP BY c.category_id, c.category_name
            ORDER BY total_price DESC, c.category_name
            """,
        )

    def report_products_by_price(self):
        self.show_report_or_error(
            "Товары по возрастанию цены",
            ["Товар", "Цена", "Категория", "Поставщик", "Склад"],
            """
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
            """,
        )

    def report_products_ordered_year(self):
        self.show_report_or_error(
            "Товары, заказанные в течение года",
            ["Товар", "Категория", "Поставщик", "Склад"],
            """
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
            """,
        )

    def report_product_purchase_stats(self):
        self.show_report_or_error(
            "Статистика по покупке продуктов",
            ["Товар", "Куплено шт.", "Заказов", "Сумма"],
            """
            SELECT
                p.product_name,
                COALESCE(SUM(oc.quantity), 0) AS total_quantity,
                COUNT(DISTINCT oc.order_id) AS orders_count,
                COALESCE(SUM(oc.quantity * p.price), 0) AS total_amount
            FROM products p
            LEFT JOIN "orders compositions" oc ON oc.product_id = p.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY total_quantity DESC, p.product_name
            """,
        )
