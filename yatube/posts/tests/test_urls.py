from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
from ..models import Group, Post
from django.urls import reverse

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        cls.author = User.objects.create_user(username='test_author')
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
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_templates(self):
        """Доступность страниц всем пользователям и соответсвие шаблонов"""
        url_names = {'/': 'posts/index.html',
                     f'/group/{self.group.slug}/': 'posts/group_list.html',
                     f'/profile/{self.user.username}/': 'posts/profile.html',
                     f'/posts/{self.post.id}/': 'posts/post_detail.html',
                     }

        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                cache.clear()
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_templates_authorized(self):
        """Доступность create авторизованным юзерам и соответсвие шаблона"""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_templates_author(self):
        """Доступность edit автору и соответсвие шаблона"""
        response = self.author_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_found(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_comment(self):
        """Доступность comment разным типам пользователей"""
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.author_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.authorized_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_follow(self):
        """Доступность follow разным типам пользователей"""
        response = self.guest_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.author_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_unfollow(self):
        """Доступность unfollow разным типам пользователей"""
        response = self.guest_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.author_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_follow_index(self):
        """Доступность follow_index разным типам пользователей"""
        response = self.authorized_client.get('/follow/')
        self.assertTemplateUsed(response, 'posts/follow.html')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.author_client.get('/follow/')
        self.assertTemplateUsed(response, 'posts/follow.html')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
