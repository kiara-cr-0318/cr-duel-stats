# ---
# title: クラロワ対戦履歴の取得・蓄積スクリプト
# client: internal（個人プロジェクト）
# type: script
# status: draft
# confidentiality: internal
# created: 2026-11-13
# updated: 2026-11-13
# tags: [clash-royale, duel, crown-series, github-actions]
# ---
"""公式API（RoyaleAPIプロキシ経由）から対戦履歴を取得し、data/ に追記保存する。

APIは直近30戦程度しか返さないため、定期実行して重複を除きながら貯めていく。
環境変数:
  CR_API_KEY    : developer.clashroyale.com のキー（IP 45.79.218.79 で発行）
  CR_PLAYER_TAG : プレイヤータグ（省略時 #2J8GG89GY）
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BATTLES = os.path.join(ROOT, "data", "battles.json")
CARDS = os.path.join(ROOT, "data", "cards.json")
TAG = os.environ.get("CR_PLAYER_TAG", "#2J8GG89GY")
BASE = "https://proxy.royaleapi.dev/v1"


def api(path):
    key = os.environ.get("CR_API_KEY", "").strip()
    if not key:
        sys.exit("CR_API_KEY が設定されていません")
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def result(a, b):
    return "W" if a > b else ("L" if a < b else "D")


def remember_card(c, card_map, support=False):
    """カード情報を card_map に登録（既存の値は新しい値で上書き、無い値は保持）。"""
    cid = str(c["id"])
    icons = c.get("iconUrls", {})
    old = card_map.get(cid, {})
    card_map[cid] = {
        "name": c.get("name") or old.get("name"),
        "elixir": c.get("elixirCost", old.get("elixir")),
        "rarity": c.get("rarity") or old.get("rarity"),
        "icon": icons.get("medium") or old.get("icon"),
        "evoIcon": icons.get("evolutionMedium") or old.get("evoIcon"),
        "heroIcon": icons.get("heroMedium") or old.get("heroIcon"),
        "support": support or old.get("support", False),
    }


def slim_cards(cards, card_map):
    out = []
    for c in cards:
        remember_card(c, card_map)
        out.append({"id": c["id"], "evo": c.get("evolutionLevel", 0)})
    return out


def convert(b, card_map):
    me, opp = b["team"][0], b["opponent"][0]
    support = me.get("supportCards") or []
    rec = {
        "id": b["battleTime"] + "_" + opp.get("tag", ""),
        "time": b["battleTime"],
        "type": b.get("type"),
        "mode": (b.get("gameMode") or {}).get("name"),
        "deckSelection": b.get("deckSelection"),
        "league": b.get("leagueNumber"),
        "crowns": me.get("crowns", 0),
        "oppCrowns": opp.get("crowns", 0),
        "oppName": opp.get("name"),
        "tt": support[0]["id"] if support else None,
        "deck": slim_cards(me.get("cards", []), card_map),
    }
    rec["result"] = result(rec["crowns"], rec["oppCrowns"])
    if me.get("rounds"):
        rounds = []
        for i, r in enumerate(me["rounds"]):
            orr = opp["rounds"][i] if i < len(opp.get("rounds", [])) else {}
            rounds.append({
                "pick": i + 1,
                "crowns": r.get("crowns", 0),
                "oppCrowns": orr.get("crowns", 0),
                "result": result(r.get("crowns", 0), orr.get("crowns", 0)),
                "deck": slim_cards(r.get("cards", []), card_map),
            })
        rec["rounds"] = rounds
    return rec


def main():
    battles = load(BATTLES, {"player": {}, "battles": []})
    card_map = load(CARDS, {})
    known = {b["id"] for b in battles["battles"]}

    # 全カード一覧（デッキを手で組むため）
    allc = api("/cards")
    for c in allc.get("items", []):
        remember_card(c, card_map)
    for c in allc.get("supportItems", []):
        remember_card(c, card_map, support=True)

    log = api("/players/" + urllib.parse.quote(TAG) + "/battlelog")
    added = 0
    for b in log:
        rec = convert(b, card_map)
        if rec["id"] not in known:
            battles["battles"].append(rec)
            known.add(rec["id"])
            added += 1
    battles["battles"].sort(key=lambda x: x["time"], reverse=True)

    p = api("/players/" + urllib.parse.quote(TAG))
    battles["player"] = {"tag": p.get("tag"), "name": p.get("name"), "trophies": p.get("trophies")}
    if added or not battles.get("updated"):
        battles["updated"] = log[0]["battleTime"] if log else battles.get("updated")

    os.makedirs(os.path.dirname(BATTLES), exist_ok=True)
    with open(BATTLES, "w", encoding="utf-8") as f:
        json.dump(battles, f, ensure_ascii=False, separators=(",", ":"))
    with open(CARDS, "w", encoding="utf-8") as f:
        json.dump(card_map, f, ensure_ascii=False, separators=(",", ":"))
    print(f"added {added} battles (total {len(battles['battles'])})")


if __name__ == "__main__":
    main()
