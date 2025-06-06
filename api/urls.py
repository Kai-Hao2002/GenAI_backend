from django.urls import path
from .views.Event_views import EventUpdateAPIView, EventDetailAPIView,EventListAPIView,EventDeleteAPIView,SaveEventVersionAPIView,EventRevertAPIView,EventVersionDetailAPIView,EditLogListAPIView,EventEditorListCreateAPIView,EventEditorDetailAPIView

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

]
