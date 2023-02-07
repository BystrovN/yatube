from http import HTTPStatus

from django.shortcuts import render


def page_not_found(request, exception):
    """Ошибка 404."""
    context = {
        'path': request.path
    }
    return render(
        request,
        'core/404.html',
        context, status=HTTPStatus.NOT_FOUND
    )


def csrf_failure(request, reason=''):
    """Ошибка 403 (csrf)."""
    return render(request, 'core/403csrf.html')


def server_error(request):
    """Ошибка 500."""
    return render(
        request,
        'core/500.html',
        status=HTTPStatus.INTERNAL_SERVER_ERROR
    )


def permission_denied(request, exception):
    """Ошибка 403."""
    return render(
        request,
        'core/403.html',
        status=HTTPStatus.FORBIDDEN
    )
