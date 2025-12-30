from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('registrar/', views.registrar_blog, name='registrar_blog'),
    path('publicar/', views.listar_publicaciones, name='listar_publicaciones'),
    path('eliminar/<int:post_id>/', views.eliminar_blog, name='eliminar_blog'),
]