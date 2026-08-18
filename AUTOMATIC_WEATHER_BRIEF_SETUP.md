# Activación del briefing meteorológico automático

El generador ya quedó preparado en `automation/generate_weather_brief.py` y el workflow en `.github/workflows/weather-brief.yml`.

## Qué hace

Cada dos horas, el workflow consulta Open-Meteo para las coordenadas configuradas, envía ese JSON meteorológico real a Gemini para redactar un informe corto adaptado a la hora local, genera un MP3 con la voz gratuita Piper `es_AR-daniela-high`, lo convierte a MP3 y lo sube con una ruta única. Si Gemini no está configurado, el fallback local sigue usando los valores reales consultados; no hay un texto meteorológico fijo.

```text
weather-briefs/<location_key>/<YYYY-MM-DD>/<slot>.mp3
```

La fila de Supabase se inserta en estado `staging`. No se modifica el lote publicado durante el día. Al comenzar el día siguiente, cuando el lote anterior tiene las doce franjas esperadas, el proceso llama a `publish_daily_brief_batch` y publica el lote cerrado completo.

El generador evita crear otra versión si para la franja actual el `forecast_hash` no cambió. La página consulta `current_weather_brief`, ordena por `generated_at` descendente y reproduce la última versión del lote que fue publicado.

## Secretos necesarios en GitHub

En el repositorio `aleotromundo/metaclima-performance-edition`, crear estos Actions secrets:

| Secreto | Valor |
|---|---|
| `SUPABASE_URL` | `https://orgaltiwyywxpjmderzq.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | La clave `service_role` del proyecto Supabase. Nunca ponerla en `index.html`. |
| `META_CLIMA_LAT` | Latitud del lugar base. |
| `META_CLIMA_LON` | Longitud del lugar base. |
| `META_CLIMA_LOCATION_LABEL` | Nombre del barrio o ciudad. |
| `META_CLIMA_TIMEZONE` | Por ejemplo `America/Argentina/Buenos_Aires`. |
| `GOOGLE_API_KEY` | Nueva clave de Google Gemini, guardada únicamente como secreto de GitHub. |
| `GOOGLE_GEMINI_MODEL` | Opcional; por defecto `gemini-2.5-flash`. |

El generador necesita una ubicación base porque un workflow programado no puede pedir permiso GPS a cada visitante. Para soportar muchas ubicaciones distintas, posteriormente se puede convertir el proceso en una cola de ubicaciones administrada desde Supabase.

## SQL pendiente

Ejecutar una vez en Supabase:

```text
supabase_daily_brief_versioning_migration.sql
```

La migración agrega lotes diarios, versiones staging, el puntero público y la función protegida de publicación.

## Prueba manual

Después de crear los secretos, abrir GitHub Actions, elegir `MetaClima · briefing meteorológico` y ejecutar `Run workflow`. El primer resultado debe mostrar `STAGED ...` y dejar el audio en el bucket `weather-briefs` sin publicarlo hasta que el lote se cierre según la política diaria.
