from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UsersFormsTests(TestCase):
    """Тестируем Forms приложения Users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()

    def test_create_user_form(self):
        """
        Проверяем создание новой записи в модели User и редирект.
        """
        users_count = User.objects.count()
        form_data = {
            'first_name': 'ivan',
            'last_name': 'ivanov',
            'username': 'ivaaaan',
            'email': 'ivan@ivan.com',
            'password1': '7851Qtebdxsf.!!t',
            'password2': '7851Qtebdxsf.!!t',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertRedirects(response, reverse('posts:index'))
