from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
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

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

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
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_found(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
