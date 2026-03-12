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
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1200,
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

*¿Cómo usarme?*

Escribe cualquier partido y te hago el análisis completo:

`madrid vs barcelona`
`alaves vs villarreal`
`dortmund vs bayern`
`liverpool vs arsenal`
"""
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    await update.message.reply_text("⏳ Analizando...")

    if re.search(r'\bvs\b|\bvs\.\b|contra|\bv\b', text):
        prompt = f"Analiza el partido: {text}"
    else:
        prompt = text

    response = await ask_claude(prompt)
    
    try:
        await update.message.reply_text(response, parse_mode='Markdown')
    except:
        await update.message.reply_text(response)

def main():
    import httpx as h, time
    try:
        h.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
        time.sleep(2)
    except:
        pass
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot iniciado...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
