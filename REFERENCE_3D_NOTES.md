# Ideas 3D adoptadas del HTML de referencia

Se adoptó el patrón de tarjetas con `transform-style: preserve-3d`, perspectiva, rotación X/Y y elevación visual mediante `translateZ`. En escritorio, el movimiento sigue el cursor con una respuesta suave; en móvil, pointer events permiten que el dedo incline la tarjeta durante el contacto sin bloquear el desplazamiento horizontal del carrusel.

También se mantuvo la idea de un héroe flotante, canvas atmosférico y cambios de ambiente según sol, nubes o lluvia. No se copió el rediseño completo ni se cambió la estructura original de MetaClima.

La prueba local confirmó que la pantalla original carga, el canvas atmosférico continúa visible y la consola solo muestra la advertencia estándar de Tailwind CDN, sin errores de JavaScript.
