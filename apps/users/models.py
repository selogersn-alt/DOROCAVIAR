from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True, help_text="Bannière de la chaîne")
    favorites = models.ManyToManyField('videos.Video', related_name='favorited_by', blank=True)
    
    # Réseau Social
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    
    # Statistiques et Profil
    is_verified = models.BooleanField(default=False)
    is_pro = models.BooleanField(default=False, help_text="Utilisateur Premium/Pro")
    subscribers_count = models.PositiveIntegerField(default=0)
    
    @property
    def display_name(self):
        if self.is_superuser or self.username == 'admin':
            return "DORO CAVIAR"
        return self.username

    def __str__(self):
        return self.display_name

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('LIKE', 'Mention J\'aime'),
        ('FOLLOW', 'Nouvel Abonné'),
        ('MESSAGE', 'Nouveau Message'),
        ('SYSTEM', 'Système'),
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    text = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} pour {self.recipient.username}"

class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Acceptée'),
        ('REJECTED', 'Refusée'),
    )
    sender = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        verbose_name = "Demande d'Ami"
        verbose_name_plural = "Demandes d'Amis"

class PrivateMessage(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True, help_text="Peut être vide si c'est juste une image")
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"De {self.sender} à {self.recipient}"

class ProfileComment(models.Model):
    profile = models.ForeignKey(User, related_name='profile_comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='written_profile_comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
