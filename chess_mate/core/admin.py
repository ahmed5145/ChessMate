from django.contrib import admin
from .models import Player, Game, GameAnalysis, Profile, Transaction

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'date_joined')
    search_fields = ('username',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits', 'rating', 'total_games', 'win_rate')
    search_fields = ('user__username',)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('user', 'white', 'black', 'result', 'platform', 'date_played')
    list_filter = ('platform', 'result')
    search_fields = ('white', 'black', 'user__username')
    ordering = ('-date_played',)

@admin.register(GameAnalysis)
class GameAnalysisAdmin(admin.ModelAdmin):
    list_display = ('game', 'created_at')
    search_fields = ('game__white', 'game__black')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'credits', 'status', 'created_at')
    list_filter = ('transaction_type', 'status')
    search_fields = ('user__username', 'stripe_payment_id')