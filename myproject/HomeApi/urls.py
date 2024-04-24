from . import views
from django.urls import path, include

urlpatterns = [
    path('add_media/', views.add_media),
    path('list_devotions/<int:user_id>/', views.list_devotions),
    path('find_user_info/<int:user_id>/', views.find_user_info),
    path('find_user_info_list/<str:username_prefix>', views.find_user_info_list),
]
