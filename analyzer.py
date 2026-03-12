import os
import httpx
import anthropic
from datetime import datetime, timedelta

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ODDS_API_KEY = os.environ.get("ODDS_KEY", "") or os.environ.get("ODDS_API_KEY", "")

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"

TEAM_ALIASES = {
    "madrid": "Real Madrid", "real madrid": "Real Madrid",
    "barca": "Barcelona", "barça": "Barcelona", "barcelona": "Barcelona",
    "atletico": "Atletico Madrid", "atleti": "Atletico Madrid", "atlético": "Atletico Madrid",
    "sevilla": "Sevilla", "valencia": "Valencia", "villarreal": "Villarreal",
    "betis": "Real Betis", "real betis": "Real Betis",
    "sociedad": "Real Sociedad", "real sociedad": "Real Sociedad",
    "athletic": "Athletic Club", "bilbao": "Athletic Club",
    "osasuna": "Osasuna", "girona": "Girona", "getafe": "Getafe",
    "rayo": "Rayo Vallecano", "celta": "Celta Vigo",
    "mallorca": "Mallorca", "alaves": "Alaves", "alavés": "Alaves",
    "las palmas": "Las Palmas", "leganes": "Leganes", "leganés": "Leganes",
    "espanol": "Espanyol", "espanyol": "Espanyol", "español": "Espanyol",
    "valladolid": "Valladolid",
    "arsenal": "Arsenal", "chelsea": "Chelsea", "liverpool": "Liverpool",
    "city": "Manchester City", "man city": "Manchester City",
    "united": "Manchester United", "man united": "Manchester United",
    "tottenham": "Tottenham", "spurs": "Tottenham",
    "newcastle": "Newcastle", "aston villa": "Aston Villa", "west ham": "West Ham",
    "brighton": "Brighton", "everton": "Everton", "fulham": "Fulham",
    "wolves": "Wolves", "brentford": "Brentford", "crystal palace": "Crystal Palace",
    "nottingham": "Nottingham Forest", "forest": "Nottingham Forest",
    "bournemouth": "Bournemouth", "leicester": "Leicester", "ipswich": "Ipswich",
    "southampton": "Southampton",
    "bayern": "Bayern Munich", "fc bayern": "Bayern Munich",
    "dortmund": "Borussia Dortmund", "bvb": "Borussia Dortmund",
    "leverkusen": "Bayer Leverkusen", "leipzig": "RB Leipzig",
    "frankfurt": "Eintracht Frankfurt", "eintracht": "Eintracht Frankfurt",
    "stuttgart": "Stuttgart", "gladbach": "Monchengladbach",
    "wolfsburg": "Wolfsburg", "hoffenheim": "Hoffenheim",
    "freiburg": "Freiburg", "augsburg": "Augsburg", "mainz": "Mainz",
    "bremen": "Werder Bremen", "werder": "Werder Bremen",
    "heidenheim": "Heidenheim", "bochum": "Bochum", "kiel": "Holstein Kiel",
    "juventus": "Juventus", "juve": "Juventus",
    "inter": "Inter Milan", "internazionale": "Inter Milan",
    "milan": "AC Milan", "ac milan": "AC Milan",
    "napoli": "Napoli", "roma": "AS Roma",
    "lazio": "Lazio", "fiorentina": "Fiorentina", "atalanta": "Atalanta",
    "torino": "Torino", "bologna": "Bologna", "monza": "Monza",
    "genoa": "Genoa", "lecce": "Lecce", "cagliari": "Cagliari",
    "psg": "Paris Saint Germain", "paris": "Paris Saint Germain",
    "marseille": "Marseille", "marsella": "Marseille",
    "lyon": "Lyon", "monaco": "Monaco", "lille": "Lille", "nice": "Nice",
    "lens": "Lens", "rennes": "Rennes", "auxerre": "Auxerre",
    "strasbourg": "Strasbourg", "nantes": "Nantes", "reims": "Reims",
    "toulouse": "Toulouse", "brest": "Brest", "montpellier": "Montpellier",
    "benfica": "Benfica", "porto": "Porto", "sporting": "Sporting CP",
    "ajax": "Ajax", "psv": "PSV", "feyenoord": "Feyenoord",
    "celtic": "Celtic", "rangers": "Rangers",
}

ODDS_SPORTS = [
    "soccer_spain_la_liga", "soccer_epl", "soccer_germany_bundesliga",
    "soccer_italy_serie_a", "soccer_france_ligue_one",
    "soccer_uefa_champs_league", "soccer_portugal_primeira_liga",
    "soccer_spain_segunda_division", "soccer_netherlands_eredivisie",
    "soccer_germany_bundesliga2", "soccer_england_league1",
]

def resolve_team_name(alias: str) -> str:
    key = alias.lower().strip()
    return TEAM_ALIASES.get(key, alias.title())

def is_within_days(date_str: str, days: int = 3) -> bool:
    try:
        game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now().astimezone()
        diff = (game_date.date() - now.date()).days
        return 0 <= diff <= days
    except:
        return False

def normalize_game(g: dict) -> dict:
    if "equipo_local" in g:
        g["home_team"] = g.get("equipo_local", "")
    if "equipo_visitante" in g:
        g["away_team"] = g.get("equipo_visitante", "")
    if "fecha_de_inicio" in g:
        g["commence_time"] = g.get("fecha_de_inicio", "")
    bm_list = g.get("bookmakers", g.get("casas de apuestas", []))
    g["bookmakers"] = bm_list
    for bm in bm_list:
        markets = bm.get("markets", bm.get("mercados", []))
        bm["markets"] = markets
        for market in markets:
            outcomes = market.get("outcomes", market.get("resultados", []))
            market["outcomes"] = outcomes
            for o in outcomes:
                if "nombre" in o:
                    o["name"] = o["nombre"]
                if "precio" in o:
                    o["price"] = o["precio"]
                if "punto" in o:
                    o["point"] = o["punto"]
                name = o.get("name", "")
                if name in ["Empate", "Sorteo"]:
                    o["name"] = "Draw"
                elif name in ["Más de", "Mas de", "Por encima", "Más"]:
                    o["name"] = "Over"
                elif name in ["Menos de", "Por debajo de"]:
                    o["name"] = "Under"
    return g

async def get_team_recent_matches(team_name: str) -> str:
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_FOOTBALL_BASE}/teams", headers=headers, params={"search": team_name}, timeout=10)
            if resp.status_code != 200:
                return f"Error buscando {team_name}"
            teams = resp.json().get("response", [])
            if not teams:
                return f"Equipo no encontrado: {team_name}"
            team = teams[0]["team"]
            team_id = team["id"]
            team_full_name = team["name"]
            resp2 = await client.get(f"{API_FOOTBALL_BASE}/fixtures", headers=headers, params={"team": team_id, "last": 6, "status": "FT"}, timeout=10)
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
                api_key = str(ODDS_API_KEY).strip()
                url = f"{ODDS_BASE_URL}/sports/{sport}/odds?apiKey={api_key}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
                resp = await client.get(url, timeout=10)
                if resp.status_code != 200:
                    continue
                for game in resp.json():
                    game = normalize_game(game)
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
    api_key = str(ODDS_API_KEY).strip()
    if not api_key:
        return "ERROR: ODDS_API_KEY esta vacia."

    all_games = []
    errors = []

    async with httpx.AsyncClient() as client:
        for sport in ODDS_SPORTS:
            try:
                url = f"{ODDS_BASE_URL}/sports/{sport}/odds?apiKey={api_key}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
                resp = await client.get(url, timeout=15)
                if resp.status_code == 200:
                    games = resp.json()
                    for g in games:
                        g = normalize_game(g)
                        g["sport"] = sport
                        all_games.append(g)
                else:
                    errors.append(f"{sport}: {resp.status_code}")
            except Exception as e:
                errors.append(f"{sport}: {str(e)[:50]}")

    if not all_games:
        return f"Sin datos de API. Errores: {', '.join(errors[:3])}"

    filtered = [g for g in all_games if is_within_days(g.get("commence_time", ""), 3)]

    if not filtered:
        sample = all_games[0]
        return f"Hay {len(all_games)} partidos pero ninguno en proximos 3 dias. Ejemplo fecha: {sample.get('commence_time','?')[:10]}"

    picks = []
    for game in filtered:
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
                        home_odd = next((o["price"] for o in outcomes if o.get("name", "").lower() == home.lower()), None)
                        draw_odd = next((o["price"] for o in outcomes if o.get("name", "") == "Draw"), None)
                        if home_odd and draw_odd and home_odd >= 1.30:
                            if not any(p["match"] == f"{home} vs {away}" for p in picks):
                                picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "1X (Local o Empate)", "odd": round(home_odd, 2)})
                        break

        elif bet_type == "over_2.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for o in market.get("outcomes", []):
                            if o.get("name") == "Over" and str(o.get("point", "")) == "2.5" and o.get("price", 0) >= 1.90:
                                if not any(p["match"] == f"{home} vs {away}" for p in picks):
                                    picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "Mas de 2.5 goles", "odd": round(o["price"], 2)})
                        break

    picks = sorted(picks, key=lambda x: x["odd"], reverse=True)[:5]

    if not picks:
        sample = filtered[0] if filtered else None
        bm_sample = sample.get("bookmakers", [{}])[0] if sample else {}
        market_sample = bm_sample.get("markets", [{}])[0] if bm_sample else {}
        outcomes_sample = str(market_sample.get("outcomes", []))[:200] if market_sample else "?"
        return f"Hay {len(filtered)} partidos en rango pero ningun pick cumple filtro.\nEjemplo mercados: {outcomes_sample}"

    titles = {"1X": "Top picks 1X — cuota min. 1.30", "over_2.5": "Top picks Mas de 2.5 goles — cuota min. 1.90"}
    lines = [f"*{titles[bet_type]}*", ""]
    for i, p in enumerate(picks, 1):
        lines.append(f"{i}. {p['match']}")
        lines.append(f"   Hora: {p['time']} UTC")
        lines.append(f"   Apuesta: {p['bet']}")
        lines.append(f"   Cuota: {p['odd']}")
        lines.append("")
    lines.append("_Cuotas reales de casas europeas._")
    return "\n".join(lines)

async def analyze_match(team1_alias: str, team2_alias: str) -> str:
    team1_name = resolve_team_name(team1_alias)
    team2_name = resolve_team_name(team2_alias)
    team1_recent = await get_team_recent_matches(team1_name)
    team2_recent = await get_team_recent_matches(team2_name)
    odds_info = await get_real_odds(team1_name, team2_name)

    prompt = f"""Eres un analista experto en futbol y apuestas deportivas. Analiza este partido:

PARTIDO: {team1_name} vs {team2_name}

{team1_recent}

{team2_recent}

{odds_info}

Formato:
📊 *{team1_name} vs {team2_name}*
🏠 *Local/Visita:* [quien juega en casa]
🏆 *Competicion:* [liga]
📈 *Forma reciente {team1_name}:* [analisis]
📉 *Forma reciente {team2_name}:* [analisis]
💪 *Motivacion:* [situacion de cada equipo]
⚽ *Analisis de goles:* [tendencia]
🟨 *Estimado tarjetas:* [estimado]
🚩 *Estimado corners:* [estimado]
---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador o doble oportunidad con %]
⚽ Goles: [mas/menos X.X con %]
💰 Cuotas: [si disponibles]
_Analisis basado en datos reales._"""

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
