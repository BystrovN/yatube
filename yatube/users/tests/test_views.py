from django import forms
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField

User = get_user_model()


class UsersViewsTests(TestCase):
    """Тестируем Views приложения Users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersViewsTests.user)

    def test_pages_users_uses_correct_template(self):
        """
        Проверяем, что namespace:name использует соответствующий шаблон.
        """
        templates_page_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:password_change'):
            'users/password_change_form.html',
            reverse('users:password_change_done'):
            'users/password_change_done.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse('users:password_reset_done'):
            'users/password_reset_done.html',
            reverse(
                'users:password_reset_email',
                args={'<uidb64>', '<token>'}
            ):
            'users/password_reset_confirm.html',
            reverse('users:password_reset_email_done'):
            'users/password_reset_complete.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_forms_correct_context(self):
        """
        Проверяем, что шаблон signup сформирован с правильным контекстом.
        """
        response = self.guest_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': UsernameField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
