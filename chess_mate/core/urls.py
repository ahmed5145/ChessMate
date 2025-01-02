from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('fetch-chess-com/<str:username>/<str:game_type>/', views.fetch_games, name='fetch_games'),
    path('analyze/<int:game_id>/', views.analyze_game_view, name='analyze_game'),
]
