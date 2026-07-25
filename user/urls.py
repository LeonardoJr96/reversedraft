from django.urls import path


from .views import RegisterView, MeView, ChangePasswordView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='user-register'),
    path('me/', MeView.as_view(), name='user-me'),
    path('change-password/', ChangePasswordView.as_view(), name='user-change-password'),
]