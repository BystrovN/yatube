import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image, ImageChops

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
MEDIUM_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    """Тестируем Forms приложения Posts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='another-test-slug',
            description='Другое тестовое описание',
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.another_uploaded = SimpleUploadedFile(
            name='medium.gif',
            content=MEDIUM_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTests.user)

    def test_create_post_form(self):
        """
        Проверяем создание новой записи в модели Post и редирект.
        """
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
            'group': PostFormsTests.group.id,
            'image': PostFormsTests.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostFormsTests.user.username}
            )
        )

    def test_edit_post_form(self):
        """
        Проверяем редактирование записи в модели Post и редирект.
        """
        test_post = PostFormsTests.post
        form_data = {
            'text': 'Изменяем тестовый пост',
            'group': PostFormsTests.another_group.id,
            'image': PostFormsTests.another_uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': test_post.id}),
            data=form_data,
            follow=True
        )
        test_post.refresh_from_db()
        self.assertEqual(test_post.text, list(form_data.values())[0])
        self.assertEqual(test_post.group, PostFormsTests.another_group)
        self.assertIsNone(
            ImageChops.difference(
                Image.open(test_post.image),
                Image.open(PostFormsTests.another_uploaded)
            ).getbbox()
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': test_post.id}
            )
        )

    def test_comment_form(self):
        """
        Проверяем создание новой записи в модели Comment и редирект.
        """
        test_post = PostFormsTests.post
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': test_post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': test_post.id}
            )
        )
