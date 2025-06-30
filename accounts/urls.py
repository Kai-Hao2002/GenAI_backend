from django.urls import path
from .views import RegisterView, LoginView, LogoutView,activate_account,ResendActivationEmailView,AccountDetailView,AccountUpdateView,AccountDeleteView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('accounts/activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('reactivate/', ResendActivationEmailView.as_view(), name='reactivate'),
    path('', AccountDetailView.as_view(), name='account-detail'),
    path('account-update/', AccountUpdateView.as_view(), name='account-update'),
    path('account-delete/', AccountDeleteView.as_view(), name='account-delete'),

]
