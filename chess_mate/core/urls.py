"""
URL configuration for the ChessMate application.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Authentication endpoints
    path("api/register/", views.register_view, name="register"),
    path("api/login/", views.login_view, name="login"),
    path("api/logout/", views.logout_view, name="logout"),

    # Game management endpoints
    path('api/fetch-games/', views.fetch_games, name='fetch_games'),
    path("api/dashboard/", views.user_games_view, name="dashboard"),  # User-specific games
    path("api/games/", views.get_saved_games, name="get_saved_games"), # All games endpoint

    # Analysis endpoints
    path("api/game/<int:game_id>/analyze/", views.analyze_game_view, name="analyze_game"),
    path("api/game/<int:game_id>/analysis/", views.analyze_game_view, name="analyze_game"),
    path("api/games/batch-analyze/", views.analyze_batch_games_view, name="batch_analyze_games"),

    # Feedback endpoints
    path('api/feedback/<int:game_id>/', views.game_feedback_view, name='game_feedback'),
    path('api/feedback/batch/', views.batch_feedback_view, name='batch_feedback'),


]
