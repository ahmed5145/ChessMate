from django.db import models


class Player(models.Model):
    username = models.CharField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Game(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="games")
    game_url = models.URLField(unique=True)
    played_at = models.DateTimeField()
    opponent = models.CharField(max_length=100)
    RESULT_CHOICES = [
        ('win', 'Win'),
        ('loss', 'Loss'),
        ('draw', 'Draw'),
    ]
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    pgn = models.TextField()
    is_white = models.BooleanField()
    opening_name = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        color = "White" if self.is_white else "Black"
        return f"Game played with {color} pieces vs {self.opponent} on {self.played_at}"

class GameAnalysis(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='analyses')
    move = models.CharField(max_length=10)
    score = models.IntegerField()
    depth = models.IntegerField()

    def __str__(self):
        return f"Analysis for Game ID {self.game.id}"

    class Meta:
        indexes = [
            models.Index(fields=['game']),
            models.Index(fields=['move']),
        ]
