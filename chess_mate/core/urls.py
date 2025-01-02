from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('fetch-chess-com/<str:username>/', views.fetch_games, name='fetch_games'),
]
