from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('gestion/dashboard/', views.dashboard_view, name='dashboard'),
    path('login/', views.auth_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('modals/<str:modal_id>/', views.modal_content, name='modal_content'),
]