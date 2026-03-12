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
    "brentford": "Brentford FC",
    "crystal palace": "Crystal Palace FC",
    "nottingham": "Nottingham Forest FC",
    "forest": "Nottingham Forest FC",
    "bournemouth": "AFC Bournemouth",
    "leicester": "Leicester City FC",
    "ipswich": "Ipswich Town FC",
    "southampton": "Southampton FC",
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
    "psg": "Paris Saint-Germain FC",
    "paris": "Paris Saint-Germain FC",
    "marseille": "Olympique de Marseille",
    "lyon": "Olympique Lyonnais",
    "monaco": "AS Monaco FC",
    "lille": "LOSC Lille",
    "nice": "OGC Nice",
    "lens": "RC Lens",
    "rennes": "Stade Rennais FC",
    "benfica": "SL Benfica",
    "porto": "FC Porto",
    "sporting": "Sporting CP",
}

LEAGUE_IDS = ["PL", "PD", "BL1", "SA", "FL1", "CL", "PPL"]
LEAGUE_NAMES = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "PPL": "Primeira Liga",
    "CL": "Champions League",
}

ODDS_SPORTS = [
    "soccer_spain_la_liga",
    "soccer_epl",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
    "soccer_portugal_primeira_liga",
]

def resolve_team_name(alias: str) -> str:
    return TEAM_ALIASES.get(alias.lower().strip(), alias.title())

async def get_team_recent_matches(team_name: str) -> str:
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        try:
            # Buscar equipo
            resp = await client.get(
                f"{FOOTBALL_BASE_URL}/teams",
                headers=headers,
                params={"name": team_name},
                timeout=10
            )
            if resp.status_code != 200:
                return f"Sin datos para {team_name}"

            teams = resp.json().get("teams", [])
            if not teams:
                return f"Equipo no encontrado: {team_name}"

            team_id = teams[0]["id"]
            team_full_name = teams[0]["name"]

            # Obtener últimos partidos
            resp2 = await client.get(
                f"{FOOTBALL_BASE_URL}/teams/{team_id}/matches",
                headers=headers,
                params={
                    "status": "FINISHED",
                    "dateFrom": date_from,
                    "dateTo": date_to,
                    "limit": 6
                },
                timeout=10
            )
            if resp2.status_code != 200:
                return f"Sin partidos recientes para {team_full_name}"

            matches = resp2.json().get("matches", [])
            if not matches:
                return f"Sin partidos recientes para {team_full_name}"

            lines = [f"Últimos partidos de {team_full_name}:"]
            for m in matches:
                home = m.get("homeTeam", {}).get("name", "?")
                away = m.get("awayTeam", {}).get("name", "?")
                score = m.get("score", {}).get("fullTime", {})
                hg = score.get("home", "?")
                ag = score.get("away", "?")
                date = m.get("utcDate", "")[:10]
                competition = m.get("competition", {}).get("name", "")
                is_home = home == team_full_name
                venue = "🏠 Local" if is_home else "✈️ Visita"
                if is_home:
                    result = "✅ W" if hg > ag else ("🤝 D" if hg == ag else "❌ L")
                else:
                    result = "✅ W" if ag > hg else ("🤝 D" if hg == ag else "❌ L")
                lines.append(f"{date} | {competition} | {venue} | {home} {hg}-{ag} {away} | {result}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error obteniendo datos: {str(e)}"

async def get_real_odds(team1: str, team2: str) -> str:
    async with httpx.AsyncClient() as client:
        for sport in ODDS_SPORTS:
            try:
                resp = await client.get(
                    f"{ODDS_BASE_URL}/sports/{sport}/odds",
                    params={
                        "apiKey": ODDS_API_KEY,
                        "regions": "eu",
                        "markets": "h2h,totals",
                        "oddsFormat": "decimal",
                        "dateFormat": "iso"
                    },
                    timeout=10
                )
                if resp.status_code != 200:
                    continue

                games = resp.json()
                for game in games:
                    home = game.get("home_team", "").lower()
                    away = game.get("away_team", "").lower()
                    t1 = team1.lower()
                    t2 = team2.lower()

                    if (t1 in home or t1 in away) and (t2 in home or t2 in away):
                        bookmakers = game.get("bookmakers", [])
                        if not bookmakers:
                            continue

                        result_text = []
                        result_text.append(f"📊 Cuotas reales: {game['home_team']} vs {game['away_team']}")

                        for bm in bookmakers[:2]:
                            bm_name = bm.get("title", "")
                            for market in bm.get("markets", []):
                                if market["key"] == "h2h":
                                    result_text.append(f"\n🏦 {bm_name} (Resultado):")
                                    for outcome in market.get("outcomes", []):
                                        result_text.append(f"  {outcome['name']}: {outcome['price']}")
                                elif market["key"] == "totals":
                                    result_text.append(f"\n🏦 {bm_name} (Goles):")
                                    for outcome in market.get("outcomes", []):
                                        result_text.append(f"  {outcome['name']} {outcome.get('point','')}: {outcome['price']}")

                        return "\n".join(result_text)

            except Exception as e:
                continue

    return "Sin cuotas disponibles para este partido en este momento."

async def get_upcoming_with_odds(bet_type: str) -> str:
    today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=23, minute=59).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_games = []

    async with httpx.AsyncClient() as client:
        for sport in ODDS_SPORTS:
            try:
                resp = await client.get(
                    f"{ODDS_BASE_URL}/sports/{sport}/odds",
                    params={
                        "apiKey": ODDS_API_KEY,
                        "regions": "eu",
                        "markets": "h2h,totals",
                        "oddsFormat": "decimal",
                        "dateFormat": "iso",
                        "commenceTimeFrom": today,
                        "commenceTimeTo": tomorrow,
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    games = resp.json()
                    for g in games:
                        g["sport"] = sport
                    all_games.extend(games)
            except Exception:
                continue

    if not all_games:
        return "❌ No encontré partidos para hoy/mañana con cuotas disponibles."

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
                        if home_odd and draw_odd:
                            # Doble oportunidad 1X = 1 / (1/home + 1/draw) aprox
                            if home_odd <= 2.5 and home_odd >= 1.30:
                                picks.append({
                                    "match": f"{home} vs {away}",
                                    "time": commence,
                                    "bet": f"1X (Local o Empate)",
                                    "odd": round(home_odd, 2),
                                    "sport": game["sport"]
                                })
                            break
                    if picks and picks[-1]["match"] == f"{home} vs {away}":
                        break

        elif bet_type == "over_1.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for outcome in market.get("outcomes", []):
                            if outcome["name"] == "Over" and outcome.get("point") == 1.5:
                                odd = outcome["price"]
                                if odd >= 1.30:
                                    picks.append({
                                        "match": f"{home} vs {away}",
                                        "time": commence,
                                        "bet": "Más de 1.5 goles",
                                        "odd": round(odd, 2),
                                        "sport": game["sport"]
                                    })
                        break

        elif bet_type == "under_3.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for outcome in market.get("outcomes", []):
                            if outcome["name"] == "Under" and outcome.get("point") == 3.5:
                                odd = outcome["price"]
                                if odd >= 1.30:
                                    picks.append({
                                        "match": f"{home} vs {away}",
                                        "time": commence,
                                        "bet": "Menos de 3.5 goles",
                                        "odd": round(odd, 2),
                                        "sport": game["sport"]
                                    })
                        break

    # Ordenar por cuota más atractiva y tomar top 5
    picks = sorted(picks, key=lambda x: x["odd"], reverse=True)[:5]

    if not picks:
        return "❌ No encontré partidos hoy/mañana con cuota mayor de 1.30 para ese mercado."

    if bet_type == "1X":
        title = "🏠 Top 5 partidos *1X* (hoy/mañana) — cuota mín. 1.30"
    elif bet_type == "over_1.5":
        title = "⚽ Top 5 partidos *Más de 1.5 goles* (hoy/mañana) — cuota mín. 1.30"
    else:
        title = "🔒 Top 5 partidos *Menos de 3.5 goles* (hoy/mañana) — cuota mín. 1.30"

    lines = [title, ""]
    for i, p in enumerate(picks, 1):
        lines.append(f"{i}. ⚽ {p['match']}")
        lines.append(f"   📅 {p['time']}")
        lines.append(f"   🎯 {p['bet']}")
        lines.append(f"   💰 Cuota real: {p['odd']}")
        lines.append("")

    lines.append("_Cuotas reales de casas de apuestas europeas._")
    return "\n".join(lines)

async def analyze_match(team1_alias: str, team2_alias: str) -> str:
    team1_name = resolve_team_name(team1_alias)
    team2_name = resolve_team_name(team2_alias)

    # Obtener datos reales en paralelo
    team1_recent = await get_team_recent_matches(team1_name)
    team2_recent = await get_team_recent_matches(team2_name)
    odds_info = await get_real_odds(team1_name, team2_name)

    prompt = f"""Eres un analista experto en fútbol y apuestas deportivas. Analiza este partido con los datos REALES que te proporciono:

PARTIDO: {team1_name} vs {team2_name}

DATOS REALES - {team1_recent}

DATOS REALES - {team2_recent}

CUOTAS REALES DEL PARTIDO:
{odds_info}

Con estos datos reales, haz un análisis con este formato EXACTO:

📊 *{team1_name} vs {team2_name}*

🏠 *Local/Visita:* [quién juega en casa según tu conocimiento]
🏆 *Competición:* [liga o torneo]

📈 *Forma reciente {team1_name}:*
[analiza sus últimos resultados reales, racha, goles marcados/recibidos]

📉 *Forma reciente {team2_name}:*
[analiza sus últimos resultados reales, racha, goles marcados/recibidos]

💪 *Motivación:*
- {team1_name}: [posición en tabla, objetivos]
- {team2_name}: [posición en tabla, objetivos]

⚽ *Análisis de goles:* [tendencia según datos reales, más 1.5 o menos 3.5]
🟨 *Estimado tarjetas:* [estimado]
🚩 *Estimado corners:* [estimado]

---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador o doble oportunidad con porcentaje]
⚽ Goles: [más/menos X.X con porcentaje]
💰 Cuotas reales: [solo si están disponibles arriba, si no omite este campo]

_Análisis basado en datos reales. No garantiza resultado._"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"❌ Error al generar análisis: {str(e)}"

async def get_recommendations(bet_type: str) -> str:
    return await get_upcoming_with_odds(bet_type)
