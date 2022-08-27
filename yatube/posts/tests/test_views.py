from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus
from ..models import Follow, Group, Post

User = get_user_model()
count_posts_for_tests: int = 13


class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='tester')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.group_url = ('posts:group_list', 'group_list.html', {
            'slug': cls.group.slug
        })

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'pk': self.post.pk}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                if reverse_name not in ('/create/',
                                        f'/posts/{self.post.pk}/edit/',
                                        '/follow/'):
                    cache.clear()
                    response = self.guest_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def check_context_page_or_post(self, context):
        self.assertIn('page_obj', context)
        post = context['page_obj'][0]
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))

        self.check_context_page_or_post(context=response.context)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        url, _, kwargs = self.group_url

        response = self.guest_client.get(reverse(url, kwargs=kwargs))
        self.check_context_page_or_post(context=response.context)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.check_context_page_or_post(context=response.context)
        author = response.context['author']
        self.assertEqual(author, self.user)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.context.get('post').author, self.user)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(
            response.context.get('post').pub_date, self.post.pub_date)
        post_id = response.context['post'].pk
        self.assertEqual(post_id, self.post.pk)

    def test_post_create_pages_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_field = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'pk': self.post.pk}))
        form_field = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        post_id = response.context['post'].pk
        self.assertEqual(post_id, self.post.pk)

    def test_index_cache(self):
        """Проверка кеширования главной страницы"""
        self.post = Post.objects.create(
            text="Текста поста для теста кеша",
            author=self.user,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_context_page_or_post(context=response.context)
        Post.objects.filter(id=self.post.pk).delete()
        cached_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cached_response.content)
        cache.clear()
        after_clear_response = self.authorized_client.get(
            reverse('posts:index'))
        self.assertNotEqual(cached_response.content,
                            after_clear_response.content)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='tester')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.posts = [
            Post(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
            ) for _ in range(count_posts_for_tests)
        ]
        Post.objects.bulk_create(cls.posts)
        cls.names_pages = {
            reverse('posts:index'):
                'index',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}):
                ('group_list'),
            reverse('posts:profile', kwargs={'username': cls.user}):
                ('profile'),
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Тест паджинатора первой страницы"""
        for reverse_name, _ in self.names_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Тест паджинатора второй страницы"""
        for reverse_name, _ in self.names_pages.items():
            cache.clear()
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(
                    reverse('posts:index') + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='tester')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_system_authorized_user(self):
        """Авторизованный пользователь может подписываться и отписываться"""

        following_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), following_count + 1)
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), following_count)

    def test_follow_system_unauthorized_user(self):
        """Неавторизованный пользователь не может подписываться"""

        following_count = Follow.objects.count()
        response = self.guest_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), following_count)
        response = self.guest_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), following_count)

    def test_follow_system_author_user(self):
        """Автор не может подписываться на самого себя"""

        following_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), following_count)
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), following_count)
