from . import views
from django.urls import path, include

urlpatterns = [
    path('add_comment/', views.add_comment),
    path('add_like/', views.add_like),
    path('add_comment_like/', views.add_comment_like),
]