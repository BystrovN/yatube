from django.core.paginator import Paginator

PAGE_NOTES_LIMIT: int = 10


def paginator_form(request, posts):
    """Форматирует паджинацию страницы."""
    paginator = Paginator(posts, PAGE_NOTES_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
