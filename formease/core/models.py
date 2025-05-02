from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', '♂ Male'),
        ('F', '♀ Female'),
        ('O', '⚥ Other')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    
    # Educational Information
    highest_education = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    field_of_study = models.CharField(max_length=100, blank=True)
    
    # Additional Details
    skills = models.TextField(blank=True, help_text="Comma-separated list of skills")
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update UserProfile when User is created/updated"""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Update the profile if it exists, create it if it doesn't
        UserProfile.objects.get_or_create(user=instance)

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Personal Information
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    summary = models.TextField()
    
    # Education
    education = models.JSONField()  # Store multiple education entries
    
    # Experience
    experience = models.JSONField()  # Store multiple experience entries
    
    # Skills
    skills = models.JSONField()  # Store skills with categories
    
    # Generated Content
    generated_content = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name}'s Resume - {self.created_at.strftime('%Y-%m-%d')}"

class PDFSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)  # Made nullable for existing records
    summary = models.TextField()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'PDF Summaries'
    
    def __str__(self):
        return self.title or self.file_name  # Fall back to file_name if title is None
        
    @classmethod
    def search(cls, user, query):
        return cls.objects.filter(
            user=user
        ).filter(
            Q(title__icontains=query) | Q(file_name__icontains=query)
        )
