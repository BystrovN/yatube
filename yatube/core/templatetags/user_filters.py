from django import template


register = template.Library()


@register.filter
def addclass(field, css):
    """
    Добавляет атрибут class="form-control" к полю.
    Говорят, без него тоскуют фронтендеры.
    """
    return field.as_widget(attrs={'class': css})
