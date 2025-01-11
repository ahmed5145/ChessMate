from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Player(models.Model):
    """
    Model representing a player.
    """
    username: models.CharField = models.CharField(max_length=100, unique=True)
    date_joined: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.username)

class Profile(models.Model):
    """
    Model representing a user profile.
    """
    user: models.OneToOneField = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio: models.TextField = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_username

    objects = models.Manager()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Signal to create a profile when a new user is created.
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """
    Signal to save the profile when the user is saved.
    """
    instance.profile.save()

class Game(models.Model):
    """
    Model representing a game.
    """
    player: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name="games")
    game_url: models.URLField = models.URLField(unique=True)
    played_at: models.DateTimeField = models.DateTimeField()
    opponent: models.CharField = models.CharField(max_length=100)
    RESULT_CHOICES = [
        ('win', 'Win'),
        ('loss', 'Loss'),
        ('draw', 'Draw'),
    ]
    result: models.CharField = models.CharField(max_length=10, choices=RESULT_CHOICES)
    pgn: models.TextField = models.TextField()
    is_white: models.BooleanField = models.BooleanField()
    opening_name: models.CharField = models.CharField(max_length=200, blank=True, null=True)

    class DoesNotExist(Exception):
        pass
    
    def get_id(self):
        """
        Returns the ID of the game.
        """
        return self.id

    def __str__(self):
        color = "White" if self.is_white else "Black"
        return f"Game played with {color} pieces vs {self.opponent} on {self.played_at}"
    
    objects = models.Manager()

class GameAnalysis(models.Model):
    """
    Model representing a game analysis.
    """
    game: models.ForeignKey = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='analyses')
    move: models.CharField = models.CharField(max_length=10)
    score: models.IntegerField = models.IntegerField()
    depth: models.IntegerField = models.IntegerField()
    time_spent: models.FloatField = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Analysis for Game ID {self.game.get_id()}"

    class Meta:
        indexes = [
            models.Index(fields=['game']),
            models.Index(fields=['move']),
        ]
    objects = models.Manager()
