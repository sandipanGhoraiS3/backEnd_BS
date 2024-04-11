from django.urls import path
from .views import UserRegistrationAPIView, UserLoginAPIView, ForgotPasswordAPIView, send_otp, LogoutAPIView, check_username, check_phone_number, verify_otp
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='user-login'),
    path('forgot_password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('send_otp/', send_otp, name='send_otp'),
    path('verify_otp/<str:phone>/<str:otp>/', verify_otp, name='verify_otp'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('check_username/<str:username>/', check_username, name='check_username'),
    path('check_phone_number/<str:phone>/', check_phone_number, name='check_phone_number'),
    # secret code check
]
