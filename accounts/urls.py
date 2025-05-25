from django.urls import path
from .views import RegisterView, LoginView, LogoutView,ActivateAccountView,ResendActivationEmailView,AccountDetailView,AccountUpdateView,AccountDeleteView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('reactivate/', ResendActivationEmailView.as_view(), name='reactivate'),
    path('', AccountDetailView.as_view(), name='account-detail'),
    path('account-update/', AccountUpdateView.as_view(), name='account-update'),
    path('account-delete/', AccountDeleteView.as_view(), name='account-delete'),

]
