# api/models.py
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slogan = models.TextField(blank=True)
    target_audience = models.CharField(max_length=255, blank=True)
    expected_attendees = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    type = models.CharField(max_length=100)
    budget = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_created')
    latest_version = models.ForeignKey('EventVersion', on_delete=models.SET_NULL, null=True, blank=True, related_name='latest_for_events')
    last_modified = models.DateTimeField(auto_now=True)


class EventVersion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True, null=True)
    event_snapshot = models.JSONField()


class TaskAssignment(models.Model):

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='task_assignments')
    count = models.IntegerField()
    role = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class VisualAsset(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='visual_assets')
    image_url = models.URLField()
    headline = models.TextField(blank=True)
    subheadline = models.TextField(blank=True)
    tone = models.CharField(max_length=100)
    color_scheme = models.CharField(max_length=100, blank=True)
    font_style = models.CharField(max_length=100, blank=True)
    layout_style = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SocialPost(models.Model):
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('x', 'X'),('threads', 'Threads'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='social_posts')
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    content = models.TextField()
    tone = models.CharField(max_length=100)
    language = models.CharField(max_length=10, default='en')


class VenueSuggestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='venue_suggestions')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    transportation_score = models.PositiveSmallIntegerField()
    map_url = models.URLField(blank=True, null=True)
    is_outdoor = models.BooleanField(default=False)


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('queued', 'Queued'),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE,related_name='email')
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=25)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,null=True, blank=True)


class EditLog(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='edit_logs')
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    edited_at = models.DateTimeField(auto_now_add=True)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registration_url = models.URLField(blank=True, null=True)
    form_title = models.CharField(max_length=255)
    event_intro = models.TextField()
    form_fields = models.JSONField()


class EventEditor(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='editors')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='editable_events')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.event.name} ({self.role})"
    
class GoogleCredentials(models.Model):
    token_json = models.TextField()  
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GoogleCredentials for {self.user.username}"