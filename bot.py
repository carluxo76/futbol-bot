import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from analyzer import analyze_match, get_recommendations
import re

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """⚽ *Bot de Análisis de Fútbol*

*¿Cómo usarme?*

🔍 *Análisis de partido:*
Escribe: `madrid vs barcelona`
Escribe: `alaves vs villarreal`
Escribe: `marsella vs auxerre`

📊 *Buscar partidos 1X (local o empate):*
Escribe: `1X`

⚽ *Buscar partidos con más de 2.5 goles:*
Escribe: `mas 2.5`

_Puedes escribir el nombre del equipo como quieras_
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()

    await update.message.reply_text("⏳ Analizando... dame un momento.")

    # Detectar tipo de consulta
    if re.search(r'\bvs\b|\bvs\.\b|contra|\bv\b', text):
        parts = re.split(r'\bvs\b|\bvs\.\b|contra|\bv\b', text)
        if len(parts) == 2:
            team1 = parts[0].strip()
            team2 = parts[1].strip()
            response = await analyze_match(team1, team2)
        else:
            response = "❌ No entendí el formato. Prueba: `madrid vs barcelona`"

    elif '1x' in text:
        response = await get_recommendations('1X')

    elif 'mas 2.5' in text or 'más 2.5' in text or 'mas2.5' in text or '+2.5' in text:
        response = await get_recommendations('over_2.5')

    else:
        response = "❓ No entendí. Escribe /start para ver los comandos disponibles."

    await update.message.reply_text(response, parse_mode='Markdown')

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot iniciado...")
    app.run_polling()

if __name__ == '__main__':
    main()
