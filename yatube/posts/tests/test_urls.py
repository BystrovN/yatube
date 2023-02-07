from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    """Тестируем URLs приложения Posts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.another_user = User.objects.create_user(username='another')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.authorized_client_another = Client()
        self.authorized_client_another.force_login(PostURLTests.another_user)
        self.post_id = PostURLTests.post.id
        self.username = PostURLTests.post.author.username
        cache.clear()

    def test_pages(self):
        """
        Проверяем, что страницы:
            1. Главная страница (index)
            2. Определенной группы (group_list)
            3. Пользователя (profile)
            4. Просмотра поста (post_detail)
            5. Несуществующая страница
        доступны любому пользователю.
        """
        url_httpstat = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.username}/': HTTPStatus.OK,
            f'/posts/{self.post_id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, http in url_httpstat.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, http)

    def test_post_create_edit_page(self):
        """
        Проверяем, что страницы:
            1. Создания поста (post_create)
            2. Редактирования поста (post_edit)
            3. Подписок пользователя (follow_index)
        доступны авторизованному пользователю.
        Для страницы редактирования и удаления пользователь - автор поста.
        """
        urls = {
            '/create/',
            f'/posts/{self.post_id}/edit/',
            '/follow/',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauth_redirect(self):
        """
        Проверяем редиректы неавторизованного пользователя.
        """
        url_redirect = {
            '/create/': '/auth/login/?next=/create/',
            '/follow/': '/auth/login/?next=/follow/',
            f'/posts/{self.post_id}/edit/':
                f'/auth/login/?next=/posts/{self.post_id}/edit/',
            f'/posts/{self.post_id}/comment/':
                f'/auth/login/?next=/posts/{self.post_id}/comment/',
            f'/profile/{self.username}/follow/':
                f'/auth/login/?next=/profile/{self.username}/follow/',
            f'/profile/{self.username}/unfollow/':
                f'/auth/login/?next=/profile/{self.username}/unfollow/',
            f'/posts/{self.post_id}/delete/':
                f'/auth/login/?next=/posts/{self.post_id}/delete/',
            f'/profile/{self.username}/delete/':
                f'/auth/login/?next=/profile/{self.username}/delete/',
        }
        for url, redirect in url_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_post_edit_delete_redirect(self):
        """
        Проверяем, что не автор перенаправляется со страницы редактирования
        и удаления на страницу просмотра поста.
        """
        urls = {
            f'/posts/{self.post_id}/edit/',
            f'/posts/{self.post_id}/delete/'
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client_another.get(url, follow=True)
                self.assertRedirects(response, f'/posts/{self.post_id}/')

    def test_user_delete_redirect(self):
        """
        Проверяем, что другой пользователь перенаправляется со страницы
        удаления на страницу просмотра аккаунта.
        """
        response = self.authorized_client_another.get(
            f'/profile/{self.username}/delete/',
            follow=True
        )
        self.assertRedirects(response, f'/profile/{self.username}/')

    def test_urls_uses_correct_template(self):
        """
        Проверяем, что URL-адрес использует соответствующий шаблон.
        """
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post_id}/':
                'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post_id}/edit/':
                'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
