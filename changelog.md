# Changelog

Registro de cambios de código relevantes para el dueño del proyecto `isp13`.

## [2026-09-16]

### Añadido
- El comunicado/publicidad que aparece en el modal de la página de inicio ahora es administrable desde `/admin/` (modelo "Comunicado del modal de inicio" en la app `core`): título, subtítulo, imagen y texto del pie se editan sin tocar código. Si no hay ningún comunicado activo, el modal simplemente no aparece (antes la imagen estaba fija en la plantilla).
- Al subir la imagen de ese comunicado en el admin, se abre un recorte fijo en proporción 2:1 (como en la librería de medios de WordPress) antes de guardar — coincide con la proporción real de la imagen usada hasta ahora (1600×800), así todas las imágenes del modal quedan con el mismo encuadre sin depender de que quien la suba la recorte a mano de antemano.
- El menú de navegación de escritorio (Inicio, Nosotros, Admisión, Gestión Académica, Unidades, Documentos De Gestión, y los ~40 ítems dentro de sus desplegables) ahora es administrable desde `/admin/` (modelos "Menú principal" e "Ítem de menú" en `core`): se puede renombrar, reordenar, activar/desactivar, agregar o quitar cualquier botón o ítem sin tocar el HTML. El contenido visual y el comportamiento (modales, enlaces) quedaron exactamente igual que antes — se migró 1 a 1 desde lo que estaba fijo en `templates/header.html`.
  - **Pendiente/fuera de alcance por ahora**: el menú de la versión **móvil** (`templates/header-mobile.html`) tiene un diseño hecho a mano muy distinto (tarjetas con gradiente, acordeones, colores por ítem) y no se conectó a esta misma base de datos — sigue siendo edición directa en el HTML. Conectarlo requeriría rediseñar esa vista para que se ajuste a una estructura genérica.
- Los 3 PDF de "Documentos De Gestión" (Reglamento Institucional, Proyecto Curricular PCI, Manual de Procesos) ahora se reemplazan desde `/admin/` (modelo "Documento de gestión (PDF)" en `core`) en vez de subir un archivo con el nombre exacto que el código esperaba. El resto de PDFs del sitio (tesis, convocatorias, resultados de admisión) ya eran administrables desde antes.
- 4 modales más del menú "Nosotros" ahora son administrables desde `/admin/`:
  - **Misión y Visión**: el texto de ambos bloques se edita desde el modelo "Contenido de modal" (`ContenidoModal`).
  - **Organigrama**: la imagen ahora se reemplaza desde el admin (se movió de `static/img/` a `media/modales/`, que es donde debe vivir un archivo que cambia con el tiempo).
  - **Directorio** (ítem "Directorio" del menú "Nosotros"): el PDF ahora se reemplaza desde `/admin/` igual que los otros documentos (se movió de `static/docs/` a `media/documentos/`).
  - **Historia**: el modelo ya soporta editar su texto desde el admin, pero **no se activó por defecto** — su diseño actual (línea de tiempo con hitos de colores) se simplificaría a texto plano en cuanto alguien lo edite. Se deja así hasta que el dueño del sitio decida conscientemente aceptar ese cambio visual a cambio de poder editarlo.
  - Las ~19 plantillas de modal restantes (Funciones de cada unidad, perfiles de programas, etc.) quedan para una siguiente etapa — tienen un formato de "tarjetas repetidas" distinto que conviene resolver aparte.

### Corregido
- En el desplegable "Unidades" (4 grupos), el último grupo ("Bienestar y Empleabilidad") aparecía muy por debajo del resto en vez de junto a los otros — una grilla de 3 columnas coloca el 4º grupo en una segunda fila completa cuando una de las columnas es más alta que las demás. Se cambió a columnas tipo "mampostería" (se auto-balancean según la altura real de cada grupo), igual que el diseño original que apilaba a mano "U. Académica" y "U. Formación Continua" en una sola columna.

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
