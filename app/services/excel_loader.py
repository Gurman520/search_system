import os
from typing import List, Dict, Any, Optional, Tuple
import openpyxl
import xlrd

def read_excel_preview(file_path: str, sheet_name: Optional[str] = None) -> Tuple[List[str], List[List[Any]]]:
    """
    Читает все строки из указанного листа Excel-файла.
    Возвращает список названий листов и данные: (sheet_names, rows)
    Если sheet_name не указан, берётся первый лист.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.xlsx':
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet_names = wb.sheetnames
        if not sheet_name:
            sheet_name = sheet_names[0]
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
        wb.close()
        return sheet_names, rows
    elif ext == '.xls':
        wb = xlrd.open_workbook(file_path)
        sheet_names = wb.sheet_names()
        if not sheet_name:
            sheet_name = sheet_names[0]
        ws = wb.sheet_by_name(sheet_name)
        rows = []
        for i in range(ws.nrows):
            row = [ws.cell_value(i, j) for j in range(ws.ncols)]
            rows.append(row)
        return sheet_names, rows
    else:
        raise ValueError("Unsupported file format")

def parse_excel_data(
    file_path: str,
    sheet_name: str,
    start_row: int,
    end_row: int,
    article_col: int,
    article_internal_col: int,
    price_col: Optional[int],
    price_cut_col: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Читает данные из Excel, начиная с start_row и заканчивая end_row (включительно).
    Нумерация строк с 1. Возвращает список словарей с ключами 'article', 'article_internal_col', 'price', 'price_cut'.
    Проверяет дубликаты артикулов.
    """
    ext = os.path.splitext(file_path)[1].lower()
    products = []
    seen_articles = set()
    seen_inter_articles = set()

    # Проверка корректности диапазона
    if start_row > end_row:
        raise ValueError("Начальная строка больше конечной")

    if ext == '.xlsx':
        wb = None
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb[sheet_name]
            # openpyxl нумерует строки с 1, можно использовать max_row для ограничения
            rows_iter = ws.iter_rows(min_row=start_row, max_row=end_row, values_only=True)
            for row in rows_iter:
                if not row:
                    continue
                article = row[article_col] if article_col < len(row) else None
                if article is None or str(article).strip() == '':
                    continue
                article_str = str(article).strip()
                if article_str in seen_articles:
                    raise ValueError(f"Дубликат артикула: {article_str}")
                seen_articles.add(article_str)

                article_inter = row[article_internal_col] if article_internal_col < len(row) else None
                if article_inter is None or str(article_inter).strip() == '':
                    continue
                article_inter_str = str(article_inter).strip()
                if article_inter_str in seen_inter_articles:
                    raise ValueError(f"Дубликат внутреннего артикула: {article_inter_str}")
                seen_inter_articles.add(article_inter_str)

                price = None
                if price_col is not None and price_col < len(row):
                    price_val = row[price_col]
                    if price_val is not None and str(price_val).strip() != '':
                        try:
                            price = float(str(price_val).replace(',', '.').replace(' ', ''))
                        except:
                            price = None

                price_cut = None
                if price_cut_col is not None and price_cut_col < len(row):
                    price_cut_val = row[price_cut_col]
                    if price_cut_val is not None and str(price_cut_val).strip() != '':
                        try:
                            price_cut = float(str(price_cut_val).replace(',', '.').replace(' ', ''))
                        except:
                            price_cut = None

                products.append({'article': article_str, 'article_internal_col': article_inter_str, 'price': price, 'price_cut': price_cut})
        finally:
            if wb is not None:
                wb.close()
    elif ext == '.xls':
        wb = xlrd.open_workbook(file_path)
        ws = wb.sheet_by_name(sheet_name)
        # xlrd нумерует с 0, поэтому start_row-1, end_row-1
        for i in range(start_row - 1, end_row):  # до end_row включительно
            if i >= ws.nrows:
                break
            row = [ws.cell_value(i, j) for j in range(ws.ncols)]
            article = row[article_col] if article_col < len(row) else None
            if article is None or str(article).strip() == '':
                continue
            article_str = str(article).strip()
            if article_str in seen_articles:
                raise ValueError(f"Дубликат артикула: {article_str}")
            seen_articles.add(article_str)

            article_inter = row[article_internal_col] if article_internal_col < len(row) else None
            if article_inter is None or str(article_inter).strip() == '':
                continue
            article_inter_str = str(article_inter).strip()
            if article_inter_str in seen_inter_articles:
                raise ValueError(f"Дубликат внутреннего артикула: {article_inter_str}")
            seen_inter_articles.add(article_inter_str)

            price = None
            if price_col is not None and price_col < len(row):
                price_val = row[price_col]
                if price_val is not None and str(price_val).strip() != '':
                    try:
                        price = float(str(price_val).replace(',', '.').replace(' ', ''))
                    except:
                        price = None

            price_cut = None
            if price_cut_col is not None and price_cut_col < len(row):
                price_cut_val = row[price_cut_col]
                if price_cut_val is not None and str(price_cut_val).strip() != '':
                    try:
                        price_cut = float(str(price_cut_val).replace(',', '.').replace(' ', ''))
                    except:
                        price_cut = None

            products.append({'article': article_str, 'article_internal_col': article_inter_str, 'price': price, 'price_cut': price_cut})
    else:
        raise ValueError("Unsupported file format")

    return products