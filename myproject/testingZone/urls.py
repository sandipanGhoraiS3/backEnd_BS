from . import views
from django.urls import path, include

urlpatterns = [
    path('upload_file/', views.upload_file),
    path('download_file/', views.download_file),
]
