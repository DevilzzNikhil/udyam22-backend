from django.urls import path
from .views import (
    # RequestPasswordResetEmail,
    # PasswordTokenCheck,
    # NewPasswordView,
    RegisterView,
)
from .views import  LoginView, LogoutView, UserUpdateView
from .api import UserInitApi

"""
TODO:
Add the urlpatterns of the endpoints, required for implementing
Todo GET (List and Detail), PUT, PATCH and DELETE.
"""

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("update/", UserUpdateView.as_view(), name="update"),
    path('google-login/', UserInitApi.as_view(), name='google-login' )

]
