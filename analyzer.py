import os
import httpx
import anthropic
from datetime import datetime, timedelta

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"

TEAM_ALIASES = {
    "madrid": "Real Madrid", "real madrid": "Real Madrid", "rm": "Real Madrid",
    "barca": "Barcelona", "barça": "Barcelona", "barcelona": "Barcelona", "fcb": "Barcelona",
    "atletico": "Atlético", "atletico madrid": "Atlético", "atleti": "Atlético",
    "sevilla": "Sevilla", "valencia": "Valencia", "villarreal": "Villarreal",
    "betis": "Betis", "sociedad": "Real Sociedad", "athletic": "Athletic Club", "bilbao": "Athletic Club",
    "osasuna": "Osasuna", "girona": "Girona", "getafe": "Getafe", "rayo": "Rayo Vallecano",
    "celta": "Celta", "mallorca": "Mallorca", "alaves": "Alavés",
    "las palmas": "Las Palmas", "leganes": "Leganés", "espanol": "Espanyol", "espanyol": "Espanyol",
    "arsenal": "Arsenal", "chelsea": "Chelsea", "liverpool": "Liverpool",
    "city": "Manchester City", "man city": "Manchester City", "manchester city": "Manchester City",
    "united": "Manchester United", "man united": "Manchester United", "manchester united": "Manchester United",
    "tottenham": "Tottenham", "spurs": "Tottenham",
    "newcastle": "Newcastle", "aston villa": "Aston Villa", "west ham": "West Ham",
    "brighton": "Brighton", "everton": "Everton", "fulham": "Fulham",
    "wolves": "Wolverhampton", "brentford": "Brentford", "crystal palace": "Crystal Palace",
    "nottingham": "Nottingham Forest", "forest": "Nottingham Forest",
    "bournemouth": "Bournemouth",
    "bayern": "Bayern", "dortmund": "Dortmund", "bvb": "Dortmund",
    "leverkusen": "Leverkusen", "leipzig": "RB Leipzig", "frankfurt": "Eintracht Frankfurt",
    "stuttgart": "Stuttgart",
    "juventus": "Juventus", "juve": "Juventus", "inter": "Inter",
    "inter milan": "Inter", "milan": "AC Milan", "ac milan": "AC Milan",
    "napoli": "Napoli", "roma": "Roma", "lazio": "Lazio",
    "fiorentina": "Fiorentina", "atalanta": "Atalanta",
    "psg": "Paris Saint-Germain", "paris": "Paris Saint-Germain",
    "marseille": "Marseille", "lyon": "Lyon", "monaco": "Monaco",
    "lille": "Lille", "benfica": "Benfica", "porto": "Porto", "sporting": "Sporting CP",
}

ODDS_SPORTS = [
    "soccer_spain_la_liga", "soccer_epl", "soccer_germany_bundesliga",
    "soccer_italy_serie_a", "soccer_france_ligue_one",
    "soccer_uefa_champs_league", "soccer_portugal_primeira_liga",
    "soccer_spain_segunda_division",
]

def resolve_team_name(alias: str) -> str:
    return TEAM_ALIASES.get(alias.lower().strip(), alias.title())

def is_today_or_tomorrow(date_str: str) -> bool:
    try:
        game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now().astimezone()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        return game_date.date() in [today, tomorrow]
    except:
        return False

async def search_team_id(team_name: str, client: httpx.AsyncClient) -> tuple:
    """Busca el ID real del equipo en la API."""
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    # Buscar en las ligas principales directamente
    leagues = ["PD", "PL", "BL1", "SA", "FL1", "CL", "PPL"]
    
    for league in leagues:
        try:
            resp = await client.get(
                f"{FOOTBALL_BASE_URL}/competitions/{league}/teams",
                headers=headers,
                timeout=10
            )
            if resp.status_code == 200:
                teams = resp.json().get("teams", [])
                for team in teams:
                    team_name_api = team.get("name", "").lower()
                    team_short = team.get("shortName", "").lower()
                    search = team_name.lower()
                    if search in team_name_api or search in team_short or team_name_api in search:
                        return team["id"], team["name"]
        except Exception:
            continue
    
    return None, team_name

async def get_team_recent_matches(team_name: str) -> str:
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        try:
            team_id, team_full_name = await search_team_id(team_name, client)

            if not team_id:
                return f"Equipo no encontrado en las ligas disponibles: {team_name}"

            resp = await client.get(
                f"{FOOTBALL_BASE_URL}/teams/{team_id}/matches",
                headers=headers,
                params={"status": "FINISHED", "dateFrom": date_from, "dateTo": date_to, "limit": 6},
                timeout=10
            )
            if resp.status_code != 200:
                return f"Sin datos recientes para {team_full_name}"

            matches = resp.json().get("matches", [])
            if not matches:
                return f"Sin partidos recientes para {team_full_name}"

            lines = [f"Ultimos partidos de {team_full_name}:"]
            for m in matches:
                home = m.get("homeTeam", {}).get("name", "?")
                away = m.get("awayTeam", {}).get("name", "?")
                score = m.get("score", {}).get("fullTime", {})
                hg = score.get("home")
                ag = score.get("away")
                date = m.get("utcDate", "")[:10]
                competition = m.get("competition", {}).get("name", "")
                is_home = team_full_name.lower() in home.lower()
                venue = "Local" if is_home else "Visita"
                if hg is not None and ag is not None:
                    result = ("W" if (is_home and hg > ag) or (not is_home and ag > hg)
                              else "D" if hg == ag else "L")
                else:
                    result = "?"
                lines.append(f"{date} | {competition} | {venue} | {home} {hg}-{ag} {away} | {result}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error obteniendo datos de {team_name}: {str(e)}"

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
                    t1 = team1.lower()
                    t2 = team2.lower()

                    if (t1 in home or t1 in away) and (t2 in home or t2 in away):
                        bookmakers = game.get("bookmakers", [])
                        if not bookmakers:
                            continue
                        lines = [f"Cuotas reales: {game['home_team']} vs {game['away_team']}"]
                        for bm in bookmakers[:2]:
                            for market in bm.get("markets", []):
                                if market["key"] == "h2h":
                                    lines.append(f"{bm['title']} - 1X2:")
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
        return "No encontre partidos para hoy/manana con cuotas disponibles."

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
        return "No encontre partidos hoy/manana con cuota mayor de 1.20 para ese mercado."

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
    team1_name = resolve_team_name(team1_alias)
    team2_name = resolve_team_name(team2_alias)

    team1_recent = await get_team_recent_matches(team1_name)
    team2_recent = await get_team_recent_matches(team2_name)
    odds_info = await get_real_odds(team1_name, team2_name)

    prompt = f"""Eres un analista experto en futbol y apuestas deportivas. Analiza este partido con los datos REALES:

PARTIDO: {team1_name} vs {team2_name}

{team1_recent}

{team2_recent}

{odds_info}

Usa SOLO estos datos reales. Si los datos son correctos, haz el analisis completo. Responde con este formato:

📊 *{team1_name} vs {team2_name}*

🏠 *Local/Visita:* [quien juega en casa]
🏆 *Competicion:* [liga]

📈 *Forma reciente {team1_name}:*
[analiza resultados reales proporcionados]

📉 *Forma reciente {team2_name}:*
[analiza resultados reales proporcionados]

💪 *Motivacion:*
- {team1_name}: [situacion en tabla]
- {team2_name}: [situacion en tabla]

⚽ *Analisis de goles:* [tendencia]
🟨 *Estimado tarjetas:* [estimado]
🚩 *Estimado corners:* [estimado]

---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador o doble oportunidad con %]
⚽ Goles: [mas/menos X.X con %]
💰 Cuotas reales: [si estan disponibles]

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
