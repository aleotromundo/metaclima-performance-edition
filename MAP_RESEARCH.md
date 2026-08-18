# Investigación del mapa meteorológico expandible

Open-Meteo ofrece variables actuales y horarias por coordenadas, incluyendo temperatura, sensación térmica, presión, humedad, nubosidad, viento, dirección del viento, precipitación y visibilidad. La API no requiere clave para uso no comercial y selecciona modelos meteorológicos aplicables a cada ubicación.

Leaflet permite un mapa interactivo con mouse y tacto, marcadores, círculos, popups y capas de tiles. La cartografía base puede usar OpenStreetMap, con atribución visible y respeto de su política de uso.

RainViewer publica un JSON de radar con marcos pasados de diez minutos y URLs de tiles para mostrar precipitación/radar. Se puede usar como capa opcional, siempre indicando que el radar tiene cobertura regional y no reemplaza el consenso puntual de Open-Meteo + MET Norway.

Diseño recomendado: tarjeta lateral izquierda con mapa cenital ampliable y pin GPS; tarjeta lateral derecha con panel de viento/precipitación y una vista expandida de detalles. En móvil, tocar cualquiera de los módulos abre un modal o tarjeta expandida; en escritorio, hover/ click muestra la vista detallada sin bloquear el carrusel.

Fuentes:
- https://open-meteo.com/en/docs
- https://leafletjs.com/examples/quick-start/
- https://www.rainviewer.com/api/weather-maps-api.html
