from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    current_year = int(datetime.today().strftime('%Y'))
    return {
        'year': current_year,
    }
