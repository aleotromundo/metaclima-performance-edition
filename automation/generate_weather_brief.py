#!/usr/bin/env python3
"""MetaClima: genera una versión breve del informe meteorológico y la guarda en Supabase.

El proceso está pensado para ejecutarse cada dos horas. Las versiones se guardan como
archivos inmutables dentro del lote local del día y como filas staging. El puntero público
solo se cambia en el cambio de día o en el bootstrap inicial.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import Any

import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
LAT = float(os.environ.get("META_CLIMA_LAT", "-34.6037"))
LON = float(os.environ.get("META_CLIMA_LON", "-58.3816"))
LOCATION_LABEL = os.environ.get("META_CLIMA_LOCATION_LABEL", "tu barrio")
TIMEZONE = os.environ.get("META_CLIMA_TIMEZONE", "America/Argentina/Buenos_Aires")
VOICE_NAME = os.environ.get("PIPER_VOICE", "es_AR-daniela-high")
PIPER_MODEL_PATH = os.environ.get("PIPER_MODEL_PATH", "models/es_AR-daniela-high.onnx")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_GEMINI_MODEL = os.environ.get("GOOGLE_GEMINI_MODEL", "gemini-2.5-flash")
AUDIO_DIR = pathlib.Path(os.environ.get("AUDIO_OUTPUT_DIR", "automation/output"))
EXPECTED_SLOTS = int(os.environ.get("EXPECTED_DAILY_SLOTS", "12"))

session = requests.Session()
session.headers.update({"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"})


def local_now() -> dt.datetime:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        return dt.datetime.now(dt.timezone.utc)


def slot_key(now: dt.datetime) -> str:
    floored = now.replace(minute=0, second=0, microsecond=0)
    floored = floored.replace(hour=(floored.hour // 2) * 2)
    return floored.strftime("%Y%m%d-%H%M")


def location_key() -> str:
    return f"{LAT:.2f}_{LON:.2f}"


def weather_data() -> dict[str, Any]:
    params = {
        "latitude": LAT, "longitude": LON,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,cloud_cover,wind_speed_10m,weather_code",
        "hourly": "precipitation_probability,temperature_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,weather_code,wind_speed_10m_max",
        "forecast_days": 2, "timezone": TIMEZONE,
    }
    response = session.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def met_label(code: int | None) -> str:
    code = int(code or 0)
    if code in (0, 1): return "cielo abierto o apenas variable"
    if code in (2, 3): return "cielo parcialmente nublado"
    if code in (45, 48): return "nieblas y visibilidad reducida"
    if code in (51, 53, 55, 56, 57): return "lloviznas"
    if code in (61, 63, 65, 66, 67, 80, 81, 82): return "lluvias"
    if code in (71, 73, 75, 77, 85, 86): return "precipitación invernal"
    if code in (95, 96, 99): return "tormentas"
    return "condiciones cambiantes"


def build_brief(data: dict[str, Any], now: dt.datetime) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    current = data["current"]
    hourly = data["hourly"]
    daily = data["daily"]
    temp = round(float(current["temperature_2m"]))
    feels = round(float(current["apparent_temperature"]))
    cloud = round(float(current.get("cloud_cover", 0)))
    wind = round(float(current.get("wind_speed_10m", 0)))
    pop = int(hourly.get("precipitation_probability", [0])[0] or 0)
    code = int(current.get("weather_code", 0))
    condition = met_label(code)
    next_max = round(float(daily["temperature_2m_max"][1]))
    next_min = round(float(daily["temperature_2m_min"][1]))
    next_pop = int(daily.get("precipitation_probability_max", [0, 0])[1] or 0)
    hour = now.hour
    if 5 <= hour < 12:
        greeting, moment, next_window = "Buen día, vecino.", "esta mañana", "la tarde"
    elif 12 <= hour < 19:
        greeting, moment, next_window = "Buenas tardes, vecino.", "esta tarde", "la noche"
    elif hour >= 19 or hour < 2:
        greeting, moment, next_window = "Buenas noches, vecino.", "esta noche", "mañana temprano"
    else:
        greeting, moment, next_window = "Todavía queda noche por delante, vecino.", "la madrugada", "el comienzo del día"
    rain_line = "Hay que tener el paraguas cerca." if pop >= 55 else "Por ahora no parece un día para salir preocupado por la lluvia."
    dialogue = [
        {"host": "A", "text": f"{greeting} Por {LOCATION_LABEL}, {moment} tenemos {temp} grados, aunque la sensación anda cerca de {feels}. El cielo viene con {condition} y una nubosidad del {cloud} por ciento."},
        {"host": "A", "text": f"El viento está en unos {wind} kilómetros por hora y la probabilidad de lluvia inmediata ronda el {pop} por ciento. {rain_line}"},
        {"host": "A", "text": f"Hacia {next_window} el panorama puede moverse un poco. Mañana se esperan unos {next_max} grados de máxima, {next_min} de mínima y una chance de lluvia del {next_pop} por ciento."},
        {"host": "A", "text": "En resumen: mirá el cielo antes de salir y más tarde volvemos a asomarnos para ver qué cambió."},
    ]
    snapshot = {"current": current, "temp": temp, "pop": pop, "wind": wind, "cloud": cloud, "code": code, "next_max": next_max, "next_min": next_min, "next_pop": next_pop}
    forecast_hash = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()[:24]
    return dialogue, snapshot, forecast_hash


def generate_ai_dialogue(data: dict[str, Any], snapshot: dict[str, Any], now: dt.datetime) -> list[dict[str, str]]:
    """Redacta el texto con datos reales; si Gemini no está configurado, usa el fallback real local."""
    if not GOOGLE_API_KEY:
        return build_brief(data, now)[0]
    hour = now.hour
    moment = "mañana" if 5 <= hour < 12 else "tarde" if 12 <= hour < 19 else "noche" if hour >= 19 or hour < 2 else "madrugada"
    payload = {"hora_local": now.isoformat(), "franja": moment, "barrio": LOCATION_LABEL, "datos": data, "resumen": snapshot}
    prompt = ("Escribí un informe meteorológico breve para un vecino, en español rioplatense natural. "
              "Usá exclusivamente los datos JSON reales de esta ejecución: no inventes valores, no menciones APIs, IA, aplicaciones ni fuentes técnicas. "
              "Debe durar aproximadamente 45 a 65 segundos al leerse en voz alta, tener cuatro intervenciones del mismo narrador, adaptarse a la franja horaria indicada, "
              "mencionar temperatura, sensación, nubosidad, lluvia, viento y el panorama siguiente, y cerrar invitando a volver a mirar más tarde. "
              'Devolvé únicamente JSON con la forma {"dialogue":[{"host":"A","text":"..."}]}. Datos reales: '
              + json.dumps(payload, ensure_ascii=False))
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_GEMINI_MODEL}:generateContent"
    response = requests.post(endpoint, params={"key": GOOGLE_API_KEY}, json={
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.65,
            "responseMimeType": "application/json",
            "responseSchema": {"type": "OBJECT", "properties": {"dialogue": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"host": {"type": "STRING"}, "text": {"type": "STRING"}}, "required": ["host", "text"]}}}, "required": ["dialogue"]}
        }
    }, timeout=30)
    response.raise_for_status()
    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    dialogue = json.loads(raw).get("dialogue", [])
    if not dialogue:
        raise RuntimeError("Gemini devolvió un diálogo vacío")
    return [{"host": "A", "text": str(item["text"]).strip()} for item in dialogue[:5] if str(item.get("text", "")).strip()]


def supabase_json(method: str, path: str, **kwargs: Any) -> requests.Response:
    response = session.request(method, f"{SUPABASE_URL}/rest/v1/{path}", timeout=30, **kwargs)
    if not response.ok:
        raise RuntimeError(f"Supabase {method} {path}: {response.status_code} {response.text[:400]}")
    return response


def run_piper(text: str, output_mp3: pathlib.Path) -> None:
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = pathlib.Path(tmp) / "brief.wav"
        subprocess.run(["piper", "--model", PIPER_MODEL_PATH, "--output_file", str(wav)], input=text.encode("utf-8"), check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(output_mp3)], check=True)


def upload_audio(local_file: pathlib.Path, remote_path: str) -> None:
    response = session.post(
        f"{SUPABASE_URL}/storage/v1/object/weather-briefs/{remote_path}",
        data=local_file.read_bytes(),
        headers={"Content-Type": "audio/mpeg", "x-upsert": "false"},
        timeout=60,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(f"Storage upload failed: {response.status_code} {response.text[:400]}")


def previous_published_batch(batch: str) -> str | None:
    try:
        response = supabase_json("GET", "daily_brief_publications", params={"select": "batch_key", "location_key": f"eq.{location_key()}", "limit": "1"})
        rows = response.json()
        return rows[0]["batch_key"] if rows else None
    except Exception:
        return None


def publish_previous_batch(previous_batch: str | None, now: dt.datetime) -> None:
    if not previous_batch:
        return
    response = supabase_json("GET", "daily_briefs", params={"select": "id", "location_key": f"eq.{location_key()}", "batch_key": f"eq.{previous_batch}", "batch_status": "eq.staging"})
    rows = response.json()
    if len(rows) < EXPECTED_SLOTS:
        print(f"WAIT {previous_batch}: {len(rows)}/{EXPECTED_SLOTS} slots; no se publica todavía")
        return
    rpc = session.post(f"{SUPABASE_URL}/rest/v1/rpc/publish_daily_brief_batch", json={"p_location_key": location_key(), "p_batch_key": previous_batch, "p_published_local_date": previous_batch}, timeout=30)
    if not rpc.ok:
        raise RuntimeError(f"Publish batch failed: {rpc.status_code} {rpc.text[:400]}")
    print(f"PUBLISHED {previous_batch}: lote cerrado y visible para el público")


def stage_row(now: dt.datetime, batch: str, slot: str, dialogue: list[dict[str, str]], snapshot: dict[str, Any], forecast_hash: str, audio_path: str) -> None:
    payload = {"location_key": location_key(), "location_label": LOCATION_LABEL, "latitude": LAT, "longitude": LON, "local_date": now.date().isoformat(), "batch_key": batch, "slot_key": slot, "forecast_hash": forecast_hash, "weather_snapshot": snapshot, "dialogue": dialogue, "audio_path": audio_path, "audio_mime_type": "audio/mpeg", "duration_seconds": 60, "voice_provider": "piper", "voice_name": VOICE_NAME, "generation_reason": "scheduled_2h", "is_current": False, "batch_status": "staging", "generated_at": now.isoformat()}
    supabase_json("POST", "daily_briefs", json=payload, headers={"Prefer": "return=minimal"})


def should_skip(batch: str, slot: str, forecast_hash: str) -> bool:
    response = supabase_json("GET", "daily_briefs", params={"select": "id,forecast_hash", "location_key": f"eq.{location_key()}", "batch_key": f"eq.{batch}", "slot_key": f"eq.{slot}", "limit": "1"})
    rows = response.json()
    return bool(rows and rows[0].get("forecast_hash") == forecast_hash)


def main() -> int:
    now = local_now()
    batch, slot = now.date().isoformat(), slot_key(now)
    previous_batch = (now.date() - dt.timedelta(days=1)).isoformat()
    publish_previous_batch(previous_batch, now)
    data = weather_data()
    dialogue, snapshot, forecast_hash = build_brief(data, now)
    dialogue = generate_ai_dialogue(data, snapshot, now)
    if should_skip(batch, slot, forecast_hash):
        print(f"SKIP {batch} {slot}: sin cambio meteorológico")
        return 0
    text = " ".join(item["text"] for item in dialogue)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    local_file = AUDIO_DIR / f"brief-{batch}-{slot}.mp3"
    run_piper(text, local_file)
    remote_path = f"{location_key()}/{batch}/{slot}.mp3"
    upload_audio(local_file, remote_path)
    stage_row(now, batch, slot, dialogue, snapshot, forecast_hash, remote_path)
    print(f"STAGED {remote_path}")
    print("El lote queda staging y no pisa el audio público durante el día.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
