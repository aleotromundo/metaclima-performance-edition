# Fuentes meteorológicas gratuitas verificadas

## Open-Meteo
Fuente oficial: https://open-meteo.com/en/pricing

Open-Meteo ofrece más de 30 modelos meteorológicos, incluyendo ECMWF, DWD, NOAA, Météo-France, JMA, KMA, KNMI, DMI, MeteoSwiss, UK Met Office, BOM, CMA y GeoSphere Austria. La opción `best_match` selecciona automáticamente el modelo de mayor resolución para las coordenadas. La API abierta es gratuita para uso no comercial, sin clave, con límites publicados de aproximadamente 600 llamadas por minuto, 5.000 por hora y 10.000 por día; la página también menciona un límite mensual de 300.000 llamadas para el nivel gratuito. Requiere atribución CC BY 4.0. La modalidad comercial requiere suscripción y endpoint dedicado.

## MET Norway
Fuente oficial: https://api.met.no/weatherapi/locationforecast/2.0/documentation

Locationforecast ofrece pronósticos para cualquier coordenada del planeta durante los próximos nueve días. El endpoint JSON compacto ya se usa en MetaClima. MET Norway exige un User-Agent identificable y puede responder 403 si no se cumple la identificación; el servicio es gratuito y tiene mayor detalle en regiones nórdicas y árticas, aunque proporciona cobertura global.

## National Weather Service / NOAA
Fuente oficial: https://www.weather.gov/documentation/services-web-API

La API NWS es gratuita y de datos abiertos, con pronósticos, observaciones y alertas. Su cobertura operativa es Estados Unidos y territorios bajo su servicio; no es una fuente aplicable como motor principal para Argentina. Puede agregarse como adaptador condicional cuando las coordenadas estén dentro de su cobertura, pero no conviene llamarla para todos los usuarios.

## RainViewer
Fuentes oficiales: https://www.rainviewer.com/api.html y https://www.rainviewer.com/api/weather-maps-api.html

RainViewer ofrece una API pública gratuita para uso personal, educativo y pequeños proyectos comunitarios, sin clave. Expone tiles de radar de las últimas dos horas en intervalos de diez minutos. Desde enero de 2026 el servicio gratuito mantiene los tiles de radar pasado, limita el zoom máximo a 7 y conserva únicamente el esquema de color Universal Blue. Exige atribución visible y no garantiza SLA. La URL de tile debe construirse usando el `host` y `path` actuales del JSON, que ahora pueden incluir una ruta hash.

## Decisión técnica provisional

Para MetaClima en Argentina, el consenso gratuito base debe ser Open-Meteo + MET Norway, aprovechando que Open-Meteo ya integra múltiples modelos independientes. RainViewer debe ser una capa visual de radar, no un motor de temperatura. NWS debe ser opcional y geográficamente condicional. No se deben sumar servicios que requieran API key o facturación sin que el usuario los proporcione y acepte sus límites.
