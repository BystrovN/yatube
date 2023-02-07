from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class UsersURLTests(TestCase):
    """Тестируем URLs приложения Users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_urls_users_uses_correct_template(self):
        """
        Проверяем, что URL-адрес использует соответствующий шаблон.
        """
        templates_url_names = {
            '/auth/signup/': 'users/signup.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
            'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_users_pages(self):
        """
        Проверяем, что страницы /auth/signup/, /auth/logout/,
        /auth/login/, '/auth/password_reset/', '/auth/password_reset/done/',
        '/auth/reset/<uidb64>/<token>/' и '/auth/reset/done/' доступны
        любому пользователю.
        """
        url_httpstat = {
            '/auth/signup/',
            '/auth/logout/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/<uidb64>/<token>/',
            '/auth/reset/done/',
        }
        for url in url_httpstat:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change_pages(self):
        """
        Проверяем, что страницы /auth/password_change/ и
        '/auth/password_change/done/' доступны авторезированному пользователю.
        """
        urls = {
            '/auth/password_change/',
            '/auth/password_change/done/',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_edit_redirect(self):
        """
        Проверяем, что неавторизованный пользователь перенаправляется
        со страниц смены пароля на страницу логина.
        """
        url_redirect = {
            '/auth/password_change/':
            '/auth/login/?next=/auth/password_change/',
            '/auth/password_change/done/':
            '/auth/login/?next=/auth/password_change/done/',
        }
        for url, redirect in url_redirect.items():
            response = self.guest_client.get(url, follow=True)
            self.assertRedirects(response, redirect)
