import os
import httpx
import anthropic
from datetime import datetime, timedelta

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"

# Mapa directo alias -> ID oficial en football-data.org
TEAM_ID_MAP = {
    # La Liga
    "real madrid": 86, "madrid": 86, "rm": 86,
    "barcelona": 81, "barca": 81, "barça": 81, "fcb": 81,
    "atletico": 78, "atleti": 78, "atletico madrid": 78,
    "sevilla": 559,
    "valencia": 95,
    "villarreal": 94,
    "betis": 90, "real betis": 90,
    "real sociedad": 92, "sociedad": 92,
    "athletic": 77, "bilbao": 77, "athletic club": 77,
    "osasuna": 79,
    "girona": 298,
    "getafe": 554,
    "rayo": 87, "rayo vallecano": 87,
    "celta": 558, "celta vigo": 558,
    "mallorca": 89,
    "alaves": 263, "alavés": 263, "deportivo alaves": 263,
    "las palmas": 275,
    "leganes": 745, "leganés": 745,
    "espanyol": 80, "espanol": 80,
    "valladolid": 250,
    # Premier League
    "arsenal": 57,
    "chelsea": 61,
    "liverpool": 64,
    "manchester city": 65, "man city": 65, "city": 65,
    "manchester united": 66, "man united": 66, "united": 66,
    "tottenham": 73, "spurs": 73,
    "newcastle": 67,
    "aston villa": 58,
    "west ham": 563,
    "brighton": 397,
    "everton": 62,
    "fulham": 63,
    "wolves": 76, "wolverhampton": 76,
    "brentford": 402,
    "crystal palace": 354,
    "nottingham": 68, "forest": 68,
    "bournemouth": 1044,
    "leicester": 338,
    "ipswich": 57, 
    "southampton": 340,
    # Bundesliga
    "bayern": 5, "fc bayern": 5,
    "dortmund": 4, "bvb": 4,
    "leverkusen": 3,
    "leipzig": 721, "rb leipzig": 721,
    "frankfurt": 9, "eintracht frankfurt": 9,
    "stuttgart": 10,
    "gladbach": 18,
    "wolfsburg": 11,
    "hoffenheim": 720,
    "freiburg": 17,
    "augsburg": 16,
    "mainz": 15,
    "bremen": 13, "werder": 13,
    "heidenheim": 1138,
    "bochum": 130,
    "kiel": 1150,
    # Serie A
    "juventus": 109, "juve": 109,
    "inter": 108, "inter milan": 108,
    "milan": 98, "ac milan": 98,
    "napoli": 113,
    "roma": 100, "as roma": 100,
    "lazio": 110,
    "fiorentina": 99,
    "atalanta": 102,
    "torino": 586,
    "bologna": 103,
    "monza": 5911,
    "genoa": 107,
    "lecce": 5890,
    "cagliari": 104,
    "parma": 112,
    "como": 2933,
    "venezia": 450,
    "udinese": 115,
    "empoli": 106,
    "hellas verona": 450,
    # Ligue 1
    "psg": 524, "paris": 524, "paris saint-germain": 524,
    "marseille": 516,
    "lyon": 523,
    "monaco": 548,
    "lille": 521,
    "nice": 522,
    "lens": 546,
    "rennes": 529,
    "strasbourg": 527,
    "nantes": 543,
    "reims": 547,
    "toulouse": 519,
    "brest": 542,
    "montpellier": 545,
    "le havre": 525,
    "angers": 544,
    "saint-etienne": 518,
    # Champions League / Portugal
    "benfica": 294,
    "porto": 297,
    "sporting": 498, "sporting cp": 498,
    "braga": 5601,
}

ODDS_SPORTS = [
    "soccer_spain_la_liga", "soccer_epl", "soccer_germany_bundesliga",
    "soccer_italy_serie_a", "soccer_france_ligue_one",
    "soccer_uefa_champs_league", "soccer_portugal_primeira_liga",
    "soccer_spain_segunda_division",
]

def resolve_team(alias: str) -> tuple:
    """Devuelve (team_id, display_name)"""
    key = alias.lower().strip()
    team_id = TEAM_ID_MAP.get(key)
    display = alias.title()
    return team_id, display

def is_today_or_tomorrow(date_str: str) -> bool:
    try:
        game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now().astimezone()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        return game_date.date() in [today, tomorrow]
    except:
        return False

async def get_team_recent_matches(alias: str) -> str:
    team_id, display_name = resolve_team(alias)
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    if not team_id:
        return f"Equipo '{alias}' no encontrado en la base de datos."

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{FOOTBALL_BASE_URL}/teams/{team_id}/matches",
                headers=headers,
                params={"status": "FINISHED", "dateFrom": date_from, "dateTo": date_to, "limit": 6},
                timeout=10
            )
            if resp.status_code != 200:
                return f"Error obteniendo partidos de {display_name} (status {resp.status_code})"

            matches = resp.json().get("matches", [])
            if not matches:
                return f"Sin partidos recientes para {display_name}"

            # Obtener nombre real del equipo desde la API
            team_info = resp.json().get("matches", [{}])[0]
            home_name = team_info.get("homeTeam", {}).get("name", "")
            away_name = team_info.get("awayTeam", {}).get("name", "")

            lines = [f"Ultimos partidos (ID {team_id}):"]
            for m in matches:
                home = m.get("homeTeam", {}).get("name", "?")
                away = m.get("awayTeam", {}).get("name", "?")
                score = m.get("score", {}).get("fullTime", {})
                hg = score.get("home")
                ag = score.get("away")
                date = m.get("utcDate", "")[:10]
                competition = m.get("competition", {}).get("name", "")
                is_home = m.get("homeTeam", {}).get("id") == team_id
                venue = "Local" if is_home else "Visita"
                if hg is not None and ag is not None:
                    result = ("W" if (is_home and hg > ag) or (not is_home and ag > hg)
                              else "D" if hg == ag else "L")
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
    team1_id, team1_display = resolve_team(team1_alias)
    team2_id, team2_display = resolve_team(team2_alias)

    team1_recent = await get_team_recent_matches(team1_alias)
    team2_recent = await get_team_recent_matches(team2_alias)
    odds_info = await get_real_odds(team1_alias, team2_alias)

    prompt = f"""Eres un analista experto en futbol y apuestas deportivas. Analiza este partido con los datos REALES:

PARTIDO SOLICITADO: {team1_display} vs {team2_display}

DATOS {team1_display}:
{team1_recent}

DATOS {team2_display}:
{team2_recent}

{odds_info}

Haz el analisis completo con estos datos. Formato:

📊 *{team1_display} vs {team2_display}*

🏠 *Local/Visita:* [quien juega en casa]
🏆 *Competicion:* [liga]

📈 *Forma reciente {team1_display}:*
[analiza los resultados reales]

📉 *Forma reciente {team2_display}:*
[analiza los resultados reales]

💪 *Motivacion:*
- {team1_display}: [situacion actual]
- {team2_display}: [situacion actual]

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
