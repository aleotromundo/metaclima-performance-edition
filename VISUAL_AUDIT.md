# Auditoría visual de MetaClima

## Estado inicial

La pantalla inicial carga correctamente en escritorio. El canvas atmosférico queda detrás del contenido, el header permanece legible y la tarjeta de consenso está centrada. No se observaron errores de JavaScript en consola, aparte de la advertencia conocida de Tailwind CDN.

## Dashboard simulado

Con un viewport de 1280x1100, las tarjetas se renderizan con alturas iguales de 617px y anchos de 350px, 390px y 400px. La tarjeta central empieza en x=420 y las laterales en x=46 y x=834. El conjunto supera el ancho visible, por lo que el contenedor depende correctamente de overflow horizontal; en escritorio conviene revisar el centrado porque la suma de anchos y gaps puede provocar que el carrusel quede ligeramente cortado en algunos anchos.

## Puntos a revisar

1. El dashboard puede quedar demasiado alto en pantallas de poca altura porque las tres tarjetas igualan su altura al contenido más largo.
2. La capa de interacción de tarjetas usa varios listeners de pointer sobre los mismos elementos; debe evitarse que el tilt normal y el spin de inercia se pisen al soltar.
3. El gesto vertical debe conservar `touch-action: pan-x` para no romper el carrusel horizontal.
4. La tarjeta central y el canvas necesitan mantener su jerarquía de z-index después de una animación Web Animations API.
5. El contenedor horizontal debe conservar padding suficiente en móvil para que la tarjeta central pueda encajar centrada.

## Auditoría móvil actualizada

En 390px se detectó un solapamiento entre el HUD atmosférico, el parlante flotante y el footer. Se corrigieron las posiciones móviles: el HUD se elevó, el parlante se ubicó por encima del pie y la etiqueta quedó alineada junto al control. La captura `mobile-audit-fixed.png` confirma que los elementos quedan separados y legibles.

## Auditoría del carrusel y permisos

La medición en navegador confirmó el orden visual aplicado: `card-yesterday` order 1, `card-left` order 2, `card-center` order 3, `card-right` order 4 y `card-tomorrow` order 5. La corrección fue necesaria porque el selector inicial apuntaba a un ID inexistente. El flujo de ubicación ahora guarda coordenadas en `localStorage`, consulta el estado de permiso y reutiliza la ubicación guardada cuando el permiso está concedido.

## Dashboard activo e inmersividad

Con datos reales de prueba en Buenos Aires, el dashboard mostró Variables Locales, Hoy/Consenso y Próximas 12 Horas en el orden correcto, con Ayer y Mañana fuera de los extremos del carrusel. El mapa permanece dentro de Próximas 12 Horas. La capa atmosférica cambió a `CLOUD FIELD`, el fondo contextual se actualizó y el parlante siguió visible sin tapar el contenido principal. La consola no mostró errores nuevos, solo la advertencia existente de Tailwind CDN.
