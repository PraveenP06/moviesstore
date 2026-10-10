from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from movies.models import Movie
from .models import Item, Order


class TopPurchasingUserAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            'admin', 'admin@example.com', 'password'
        )
        cls.first_user = User.objects.create_user(
            'first', password='password'
        )
        cls.second_user = User.objects.create_user(
            'second', password='password'
        )
        cls.movie = Movie.objects.create(
            name='Example Movie',
            price=10,
            description='Example',
            image='movie_images/example.jpg',
        )
        cls.url = reverse('admin:cart_order_top_purchasing_user')

    def add_purchase(self, user, quantity):
        order = Order.objects.create(
            user=user,
            total=10 * quantity
        )
        Item.objects.create(
            order=order,
            movie=self.movie,
            price=10,
            quantity=quantity
        )

    def test_leader_changes_when_another_user_purchases_more(self):
        self.client.force_login(self.admin_user)

        self.add_purchase(self.first_user, 2)

        response = self.client.get(self.url)

        self.assertEqual(
            response.context['leaders'][0]['order__user__username'],
            'first'
        )
        self.assertEqual(response.context['movies_purchased'], 2)

        self.add_purchase(self.second_user, 3)

        response = self.client.get(self.url)

        self.assertEqual(
            response.context['leaders'][0]['order__user__username'],
            'second'
        )
        self.assertEqual(response.context['movies_purchased'], 3)

    def test_ties_and_staff_purchases(self):
        self.client.force_login(self.admin_user)

        self.add_purchase(self.first_user, 2)
        self.add_purchase(self.second_user, 2)
        self.add_purchase(self.admin_user, 10)

        response = self.client.get(self.url)

        self.assertEqual(response.context['movies_purchased'], 2)

        self.assertEqual(
            [
                leader['order__user__username']
                for leader in response.context['leaders']
            ],
            ['first', 'second']
        )

    def test_empty_state_and_orders_link(self):
        self.client.force_login(self.admin_user)

        self.assertContains(
            self.client.get(self.url),
            'No movies have been purchased yet.'
        )

        self.assertContains(
            self.client.get(
                reverse('admin:cart_order_changelist')
            ),
            self.url
        )

    def test_access_requires_staff_and_order_view_permission(self):
        self.client.force_login(self.first_user)

        self.assertEqual(
            self.client.get(self.url).status_code,
            302
        )

        staff_user = User.objects.create_user(
            'staff',
            password='password',
            is_staff=True
        )

        self.client.force_login(staff_user)

        self.assertEqual(
            self.client.get(self.url).status_code,
            403
        )

        staff_user.user_permissions.add(
            Permission.objects.get(codename='view_order')
        )

        self.assertEqual(
            self.client.get(self.url).status_code,
            200
        )