# ⚽ Bot de Análisis de Fútbol - Telegram

## Variables de entorno necesarias en Railway:

| Variable | Descripción |
|---|---|
| `TELEGRAM_TOKEN` | Token de @BotFather |
| `FOOTBALL_API_KEY` | API Key de football-data.org |
| `ANTHROPIC_API_KEY` | API Key de Anthropic (Claude) |

## Comandos del bot:

- `madrid vs barcelona` → Análisis completo del partido
- `1X` → Top 5 partidos para apostar Local o Empate
- `mas 1.5` → Top 5 partidos con más de 1.5 goles
- `menos 3.5` → Top 5 partidos con menos de 3.5 goles
- `/start` → Ver ayuda

## Equipos reconocidos:
El bot reconoce nombres en cualquier formato:
- barca, barça, fcb, barcelona → FC Barcelona
- madrid, rm, real madrid → Real Madrid
- city, man city → Manchester City
- etc.
