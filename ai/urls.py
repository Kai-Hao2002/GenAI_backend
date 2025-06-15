from django.urls import path
from ai.views import GenerateEventAPIView,TaskAssignmentGenerationAPIView,VenueSuggestionGenerationAPIView,RegistrationFormGenerationAPIView,InvitationGenerationAPIView,SocialPostGenerationAPIView
from ai.google_form_views import google_auth_init,google_auth_callback

urlpatterns = [
    path('generate-event/', GenerateEventAPIView.as_view(), name='generate-event'),
    path('generate-tasks/<int:event_id>/', TaskAssignmentGenerationAPIView.as_view(), name='task-generate'),
    path('generate-venues/<int:event_id>/', VenueSuggestionGenerationAPIView.as_view(), name='venue-generate'),
    path('generate-forms/<int:event_id>/', RegistrationFormGenerationAPIView.as_view(), name='form-generate'),
    path('generate-invitation/<int:event_id>/', InvitationGenerationAPIView.as_view(), name='invitaion-generate'),
    path('generate-social-post/<int:event_id>/', SocialPostGenerationAPIView.as_view(), name='social-post-generate'),


    path('google-auth/', google_auth_init, name='google_auth_init'),
    path('oauth2callback', google_auth_callback, name='google_auth_callback'),
]
