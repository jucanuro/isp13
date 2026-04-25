from django.urls import path
from . import views

app_name = 'admision'

urlpatterns = [
    path(
        'resultados-admision/',
        views.resultados_admision_modal,
        name='resultados_admision_modal'
    ),
]