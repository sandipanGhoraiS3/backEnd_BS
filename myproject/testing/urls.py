from django.urls import path
from .views import UserRegistrationAPIView, UserLoginAPIView, ForgotPasswordAPIView, send_otp_forgot, send_otp_login, LogoutAPIView, check_username, check_phone_number, verify_otp_forgot, verify_otp_login, check_passcode
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='user-login'),
    path('forgot_password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('send_otp_forgot/', send_otp_forgot, name='send_otp_forgot'),
    path('send_otp_login/', send_otp_login, name='send_otp_login'),
    path('verify_otp_forgot/<str:phone>/<str:otp>/', verify_otp_forgot, name='verify_otp_forgot'),
    path('verify_otp_login/<str:phone>/<str:otp>/', verify_otp_login, name='verify_otp_login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('check_username/<str:username>/', check_username, name='check_username'),
    path('check_phone_number/<str:phone>/', check_phone_number, name='check_phone_number'),
    path('check_passcode/<str:code>/', check_passcode, name='check_passcode'),
]
