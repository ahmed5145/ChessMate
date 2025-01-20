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
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from typing import Any

class Player(models.Model):
    """Model representing a player."""
    username = models.CharField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.username)

class Profile(models.Model):
    """User profile model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=1200)
    credits = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    def total_games(self):
        return self.user.game_set.count()

    def win_rate(self):
        total = self.total_games()
        if total == 0:
            return "0%"
        wins = self.user.game_set.filter(result="win").count()
        return f"{(wins / total * 100):.1f}%"

    def __str__(self):
        return f"{self.user.username}'s profile"

    class Meta:
        indexes = [
            models.Index(fields=['user', 'rating']),
        ]

    def verify_email(self):
        """Mark email as verified."""
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.email_verification_token = None
        self.save()

    def get_preference(self, key, default=None):
        """Get a specific preference value."""
        return self.preferences.get(key, default)

    def set_preference(self, key, value):
        """Set a specific preference value."""
        self.preferences[key] = value
        self.save()

@receiver(post_save, sender=User)
def create_user_profile(sender: Any, instance: User, created: bool, **kwargs: Any) -> None:
    """Create a Profile instance when a new User is created."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender: Any, instance: User, **kwargs: Any) -> None:
    """Save the Profile instance when the User is saved."""
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

def get_default_user():
    """Get or create a default user for legacy data."""
    return User.objects.get_or_create(username='legacy_user')[0].id

class Game(models.Model):
    """Model representing a game."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games', default=get_default_user)
    platform = models.CharField(max_length=20)  # 'chess.com' or 'lichess'
    game_id = models.CharField(max_length=100)
    pgn = models.TextField()
    result = models.CharField(max_length=10)  # win, loss, draw
    white = models.CharField(max_length=100)
    black = models.CharField(max_length=100)
    opponent = models.CharField(max_length=100, default="Unknown")
    opening_name = models.CharField(max_length=200, default="Unknown Opening")
    date_played = models.DateTimeField()
    analysis = models.JSONField(null=True, blank=True)
    feedback = models.JSONField(null=True, blank=True)  # Store analysis feedback
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} vs {self.opponent} ({self.result})"

    class Meta:
        db_table = 'games'
        unique_together = ('user', 'platform', 'game_id')
        ordering = ['-date_played']

class GameAnalysis(models.Model):
    """Model representing a game analysis."""
    game = models.OneToOneField(Game, on_delete=models.CASCADE)
    analysis_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Analysis for {self.game}"

    class Meta:
        db_table = 'game_analysis'

class Transaction(models.Model):
    """Model representing a credit transaction."""
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('usage', 'Usage'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credits = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    stripe_payment_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.transaction_type} - {self.credits} credits for {self.user.username}"

    class Meta:
        db_table = 'transactions'
