import os
import httpx
import anthropic
from datetime import datetime, timedelta

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"

# IDs oficiales en football-data.org
TEAM_IDS = {
    "real madrid": 86,
    "madrid": 86,
    "rm": 86,
    "fc barcelona": 81,
    "barcelona": 81,
    "barca": 81,
    "barça": 81,
    "fcb": 81,
    "atletico de madrid": 78,
    "atletico madrid": 78,
    "atletico": 78,
    "atleti": 78,
    "sevilla fc": 559,
    "sevilla": 559,
    "valencia cf": 95,
    "valencia": 95,
    "villarreal cf": 94,
    "villarreal": 94,
    "real betis": 90,
    "betis": 90,
    "real sociedad": 92,
    "sociedad": 92,
    "athletic club": 77,
    "athletic": 77,
    "bilbao": 77,
    "osasuna": 79,
    "girona fc": 298,
    "girona": 298,
    "getafe cf": 82,
    "getafe": 82,
    "rayo vallecano": 87,
    "rayo": 87,
    "celta de vigo": 558,
    "celta": 558,
    "rcd mallorca": 89,
    "mallorca": 89,
    "deportivo alaves": 263,
    "alaves": 263,
    "ud las palmas": 275,
    "las palmas": 275,
    "cd leganes": 745,
    "leganes": 745,
    "rcd espanyol": 80,
    "espanyol": 80,
    "espanol": 80,
    # Inglaterra
    "arsenal fc": 57,
    "arsenal": 57,
    "chelsea fc": 61,
    "chelsea": 61,
    "liverpool fc": 64,
    "liverpool": 64,
    "manchester city fc": 65,
    "manchester city": 65,
    "man city": 65,
    "city": 65,
    "manchester united fc": 66,
    "manchester united": 66,
    "man united": 66,
    "united": 66,
    "tottenham hotspur fc": 73,
    "tottenham": 73,
    "spurs": 73,
    "newcastle united fc": 67,
    "newcastle": 67,
    "aston villa fc": 58,
    "aston villa": 58,
    "west ham united fc": 563,
    "west ham": 563,
    "brighton": 397,
    "everton fc": 62,
    "everton": 62,
    "fulham fc": 63,
    "fulham": 63,
    "brentford fc": 402,
    "brentford": 402,
    "crystal palace fc": 354,
    "crystal palace": 354,
    "nottingham forest fc": 351,
    "nottingham": 351,
    "forest": 351,
    "bournemouth": 1044,
    "wolverhampton": 76,
    "wolves": 76,
    "leicester city fc": 338,
    "leicester": 338,
    "ipswich town fc": 349,
    "ipswich": 349,
    "southampton fc": 340,
    "southampton": 340,
    # Alemania
    "fc bayern munchen": 5,
    "bayern munich": 5,
    "bayern": 5,
    "borussia dortmund": 4,
    "dortmund": 4,
    "bvb": 4,
    "bayer 04 leverkusen": 3,
    "leverkusen": 3,
    "rb leipzig": 721,
    "leipzig": 721,
    "eintracht frankfurt": 19,
    "frankfurt": 19,
    "vfb stuttgart": 10,
    "stuttgart": 10,
    # Italia
    "juventus fc": 109,
    "juventus": 109,
    "juve": 109,
    "fc internazionale milano": 108,
    "inter milan": 108,
    "inter": 108,
    "ac milan": 98,
    "milan": 98,
    "ssc napoli": 113,
    "napoli": 113,
    "as roma": 100,
    "roma": 100,
    "ss lazio": 110,
    "lazio": 110,
    "atalanta bc": 102,
    "atalanta": 102,
    # Francia
    "paris saint-germain fc": 524,
    "psg": 524,
    "paris": 524,
    "olympique de marseille": 516,
    "marseille": 516,
    "olympique lyonnais": 523,
    "lyon": 523,
    "as monaco fc": 548,
    "monaco": 548,
    # Portugal
    "sl benfica": 294,
    "benfica": 294,
    "fc porto": 503,
    "porto": 503,
    "sporting cp": 498,
    "sporting": 498,
}

LEAGUE_IDS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "PPL": "Primeira Liga",
    "CL": "Champions League",
}

def resolve_team_id(alias: str) -> int:
    return TEAM_IDS.get(alias.lower().strip())

async def get_team_matches(team_id: int, limit: int = 5) -> list:
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_from = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{FOOTBALL_BASE_URL}/teams/{team_id}/matches",
                headers=headers,
                params={
                    "status": "FINISHED",
                    "dateFrom": date_from,
                    "dateTo": date_to,
                    "limit": limit
                },
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("matches", [])
        except Exception as e:
            print(f"Error obteniendo partidos: {e}")
    return []

async def get_upcoming_matches() -> list:
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_from = datetime.now().strftime("%Y-%m-%d")
    date_to = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
    
    all_matches = []
    leagues = ["PL", "PD", "BL1", "SA", "FL1", "CL"]
    
    async with httpx.AsyncClient() as client:
        for league in leagues:
            try:
                response = await client.get(
                    f"{FOOTBALL_BASE_URL}/competitions/{league}/matches",
                    headers=headers,
                    params={
                        "dateFrom": date_from,
                        "dateTo": date_to,
                        "status": "SCHEDULED"
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get("matches", [])
                    for m in matches:
                        m["league"] = LEAGUE_IDS.get(league, league)
                    all_matches.extend(matches)
            except Exception as e:
                print(f"Error league {league}: {e}")
    
    return all_matches

def format_matches(matches: list) -> str:
    result = []
    for m in matches[:5]:
        home = m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("name", "?")
        score = m.get("score", {}).get("fullTime", {})
        hg = score.get("home", "?")
        ag = score.get("away", "?")
        date = m.get("utcDate", "")[:10]
        comp = m.get("competition", {}).get("name", "")
        result.append(f"{date} | {comp} | {home} {hg}-{ag} {away}")
    return "\n".join(result) if result else "Sin datos disponibles"

async def analyze_match(team1_alias: str, team2_alias: str) -> str:
    team1_id = resolve_team_id(team1_alias)
    team2_id = resolve_team_id(team2_alias)
    
    team1_name = team1_alias.title()
    team2_name = team2_alias.title()
    
    for key, val in TEAM_IDS.items():
        if val == team1_id and len(key) > len(team1_alias):
            team1_name = key.title()
            break
    for key, val in TEAM_IDS.items():
        if val == team2_id and len(key) > len(team2_alias):
            team2_name = key.title()
            break

    team1_recent = "Sin datos disponibles"
    team2_recent = "Sin datos disponibles"

    if team1_id:
        matches = await get_team_matches(team1_id)
        team1_recent = format_matches(matches)
    
    if team2_id:
        matches = await get_team_matches(team2_id)
        team2_recent = format_matches(matches)

    prompt = f"""Eres un analista experto en fútbol y apuestas deportivas. Analiza este partido:

PARTIDO: {team1_name} vs {team2_name}

ÚLTIMOS PARTIDOS DE {team1_name}:
{team1_recent}

ÚLTIMOS PARTIDOS DE {team2_name}:
{team2_recent}

Basándote en estos datos y en tu conocimiento del fútbol europeo actual, proporciona este análisis EXACTO:

📊 *{team1_name} vs {team2_name}*

🏠 *Local/Visita:* [quién juega en casa y por qué]
🏆 *Competición:* [nombre de la competición]

📈 *Forma {team1_name}:* [análisis breve de sus últimos resultados]
📉 *Forma {team2_name}:* [análisis breve de sus últimos resultados]

💪 *Motivación:*
- {team1_name}: [motivación real para este partido]
- {team2_name}: [motivación real para este partido]

⚽ *Tendencia goles:* [más 1.5 o menos 3.5, con justificación]
🟨 *Tarjetas estimadas:* [número estimado]
🚩 *Corners estimados:* [número estimado]

---
🎯 *APUESTA SUGERIDA:*
✅ [ganador o doble oportunidad] — [X]%
⚽ [más/menos X.X goles]
📊 Confianza: [X]%

_Análisis orientativo. No garantiza resultado._"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"❌ Error al generar análisis: {str(e)}"

async def get_recommendations(bet_type: str) -> str:
    upcoming = await get_upcoming_matches()
    
    if not upcoming:
        return "❌ No encontré partidos próximos. Intenta más tarde."
    
    matches_text = []
    for m in upcoming[:30]:
        home = m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("name", "?")
        date = m.get("utcDate", "")[:16].replace("T", " ")
        league = m.get("league", "")
        matches_text.append(f"{date} | {league} | {home} vs {away}")
    
    matches_str = "\n".join(matches_text)
    
    if bet_type == "1X":
        instruction = "Selecciona los 5 partidos donde el equipo LOCAL tiene mayor probabilidad de ganar o empatar (doble oportunidad 1X). Cuota mínima estimada 1.30."
        title = "🏠 Top 5 para apostar *1X* (Local o Empate)"
    elif bet_type == "over_1.5":
        instruction = "Selecciona los 5 partidos con mayor probabilidad de terminar con MÁS DE 1.5 goles. Cuota mínima estimada 1.30."
        title = "⚽ Top 5 para *Más de 1.5 goles*"
    else:
        instruction = "Selecciona los 5 partidos con mayor probabilidad de terminar con MENOS DE 3.5 goles. Cuota mínima estimada 1.30."
        title = "🔒 Top 5 para *Menos de 3.5 goles*"
    
    prompt = f"""Eres un analista experto en apuestas de fútbol.

PARTIDOS PRÓXIMOS:
{matches_str}

TAREA: {instruction}

Responde con este formato EXACTO:

{title}

1. 🏆 [Liga] | [Equipo A] vs [Equipo B]
   📅 [Fecha y hora]
   📊 Probabilidad: [X]%
   💰 Cuota estimada: [X.XX]
   📝 [motivo breve]

[repetir para los 5 partidos]

_Análisis orientativo. No garantiza resultado._"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"❌ Error al generar recomendaciones: {str(e)}"
