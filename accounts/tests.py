from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from movies.models import Movie


class TopPurchasersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser('admin', password='password')
        cls.first_user = User.objects.create_user('first', password='password')
        cls.second_user = User.objects.create_user('second', password='password')
        cls.movie = Movie.objects.create(
            name='Example Movie', price=10, description='Example',
            image='movie_images/example.jpg',
        )

    def purchase(self, user, quantity):
        self.client.force_login(user)
        session = self.client.session
        session['cart'] = {str(self.movie.id): str(quantity)}
        session.save()
        self.assertEqual(self.client.get(reverse('cart.purchase')).status_code, 200)

    def test_ranking_updates_after_purchases_and_shows_order_counts(self):
        self.purchase(self.first_user, 2)
        self.client.force_login(self.staff)
        response = self.client.get(reverse('accounts.top_purchasers'))
        self.assertEqual(response.context['template_data']['users'][0].username, 'first')
        self.assertEqual(response.context['template_data']['users'][0].purchase_count, 2)

        self.purchase(self.second_user, 3)
        self.client.force_login(self.staff)
        response = self.client.get(reverse('accounts.top_purchasers'))
        users = list(response.context['template_data']['users'])
        self.assertEqual(users[0].username, 'second')
        self.assertEqual(users[0].purchase_count, 3)
        self.assertEqual(users[0].order_count, 1)
        self.assertNotIn('admin', [user.username for user in users])
        self.assertContains(response, '<td>3</td>', html=True)
        self.assertContains(response, '<td>1</td>', html=True)

    def test_only_staff_can_view_ranking_and_invalid_size_shows_error(self):
        url = reverse('accounts.top_purchasers')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.first_user)
        self.assertRedirects(self.client.get(url), reverse('home.index'))

        self.client.force_login(self.staff)
        response = self.client.get(url, {'list_size': 'invalid'})
        self.assertContains(response, 'List size must be a whole number')
        response = self.client.get(url, {'list_size': '1'})
        self.assertContains(response, 'Showing the top 1 user.')
        self.assertEqual(len(response.context['template_data']['users']), 1)
