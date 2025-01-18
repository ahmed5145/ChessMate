"""
This module defines the database models for the ChessMate application.

Models:
- Player: Represents a player in the application.
- Profile: Represents a user profile with additional information.
- Game: Represents a chess game played by a user.
- GameAnalysis: Represents the analysis of a chess game, including move details and scores.
"""

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
    credits: models.IntegerField = models.IntegerField(default=0)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    objects = models.Manager()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create or save a profile when a user is created or saved.
    """
    if created:
        Profile.objects.create(user=instance, credits=5)  # Give 5 free credits to new users

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to create or save a profile when a user is created or saved.
    """
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance, credits=5)
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
    analysis: models.JSONField = models.JSONField(null=True, blank=True)  # New field to store analysis as JSON

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
    move: models.CharField = models.CharField(max_length=20)
    score: models.IntegerField = models.IntegerField()
    depth: models.IntegerField = models.IntegerField()
    time_spent: models.FloatField = models.FloatField(null=True, blank=True)
    is_capture: models.BooleanField = models.BooleanField(default=False)  # New field to indicate if the move is a capture
    move_number: models.IntegerField = models.IntegerField(default=0)  # New field to indicate the move number
    evaluation_trend: models.CharField = models.CharField(max_length=10, null=True, blank=True)  # New field to track evaluation trend

    def __str__(self):
        return f"Analysis for Game ID {self.game.id}"

    class Meta:
        indexes = [
            models.Index(fields=['game']),
            models.Index(fields=['move']),
        ]
    objects = models.Manager()
