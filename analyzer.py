import os
import httpx
import anthropic
from datetime import datetime, timedelta

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"

TEAM_ALIASES = {
    # España
    "madrid": "Real Madrid", "real madrid": "Real Madrid", "rm": "Real Madrid",
    "barca": "Barcelona", "barça": "Barcelona", "barcelona": "Barcelona", "fcb": "Barcelona", "fc barcelona": "Barcelona",
    "atletico": "Atletico Madrid", "atleti": "Atletico Madrid", "atletico madrid": "Atletico Madrid", "atlético": "Atletico Madrid",
    "sevilla": "Sevilla", "valencia": "Valencia", "villarreal": "Villarreal",
    "betis": "Real Betis", "real betis": "Real Betis",
    "sociedad": "Real Sociedad", "real sociedad": "Real Sociedad",
    "athletic": "Athletic Club", "bilbao": "Athletic Club", "athletic club": "Athletic Club",
    "osasuna": "Osasuna", "girona": "Girona", "getafe": "Getafe",
    "rayo": "Rayo Vallecano", "rayo vallecano": "Rayo Vallecano",
    "celta": "Celta Vigo", "celta vigo": "Celta Vigo",
    "mallorca": "Mallorca", "alaves": "Alaves", "alavés": "Alaves", "deportivo alaves": "Alaves",
    "las palmas": "Las Palmas", "leganes": "Leganes", "leganés": "Leganes",
    "espanol": "Espanyol", "espanyol": "Espanyol", "español": "Espanyol",
    "valladolid": "Valladolid",
    # Inglaterra
    "arsenal": "Arsenal", "chelsea": "Chelsea", "liverpool": "Liverpool",
    "city": "Manchester City", "man city": "Manchester City", "manchester city": "Manchester City",
    "united": "Manchester United", "man united": "Manchester United", "manchester united": "Manchester United",
    "tottenham": "Tottenham", "spurs": "Tottenham",
    "newcastle": "Newcastle", "aston villa": "Aston Villa", "west ham": "West Ham",
    "brighton": "Brighton", "everton": "Everton", "fulham": "Fulham",
    "wolves": "Wolves", "wolverhampton": "Wolves",
    "brentford": "Brentford", "crystal palace": "Crystal Palace",
    "nottingham": "Nottingham Forest", "forest": "Nottingham Forest",
    "bournemouth": "Bournemouth", "leicester": "Leicester", "ipswich": "Ipswich",
    "southampton": "Southampton",
    # Alemania
    "bayern": "Bayern Munich", "fc bayern": "Bayern Munich", "bayern munich": "Bayern Munich",
    "dortmund": "Borussia Dortmund", "bvb": "Borussia Dortmund",
    "leverkusen": "Bayer Leverkusen", "bayer leverkusen": "Bayer Leverkusen",
    "leipzig": "RB Leipzig", "rb leipzig": "RB Leipzig",
    "frankfurt": "Eintracht Frankfurt", "eintracht": "Eintracht Frankfurt",
    "stuttgart": "Stuttgart", "gladbach": "Monchengladbach",
    "wolfsburg": "Wolfsburg", "hoffenheim": "Hoffenheim",
    "freiburg": "Freiburg", "augsburg": "Augsburg", "mainz": "Mainz",
    "bremen": "Werder Bremen", "werder": "Werder Bremen",
    "heidenheim": "Heidenheim", "bochum": "Bochum", "kiel": "Holstein Kiel",
    # Italia
    "juventus": "Juventus", "juve": "Juventus",
    "inter": "Inter Milan", "inter milan": "Inter Milan", "internazionale": "Inter Milan",
    "milan": "AC Milan", "ac milan": "AC Milan",
    "napoli": "Napoli", "roma": "AS Roma", "as roma": "AS Roma",
    "lazio": "Lazio", "fiorentina": "Fiorentina", "atalanta": "Atalanta",
    "torino": "Torino", "bologna": "Bologna", "monza": "Monza",
    "genoa": "Genoa", "lecce": "Lecce", "cagliari": "Cagliari",
    "parma": "Parma", "como": "Como", "udinese": "Udinese", "empoli": "Empoli",
    # Francia
    "psg": "Paris Saint Germain", "paris": "Paris Saint Germain", "paris saint germain": "Paris Saint Germain",
    "marseille": "Marseille", "marsella": "Marseille", "olympique marseille": "Marseille",
    "lyon": "Lyon", "olympique lyon": "Lyon",
    "monaco": "Monaco", "lille": "Lille", "nice": "Nice",
    "lens": "Lens", "rennes": "Rennes", "auxerre": "Auxerre",
    "strasbourg": "Strasbourg", "nantes": "Nantes", "reims": "Reims",
    "toulouse": "Toulouse", "brest": "Brest", "montpellier": "Montpellier",
    "le havre": "Le Havre", "angers": "Angers", "saint etienne": "Saint-Etienne",
    # Portugal
    "benfica": "Benfica", "porto": "Porto", "sporting": "Sporting CP", "sporting cp": "Sporting CP",
    "braga": "Braga",
    # Otros
    "ajax": "Ajax", "psv": "PSV", "feyenoord": "Feyenoord",
    "celtic": "Celtic", "rangers": "Rangers",
}

ODDS_SPORTS = [
    "soccer_spain_la_liga", "soccer_epl", "soccer_germany_bundesliga",
    "soccer_italy_serie_a", "soccer_france_ligue_one",
    "soccer_uefa_champs_league", "soccer_portugal_primeira_liga",
    "soccer_spain_segunda_division", "soccer_france_ligue_two",
    "soccer_netherlands_eredivisie", "soccer_germany_bundesliga2",
    "soccer_italy_serie_b", "soccer_england_league1",
]

def resolve_team_name(alias: str) -> str:
    key = alias.lower().strip()
    return TEAM_ALIASES.get(key, alias.title())

def is_today_or_tomorrow(date_str: str) -> bool:
    """Acepta partidos de hoy, manana y pasado manana."""
    try:
        game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now().astimezone()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        return game_date.date() in [today, tomorrow, today + timedelta(days=2)]
    except:
        return False

async def get_team_recent_matches(team_name: str) -> str:
    headers = {"x-apisports-key": API_FOOTBALL_KEY}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{API_FOOTBALL_BASE}/teams",
                headers=headers,
                params={"search": team_name},
                timeout=10
            )
            if resp.status_code != 200:
                return f"Error buscando {team_name}"

            teams = resp.json().get("response", [])
            if not teams:
                return f"Equipo no encontrado: {team_name}"

            team = teams[0]["team"]
            team_id = team["id"]
            team_full_name = team["name"]

            resp2 = await client.get(
                f"{API_FOOTBALL_BASE}/fixtures",
                headers=headers,
                params={"team": team_id, "last": 6, "status": "FT"},
                timeout=10
            )
            if resp2.status_code != 200:
                return f"Sin datos recientes para {team_full_name}"

            fixtures = resp2.json().get("response", [])
            if not fixtures:
                return f"Sin partidos recientes para {team_full_name}"

            lines = [f"Ultimos partidos de {team_full_name}:"]
            for f in fixtures:
                home = f["teams"]["home"]["name"]
                away = f["teams"]["away"]["name"]
                hg = f["goals"]["home"]
                ag = f["goals"]["away"]
                date = f["fixture"]["date"][:10]
                league = f["league"]["name"]
                is_home = f["teams"]["home"]["id"] == team_id
                venue = "Local" if is_home else "Visita"
                winner = f["teams"]["home"]["winner"]
                if winner is None:
                    result = "D"
                elif (is_home and winner) or (not is_home and not winner):
                    result = "W"
                else:
                    result = "L"
                lines.append(f"{date} | {league} | {venue} | {home} {hg}-{ag} {away} | {result}")

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

    total_before = len(all_games)
    all_games = [g for g in all_games if is_today_or_tomorrow(g.get("commence_time", ""))]
    total_after = len(all_games)

    if not all_games:
        from datetime import datetime
        now = datetime.now().astimezone()
        sample_dates = []
        return f"Debug: {total_before} partidos totales, {total_after} en rango de fechas. Fecha actual servidor: {now.date()}. Revisa logs."

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
                        home_odd = next((o["price"] for o in outcomes if o.get("name","").lower() == home.lower()), None)
                        draw_odd = next((o["price"] for o in outcomes if o.get("name","").lower() in ["draw", "empate"]), None)
                        if home_odd and draw_odd and home_odd >= 1.30:
                            if not any(p["match"] == f"{home} vs {away}" for p in picks):
                                picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "1X (Local o Empate)", "odd": round(home_odd, 2)})
                        break

        elif bet_type == "over_2.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for o in market.get("outcomes", []):
                            name = o.get("name", "")
                            point = str(o.get("point", ""))
                            price = o.get("price", 0)
                            is_over = name in ["Over", "Más de", "Mas de", "Más", "Por encima"]
                            if is_over and point == "2.5" and price >= 1.90:
                                if not any(p["match"] == f"{home} vs {away}" for p in picks):
                                    picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "Mas de 2.5 goles", "odd": round(price, 2)})
                        break

    picks = sorted(picks, key=lambda x: x["odd"], reverse=True)[:5]

    if not picks:
        if bet_type == "1X":
            return "No encontre partidos hoy/manana con cuota 1X mayor de 1.30."
        else:
            return "No encontre partidos hoy/manana con cuota Mas de 2.5 goles mayor de 1.90."

    titles = {
        "1X": "Top 5 partidos 1X — cuota min. 1.30",
        "over_2.5": "Top 5 Mas de 2.5 goles — cuota min. 1.90",
    }
    lines = [f"*{titles[bet_type]}* — hoy/manana", ""]
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

Haz el analisis completo. Formato:

📊 *{team1_name} vs {team2_name}*

🏠 *Local/Visita:* [quien juega en casa]
🏆 *Competicion:* [liga]

📈 *Forma reciente {team1_name}:*
[analiza los resultados reales]

📉 *Forma reciente {team2_name}:*
[analiza los resultados reales]

💪 *Motivacion:*
- {team1_name}: [situacion actual]
- {team2_name}: [situacion actual]

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
