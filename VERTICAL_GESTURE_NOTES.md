# Gesto vertical de tarjetas

Se agregó un gesto vertical separado del desplazamiento horizontal. Si el dedo se mueve principalmente hacia arriba o abajo, la tarjeta rota brevemente sobre los ejes X/Y/Z, se desplaza unos píxeles y vuelve con una animación elástica. Si el gesto es horizontal, el carrusel conserva su comportamiento normal.

El efecto usa pointer events, funciona con mouse y tacto, limita la rotación para evitar mareos y respeta prefers-reduced-motion mediante las reglas existentes.

La pantalla inicial se verificó en local y la consola solo muestra la advertencia habitual de Tailwind CDN; no hay errores de JavaScript.
