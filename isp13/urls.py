import re

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from convocatorias.views import home

admin.site.site_header = 'IESPP "13 de Julio de 1882"'
admin.site.site_title = "Panel de administración"
admin.site.index_title = "Gestión institucional"

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('core.urls')),
    path('', include('investigacion.urls', namespace='investigacion')),
    path('', home, name='home'),
    path('blog/', include('blog.urls', namespace='blog')),
    path('soporte/', include('soporte.urls', namespace='soporte')),
    path('convocatorias/', include('convocatorias.urls', namespace='convocatoria')),
    path('admision/', include('admision.urls')),

    # django.conf.urls.static.static() es un no-op cuando DEBUG=False, y este
    # proyecto no tiene todavía un servidor (nginx u otro) configurado para
    # servir /media/ por fuera de Django. Sin esta ruta explícita, cada PDF
    # de tesis/convocatorias/admisión daría 404 en producción. Cuando se
    # configure un servidor web que sirva /media/ directamente, esta ruta
    # puede quitarse.
    re_path(
        r'^%s(?P<path>.*)$' % re.escape(settings.MEDIA_URL.lstrip('/')),
        serve,
        {'document_root': settings.MEDIA_ROOT},
    ),
]