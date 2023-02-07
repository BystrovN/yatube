from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import SLICE_STOP, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тестируем Models приложения Posts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_post_model_str(self):
        """
        Проверяем, что у модели Post корректно работает __str__.
        """
        test_post = PostModelTest.post
        expected_text = test_post.text[:SLICE_STOP]
        self.assertEqual(
            str(test_post),
            expected_text,
            'Метод __str__ модели Post работает некорректно'
        )

    def test_group_model_str(self):
        """
        Проверяем, что у модели Group корректно работает __str__.
        """
        group = PostModelTest.group
        expected_title = group.title
        self.assertEqual(
            str(group),
            expected_title,
            'Метод __str__ модели Group работает некорректно'
        )

    def test_post_model_verbose_name(self):
        """
        Проверяем, что verbose_name в полях модели Post совпадает с ожидаемым.
        """
        test_post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_post._meta.get_field(field).verbose_name,
                    expected_value,
                    'verbose_name в полях модели Post не совпадает с ожидаемым'
                )

    def test_post_model_help_text(self):
        """
        Проверяем, что help_text в полях модели Post совпадает с ожидаемым.
        """
        test_post = PostModelTest.post
        field_help = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_post._meta.get_field(field).help_text,
                    expected_value,
                    'help_text в полях модели Post не совпадает с ожидаемым'
                )
