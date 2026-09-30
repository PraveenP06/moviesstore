from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Rating
from django.contrib.auth.decorators import login_required
from django.db.models import Avg

# Create your views here.

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html',
                  {'template_data': template_data})


def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie, offensive=False) #only show non offensive movies
    rating = Rating.objects.filter(movie=movie)
    average_rating = rating.aggregate(avg=Avg('rating'))
    user_rating = rating.filter(user=request.user).first() if request.user.is_authenticated else None
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    template_data["average_rating"] = average_rating['avg']
    template_data['user_rating'] = user_rating
    return render(request, 'movies/show.html',
                  {'template_data': template_data})


@login_required
def create_rating(request, id):
    if request.method == 'POST': 
        value = int(request.POST['rating'])
        if value >= 1 and value <= 5:
            movie = Movie.objects.get(id=id)
            Rating.objects.update_or_create(
                movie=movie,
                user=request.user,
                defaults={
                    'rating': value
                }
            )
    return redirect('movies.show', id=id)





@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
    
@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html',
            {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
    
@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

#function to report reviews and get rid of reported reviews for that page
@login_required
def report_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.offensive = True
    review.save()
    return redirect('movies.show', id=id)