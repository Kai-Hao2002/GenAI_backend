from django.urls import path
from .views.google_form_views import google_auth_init,google_auth_callback
from .views.Event_views import (
    EventUpdateAPIView, EventDetailAPIView,EventListAPIView,EventDeleteAPIView,SaveEventVersionAPIView,
    EventRevertAPIView,EventVersionDetailAPIView,EditLogListAPIView,EventEditorListCreateAPIView,EventEditorDetailAPIView,
)
from .views.Task_views import TaskAssignmentListCreateAPIView,TaskAssignmentDetailAPIView
from .views.Venue_views import VenueSuggestionDetailAPIView,VenueSuggestionListCreateAPIView
from .views.Invitation_views import EmailLogListCreateAPIView,EmailLogDetailAPIView,EmailLogAutoSendAPIView
from .views.SocialPost_views import SocialPostDetailAPIView,SocialPostListCreateAPIView
from .views.Registration_views import GoogleFormCreateAPIView,RegistrationDetailAPIView,RegistrationListCreateAPIView
urlpatterns = [
    path("events/", EventListAPIView.as_view(), name="event-list"),
    path("events/<int:pk>/", EventDetailAPIView.as_view(), name="event-detail"),
    path("events/<int:pk>/update/", EventUpdateAPIView.as_view(), name="event-update"),
    path("events/<int:pk>/delete/", EventDeleteAPIView.as_view(), name="event-delete"),
    path('events/<int:pk>/save-version/', SaveEventVersionAPIView.as_view(), name='event-save-version'),
    path('events/<int:event_id>/revert/<int:version_id>/', EventRevertAPIView.as_view(), name='event-revert'),
    path('events/<int:event_id>/versions/<int:version_id>/', EventVersionDetailAPIView.as_view(), name='event-version-detail'),
    path('events/<int:event_id>/edit-logs/', EditLogListAPIView.as_view(), name='event-edit-logs'),
    path('events/<int:event_id>/editors/', EventEditorListCreateAPIView.as_view(), name='editor-list-create'),
    path('events/<int:event_id>/editors/<int:user_id>/', EventEditorDetailAPIView.as_view(), name='editor-detail'),

    path('events/<int:event_id>/assignments/', TaskAssignmentListCreateAPIView.as_view(), name='taskassignment-list-create'),
    path('assignments/<int:pk>/', TaskAssignmentDetailAPIView.as_view(), name='taskassignment-detail'),


    path('events/<int:event_id>/venue-suggestions/', VenueSuggestionListCreateAPIView.as_view(), name='venue-suggestion-list-create'),
    path('venue-suggestions/<int:pk>/', VenueSuggestionDetailAPIView.as_view(), name='venue-suggestion-detail'),

    
    path('events/<int:event_id>/invitation/', EmailLogListCreateAPIView.as_view(), name='invitation-list-create'),
    path('invitation/<int:pk>/', EmailLogDetailAPIView.as_view(), name='invitation-detail'),
    path('email/<int:event_id>/', EmailLogAutoSendAPIView.as_view(), name='email'),


    path('events/<int:event_id>/social-posts/', SocialPostListCreateAPIView.as_view(), name='social-posts-list-create'),
    path('social-posts/<int:pk>/', SocialPostDetailAPIView.as_view(), name='social-posts-detail'),


    path('events/<int:event_id>/generate-google-form/', GoogleFormCreateAPIView.as_view(), name='generate-google-form-create'),
    path('google-auth/', google_auth_init, name='google_auth_init'),
    path('oauth2callback', google_auth_callback, name='google_auth_callback'),
    path('events/<int:event_id>/registration/', RegistrationListCreateAPIView.as_view(), name='registration-list-create'),
    path('registration/<int:pk>/', RegistrationDetailAPIView.as_view(), name='registration-detail'),
]
