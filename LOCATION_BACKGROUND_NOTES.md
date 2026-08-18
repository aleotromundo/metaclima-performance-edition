# Fondo contextual por ubicación

Cuando el GPS entrega coordenadas, MetaClima consulta reverse geocoding de Open-Meteo para identificar ciudad, región y país. Esa identidad aparece en la tarjeta central como contexto del consenso.

Después busca una imagen contextual en Wikimedia Commons usando la ciudad y el país. La imagen se precarga y se aplica al fondo con una capa oscura para mantener legibilidad del glassmorphism. Si no existe imagen, falla la consulta o no hay GPS, se conserva el fondo meteorológico original y se muestra una etiqueta de fallback.

La pantalla inicial y la atmósfera 3D existente se mantienen. La prueba local cargó correctamente y la consola no mostró errores de JavaScript; solo la advertencia estándar sobre Tailwind CDN.
