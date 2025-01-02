from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('fetch-chess-com/<str:username>/<str:game_type>/', views.fetch_games, name='fetch_games'),
    path('analyze/<int:game_id>/', views.analyze_game_view, name='analyze_game'),
    path('feedback/<int:game_id>/', views.game_feedback_view, name='game_feedback'),
    path("api/register/", views.register_view, name="register"),
    path("api/login/", views.login_view, name="login"),
    path("api/games/", views.games_view, name="games"),
    path("api/game/<int:game_id>/analysis/", views.game_analysis_view, name="game_analysis"),

]
