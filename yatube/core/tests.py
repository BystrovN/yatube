from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    """Тестируем Views приложения Core."""

    def test_error_page(self):
        """Проверяем корректность кода ошибки 404 и используемый шаблон."""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
