# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group, Permission
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from djangosanetesting.cases import DatabaseTestCase

from ella.core.models import Category, Author
from ella.articles.models import Article, ArticleContents

from ella.newman.models import CategoryUserRole
from ella.newman.models import has_category_permission, has_object_permission, compute_applicable_categories
from ella.newman.models import applicable_categories, permission_filtered_model_qs, is_category_fk, model_category_fk, model_category_fk_value

class UserWithPermissionTestCase(DatabaseTestCase):

    def setUp(self):
        super(UserWithPermissionTestCase, self).setUp()

        self.site = Site.objects.get(name='example.com')

        self.user = User.objects.create(
            username='newman',
            first_name='Paul',
            last_name='Newman',
            email='',
            is_active=True,
            is_staff=True,
            is_superuser=False
        )

        self.author = Author.objects.create(name='igorko', slug='igorko')

        self.create_categories()
        self.create_permissions()
        self.create_groups()
        self.create_roles()

    def create_categories(self):
        site = self.site
        # Category Tree A
        self.category_top_level = Category.objects.create(slug='a0-top', title='a0 top', description='A top category', site=site)
        self.nested_first_level = Category.objects.create(
            tree_parent=self.category_top_level,
            slug='a1-first-nested-level',
            title='a1 first nested level',
            description='nested',
            site=site
        )
        self.nested_first_level_two = Category.objects.create(
            tree_parent=self.category_top_level,
            slug='a2-first-nested-level',
            title='a2 first nested level',
            description='nested',
            site=site
        )
        self.nested_second_level = Category.objects.create(
            tree_parent=self.nested_first_level,
            slug='a4-second-nested-level',
            title='a4 second nested level',
            description='nested',
            site=site
        )
        self.nested_second_level_two = Category.objects.create(
            tree_parent=self.nested_first_level_two,
            slug='a5-second-nested-level',
            title='a5 second nested level',
            description='nested',
            site=site
        )

        self.categories = [self.category_top_level, self.nested_first_level, self.nested_first_level_two, self.nested_second_level, self.nested_second_level_two]

    def create_permissions(self):
        self.article_ct = ContentType.objects.get_for_model(Article)
        for i in ['view']:
            setattr(self, "permission_%s_article" % i, Permission.objects.create(content_type=self.article_ct, codename='%s_article' % i, name="Can view aritcle"))

    def create_groups(self):
        self.group_vca = Group.objects.create(name=u'Permission Group: View, Change, Add')
        for perm in ["view", "change", "add"]:
            self.group_vca.permissions.add(Permission.objects.get(content_type=self.article_ct, codename="%s_article" % perm))
        self.group_vca.save()

        self.group_all = Group.objects.create(name=u'Permission Group: Do Whatever Ya Want')
        for perm in ["view", "change", "add", "delete"]:
            self.group_all.permissions.add(Permission.objects.get(content_type=self.article_ct, codename="%s_article" % perm))
        self.group_all.save()


    def create_roles(self):
        self.role_vca = CategoryUserRole(user=self.user)
        self.role_vca.group = self.group_vca
        self.role_vca.save()
        self.role_vca.category.add(self.nested_first_level_two)
        self.role_vca.save()

        self.role_all = CategoryUserRole(user=self.user)
        self.role_all.group = self.group_all
        self.role_all.save()
        self.role_all.category.add(self.nested_second_level_two)
        self.role_all.save()

    def _create_author_and_article(self):
        article = Article.objects.create(title=u'Testable rabbit', perex=u'Perex', category=self.nested_first_level_two)
        ArticleContents.objects.create(title=u'Testable rabbit, 你好', content=u'Long vehicle', article=article)
        article.authors.add(self.author)
        article.save()
        self.assert_equals(1, Article.objects.count())

        return article

class TestArticleForeignKeys(UserWithPermissionTestCase):

    def setUp(self):
        super(TestArticleForeignKeys, self).setUp()
        self.article_fields = dict([(field.name, field) for field in Article._meta.fields])

    def test_is_category_fk_success(self):
        self.assert_true(is_category_fk(self.article_fields['category']))

    def test_is_category_fk_title_not_fk(self):
        self.assert_false(is_category_fk(self.article_fields['title']))

    def test_model_category_fk_from_article(self):
        self.assert_equals(self.article_fields['category'], model_category_fk(Article))

    def test_model_category_fk_from_contents(self):
        self.assert_equals(None, model_category_fk(ArticleContents))

    def test_model_category_fk_value_parent_category_value(self):
        self.assert_equals(self.nested_first_level, model_category_fk_value(self.nested_second_level))

class TestCategoryPermissions(UserWithPermissionTestCase):

    def test_denormalized_applicable_categories_same_as_computed_ones(self):
        # test applicable_categories() compare results of  compute_applicable_categories
        computed_categories = compute_applicable_categories(self.user)
        computed_categories.sort()

        denormalized_categories = applicable_categories(self.user)
        denormalized_categories.sort()

        self.assert_equals(computed_categories, denormalized_categories)

    def test_denormalized_applicable_categories_same_as_computed_ones_using_permissions(self):
        computed_categories = compute_applicable_categories(self.user, 'articles.view_article')
        computed_categories.sort()

        denormalized_categories = applicable_categories(self.user, 'articles.view_article')
        denormalized_categories.sort()

        self.assert_equals(computed_categories, denormalized_categories)

    def test_applicable_categories_for_user(self):
        categories = applicable_categories(self.user)
        # we expect category from roles + nested ones
        expected_categories = [self.nested_first_level_two.pk, self.nested_second_level_two.pk]

        self.assert_equals(expected_categories, categories)

    def test_applicable_categories_for_user_permission_view(self):
        categories = applicable_categories(self.user, 'articles.view_article')
        # we expect category from roles + nested ones
        expected_categories = [self.nested_first_level_two.pk, self.nested_second_level_two.pk]

        self.assert_equals(expected_categories, categories)

    def test_applicable_categories_for_user_permission_delete(self):
        categories = applicable_categories(self.user, 'articles.delete_article')
        self.assert_equals(self.nested_second_level_two.pk, categories[0])

    def test_has_category_permission_success(self):
        self.assert_true(has_category_permission(self.user, self.nested_second_level_two, 'articles.view_article'))
        self.assert_true(has_category_permission(self.user, self.nested_second_level_two, 'articles.add_article'))
        self.assert_true(has_category_permission(self.user, self.nested_second_level_two, 'articles.change_article'))
        self.assert_true(has_category_permission(self.user, self.nested_second_level_two, 'articles.delete_article'))

    def test_has_category_permission_invalid_permission_name(self):
        self.assert_false(has_category_permission(self.user, self.nested_second_level_two, 'articles.nonexistent'))

    def test_has_category_permission_permission_not_given(self):
        self.assert_false(has_category_permission(self.user, self.nested_first_level_two, 'articles.delete_article'))

class TestObjectPermission(UserWithPermissionTestCase):

    def test_has_object_permission_success(self):
        article = self._create_author_and_article()
        # test
        self.assert_true(has_object_permission(self.user, article, 'articles.view_article'))
        self.assert_true(has_object_permission(self.user, article, 'articles.change_article'))
        self.assert_true(has_object_permission(self.user, article, 'articles.add_article'))

    def test_has_object_permission_not_given(self):
        article = self._create_author_and_article()
        self.assert_false(has_object_permission(self.user, article, 'articles.delete_article'))

class TestAdminChangelistQuerySet(UserWithPermissionTestCase):

    def test_only_viewable_articles_retrieved(self):
        # article1
        accessible_article = Article.objects.create(title=u'Testable rabbit', perex='Perex', category=self.nested_first_level_two)
        accessible_article.authors.add(self.author)
        accessible_article.save()

        inaccessible_article = Article.objects.create(title='Lost rabbit', perex='Perex', category=self.nested_first_level)
        inaccessible_article.authors.add(self.author)
        inaccessible_article.save()

        # test
        filtered_qs = permission_filtered_model_qs(
            Article.objects.all(),
            self.user,
            ['articles.view_article', 'articles.change_article']
        )

        available_articles = list(filtered_qs.all())

        self.assert_equals(accessible_article, available_articles[0])
        self.assert_equals(1, len(available_articles))

