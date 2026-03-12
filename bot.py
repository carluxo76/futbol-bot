import os
import logging
import httpx
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip().replace("\n", "").replace("\r", "")

SYSTEM_PROMPT = """Eres un analista experto en fútbol y apuestas deportivas. 
Cuando te pidan analizar un partido responde SIEMPRE en este formato:

📊 *[Equipo A] vs [Equipo B]*
🏠 *Local:* [quien juega en casa] | 🏆 *Competición:* [liga]
📅 *Fecha probable:* [fecha si la sabes]

📈 *Forma reciente [Equipo A]:*
[últimos 5 resultados aproximados y tendencia]

📉 *Forma reciente [Equipo B]:*
[últimos 5 resultados aproximados y tendencia]

💪 *Motivación:*
- [Equipo A]: [situación en tabla, objetivos]
- [Equipo B]: [situación en tabla, objetivos]

⚽ *Análisis de goles:* [tendencia goles, más o menos 2.5]
🟨 *Estimado tarjetas:* [estimado]
🚩 *Estimado corners:* [estimado]
🏥 *Bajas importantes:* [si las conoces]

---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador o doble oportunidad con % de probabilidad]
⚽ Goles: [más/menos X.X con % de probabilidad]
🚩 Corners: [estimado]

_Análisis basado en conocimiento hasta agosto 2025. No garantiza resultado._

Cuando te pidan picks 1X responde con 5 partidos próximos donde el local tiene ventaja clara.
Cuando te pidan picks mas 2.5 responde con 5 partidos con tendencia a muchos goles.
Sé directo y conciso."""

async def ask_claude(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
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

🔍 *Análisis de partido:*
`madrid vs barcelona`
`alaves vs villarreal`
`dortmund vs bayern`

📊 *Picks recomendados:*
`1X` → partidos con local favorito
`mas 2.5` → partidos con muchos goles
"""
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    await update.message.reply_text("⏳ Analizando...")

    if re.search(r'\bvs\b|\bvs\.\b|contra|\bv\b', text):
        prompt = f"Analiza el partido: {text}"
    elif '1x' in text:
        prompt = "Dame 5 picks 1X (local o empate) para los próximos días en las principales ligas europeas. Para cada partido indica equipos, liga, por qué el local tiene ventaja y probabilidad estimada."
    elif 'mas 2.5' in text or 'más 2.5' in text or '+2.5' in text:
        prompt = "Dame 5 picks de más de 2.5 goles para los próximos días en las principales ligas europeas. Para cada partido indica equipos, liga, por qué esperas muchos goles y probabilidad estimada."
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
