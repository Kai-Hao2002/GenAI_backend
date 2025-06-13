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

    name = models.CharField(max_length=255,null=True,blank=True)
    description = models.TextField(blank=True)
    slogan = models.TextField(blank=True)
    target_audience = models.CharField(max_length=255, blank=True)
    expected_attendees = models.PositiveIntegerField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    type = models.CharField(max_length=100)
    budget = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_created')
    latest_version = models.ForeignKey('EventVersion', on_delete=models.SET_NULL, null=True, blank=True, related_name='latest_for_events')
    last_modified = models.DateTimeField(auto_now=True)


class EventVersion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    changes_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_snapshot = models.JSONField()


class TaskAssignment(models.Model):

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='task_assignments')
    count = models.IntegerField()
    role = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class AssetTemplate(models.Model):
    TYPE_CHOICES = [
        ('poster', 'Poster'),
        ('invitation', 'Invitation'),
        ('map', 'Map'),
        ('layout', 'Layout'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    tone = models.CharField(max_length=100)
    color_scheme = models.CharField(max_length=100, blank=True)
    font_style = models.CharField(max_length=100, blank=True)
    layout_style = models.CharField(max_length=100, blank=True)
    sample_image_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)


class VisualAsset(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='visual_assets')
    image_url = models.URLField()
    generated_by = models.CharField(max_length=50)  # e.g. 'system' or 'user'
    created_at = models.DateTimeField(auto_now_add=True)
    template = models.ForeignKey('AssetTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField(blank=True)


class SocialPost(models.Model):
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('x', 'X'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='social_posts')
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    content = models.TextField()
    tone = models.CharField(max_length=100)
    scheduled_time = models.DateTimeField()
    language = models.CharField(max_length=10, default='en')


class VenueSuggestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='venue_suggestions')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    transportation_score = models.PositiveSmallIntegerField()
    map_url = models.URLField(blank=True)
    is_outdoor = models.BooleanField(default=False)


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('queued', 'Queued'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_email = models.EmailField()
    template_name = models.CharField(max_length=100)
    tone = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)


class EditLog(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='edit_logs')
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    edited_at = models.DateTimeField(auto_now_add=True)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registration_url = models.URLField(blank=True)
    edit_url = models.URLField(blank=True)


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