from django.shortcuts import render
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from .forms import CustomUserCreationForm, CustomErrorList
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from movies.models import Movie


# Create your views here.
@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')
def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html',
            {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username = request.POST['username'],
            password = request.POST['password']
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html',
                {'template_data': template_data})
        else:
            auth_login(request, user)
            return redirect('home.index')
        
def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html',
            {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            form.save()
            return redirect('accounts.login')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html',
                {'template_data': template_data})
        

@login_required
def orders(request):
    template_data = {}
    template_data['title'] = 'Orders'
    template_data['orders'] = request.user.order_set.all()
    return render(request, 'accounts/orders.html',
        {'template_data': template_data})

@login_required
def top_purchasers(request):
    if not request.user.is_staff:
        return redirect('home.index')
    users = User.objects.filter(is_staff=False, is_superuser=False).annotate(
        purchase_count=Coalesce(Sum('order__item__quantity'), 0),
        order_count=Count('order', distinct=True),
    ).order_by('-purchase_count', 'username')
    list_size_input = request.GET.get('list_size', '').strip()
    list_size = None
    error = None

    if list_size_input != '':
        try:
            list_size = int(list_size_input)
            if list_size <= 0:
                error = 'List size must be a whole positive number, showing all users.'
                list_size = None
        except ValueError:
            error = 'List size must be a whole number, showing all users.'
            list_size = None

    if list_size is not None:
        users = users[:list_size]

    template_data = {}
    template_data['title'] = 'Top Purchasers'
    template_data['users'] = users
    template_data['list_size_input'] = list_size_input
    template_data['list_size'] = list_size
    template_data['error'] = error

    return render(request, 'accounts/top_purchasers.html', {'template_data': template_data})

@login_required
def top_commenters(request):
    if not request.user.is_staff:
        return redirect('home.index')

    users = User.objects.filter(
        is_staff=False,
        is_superuser=False
    ).annotate(
        comment_count=Count('review')
    ).filter(
        comment_count__gt=0
    ).order_by(
        '-comment_count',
        'username'
    )

    template_data = {}
    template_data['title'] = 'Top Commenters'
    template_data['users'] = users

    return render(
        request,
        'accounts/top_commenters.html',
        {'template_data': template_data}
    )

@login_required
def movie_stats(request):
    if not request.user.is_staff:
        return redirect('home.index')

    # Two separate queries on purpose: annotating Sum and Count in the same
    # query joins items x reviews and inflates both numbers.
    bought = Movie.objects.annotate(
        times_bought=Sum('item__quantity')
    ).filter(times_bought__gt=0)
    reviewed = Movie.objects.annotate(
        times_reviewed=Count('review', filter=Q(review__offensive=False))
    ).filter(times_reviewed__gt=0)

    # Find the top count, then keep every movie tied at that count.
    top_bought = bought.order_by('-times_bought').first()
    top_reviewed = reviewed.order_by('-times_reviewed').first()
    most_bought = []
    most_reviewed = []
    if top_bought:
        most_bought = bought.filter(times_bought=top_bought.times_bought).order_by('name')
    if top_reviewed:
        most_reviewed = reviewed.filter(times_reviewed=top_reviewed.times_reviewed).order_by('name')

    template_data = {}
    template_data['title'] = 'Movie Stats'
    template_data['most_bought'] = most_bought
    template_data['most_reviewed'] = most_reviewed
    return render(request, 'accounts/movie_stats.html', {'template_data': template_data})

