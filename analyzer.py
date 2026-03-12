import os
import httpx
import anthropic
from datetime import datetime, timedelta

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"

# IDs fijos de equipos en football-data.org
TEAM_IDS = {
    "real madrid": 86, "fc barcelona": 81, "atletico de madrid": 78,
    "sevilla fc": 559, "valencia cf": 95, "villarreal cf": 94,
    "real betis": 90, "real sociedad": 92, "athletic club": 77,
    "ca osasuna": 79, "girona fc": 298, "getafe cf": 554,
    "rayo vallecano": 87, "celta de vigo": 558, "rcd mallorca": 89,
    "deportivo alaves": 263, "ud las palmas": 275, "cd leganes": 745,
    "rcd espanyol": 80,
    "arsenal fc": 57, "chelsea fc": 61, "liverpool fc": 64,
    "manchester city fc": 65, "manchester united fc": 66,
    "tottenham hotspur fc": 73, "newcastle united fc": 67,
    "aston villa fc": 58, "west ham united fc": 563,
    "brighton & hove albion fc": 397, "everton fc": 62,
    "fulham fc": 63, "wolverhampton wanderers fc": 76,
    "brentford fc": 402, "crystal palace fc": 354,
    "nottingham forest fc": 68, "afc bournemouth": 1044,
    "fc bayern munchen": 5, "borussia dortmund": 4,
    "bayer 04 leverkusen": 3, "rb leipzig": 721,
    "eintracht frankfurt": 9, "vfb stuttgart": 10,
    "juventus fc": 109, "fc internazionale milano": 108,
    "ac milan": 98, "ssc napoli": 113, "as roma": 100,
    "ss lazio": 110, "acf fiorentina": 99, "atalanta bc": 102,
    "paris saint-germain fc": 524, "olympique de marseille": 516,
    "olympique lyonnais": 523, "as monaco fc": 548,
    "losc lille": 521, "sl benfica": 294, "fc porto": 297,
    "sporting cp": 498,
}

TEAM_ALIASES = {
    "madrid": "real madrid", "real madrid": "real madrid", "rm": "real madrid",
    "barca": "fc barcelona", "barça": "fc barcelona", "barcelona": "fc barcelona", "fcb": "fc barcelona",
    "atletico": "atletico de madrid", "atletico madrid": "atletico de madrid", "atleti": "atletico de madrid",
    "sevilla": "sevilla fc", "valencia": "valencia cf", "villarreal": "villarreal cf",
    "betis": "real betis", "sociedad": "real sociedad", "athletic": "athletic club", "bilbao": "athletic club",
    "osasuna": "ca osasuna", "girona": "girona fc", "getafe": "getafe cf", "rayo": "rayo vallecano",
    "celta": "celta de vigo", "mallorca": "rcd mallorca", "alaves": "deportivo alaves",
    "las palmas": "ud las palmas", "leganes": "cd leganes", "espanol": "rcd espanyol", "espanyol": "rcd espanyol",
    "arsenal": "arsenal fc", "chelsea": "chelsea fc", "liverpool": "liverpool fc",
    "city": "manchester city fc", "man city": "manchester city fc", "manchester city": "manchester city fc",
    "united": "manchester united fc", "man united": "manchester united fc", "manchester united": "manchester united fc",
    "tottenham": "tottenham hotspur fc", "spurs": "tottenham hotspur fc",
    "newcastle": "newcastle united fc", "aston villa": "aston villa fc", "west ham": "west ham united fc",
    "brighton": "brighton & hove albion fc", "everton": "everton fc", "fulham": "fulham fc",
    "wolves": "wolverhampton wanderers fc", "brentford": "brentford fc", "crystal palace": "crystal palace fc",
    "nottingham": "nottingham forest fc", "forest": "nottingham forest fc",
    "bournemouth": "afc bournemouth",
    "bayern": "fc bayern munchen", "dortmund": "borussia dortmund", "bvb": "borussia dortmund",
    "leverkusen": "bayer 04 leverkusen", "leipzig": "rb leipzig", "frankfurt": "eintracht frankfurt",
    "stuttgart": "vfb stuttgart",
    "juventus": "juventus fc", "juve": "juventus fc", "inter": "fc internazionale milano",
    "inter milan": "fc internazionale milano", "milan": "ac milan", "ac milan": "ac milan",
    "napoli": "ssc napoli", "roma": "as roma", "lazio": "ss lazio",
    "fiorentina": "acf fiorentina", "atalanta": "atalanta bc",
    "psg": "paris saint-germain fc", "paris": "paris saint-germain fc",
    "marseille": "olympique de marseille", "lyon": "olympique lyonnais", "monaco": "as monaco fc",
    "lille": "losc lille", "benfica": "sl benfica", "porto": "fc porto", "sporting": "sporting cp",
}

ODDS_SPORTS = [
    "soccer_spain_la_liga", "soccer_epl", "soccer_germany_bundesliga",
    "soccer_italy_serie_a", "soccer_france_ligue_one",
    "soccer_uefa_champs_league", "soccer_portugal_primeira_liga",
    "soccer_spain_segunda_division",
]

def resolve_team_name(alias: str) -> str:
    return TEAM_ALIASES.get(alias.lower().strip(), alias.lower().strip())

def get_team_id(team_key: str) -> int:
    return TEAM_IDS.get(team_key.lower().strip())

def is_today_or_tomorrow(date_str: str) -> bool:
    try:
        game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now().astimezone()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        return game_date.date() in [today, tomorrow]
    except:
        return False

async def get_team_recent_matches(team_key: str) -> str:
    team_id = get_team_id(team_key)
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        try:
            if not team_id:
                resp = await client.get(
                    f"{FOOTBALL_BASE_URL}/teams",
                    headers=headers,
                    params={"name": team_key},
                    timeout=10
                )
                if resp.status_code == 200:
                    teams = resp.json().get("teams", [])
                    if teams:
                        team_id = teams[0]["id"]
                        team_key = teams[0]["name"]

            if not team_id:
                return f"Equipo no encontrado: {team_key}"

            resp2 = await client.get(
                f"{FOOTBALL_BASE_URL}/teams/{team_id}/matches",
                headers=headers,
                params={"status": "FINISHED", "dateFrom": date_from, "dateTo": date_to, "limit": 6},
                timeout=10
            )
            if resp2.status_code != 200:
                return f"Sin datos recientes para {team_key} (error {resp2.status_code})"

            matches = resp2.json().get("matches", [])
            if not matches:
                return f"Sin partidos recientes para {team_key}"

            lines = [f"Ultimos partidos de {team_key.title()}:"]
            for m in matches:
                home = m.get("homeTeam", {}).get("name", "?")
                away = m.get("awayTeam", {}).get("name", "?")
                score = m.get("score", {}).get("fullTime", {})
                hg = score.get("home")
                ag = score.get("away")
                date = m.get("utcDate", "")[:10]
                competition = m.get("competition", {}).get("name", "")
                is_home = home.lower() == team_key.lower()
                venue = "Local" if is_home else "Visita"
                if hg is not None and ag is not None:
                    if is_home:
                        result = "W" if hg > ag else ("D" if hg == ag else "L")
                    else:
                        result = "W" if ag > hg else ("D" if hg == ag else "L")
                else:
                    result = "?"
                lines.append(f"{date} | {competition} | {venue} | {home} {hg}-{ag} {away} | {result}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error: {str(e)}"

async def get_real_odds(team1: str, team2: str) -> str:
    async with httpx.AsyncClient() as client:
        for sport in ODDS_SPORTS:
            try:
                resp = await client.get(
                    f"{ODDS_BASE_URL}/sports/{sport}/odds",
                    params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal"},
                    timeout=10
                )
                if resp.status_code != 200:
                    continue

                for game in resp.json():
                    home = game.get("home_team", "").lower()
                    away = game.get("away_team", "").lower()
                    t1 = team1.lower().replace("fc ", "").replace(" fc", "").replace("ssc ", "").replace("ac ", "")
                    t2 = team2.lower().replace("fc ", "").replace(" fc", "").replace("ssc ", "").replace("ac ", "")

                    if (t1 in home or t1 in away) and (t2 in home or t2 in away):
                        bookmakers = game.get("bookmakers", [])
                        if not bookmakers:
                            continue
                        lines = [f"Cuotas reales: {game['home_team']} vs {game['away_team']}"]
                        for bm in bookmakers[:2]:
                            for market in bm.get("markets", []):
                                if market["key"] == "h2h":
                                    lines.append(f"{bm['title']} - Resultado 1X2:")
                                    for o in market.get("outcomes", []):
                                        lines.append(f"  {o['name']}: {o['price']}")
                                elif market["key"] == "totals":
                                    lines.append(f"{bm['title']} - Goles:")
                                    for o in market.get("outcomes", []):
                                        lines.append(f"  {o['name']} {o.get('point','')}: {o['price']}")
                        return "\n".join(lines)

            except Exception:
                continue

    return "Sin cuotas disponibles para este partido."

async def get_upcoming_with_odds(bet_type: str) -> str:
    all_games = []

    async with httpx.AsyncClient() as client:
        for sport in ODDS_SPORTS:
            try:
                resp = await client.get(
                    f"{ODDS_BASE_URL}/sports/{sport}/odds",
                    params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal"},
                    timeout=10
                )
                if resp.status_code == 200:
                    for g in resp.json():
                        g["sport"] = sport
                        all_games.append(g)
            except Exception:
                continue

    all_games = [g for g in all_games if is_today_or_tomorrow(g.get("commence_time", ""))]

    if not all_games:
        return "No encontre partidos para hoy/mañana con cuotas disponibles."

    picks = []

    for game in all_games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        commence = game.get("commence_time", "")[:16].replace("T", " ")
        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            continue

        if bet_type == "1X":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "h2h":
                        outcomes = market.get("outcomes", [])
                        home_odd = next((o["price"] for o in outcomes if o["name"] == home), None)
                        draw_odd = next((o["price"] for o in outcomes if o["name"] == "Draw"), None)
                        if home_odd and draw_odd and 1.20 <= home_odd <= 2.20:
                            if not any(p["match"] == f"{home} vs {away}" for p in picks):
                                picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "1X (Local o Empate)", "odd": round(home_odd, 2)})
                        break

        elif bet_type == "over_1.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for o in market.get("outcomes", []):
                            if o["name"] == "Over" and str(o.get("point", "")) == "1.5" and o["price"] >= 1.20:
                                if not any(p["match"] == f"{home} vs {away}" for p in picks):
                                    picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "Mas de 1.5 goles", "odd": round(o["price"], 2)})
                        break

        elif bet_type == "under_3.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for o in market.get("outcomes", []):
                            if o["name"] == "Under" and str(o.get("point", "")) == "3.5" and o["price"] >= 1.20:
                                if not any(p["match"] == f"{home} vs {away}" for p in picks):
                                    picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "Menos de 3.5 goles", "odd": round(o["price"], 2)})
                        break

    picks = sorted(picks, key=lambda x: x["odd"], reverse=True)[:5]

    if not picks:
        return "No encontre partidos hoy/mañana con cuota mayor de 1.20 para ese mercado."

    titles = {
        "1X": "Top 5 partidos 1X",
        "over_1.5": "Top 5 Mas de 1.5 goles",
        "under_3.5": "Top 5 Menos de 3.5 goles"
    }
    lines = [f"*{titles[bet_type]}* — hoy/manana | cuota min. 1.20", ""]
    for i, p in enumerate(picks, 1):
        lines.append(f"{i}. {p['match']}")
        lines.append(f"   Hora: {p['time']} UTC")
        lines.append(f"   Apuesta: {p['bet']}")
        lines.append(f"   Cuota real: {p['odd']}")
        lines.append("")

    lines.append("_Cuotas reales de casas de apuestas europeas._")
    return "\n".join(lines)

async def analyze_match(team1_alias: str, team2_alias: str) -> str:
    team1_key = resolve_team_name(team1_alias)
    team2_key = resolve_team_name(team2_alias)

    team1_recent = await get_team_recent_matches(team1_key)
    team2_recent = await get_team_recent_matches(team2_key)
    odds_info = await get_real_odds(team1_key, team2_key)

    prompt = f"""Eres un analista experto en futbol y apuestas deportivas. Analiza este partido con los datos REALES proporcionados:

PARTIDO: {team1_key.title()} vs {team2_key.title()}

{team1_recent}

{team2_recent}

{odds_info}

Usa SOLO estos datos reales para el analisis. No inventes datos. Responde con este formato:

📊 *{team1_key.title()} vs {team2_key.title()}*

🏠 *Local/Visita:* [quien juega en casa segun tu conocimiento del calendario]
🏆 *Competicion:* [liga o torneo]

📈 *Forma reciente {team1_key.title()}:*
[analiza los resultados reales que te di, racha, goles marcados/recibidos en casa y fuera]

📉 *Forma reciente {team2_key.title()}:*
[analiza los resultados reales que te di, racha, goles marcados/recibidos]

💪 *Motivacion:*
- {team1_key.title()}: [objetivos actuales en la clasificacion]
- {team2_key.title()}: [objetivos actuales en la clasificacion]

⚽ *Analisis de goles:* [tendencia segun datos reales]
🟨 *Estimado tarjetas:* [estimado]
🚩 *Estimado corners:* [estimado]

---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador o doble oportunidad con porcentaje]
⚽ Goles: [mas/menos X.X con porcentaje]
💰 Cuotas reales: [solo si estan disponibles en los datos]

_Analisis basado en datos reales. No garantiza resultado._"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error al generar analisis: {str(e)}"

async def get_recommendations(bet_type: str) -> str:
    return await get_upcoming_with_odds(bet_type)
