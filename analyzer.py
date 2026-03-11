import os
import httpx
import anthropic
from datetime import datetime, timedelta

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"

# Diccionario de alias de equipos
TEAM_ALIASES = {
    # España
    "madrid": "Real Madrid",
    "real madrid": "Real Madrid",
    "rm": "Real Madrid",
    "barca": "FC Barcelona",
    "barça": "FC Barcelona",
    "barcelona": "FC Barcelona",
    "fcb": "FC Barcelona",
    "atletico": "Atlético de Madrid",
    "atletico madrid": "Atlético de Madrid",
    "atleti": "Atlético de Madrid",
    "sevilla": "Sevilla FC",
    "valencia": "Valencia CF",
    "villarreal": "Villarreal CF",
    "betis": "Real Betis",
    "sociedad": "Real Sociedad",
    "athletic": "Athletic Club",
    "bilbao": "Athletic Club",
    "osasuna": "CA Osasuna",
    "girona": "Girona FC",
    "getafe": "Getafe CF",
    "rayo": "Rayo Vallecano",
    "celta": "Celta de Vigo",
    "mallorca": "RCD Mallorca",
    "alaves": "Deportivo Alavés",
    "las palmas": "UD Las Palmas",
    "leganes": "CD Leganés",
    "espanol": "RCD Espanyol",
    "espanyol": "RCD Espanyol",
    
    # Inglaterra
    "arsenal": "Arsenal FC",
    "chelsea": "Chelsea FC",
    "liverpool": "Liverpool FC",
    "city": "Manchester City FC",
    "man city": "Manchester City FC",
    "manchester city": "Manchester City FC",
    "united": "Manchester United FC",
    "man united": "Manchester United FC",
    "manchester united": "Manchester United FC",
    "tottenham": "Tottenham Hotspur FC",
    "spurs": "Tottenham Hotspur FC",
    "newcastle": "Newcastle United FC",
    "aston villa": "Aston Villa FC",
    "west ham": "West Ham United FC",
    "brighton": "Brighton & Hove Albion FC",
    "everton": "Everton FC",
    "fulham": "Fulham FC",
    "wolves": "Wolverhampton Wanderers FC",
    "wolverhampton": "Wolverhampton Wanderers FC",
    "brentford": "Brentford FC",
    "crystal palace": "Crystal Palace FC",
    "nottingham": "Nottingham Forest FC",
    "forest": "Nottingham Forest FC",
    "bournemouth": "AFC Bournemouth",
    "leicester": "Leicester City FC",
    "ipswich": "Ipswich Town FC",
    "southampton": "Southampton FC",
    
    # Alemania
    "bayern": "FC Bayern München",
    "dortmund": "Borussia Dortmund",
    "bvb": "Borussia Dortmund",
    "leverkusen": "Bayer 04 Leverkusen",
    "leipzig": "RB Leipzig",
    "frankfurt": "Eintracht Frankfurt",
    "stuttgart": "VfB Stuttgart",
    "gladbach": "Borussia Mönchengladbach",
    "hoffenheim": "TSG 1899 Hoffenheim",
    "wolfsburg": "VfL Wolfsburg",
    
    # Italia
    "juventus": "Juventus FC",
    "juve": "Juventus FC",
    "inter": "FC Internazionale Milano",
    "inter milan": "FC Internazionale Milano",
    "milan": "AC Milan",
    "ac milan": "AC Milan",
    "napoli": "SSC Napoli",
    "roma": "AS Roma",
    "lazio": "SS Lazio",
    "fiorentina": "ACF Fiorentina",
    "atalanta": "Atalanta BC",
    "torino": "Torino FC",
    "bologna": "Bologna FC 1909",
    
    # Francia
    "psg": "Paris Saint-Germain FC",
    "paris": "Paris Saint-Germain FC",
    "marseille": "Olympique de Marseille",
    "lyon": "Olympique Lyonnais",
    "monaco": "AS Monaco FC",
    "lille": "LOSC Lille",
    "nice": "OGC Nice",
    "lens": "RC Lens",
    "rennes": "Stade Rennais FC",
    
    # Portugal
    "benfica": "SL Benfica",
    "porto": "FC Porto",
    "sporting": "Sporting CP",
    "sporting cp": "Sporting CP",
    
    # Champions
    "psg": "Paris Saint-Germain FC",
}

LEAGUE_IDS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "PPL": "Primeira Liga",
    "CL": "Champions League",
    "EC": "Euros",
    "WC": "World Cup",
}

def resolve_team_name(alias: str) -> str:
    """Convierte alias en nombre oficial del equipo."""
    return TEAM_ALIASES.get(alias.lower().strip(), alias.title())

async def get_team_data(team_name: str) -> dict:
    """Busca datos del equipo en la API."""
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{FOOTBALL_BASE_URL}/teams",
                headers=headers,
                params={"name": team_name},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                teams = data.get("teams", [])
                if teams:
                    return teams[0]
        except Exception as e:
            print(f"Error buscando equipo: {e}")
    return None

async def get_team_matches(team_id: int, limit: int = 5) -> list:
    """Obtiene últimos partidos de un equipo."""
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
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
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("matches", [])
        except Exception as e:
            print(f"Error obteniendo partidos: {e}")
    return []

async def get_upcoming_matches() -> list:
    """Obtiene partidos de los próximos 3 días de las ligas principales."""
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_from = datetime.now().strftime("%Y-%m-%d")
    date_to = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
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
                    timeout=10
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

def format_matches_for_ai(matches: list, team_name: str, is_home: bool) -> str:
    """Formatea partidos para enviar a la IA."""
    result = []
    for m in matches:
        home = m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("name", "?")
        score = m.get("score", {}).get("fullTime", {})
        home_goals = score.get("home", "?")
        away_goals = score.get("away", "?")
        date = m.get("utcDate", "")[:10]
        competition = m.get("competition", {}).get("name", "")
        result.append(f"{date} | {competition} | {home} {home_goals}-{away_goals} {away}")
    return "\n".join(result)

async def analyze_match(team1_alias: str, team2_alias: str) -> str:
    """Análisis completo de un partido."""
    team1_name = resolve_team_name(team1_alias)
    team2_name = resolve_team_name(team2_alias)
    
    # Obtener datos de ambos equipos
    team1_data = await get_team_data(team1_name)
    team2_data = await get_team_data(team2_name)
    
    team1_matches_raw = []
    team2_matches_raw = []
    
    if team1_data:
        team1_matches_raw = await get_team_matches(team1_data["id"])
    if team2_data:
        team2_matches_raw = await get_team_matches(team2_data["id"])
    
    # Formatear datos para la IA
    team1_recent = format_matches_for_ai(team1_matches_raw, team1_name, True) or "Sin datos disponibles"
    team2_recent = format_matches_for_ai(team2_matches_raw, team2_name, False) or "Sin datos disponibles"
    
    team1_area = team1_data.get("area", {}).get("name", "") if team1_data else ""
    team2_area = team2_data.get("area", {}).get("name", "") if team2_data else ""
    
    # Construir prompt para Claude
    prompt = f"""Eres un analista experto en fútbol y mercados de apuestas. Analiza este partido:

PARTIDO: {team1_name} vs {team2_name}

ÚLTIMOS 5 PARTIDOS DE {team1_name} ({team1_area}):
{team1_recent}

ÚLTIMOS 5 PARTIDOS DE {team2_name} ({team2_area}):
{team2_recent}

Basándote en estos datos reales, proporciona un análisis conciso con este formato EXACTO:

📊 *{team1_name} vs {team2_name}*

🏠 *Local/Visita:* Determina quién juega en casa basándote en tu conocimiento del calendario actual.

📈 *Forma reciente {team1_name}:* [análisis breve]
📉 *Forma reciente {team2_name}:* [análisis breve]

💪 *Motivación:*
- {team1_name}: [motivación real]
- {team2_name}: [motivación real]

⚽ *Análisis de goles:* [tendencia goles, más 1.5 o menos 3.5]
🟨 *Estimado tarjetas:* [estimado]
🚩 *Estimado corners:* [estimado]

---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador o doble oportunidad] con [X]%
⚽ Goles: [más/menos X.X]
📊 Confianza general: [X]%

_Análisis basado en datos reales. No garantiza resultado._"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"❌ Error al generar análisis: {str(e)}"

async def get_recommendations(bet_type: str) -> str:
    """Obtiene recomendaciones de partidos según tipo de apuesta."""
    upcoming = await get_upcoming_matches()
    
    if not upcoming:
        return "❌ No encontré partidos próximos. Intenta más tarde."
    
    # Formatear partidos para la IA
    matches_text = []
    for m in upcoming[:30]:  # máximo 30 partidos para no saturar
        home = m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("name", "?")
        date = m.get("utcDate", "")[:16].replace("T", " ")
        league = m.get("league", "")
        matches_text.append(f"{date} | {league} | {home} vs {away}")
    
    matches_str = "\n".join(matches_text)
    
    if bet_type == "1X":
        instruction = "Selecciona los 5 partidos donde el equipo LOCAL tiene mayor probabilidad de ganar o empatar (doble oportunidad 1X). Cuota mínima estimada 1.30."
        title = "🏠 Top 5 partidos para apostar *1X* (Local o Empate)"
    elif bet_type == "over_1.5":
        instruction = "Selecciona los 5 partidos con mayor probabilidad de terminar con MÁS DE 1.5 goles. Cuota mínima estimada 1.30."
        title = "⚽ Top 5 partidos para *Más de 1.5 goles*"
    else:  # under_3.5
        instruction = "Selecciona los 5 partidos con mayor probabilidad de terminar con MENOS DE 3.5 goles. Cuota mínima estimada 1.30."
        title = "🔒 Top 5 partidos para *Menos de 3.5 goles*"
    
    prompt = f"""Eres un analista experto en apuestas de fútbol. 

PARTIDOS PRÓXIMOS:
{matches_str}

TAREA: {instruction}

Responde con este formato EXACTO para cada partido:

{title}

1. 🏆 [Liga] | [Equipo A] vs [Equipo B]
   📅 [Fecha y hora]
   📊 Probabilidad: [X]%
   💰 Cuota estimada: [X.XX]
   📝 Razón: [motivo breve en 1 línea]

[repetir para los 5 partidos]

_Análisis propio. No garantiza resultado._"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"❌ Error al generar recomendaciones: {str(e)}"
