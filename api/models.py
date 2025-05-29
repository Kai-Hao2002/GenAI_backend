# api/models.py
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    target_audience = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    expected_attendees = models.IntegerField()
    budget = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_outdoor = models.BooleanField()
    weather_risk = models.TextField()
    status = models.CharField(max_length=50)  # draft / published / completed
    version_group_id = models.IntegerField()
    latest_version = models.ForeignKey('EventVersion', on_delete=models.SET_NULL, null=True, related_name='latest_for_event')
    last_modified = models.DateTimeField()
    version_number = models.IntegerField()
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_events')


class EventVersion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    version_number = models.IntegerField()
    changes_summary = models.TextField()
    created_at = models.DateTimeField()
    event_snapshot = models.JSONField()


class TaskAssignment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=50)  # pending / in_progress / done
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class VisualAsset(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    type = models.CharField(max_length=100)  # poster / invitation / map / layout
    image_url = models.URLField()
    generated_by = models.CharField(max_length=50)  # system or user
    created_at = models.DateTimeField()


class SocialPost(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    platform = models.CharField(max_length=100)  # Facebook / IG / X
    content = models.TextField()
    tone = models.CharField(max_length=100)  # light-hearted / mystical / coaching
    scheduled_time = models.DateTimeField()


class VenueSuggestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    capacity = models.IntegerField()
    rental_cost = models.DecimalField(max_digits=10, decimal_places=2)
    transportation_score = models.IntegerField()  # 1-5
    map_url = models.URLField()


class CardOfTheDay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    content = models.TextField()
    image_url = models.URLField()


class EmailLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    recipient_email = models.EmailField()
    template_name = models.CharField(max_length=100)  # standard_invite, vip_invite
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField()
    status = models.CharField(max_length=50)  # sent / failed / queued


class EditLog(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    edited_at = models.DateTimeField()
    field_changed = models.CharField(max_length=255)
    old_value = models.TextField()
    new_value = models.TextField()

class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    comment = models.TextField()
    registered_at = models.DateTimeField()
    status = models.CharField(max_length=50)
