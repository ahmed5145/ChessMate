from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/fetch-games/', views.fetch_games, name='fetch_games'),
    path("api/game/<int:game_id>/analyze/", views.analyze_game_view, name="analyze_game"),
    path('feedback/<int:game_id>/', views.game_feedback_view, name='game_feedback'),
    path("api/register/", views.register_view, name="register"),
    path("api/login/", views.login_view, name="login"),
    path("api/dashboard/", views.user_games_view, name="dashboard"),  # User-specific games
    path("api/games/", views.get_saved_games, name="get_saved_games"), # All games endpoint
    path("api/game/<int:game_id>/analysis/", views.analyze_game_view, name="analyze_game"),
    path("api/games/batch-analyze/", views.analyze_batch_games_view, name="batch_analyze_games"),
    path('api/feedback/<int:game_id>/', views.game_feedback_view, name='game_feedback'),
    path('api/feedback/batch/', views.batch_feedback_view, name='batch_feedback'),


]
