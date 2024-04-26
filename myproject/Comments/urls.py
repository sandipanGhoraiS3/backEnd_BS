from . import views
from django.urls import path, include

urlpatterns = [
    path('add_comment/', views.add_comment),
    path('add_like/', views.add_like),
    path('add_admin_like/', views.add_admin_like),
    path('list_comments/<int:media_id>/', views.list_comments),
    path('list_likes/<int:media_id>/', views.list_likes),
    
]