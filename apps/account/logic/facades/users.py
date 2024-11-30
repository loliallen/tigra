import io

import xlwt

from apps.account.logic.selectors.users import users_with_visits


def make_report() -> io.BytesIO:
    qs = (
        users_with_visits().values_list(
            "username",
            "phone",
            "email",
            "children__name",
            "children__birth_date",
            "children__age",
            "visits_count",
            "last_visit",
            "last_mobile_app_visit_date",
            "date_joined"
        )
    )
    wb = xlwt.Workbook()
    sheet = wb.add_sheet('Отчет')

    header = [
        "Фио",
        "Телефон",
        "Email",
        "Имя ребенка",
        "Дата рождения ребенка",
        "Возраст ребенка",
        "Количество визитов",
        "Последний визит",
        "Последний вход в мобильное приложение",
        "Дата регистрации",
    ]
    for column, heading in enumerate(header):
        sheet.write(0, column, heading)

    for row_id, row in enumerate(qs, start=1):
        for column, value in enumerate(row):
            sheet.write(row_id, column, str(value))

    f = io.BytesIO()
    wb.save(f)
    return f
