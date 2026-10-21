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


class MovieStatsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser('admin', password='password')
        cls.user = User.objects.create_user('user', password='password')
        cls.movie_a = Movie.objects.create(
            name='Movie A', price=10, description='Example',
            image='movie_images/example.jpg',
        )
        cls.movie_b = Movie.objects.create(
            name='Movie B', price=10, description='Example',
            image='movie_images/example.jpg',
        )

    def purchase(self, movie):
        self.client.force_login(self.user)
        session = self.client.session
        session['cart'] = {str(movie.id): '1'}
        session.save()
        self.assertEqual(self.client.get(reverse('cart.purchase')).status_code, 200)

    def get_stats(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('accounts.movie_stats'))
        self.assertEqual(response.status_code, 200)
        return response.context['template_data']

    def test_story_scenario(self):
        # Comment on movie A and purchase it: A tops both lists.
        self.client.force_login(self.user)
        self.client.post(
            reverse('movies.create_review', args=[self.movie_a.id]),
            {'comment': 'Great movie'},
        )
        self.purchase(self.movie_a)
        stats = self.get_stats()
        self.assertEqual([(m.name, m.times_bought) for m in stats['most_bought']], [('Movie A', 1)])
        self.assertEqual([(m.name, m.times_reviewed) for m in stats['most_reviewed']], [('Movie A', 1)])

        # Purchase movie B twice: B is most bought, A is still most reviewed.
        self.purchase(self.movie_b)
        self.purchase(self.movie_b)
        stats = self.get_stats()
        self.assertEqual([(m.name, m.times_bought) for m in stats['most_bought']], [('Movie B', 2)])
        self.assertEqual([(m.name, m.times_reviewed) for m in stats['most_reviewed']], [('Movie A', 1)])

    def test_only_staff_can_view_stats(self):
        url = reverse('accounts.movie_stats')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(url), reverse('home.index'))
