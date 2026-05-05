from html import escape

from PyQt6 import QtWidgets
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtSql import QSqlQuery


class ReportWindow(QtWidgets.QDialog):
    def __init__(self, title, html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 650)
        self.html = html

        self.viewer = QtWidgets.QTextBrowser(self)
        self.viewer.setOpenExternalLinks(False)
        self.viewer.setHtml(html)

        self.b_save = QtWidgets.QPushButton("Сохранить в PDF", self)
        self.b_close = QtWidgets.QPushButton("Закрыть", self)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.b_save)
        buttons.addWidget(self.b_close)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.viewer)
        layout.addLayout(buttons)

        self.b_save.clicked.connect(self.save_pdf)
        self.b_close.clicked.connect(self.close)

    def save_pdf(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт",
            f"{self.windowTitle()}.pdf",
            "PDF files (*.pdf)",
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)

        document = QTextDocument()
        document.setHtml(self.html)
        document.print(printer)
        QtWidgets.QMessageBox.information(self, "Готово", f"Отчёт сохранён:\n{path}")


def table_html(title, headers, rows):
    header_cells = "".join(f"<th>{escape(str(header))}</th>" for header in headers)
    body = []
    for row in rows:
        cells = "".join(f"<td>{escape('' if value is None else str(value))}</td>" for value in row)
        body.append(f"<tr>{cells}</tr>")

    if not body:
        body.append(f"<tr><td colspan='{len(headers)}'>Нет данных</td></tr>")

    return f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: Arial, sans-serif; color: #202124; }}
        h1 {{ font-size: 22px; margin-bottom: 8px; }}
        .meta {{ color: #5f6368; margin-bottom: 18px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th {{ background: #f1f3f4; font-weight: bold; }}
        th, td {{ border: 1px solid #dadce0; padding: 7px 9px; text-align: left; }}
        tr:nth-child(even) td {{ background: #fafafa; }}
      </style>
    </head>
    <body>
      <h1>{escape(title)}</h1>
      <div class="meta">Сформировано из текущих данных базы</div>
      <table>
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{"".join(body)}</tbody>
      </table>
    </body>
    </html>
    """


def show_report(parent, title, headers, rows):
    window = ReportWindow(title, table_html(title, headers, rows), parent)
    window.show()
    return window


def query_rows(sql, params=None):
    query = QSqlQuery()
    if params:
        query.prepare(sql)
        for value in params:
            query.addBindValue(value)
        ok = query.exec()
    else:
        ok = query.exec(sql)

    if not ok:
        raise RuntimeError(query.lastError().text())

    rows = []
    while query.next():
        rows.append([query.value(index) for index in range(query.record().count())])
    return rows


def model_rows(model, columns):
    rows = []
    for row in range(model.rowCount()):
        rows.append([model.index(row, column).data() for column, _ in columns])
    return rows
