# Changelog

Registro de cambios de código relevantes para el dueño del proyecto `isp13`.

## [2026-09-16]

### Añadido
- El comunicado/publicidad que aparece en el modal de la página de inicio ahora es administrable desde `/admin/` (modelo "Comunicado del modal de inicio" en la app `core`): título, subtítulo, imagen y texto del pie se editan sin tocar código. Si no hay ningún comunicado activo, el modal simplemente no aparece (antes la imagen estaba fija en la plantilla).
- Al subir la imagen de ese comunicado en el admin, se abre un recorte fijo en proporción 2:1 (como en la librería de medios de WordPress) antes de guardar — coincide con la proporción real de la imagen usada hasta ahora (1600×800), así todas las imágenes del modal quedan con el mismo encuadre sin depender de que quien la suba la recorte a mano de antemano.

## [2026-09-15]

### Añadido
- Mensajes visuales de confirmación/error (arriba a la derecha) en **todo el sitio**: antes, al guardar un formulario (por ejemplo "Registrar Tesis"), la página se recargaba sin ningún aviso y no había forma de saber si se guardó o falló; ahora se muestra un mensaje verde de éxito o uno rojo con el detalle del error.
- Nuevo acceso directo "Biblioteca" (ícono de libro) en el menú flotante de la página de inicio, junto al de "Repositorio".
- Filtros por programa académico y por año de publicación en `/repositorios/`, además de la búsqueda por texto que ya existía.
- Paginación real en `/repositorios/` (9 tesis por página, con controles anterior/siguiente y números de página), con recorte de la lista de páginas (`1 … 10 11 12 13 14 … 23`) para que no se listen cientos de números si hay muchos resultados.
- Comando de administración `seed_repositorio` para generar tesis de prueba publicadas (uso interno/desarrollo, no afecta producción).
- Contador de caracteres (`0/500`) en el campo "Título de la obra" del formulario de registro de tesis, y mensaje de error al salir del campo si queda vacío o con menos de 10 caracteres.
- Vista previa del archivo seleccionado en los 4 campos de documento de "Registrar/Editar Tesis" (PDF de tesis, constancia de originalidad, reporte Turnitin, autorización): ahora muestra nombre, tipo y tamaño (ej. "PDF · 2.3 MB"), no solo el nombre.
- Marca institucional en `/admin/`: nombre de la institución, logo y colores propios en vez de la apariencia genérica de Django (cero cambios funcionales, solo visual).
- Páginas de error propias (403, 404, 500) con la identidad del sitio en vez de la página en blanco por defecto de Django.
- Favicon del sitio (la insignia institucional) en todas las páginas, incluidas las de error — antes ninguna página tenía ícono en la pestaña del navegador.
- Verificación de seguridad al arrancar: si `DEBUG=False` y el `SECRET_KEY` sigue siendo el de desarrollo (inseguro o corto), el proyecto ya no arranca — obliga a configurar una clave real antes de poder desplegar a producción, en vez de arrancar en silencio con una clave débil.

### Corregido (crítico para producción)
- **Los archivos de `/media/` (PDF de tesis, convocatorias, resultados de admisión) no se servían en absoluto con `DEBUG=False`** — cualquier botón "Descargar PDF" del sitio habría dado 404 en producción, porque el helper de Django usado (`static()`) es un no-op fuera de modo debug y el proyecto no tenía un servidor externo configurado para `/media/`. Ahora se sirve siempre, sin depender de `DEBUG`. Verificado con `DEBUG=False` real: antes 404, ahora 200.
- **Bucle infinito de redirecciones 301 al acceder detrás de un proxy/túnel (ej. Cloudflare) con `DEBUG=False`**: Django no sabía que la conexión ya era HTTPS (el túnel le entrega HTTP plano) y `SECURE_SSL_REDIRECT` la mandaba a HTTPS una y otra vez. Se agregó `SECURE_PROXY_SSL_HEADER` para que confíe en el encabezado `X-Forwarded-Proto` que pone el proxy.

### Cambiado
- Los mensajes de error (rojos) ya no desaparecen solos a los 6 segundos — se quedan hasta que el usuario los cierra con la "×", para no perderse un error importante. Los de éxito siguen desapareciendo solos.
- La página del repositorio institucional ahora vive en `/repositorios/` (antes `/repositorio/`).
- El botón "Explorar Repositorio Completo" ya no aparece dentro de la propia página `/repositorios/` (antes se mostraba ahí mismo, redirigiendo a sí misma); sigue apareciendo en la página de inicio para llevar al repositorio completo.

### Corregido
- El enlace "Inicio" del menú de navegación apuntaba al dominio de producción (`https://13dejuliode1882sp.edu.pe/`) en vez de la página de inicio del propio sitio; ahora usa una ruta interna.
- El botón "Explorar Repositorio Completo" apuntaba a una URL de producción (`https://repositorio.13dejuliode1882sp.edu.pe/repositorio/`); ahora usa una ruta interna.
- `/repositorios/` solo mostraba 5 tesis sin importar cuántas hubiera publicadas, por un límite fijo en la plantilla que ignoraba la paginación ya preparada en el backend.
- `/lista/` (panel de gestión de tesis) listaba un botón por cada página existente (41 con los datos de prueba actuales) en vez de recortar la lista; ahora usa el mismo recorte con "…" que `/repositorios/`.
- En "Registrar Tesis" / "Editar Tesis", si el guardado fallaba (por ejemplo un dato inválido), la página se recargaba por completo y se perdía el PDF ya seleccionado, obligando a volver a adjuntarlo. Ahora el envío se hace sin recargar la página: si falla, se muestra el mensaje de error y el archivo seleccionado se mantiene; si se guarda bien, muestra el mensaje de éxito y recién ahí pasa al listado.
