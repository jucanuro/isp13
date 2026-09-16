# Changelog

Registro de cambios de código relevantes para el dueño del proyecto `isp13`.

## [2026-09-15]

### Añadido
- Mensajes visuales de confirmación/error (arriba a la derecha) en **todo el sitio**: antes, al guardar un formulario (por ejemplo "Registrar Tesis"), la página se recargaba sin ningún aviso y no había forma de saber si se guardó o falló; ahora se muestra un mensaje verde de éxito o uno rojo con el detalle del error.
- Nuevo acceso directo "Biblioteca" (ícono de libro) en el menú flotante de la página de inicio, junto al de "Repositorio".
- Filtros por programa académico y por año de publicación en `/repositorios/`, además de la búsqueda por texto que ya existía.
- Paginación real en `/repositorios/` (9 tesis por página, con controles anterior/siguiente y números de página), con recorte de la lista de páginas (`1 … 10 11 12 13 14 … 23`) para que no se listen cientos de números si hay muchos resultados.
- Comando de administración `seed_repositorio` para generar tesis de prueba publicadas (uso interno/desarrollo, no afecta producción).
- Contador de caracteres (`0/500`) en el campo "Título de la obra" del formulario de registro de tesis, y mensaje de error al salir del campo si queda vacío o con menos de 10 caracteres.

### Cambiado
- La página del repositorio institucional ahora vive en `/repositorios/` (antes `/repositorio/`).
- El botón "Explorar Repositorio Completo" ya no aparece dentro de la propia página `/repositorios/` (antes se mostraba ahí mismo, redirigiendo a sí misma); sigue apareciendo en la página de inicio para llevar al repositorio completo.

### Corregido
- El enlace "Inicio" del menú de navegación apuntaba al dominio de producción (`https://13dejuliode1882sp.edu.pe/`) en vez de la página de inicio del propio sitio; ahora usa una ruta interna.
- El botón "Explorar Repositorio Completo" apuntaba a una URL de producción (`https://repositorio.13dejuliode1882sp.edu.pe/repositorio/`); ahora usa una ruta interna.
- `/repositorios/` solo mostraba 5 tesis sin importar cuántas hubiera publicadas, por un límite fijo en la plantilla que ignoraba la paginación ya preparada en el backend.
- `/lista/` (panel de gestión de tesis) listaba un botón por cada página existente (41 con los datos de prueba actuales) en vez de recortar la lista; ahora usa el mismo recorte con "…" que `/repositorios/`.
- En "Registrar Tesis" / "Editar Tesis", si el guardado fallaba (por ejemplo un dato inválido), la página se recargaba por completo y se perdía el PDF ya seleccionado, obligando a volver a adjuntarlo. Ahora el envío se hace sin recargar la página: si falla, se muestra el mensaje de error y el archivo seleccionado se mantiene; si se guarda bien, muestra el mensaje de éxito y recién ahí pasa al listado.
