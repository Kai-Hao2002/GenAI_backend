from django.urls import path
from ai.views import GenerateEventAPIView,TaskAssignmentGenerationAPIView,VenueSuggestionGenerationAPIView

urlpatterns = [
    path('generate-event/', GenerateEventAPIView.as_view(), name='generate-event'),
    path('generate-tasks/<int:event_id>/', TaskAssignmentGenerationAPIView.as_view(), name='task-generate'),
    path('generate-venues/<int:event_id>/', VenueSuggestionGenerationAPIView.as_view(), name='venue-generate'),
]
