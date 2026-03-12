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
    "barca": "FC Barcelona", "barça": "FC Barcelona", "barcelona": "FC Barcelona", "fcb": "FC Barcelona",
    "atletico": "Atlético de Madrid", "atletico madrid": "Atlético de Madrid", "atleti": "Atlético de Madrid",
    "sevilla": "Sevilla FC", "valencia": "Valencia CF", "villarreal": "Villarreal CF",
    "betis": "Real Betis", "sociedad": "Real Sociedad", "athletic": "Athletic Club", "bilbao": "Athletic Club",
    "osasuna": "CA Osasuna", "girona": "Girona FC", "getafe": "Getafe CF", "rayo": "Rayo Vallecano",
    "celta": "Celta de Vigo", "mallorca": "RCD Mallorca", "alaves": "Deportivo Alavés",
    "las palmas": "UD Las Palmas", "leganes": "CD Leganés", "espanol": "RCD Espanyol", "espanyol": "RCD Espanyol",
    "arsenal": "Arsenal FC", "chelsea": "Chelsea FC", "liverpool": "Liverpool FC",
    "city": "Manchester City FC", "man city": "Manchester City FC", "manchester city": "Manchester City FC",
    "united": "Manchester United FC", "man united": "Manchester United FC", "manchester united": "Manchester United FC",
    "tottenham": "Tottenham Hotspur FC", "spurs": "Tottenham Hotspur FC",
    "newcastle": "Newcastle United FC", "aston villa": "Aston Villa FC", "west ham": "West Ham United FC",
    "brighton": "Brighton & Hove Albion FC", "everton": "Everton FC", "fulham": "Fulham FC",
    "wolves": "Wolverhampton Wanderers FC", "brentford": "Brentford FC", "crystal palace": "Crystal Palace FC",
    "nottingham": "Nottingham Forest FC", "forest": "Nottingham Forest FC",
    "bournemouth": "AFC Bournemouth", "leicester": "Leicester City FC", "ipswich": "Ipswich Town FC",
    "bayern": "FC Bayern München", "dortmund": "Borussia Dortmund", "bvb": "Borussia Dortmund",
    "leverkusen": "Bayer 04 Leverkusen", "leipzig": "RB Leipzig", "frankfurt": "Eintracht Frankfurt",
    "stuttgart": "VfB Stuttgart", "gladbach": "Borussia Mönchengladbach", "wolfsburg": "VfL Wolfsburg",
    "juventus": "Juventus FC", "juve": "Juventus FC", "inter": "FC Internazionale Milano",
    "milan": "AC Milan", "ac milan": "AC Milan", "napoli": "SSC Napoli", "roma": "AS Roma",
    "lazio": "SS Lazio", "fiorentina": "ACF Fiorentina", "atalanta": "Atalanta BC",
    "psg": "Paris Saint-Germain FC", "paris": "Paris Saint-Germain FC",
    "marseille": "Olympique de Marseille", "lyon": "Olympique Lyonnais", "monaco": "AS Monaco FC",
    "benfica": "SL Benfica", "porto": "FC Porto", "sporting": "Sporting CP",
}

ODDS_SPORTS = [
    "soccer_spain_la_liga",
    "soccer_epl",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
    "soccer_portugal_primeira_liga",
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

async def get_team_recent_matches(team_name: str) -> str:
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        try:
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

            resp2 = await client.get(
                f"{FOOTBALL_BASE_URL}/teams/{team_id}/matches",
                headers=headers,
                params={"status": "FINISHED", "dateFrom": date_from, "dateTo": date_to, "limit": 6},
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
                    result = "✅ W" if (isinstance(hg, int) and isinstance(ag, int) and hg > ag) else ("🤝 D" if hg == ag else "❌ L")
                else:
                    result = "✅ W" if (isinstance(hg, int) and isinstance(ag, int) and ag > hg) else ("🤝 D" if hg == ag else "❌ L")
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
                    params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal"},
                    timeout=10
                )
                if resp.status_code != 200:
                    continue

                for game in resp.json():
                    home = game.get("home_team", "").lower()
                    away = game.get("away_team", "").lower()
                    t1 = team1.lower().replace("fc ", "").replace(" fc", "")
                    t2 = team2.lower().replace("fc ", "").replace(" fc", "")

                    if (t1 in home or t1 in away) and (t2 in home or t2 in away):
                        bookmakers = game.get("bookmakers", [])
                        if not bookmakers:
                            continue
                        result_text = [f"📊 Cuotas reales: {game['home_team']} vs {game['away_team']}"]
                        for bm in bookmakers[:2]:
                            for market in bm.get("markets", []):
                                if market["key"] == "h2h":
                                    result_text.append(f"\n🏦 {bm['title']} (Resultado 1X2):")
                                    for o in market.get("outcomes", []):
                                        result_text.append(f"  {o['name']}: {o['price']}")
                                elif market["key"] == "totals":
                                    result_text.append(f"\n🏦 {bm['title']} (Goles):")
                                    for o in market.get("outcomes", []):
                                        result_text.append(f"  {o['name']} {o.get('point','')}: {o['price']}")
                        return "\n".join(result_text)

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

    # Filtrar solo hoy y mañana
    all_games = [g for g in all_games if is_today_or_tomorrow(g.get("commence_time", ""))]

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
                        if home_odd and draw_odd and 1.30 <= home_odd <= 2.20:
                            already = any(p["match"] == f"{home} vs {away}" for p in picks)
                            if not already:
                                picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "1X (Local o Empate)", "odd": round(home_odd, 2)})
                        break

        elif bet_type == "over_1.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for o in market.get("outcomes", []):
                            if o["name"] == "Over" and str(o.get("point", "")) == "1.5" and o["price"] >= 1.30:
                                already = any(p["match"] == f"{home} vs {away}" for p in picks)
                                if not already:
                                    picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "Más de 1.5 goles", "odd": round(o["price"], 2)})
                        break

        elif bet_type == "under_3.5":
            for bm in bookmakers:
                for market in bm.get("markets", []):
                    if market["key"] == "totals":
                        for o in market.get("outcomes", []):
                            if o["name"] == "Under" and str(o.get("point", "")) == "3.5" and o["price"] >= 1.30:
                                already = any(p["match"] == f"{home} vs {away}" for p in picks)
                                if not already:
                                    picks.append({"match": f"{home} vs {away}", "time": commence, "bet": "Menos de 3.5 goles", "odd": round(o["price"], 2)})
                        break

    picks = sorted(picks, key=lambda x: x["odd"], reverse=True)[:5]

    if not picks:
        return "❌ No encontré partidos hoy/mañana con cuota mayor de 1.30 para ese mercado."

    titles = {"1X": "🏠 Top 5 partidos *1X*", "over_1.5": "⚽ Top 5 *Más de 1.5 goles*", "under_3.5": "🔒 Top 5 *Menos de 3.5 goles*"}
    lines = [f"{titles[bet_type]} — hoy/mañana | cuota mín. 1.30", ""]
    for i, p in enumerate(picks, 1):
        lines.append(f"{i}. ⚽ {p['match']}")
        lines.append(f"   📅 {p['time']} UTC")
        lines.append(f"   🎯 {p['bet']}")
        lines.append(f"   💰 Cuota real: {p['odd']}")
        lines.append("")

    lines.append("_Cuotas reales de casas de apuestas europeas._")
    return "\n".join(lines)

async def analyze_match(team1_alias: str, team2_alias: str) -> str:
    team1_name = resolve_team_name(team1_alias)
    team2_name = resolve_team_name(team2_alias)

    team1_recent = await get_team_recent_matches(team1_name)
    team2_recent = await get_team_recent_matches(team2_name)
    odds_info = await get_real_odds(team1_name, team2_name)

    prompt = f"""Eres un analista experto en fútbol y apuestas deportivas. Analiza este partido con los datos REALES:

PARTIDO: {team1_name} vs {team2_name}

DATOS REALES:
{team1_recent}

DATOS REALES:
{team2_recent}

CUOTAS REALES:
{odds_info}

Responde con este formato EXACTO:

📊 *{team1_name} vs {team2_name}*

🏠 *Local/Visita:* [quién juega en casa]
🏆 *Competición:* [liga o torneo]

📈 *Forma reciente {team1_name}:*
[analiza resultados reales, racha, goles]

📉 *Forma reciente {team2_name}:*
[analiza resultados reales, racha, goles]

💪 *Motivación:*
- {team1_name}: [objetivos actuales]
- {team2_name}: [objetivos actuales]

⚽ *Análisis de goles:* [tendencia según datos]
🟨 *Estimado tarjetas:* [estimado]
🚩 *Estimado corners:* [estimado]

---
🎯 *APUESTA SUGERIDA:*
✅ Resultado: [ganador o doble oportunidad con %]
⚽ Goles: [más/menos X.X con %]
💰 Cuotas reales disponibles: [solo si están en los datos, si no omite]

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
