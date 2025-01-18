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
from typing import Any

class Player(models.Model):
    """Model representing a player."""
    objects = models.Manager()
    username = models.CharField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.username)

class Profile(models.Model):
    """Model representing a user profile."""
    objects = models.Manager()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.IntegerField(default=5)  # New users get 5 free credits
    rating = models.IntegerField(default=1200)
    total_games = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0)
    recent_performance = models.CharField(max_length=20, default='stable')
    preferred_openings = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.get_username()}'s profile"

    class Meta:
        db_table = 'core_profile'

@receiver(post_save, sender=User)
def create_user_profile(sender: Any, instance: User, created: bool, **kwargs: Any) -> None:
    """Create a Profile instance for all newly created User instances."""
    if created:
        Profile.objects.create(user=instance)

class Game(models.Model):
    """Model representing a game."""
    objects = models.Manager()
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    game_url = models.URLField(unique=True)
    played_at = models.DateTimeField()
    opponent = models.CharField(max_length=100)
    result = models.CharField(max_length=10)
    pgn = models.TextField()
    is_white = models.BooleanField()
    opening_name = models.CharField(max_length=100, blank=True, null=True)
    analysis = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.player.get_username()} vs {self.opponent} ({self.played_at})"

    class Meta:
        db_table = 'core_game'
        ordering = ['-played_at']

class GameAnalysis(models.Model):
    """Model representing a game analysis."""
    objects = models.Manager()
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='analyses')
    move = models.CharField(max_length=20)
    score = models.IntegerField()
    depth = models.IntegerField()
    time_spent = models.FloatField(null=True, blank=True)
    is_capture = models.BooleanField(default=False)
    move_number = models.IntegerField(default=0)
    evaluation_trend = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self) -> str:
        return f"Analysis for Game {self.game.pk}"

    class Meta:
        indexes = [
            models.Index(fields=['game']),
            models.Index(fields=['move']),
        ]

class Transaction(models.Model):
    """Model representing a credit transaction."""
    objects = models.Manager()
    
    TRANSACTION_TYPES = [
        ('purchase', 'Credit Purchase'),
        ('usage', 'Credit Usage'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus Credits')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    credits = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.get_username()} - {self.transaction_type} - {self.credits} credits"

    class Meta:
        db_table = 'core_transaction'
        ordering = ['-created_at']
