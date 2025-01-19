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
    path('api/token/refresh/', views.token_refresh_view, name='token_refresh'),

    # Game management endpoints
    path('api/fetch-games/', views.fetch_games, name='fetch_games'),
    path("api/dashboard/", views.dashboard_view, name="dashboard"),
    path("api/games/", views.get_saved_games, name="get_saved_games"),

    # Analysis endpoints
    path("api/game/<int:game_id>/analysis/", views.analyze_game_view, name="analyze_game"),
    path("api/games/batch-analyze/", views.analyze_batch_games_view, name="batch_analyze_games"),

    # Feedback endpoints
    path('api/feedback/<int:game_id>/', views.game_feedback_view, name='game_feedback'),
    path('api/feedback/batch/', views.batch_feedback_view, name='batch_feedback'),

    # Credit system endpoints
    path('api/credits/', views.get_credits, name='get_credits'),
    path('api/credits/deduct/', views.deduct_credits, name='deduct_credits'),
    path('api/purchase-credits/', views.purchase_credits, name='purchase_credits'),
    path('api/confirm-purchase/', views.confirm_purchase, name='confirm_purchase'),

    # Email verification endpoint
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),

]
