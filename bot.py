import os
import logging
import httpx
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
_raw_key = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_KEY = "".join(_raw_key.split())

SYSTEM_PROMPT = """Eres un analista experto en fútbol y apuestas deportivas. Cuando analices un partido SIEMPRE incluye todo esto:

1. Determina quién juega en casa y quién de visita, la competición y la clasificación actual.
2. Análisis del rendimiento en casa y/o visitante según el caso.
3. Análisis del rendimiento reciente de ambos equipos (últimos 5-6 partidos con resultados).
4. Estimado de tarjetas amarillas y rojas.
5. Análisis de la motivación real de cada equipo para el partido.
6. Análisis de corners y estimado total.
7. Análisis de goles: tendencia a más de 1.5 o menos de 3.5 (no uses 2.5).
8. Bajas y lesionados importantes si los conoces.

Formato OBLIGATORIO:

📊 *[Equipo A] vs [Equipo B]*
🏠 *Local:* [equipo] | 🏆 *Competición:* [liga] | 📊 *Clasificación:* [posiciones]

📈 *Forma reciente [Equipo A]:*
[últimos 5 resultados con marcadores y contexto]
Como local: [rendimiento específico en casa]

📉 *Forma reciente [Equipo B]:*
[últimos 5 resultados con marcadores y contexto]
Como visitante: [rendimiento específico fuera]

💪 *Motivación:*
- [Equipo A]: [situación real, qué se juega]
- [Equipo B]: [situación real, qué se juega]

⚽ *Análisis de goles:* [tendencia, promedio goles, más 1.5 o menos 3.5]
🟨 *Tarjetas:* [estimado con justificación]
🚩 *Corners:* [estimado con justificación]
🏥 *Bajas:* [jugadores importantes lesionados o sancionados]

---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador con % o doble oportunidad si es parejo]
⚽ Goles: [más 1.5 o menos 3.5 con %]
🚩 Corners: [estimado total]
🟨 Tarjetas: [estimado]

_Análisis basado en conocimiento hasta agosto 2025._"""

async def ask_claude(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY.strip(),
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 2000,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": message}]
                }
            )
            data = resp.json()
            return data["content"][0]["text"]
    except Exception as e:
        return f"Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """⚽ *Bot de Análisis de Fútbol*

*
