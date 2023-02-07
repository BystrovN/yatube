import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post
from ..utils import PAGE_NOTES_LIMIT

User = get_user_model()

AUTHOR_POST_QUANTITY: int = 15
BULK_CREATE_QUANTITY: int = 3
LAST_ORDER_POST: int = 0
LAST_POST_ID: int = AUTHOR_POST_QUANTITY * BULK_CREATE_QUANTITY
FIRST_COMMENT: int = 0
FIRST_POST_ID: int = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    """Тестируем Views приложения Posts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.follower_user = User.objects.create_user(username='follower')
        cls.following_user = User.objects.create_user(username='following')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_another = Group.objects.create(
            title='Другая тестовая группа',
            slug='test-slug-another',
            description='Другое тестовое описание',
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif',
        )
        Post.objects.bulk_create(
            Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group,
                image=cls.uploaded,
            ) for i in range(AUTHOR_POST_QUANTITY)
        )
        Post.objects.bulk_create(
            Post(
                text=f'Тестовый пост для подписок (follower) {i}',
                author=cls.follower_user,
                group=cls.group,
            ) for i in range(AUTHOR_POST_QUANTITY)
        )
        Post.objects.bulk_create(
            Post(
                text=f'Тестовый пост для подписок (following) {i}',
                author=cls.following_user,
                group=cls.group,
            ) for i in range(AUTHOR_POST_QUANTITY)
        )
        cls.comment = Comment.objects.create(
            post=Post.objects.get(id=FIRST_POST_ID),
            author=cls.user,
            text='Тестовый комментарий',
        )
        Follow.objects.create(
            user=cls.follower_user,
            author=cls.following_user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(
            PostViewsTests.follower_user
        )
        self.authorized_client_following = Client()
        self.authorized_client_following.force_login(
            PostViewsTests.following_user
        )
        cache.clear()

    def test_pages_uses_correct_template(self):
        """
        Проверяем, что namespace:name использует соответствующий шаблон.
        """
        test_post = Post.objects.get(id=FIRST_POST_ID)
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': test_post.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': test_post.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': test_post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': test_post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_views_forms_correct_context(self):
        """
        Проверяем, что шаблоны post_create и post_edit сформированы с
        правильным контекстом.
        """
        test_post = Post.objects.get(id=FIRST_POST_ID)
        reverses = {
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': test_post.id}
            ),
        }
        for item in reverses:
            response = self.authorized_client.get(item)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_detail_correct_context(self):
        """
        Проверяем, что шаблон post_detail сформирован с правильным контекстом.
        """
        test_post = Post.objects.get(id=FIRST_POST_ID)
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': test_post.id}
            )
        )
        post = response.context.get('post')
        comment = response.context.get('comments')[FIRST_COMMENT]
        form_field = response.context.get('form').fields['text']
        self.assertEqual(post.text, test_post.text)
        self.assertEqual(post.author, test_post.author)
        self.assertEqual(post.image, test_post.image)
        self.assertEqual(comment.text, PostViewsTests.comment.text)
        self.assertIsInstance(form_field, forms.fields.CharField)

    def test_index_correct_context(self):
        """
        Проверяем, что шаблон index сформирован с правильным контекстом.
        """
        test_post = Post.objects.get(id=LAST_POST_ID)
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][LAST_ORDER_POST]
        self.assertEqual(first_object.text, test_post.text)
        self.assertEqual(first_object.author, test_post.author)
        self.assertEqual(first_object.image, test_post.image)

    def test_group_posts_correct_context(self):
        """
        Проверяем, что шаблон group_list сформирован с правильным контекстом.
        """
        test_post = Post.objects.get(id=LAST_POST_ID)
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': test_post.group.slug}
            )
        )
        group = response.context['group']
        first_object = response.context['page_obj'][LAST_ORDER_POST]
        self.assertEqual(group, test_post.group)
        self.assertEqual(first_object.text, test_post.text)
        self.assertEqual(first_object.author, test_post.author)
        self.assertEqual(first_object.image, test_post.image)

    def test_profile_correct_context(self):
        """
        Проверяем, что шаблон profile сформирован с правильным контекстом.
        """
        test_post = Post.objects.get(id=LAST_POST_ID)
        response = self.authorized_client_follower.get(
            reverse(
                'posts:profile',
                kwargs={'username': test_post.author.username}
            )
        )
        users = response.context['users']
        first_object = response.context['page_obj'][LAST_ORDER_POST]
        following = response.context['following']
        self.assertEqual(users, test_post.author)
        self.assertEqual(first_object.text, test_post.text)
        self.assertEqual(first_object.author, test_post.author)
        self.assertEqual(first_object.image, test_post.image)
        self.assertTrue(following)

    def test_paginator(self):
        """
        Проверяем паджинацию шаблонов index, group_list, profile.
        """
        test_post = Post.objects.get(id=LAST_POST_ID)
        reverses = {
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': test_post.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': test_post.author.username}
            )
        }
        for item in reverses:
            with self.subTest(item=item):
                response = self.guest_client.get(item)
                self.assertEqual(
                    len(response.context['page_obj']),
                    PAGE_NOTES_LIMIT
                )

    def test_paginator_follow(self):
        """
        Проверяем паджинацию шаблона follow.
        """
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            len(response.context['page_obj']),
            PAGE_NOTES_LIMIT
        )

    def test_correct_group(self):
        """
        Проверяем, что пост не попал в группу, для которой не был предназначен.
        """
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewsTests.group.slug}
            )
        )
        group = response.context['group']
        self.assertNotEqual(group, PostViewsTests.group_another)

    def test_post_group_exist(self):
        """
        Проверяем наличие поста на страницах index, group_list, profile,
        если при создании указана группа.
        """
        test_post = Post.objects.get(id=LAST_POST_ID)
        reverses = {
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': test_post.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': test_post.author.username}
            )
        }
        for item in reverses:
            with self.subTest(item=item):
                response = self.guest_client.get(item)
                object = response.context['page_obj']
                self.assertTrue(test_post in object)

    def test_add_comment(self):
        """
        Проверяем, что после успешной отправки комментарий появляется на
        странице поста.
        """
        test_post = Post.objects.get(id=FIRST_POST_ID)
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': test_post.id}
            )
        )
        comment = response.context['comments']
        self.assertTrue(PostViewsTests.comment in comment)

    def test_index_cache(self):
        """
        Проверяем кеширование главной страницы.
        """
        test_post = Post.objects.get(id=LAST_POST_ID)
        response_first = self.guest_client.get(reverse('posts:index'))
        test_post.delete()
        response_second = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        response_third = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_first.content, response_third.content)

    def test_profile_follow(self):
        """
        Проверяем подписку на и отписку от авторов.
        """
        user = PostViewsTests.user
        author = PostViewsTests.following_user
        follow_count = Follow.objects.count()
        Follow.objects.create(user=user, author=author)
        exist = user.follower.filter(author=author).exists()
        self.assertTrue(exist)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        Follow.objects.filter(user=user, author=author).delete()
        not_exist = user.follower.filter(author=author).exists()
        self.assertFalse(not_exist)
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow(self):
        """
        Проверяем, что новая запись пользователя появляется только в ленте тех,
        кто на него подписан.
        """
        test_post = Post.objects.filter(
            author=PostViewsTests.following_user
        )[LAST_ORDER_POST]
        response_first = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        response_second = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        object_first = response_first.context['page_obj']
        object_second = response_second.context['page_obj']
        self.assertFalse(test_post in object_first)
        self.assertTrue(test_post in object_second)

    def test_post_delete(self):
        """
        Проверяем удаление поста автором и редирект.
        """
        new_post = Post.objects.create(
            author=PostViewsTests.user,
            text='этот удалим',
        )
        post_count = Post.objects.count()
        response = self.authorized_client.get(
            reverse(
                'posts:post_delete',
                kwargs={'post_id': new_post.id}
            ),
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count - 1)
        self.assertRedirects(response, reverse('posts:index'))

    def test_user_delete(self):
        """
        Проверяем удаление аккаунта автором и редирект.
        """
        new_user = User.objects.create_user(username='for_delete')
        self.new_authorized_client = Client()
        self.new_authorized_client.force_login(new_user)
        user_count = User.objects.count()
        response = self.new_authorized_client.get(
            reverse(
                'posts:user_delete',
                kwargs={'username': new_user.username}
            ),
            follow=True
        )
        self.assertEqual(User.objects.count(), user_count - 1)
        self.assertRedirects(response, reverse('posts:index'))
