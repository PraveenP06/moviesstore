from django.shortcuts import render
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from .forms import CustomUserCreationForm, CustomErrorList
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce


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

