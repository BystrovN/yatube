from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class AboutURLTests(TestCase):
    """Тестируем URLs приложения About."""

    def setUp(self):
        self.guest_client = Client()

    def test_static_pages(self):
        """
        Проверяем, что страницы /about/tech/ и /about/author/ доступны.
        """
        urls = {'/about/tech/', '/about/author/'}
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_static_pages_template(self):
        """
        Проверяем, что URL-адрес использует соответствующий шаблон.
        """
        templates_url_names = {
            '/about/tech/': 'about/tech.html',
            '/about/author/': 'about/author.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)


class PostViewsTests(TestCase):
    """Тестируем Views приложения About."""

    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """
        Проверяем, что namespace:name использует соответствующий шаблон.
        """
        templates_page_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
