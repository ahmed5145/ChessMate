from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Player(models.Model):
    username = models.CharField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    objects = models.Manager()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

class Game(models.Model):
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name="games")
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
    
    objects = models.Manager()

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
    objects = models.Manager()
