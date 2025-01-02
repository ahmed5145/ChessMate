from django.contrib import admin
from .models import Player, Game, GameAnalysis

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'date_joined')

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('player', 'opponent', 'result', 'played_at')

@admin.register(GameAnalysis)
class GameAnalysisAdmin(admin.ModelAdmin):
    list_display = ('game', 'move', 'score', 'depth')