from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='author_test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст для проверки __str__',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post,
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )

    def test_models_have_correct_field_str(self):
        """__str__ совпадает с ожидаемым."""
        group = self.group
        post = self.post
        comment = self.comment
        follow = self.follow
        expected_str_group = group.title
        expected_str_post = post.text[:15]
        expected_str_comment = comment.text[:15]
        expected_str_follow = f'{self.user} подписан на {self.author}'
        self.assertEqual(expected_str_group, str(group))
        self.assertEqual(expected_str_post, str(post))
        self.assertEqual(expected_str_comment, str(comment))
        self.assertEqual(expected_str_follow, str(follow))

    def test_models_have_correct_object_names(self):
        """verbose_name совпадает с ожидаемым."""
        group = self.group
        post = self.post
        comment = self.comment
        follow = self.follow
        verbose_group = group._meta.get_field('title').verbose_name
        verbose_post = post._meta.get_field('text').verbose_name
        verbose_comment = comment._meta.get_field('author').verbose_name
        verbose_follow = follow._meta.get_field('user').verbose_name
        self.assertEqual(verbose_group, 'Заголовок')
        self.assertEqual(verbose_post, 'Текст')
        self.assertEqual(verbose_comment, 'Комментатор')
        self.assertEqual(verbose_follow, 'Подписчик')
