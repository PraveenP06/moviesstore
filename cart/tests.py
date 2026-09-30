from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from movies.models import Movie


class PurchaseLeaderTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('admin', password='testpass', is_staff=True)
        self.first_user = User.objects.create_user('first', password='testpass')
        self.second_user = User.objects.create_user('second', password='testpass')
        self.movie = Movie.objects.create(
            name='Test movie', price=10, description='Test', image='movie_images/test.jpg')
        self.url = reverse('admin.purchase_leader')

    def purchase(self, user, quantity):
        self.client.force_login(user)
        session = self.client.session
        session['cart'] = {str(self.movie.id): str(quantity)}
        session.save()
        self.assertEqual(self.client.get(reverse('cart.purchase')).status_code, 200)

    def test_only_staff_can_view_purchase_leader(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.first_user)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertContains(self.client.get(reverse('admin:index')), self.url)

    def test_leader_updates_after_purchases(self):
        self.purchase(self.first_user, 2)
        self.purchase(self.second_user, 1)
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.context['top_user'], self.first_user)
        self.assertEqual(response.context['top_user'].movie_count, 2)

        self.purchase(self.second_user, 2)
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.context['top_user'], self.second_user)
        self.assertEqual(response.context['top_user'].movie_count, 3)

    def test_empty_state(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, 'No regular users have purchased movies yet.')
