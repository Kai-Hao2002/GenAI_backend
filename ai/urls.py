from django.urls import path
from ai.views import GenerateEventAPIView

urlpatterns = [
    path('generate-event/', GenerateEventAPIView.as_view(), name='generate-event'),
]
