from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from convocatorias.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', include('core.urls')),
    path('', include('investigacion.urls', namespace='investigacion')),
    path('', home, name='home'),
    path('blog/', include('blog.urls', namespace='blog')),
    path('soporte/', include('soporte.urls', namespace='soporte')),
    path('convocatorias/', include('convocatorias.urls', namespace='convocatoria')),
    path('admision/', include('admision.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)