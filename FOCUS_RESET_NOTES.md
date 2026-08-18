# Restauración de tarjetas fuera de foco

Se añadió una sincronización de selección basada en la tarjeta más cercana al centro visible del carrusel. Al cambiar el scroll, las tarjetas que dejan de ser seleccionadas cancelan cualquier animación activa, eliminan el transform inline y vuelven a su estado original.

La pantalla inicial se verificó visualmente después del cambio: header, tarjeta de consenso, fondo atmosférico, footer y CTA permanecen en su posición. La consola no muestra errores nuevos; solo aparece la advertencia estándar de Tailwind CDN.
