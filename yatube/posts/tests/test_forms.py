import shutil
import tempfile

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from ..forms import PostForm, CommentForm
from ..models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

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
        cls.form = PostForm()
        # cls.comment = Comment.objects.create(
        #     text='Тестовый комментарий'
        # )
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_authorized_user(self):
        """Авторизованный пользователь создает запись."""

        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': 1,
            'image': uploaded,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.gif'
            ).exists())

    def test_edit_post_authorized_user(self):
        """Авторизованный пользователь редактирует запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': 1,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'pk': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
            ).exists())

    def test_create_post_unauthorized_user(self):
        """Неавторизованный пользователь создает запись."""
        posts_count = Post.objects.count()
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_unauthorized_user(self):
        """Невторизованный пользователь редактирует запись."""
        posts_count = Post.objects.count()
        response = self.guest_client.get(
            reverse('posts:post_edit', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), posts_count)

    # def test_create_comment_authorized_user(self):
    #     """Авторизованный пользователь комментирует пост"""
    #     comments_count = Comment.objects.count()
    #     form_data = {
    #         'text': 'Измененный текст',
    #         'group': 1,
    #     }
    #     response = self.authorized_client.post(
    #         reverse('posts:post_edit', kwargs={'pk': self.post.pk}),
    #         data=form_data,
    #         follow=True
    #     )
    #     self.assertRedirects(
    #         response,
    #         reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
    #     self.assertEqual(Post.objects.count(), posts_count)
    #     self.assertTrue(
    #         Post.objects.filter(
    #             text=form_data['text'],
    #             group=form_data['group'],
    #         ).exists())