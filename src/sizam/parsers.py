import logging
from typing import NamedTuple, Optional

from openpyxl import load_workbook


logger = logging.getLogger(__name__)


class UnitWithCourse(NamedTuple):
    unit_id: int
    course_id: int


class InvalidHeader(Exception):
    'Неверный формат первой строки в файле'


def get_data(
        path: str,
        sheet: Optional[str] = None,
) -> list[UnitWithCourse]:
    workbook = load_workbook(path, read_only=True)
    if sheet is None:
        worksheet = workbook.active
    else:
        worksheet = workbook[sheet]

    it = worksheet.iter_rows(values_only=True)

    header = next(it)
    if not any(header):
        raise InvalidHeader("Первая строка не найдена")

    header_template = ["unti_id", "course_id"]

    if [v.lower() for v in header] != header_template:
        raise InvalidHeader("Формат первой строки не соответствует шаблону: %s" % ", ".join(header_template))

    result = []
    for row in it:
        result.append(
            UnitWithCourse(unit_id=int(row[0]), course_id=int(row[1]))
        )
    return result
