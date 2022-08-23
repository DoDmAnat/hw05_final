from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для проверки __str__',
        )

    def test_models_have_correct_field_str(self):
        """__str__ совпадает с ожидаемым."""
        group = PostModelTest.group
        post = PostModelTest.post
        expected_str_group = group.title
        expected_str_post = post.text[:15]
        self.assertEqual(expected_str_group, str(group))
        self.assertEqual(expected_str_post, str(post))

    def test_models_have_correct_object_names(self):
        """verbose_name совпадает с ожидаемым."""
        group = PostModelTest.group
        post = PostModelTest.post
        verbose_group = group._meta.get_field('title').verbose_name
        verbose_post = post._meta.get_field('text').verbose_name
        self.assertEqual(verbose_group, 'Заголовок')
        self.assertEqual(verbose_post, 'Текст')
