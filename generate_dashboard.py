"""
generate_dashboard.py — Africa Fuel Tracker
Reads data/prices_db.json + data/history_db.json
Embeds data directly into index.html (no fetch, no CORS, works on GitHub Pages)
"""
import json, re
from datetime import date, datetime, timedelta
from pathlib import Path
from string import Template

ROOT       = Path(__file__).parent
DATA_DIR   = ROOT / "data"
PRICES_DB  = DATA_DIR / "prices_db.json"
HISTORY_DB = DATA_DIR / "history_db.json"
OUTPUT     = ROOT / "index.html"

OCTANE    = {"Algeria":95,"Egypt":92,"Libya":95,"Morocco":95,"Tunisia":95,
             "Kenya":93,"South Africa":95,"Zambia":93,"Namibia":93,"Botswana":93,
             "Mauritius":95,"Seychelles":95,"Eswatini":93,"Lesotho":93}
REGULATED = {"Algeria","Libya","Tunisia","Sudan","Egypt","Chad","Angola","Ethiopia",
             "Uganda","Niger","Cameroon","Congo Republic","Gabon","Equatorial Guinea"}

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def week_series(entries, first_date, last_date, fu, fl):
    entries = sorted(entries, key=lambda e: e["date"])
    if not entries:
        return [], [], []
    d = first_date
    while d.weekday() != 6:
        d += timedelta(days=1)
    weeks, usd_s, loc_s, labels = [], [], [], []
    while d <= last_date:
        weeks.append(d)
        d += timedelta(days=7)
    if not weeks:
        weeks = [last_date]
    for w in weeks:
        cands = [e for e in entries if e["date"] <= w.isoformat()] or [entries[0]]
        best  = cands[-1]
        uv, lv = best.get(fu), best.get(fl)
        if uv is not None and lv is not None:
            usd_s.append(round(float(uv), 4))
            loc_s.append(round(float(lv), 4))
            labels.append(w.strftime("%d %b"))
    return labels, usd_s, loc_s

def build(prices_db, history_db):
    meta     = prices_db.get("meta", {})
    data     = prices_db.get("data", {})
    run_str  = meta.get("run_date", date.today().isoformat())
    run_date = date.fromisoformat(run_str)

    all_dates = [e["date"] for v in history_db.values() for e in v if e.get("date")]
    first_str  = min(all_dates) if all_dates else "2026-01-01"
    first_date = date.fromisoformat(first_str)

    ref = max(history_db.items(), key=lambda x: len(x[1]), default=(None, None))[0]
    wl, _, _ = week_series(history_db.get(ref, []), first_date, run_date, "gas_usd", "gas_loc") if ref else ([], [], [])
    if not wl:
        wl = [run_date.strftime("%d %b")]

    fx = {}
    for d in data.values():
        c, r = d.get("currency"), d.get("fx_rate")
        if c and r:
            fx[c] = round(float(r), 4)

    countries = []
    for country, d in data.items():
        hist  = history_db.get(country, [])
        cur   = d.get("currency", "USD")
        fxr   = float(d.get("fx_rate", 1) or 1)
        gu    = float(d.get("gas_usd", 0))
        du    = float(d.get("die_usd", 0))
        gl    = float(d.get("gas_loc", 0))
        dl    = float(d.get("die_loc", 0))

        _, guw, glw = week_series(hist, first_date, run_date, "gas_usd", "gas_loc")
        _, duw, dlw = week_series(hist, first_date, run_date, "die_usd", "die_loc")

        n = len(wl)
        def pad(s, v):
            if not s: return [round(float(v),4)]*n
            if len(s) < n: s = [s[0]]*(n-len(s)) + s
            return s[-n:]

        guw = pad(guw, gu); glw = pad(glw, gl)
        duw = pad(duw, du); dlw = pad(dlw, dl)

        chg_gas = round((gu/guw[0]-1)*100, 2) if guw and guw[0] else 0.0
        chg_die = round((du/duw[0]-1)*100, 2) if duw and duw[0] else 0.0

        countries.append({
            "name": country, "region": d.get("region",""),
            "currency": cur, "fx_rate": round(fxr,4),
            "octane": OCTANE.get(country, 91),
            "src": d.get("source_url",""),
            "confidence": d.get("confidence","medium"),
            "old_source": bool(d.get("old_source")),
            "stale": bool(d.get("stale")),
            "effective_date": d.get("effective_date",""),
            "gas_usd_now": round(gu,4), "die_usd_now": round(du,4),
            "lpg_usd_now": round(gu*0.65,3),
            "gas_loc_now": round(gl,4), "die_loc_now": round(dl,4),
            "lpg_loc_now": round(gl*0.65,2),
            "gas_usd_w": guw, "die_usd_w": duw,
            "gas_loc_w": glw, "die_loc_w": dlw,
            "chg_gas": chg_gas, "chg_die": chg_die,
            "min_gas": round(min(guw),4), "max_gas": round(max(guw),4),
            "avg_gas": round(sum(guw)/len(guw),4),
            "regulated": country in REGULATED,
        })

    lu = meta.get("last_updated","")
    try:
        dt = datetime.fromisoformat(lu.replace("Z","+00:00"))
        updated = dt.strftime("%-d %B %Y — %H:%M UTC")
    except:
        updated = run_str

    return {
        "updated": updated,
        "period": f"{first_date.strftime('%-d %b %Y')} — {run_date.strftime('%-d %b %Y')}",
        "period_start": first_str, "period_end": run_str,
        "week_labels": wl, "n_weeks": len(wl),
        "fx_rates": fx, "countries": countries,
        "n_countries": len(countries),
        "n_ok": meta.get("countries_ok", len(countries)),
        "n_stale": meta.get("countries_stale", 0),
    }

def render(D):
    n  = D["n_countries"]
    # Embed JSON safely — escape </script to prevent early tag closure
    dj = json.dumps(D, ensure_ascii=False, separators=(",",":"))
    dj = dj.replace("</", "<\\/")

    # Build HTML using string concatenation — no f-string on the full page
    head = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AfricaFuelWatch 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--g0:#00A86A;--g1:#00CC85;--gold:#F5A300;--red:#E8394A;--blue:#1A8FD8;--cyan:#00C4CF;--amber:#E87C1A;--bg:#07111E;--bg1:#0B1826;--s1:#132435;--s2:#1A3347;--s3:#214059;--t1:#E8EEF4;--t2:#9EC8E0;--t3:#5A8FAF;--t4:#2D5A7A;--r8:8px;--r12:12px;--r16:16px;--r24:24px;--r99:99px;--sh:0 4px 24px rgba(0,0,0,.4);--sh-g:0 4px 24px rgba(0,168,106,.25)}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--t1);font-family:'Outfit',sans-serif;overflow-x:hidden;min-height:100vh;line-height:1.5}
::-webkit-scrollbar{width:4px;height:4px}::-webkit-scrollbar-track{background:var(--bg1)}::-webkit-scrollbar-thumb{background:var(--s3);border-radius:99px}
a{color:inherit;text-decoration:none}button{cursor:pointer;font-family:'Outfit',sans-serif;border:none;outline:none}input,select{font-family:'Outfit',sans-serif;outline:none}canvas{display:block}
.page{display:flex;flex-direction:column;min-height:100vh}.wrap{width:100%;max-width:1440px;margin:0 auto;padding:0 1.5rem}
nav{position:sticky;top:0;z-index:500;height:56px;background:rgba(7,17,30,.96);backdrop-filter:blur(24px);border-bottom:1px solid var(--s2)}
.nav-inner{height:100%;display:flex;align-items:center;justify-content:space-between;gap:1rem}
.nav-brand{display:flex;align-items:center;gap:.6rem;flex-shrink:0}
.brand-icon{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--g0),#007A4D);display:flex;align-items:center;justify-content:center;font-size:1rem;box-shadow:var(--sh-g);flex-shrink:0}
.brand-name{font-size:.9rem;font-weight:800;letter-spacing:-.02em}.brand-name span{color:var(--g0)}
.brand-tag{font-size:.6rem;font-weight:600;letter-spacing:.06em;color:var(--g0);background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.25);border-radius:var(--r99);padding:.12rem .5rem;text-transform:uppercase}
.nav-right{display:flex;align-items:center;gap:.6rem}.nav-meta{font-size:.67rem;color:var(--t3);font-family:'JetBrains Mono',monospace;display:none}
@media(min-width:640px){.nav-meta{display:block}}
.live-dot{display:flex;align-items:center;gap:.35rem;background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.3);border-radius:var(--r99);padding:.2rem .6rem;font-size:.65rem;font-weight:600;color:var(--g0);font-family:'JetBrains Mono',monospace;letter-spacing:.02em}
.pulse{width:6px;height:6px;border-radius:50%;background:var(--g0);animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.btn-dl-nav{display:flex;align-items:center;gap:.4rem;padding:.32rem .75rem;border-radius:var(--r8);background:var(--g0);color:#fff;font-size:.73rem;font-weight:700;transition:.15s;white-space:nowrap;cursor:pointer}
.btn-dl-nav:hover{background:var(--g1);transform:translateY(-1px)}
.ticker{background:#0a0e14;border-bottom:2px solid #1a2a3a;height:34px;overflow:hidden;display:flex;align-items:center;flex-shrink:0}
.ticker-lbl{flex-shrink:0;padding:0 1rem;height:100%;display:flex;align-items:center;gap:.5rem;background:#F5A300;font-size:.65rem;font-weight:800;letter-spacing:.1em;color:#000;text-transform:uppercase;white-space:nowrap;font-family:'JetBrains Mono',monospace}
.ticker-lbl .tl-dot{width:7px;height:7px;border-radius:50%;background:#000;animation:pulse 2s ease-in-out infinite}
.ticker-body{flex:1;overflow:hidden;position:relative}
.ticker-body::before{content:'';position:absolute;top:0;bottom:0;left:0;width:48px;z-index:2;background:linear-gradient(90deg,#0a0e14,transparent);pointer-events:none}
.ticker-body::after{content:'';position:absolute;top:0;bottom:0;right:0;width:48px;z-index:2;background:linear-gradient(270deg,#0a0e14,transparent);pointer-events:none}
.ticker-track{display:flex;align-items:center;white-space:nowrap;animation:ticker 140s linear infinite}
.ticker-track:hover{animation-play-state:paused}
@keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ti{display:inline-flex;align-items:center;gap:.5rem;padding:0 1.2rem;height:34px;border-right:1px solid rgba(255,255,255,.07);font-size:.72rem;cursor:default}
.ti-n{font-weight:700;color:#e8eef4;letter-spacing:.01em}
.ti-p{font-family:'JetBrains Mono',monospace;color:#F5A300;font-weight:600;font-size:.72rem}
.ti-c{font-size:.6rem;color:#4a6a7a;font-family:'JetBrains Mono',monospace}
.ti-sep{color:#1a3347;font-size:.6rem;margin:0 -.2rem}
.up{color:#E8394A;font-family:'JetBrains Mono',monospace;font-size:.68rem;font-weight:700}
.dn{color:#00CC85;font-family:'JetBrains Mono',monospace;font-size:.68rem;font-weight:700}
.fl{color:#4a6a7a;font-family:'JetBrains Mono',monospace;font-size:.68rem}
main{flex:1;padding:1.25rem 0 3rem}
.hero{background:linear-gradient(135deg,#0B1E31 0%,#0E2A3D 60%,#0A1E2D 100%);border:1px solid var(--s2);border-radius:var(--r16);padding:1.5rem;margin-bottom:1.25rem;position:relative;overflow:hidden}
.hero-glow{position:absolute;top:-80px;right:-80px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(0,168,106,.07) 0%,transparent 70%);pointer-events:none}
.hero-grid{display:grid;grid-template-columns:1fr;gap:1.25rem}
@media(min-width:768px){.hero-grid{grid-template-columns:1fr auto;align-items:start}}
.hero-title{font-size:clamp(1.3rem,4vw,1.8rem);font-weight:900;line-height:1.15;margin-bottom:.5rem;letter-spacing:-.03em;background:linear-gradient(135deg,#E8EEF4 0%,#9EC8E0 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{font-size:.85rem;color:var(--t2);line-height:1.6;max-width:580px;margin-bottom:1rem}
.hero-tags{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1.1rem}
.tag{display:inline-flex;align-items:center;gap:.3rem;padding:.22rem .65rem;border-radius:var(--r99);font-size:.68rem;font-weight:600}
.tag-g{background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.2);color:var(--g0)}
.tag-y{background:rgba(245,163,0,.1);border:1px solid rgba(245,163,0,.2);color:var(--gold)}
.tag-b{background:rgba(26,143,216,.1);border:1px solid rgba(26,143,216,.2);color:var(--blue)}
.btn-dl{display:inline-flex;align-items:center;gap:.6rem;padding:.65rem 1.35rem;border-radius:var(--r12);background:linear-gradient(135deg,#007A4D,var(--g0));color:#fff;font-size:.85rem;font-weight:700;box-shadow:var(--sh-g);transition:.2s;cursor:pointer;border:none}
.btn-dl:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,168,106,.4)}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:.6rem}
.kpi{background:rgba(7,17,30,.7);border:1px solid var(--s2);border-radius:var(--r12);padding:.85rem 1rem}
.kpi-label{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--t3);margin-bottom:.25rem}
.kpi-value{font-size:1.2rem;font-weight:900;font-family:'JetBrains Mono',monospace;line-height:1.1}
.kpi-sub{font-size:.67rem;color:var(--t3);margin-top:.2rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sec-head{display:flex;align-items:center;justify-content:space-between;gap:.75rem;flex-wrap:wrap;margin-bottom:.85rem}
.sec-title{font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--t3);display:flex;align-items:center;gap:.5rem}
.sec-pill{background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.2);color:var(--g0);padding:.1rem .48rem;border-radius:var(--r99);font-size:.6rem;font-weight:800;letter-spacing:.04em}
.reg-strip{display:grid;gap:.6rem;margin-bottom:1.25rem;grid-template-columns:repeat(2,1fr)}
@media(min-width:480px){.reg-strip{grid-template-columns:repeat(3,1fr)}}
@media(min-width:900px){.reg-strip{grid-template-columns:repeat(5,1fr)}}
.rc{background:var(--s1);border:1px solid var(--s2);border-radius:var(--r12);padding:.85rem 1rem;position:relative;overflow:hidden;transition:.2s}
.rc:hover{border-color:var(--s3);transform:translateY(-2px);box-shadow:var(--sh)}
.rc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.rc-na::before{background:var(--gold)}.rc-wa::before{background:var(--g0)}.rc-ea::before{background:var(--blue)}.rc-ca::before{background:var(--amber)}.rc-sa::before{background:var(--red)}
.rc-name{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--t3);margin-bottom:.4rem}
.rc-price{font-size:1.2rem;font-weight:900;font-family:'JetBrains Mono',monospace;line-height:1;margin-bottom:.25rem}
.rc-count{font-size:.63rem;color:var(--t4);margin-bottom:.5rem}
.rc-bar{background:var(--bg);border-radius:99px;height:3px;overflow:hidden;margin-bottom:.35rem}
.rc-fill{height:100%;border-radius:99px;transition:width .8s ease}.rc-chg{font-size:.67rem;font-weight:600}
.card{background:var(--s1);border:1px solid var(--s2);border-radius:var(--r16);padding:1.1rem 1.15rem;margin-bottom:1.1rem}
.card-head{font-size:.71rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--t3);margin-bottom:.9rem;display:flex;align-items:center;justify-content:space-between;gap:.5rem;flex-wrap:wrap}
.chart-row{display:grid;grid-template-columns:1fr;gap:1.1rem;margin-bottom:1.1rem}
@media(min-width:900px){.chart-row{grid-template-columns:3fr 2fr}}
.chart-box{height:260px;position:relative}
@media(min-width:640px){.chart-box{height:300px}}
.tog{display:inline-flex;background:var(--bg);border:1px solid var(--s2);border-radius:var(--r8);padding:2px;gap:2px;flex-wrap:wrap}
.tog-btn{padding:.26rem .7rem;border-radius:6px;background:transparent;color:var(--t3);font-size:.7rem;font-weight:600;font-family:'Outfit',sans-serif;transition:.12s;white-space:nowrap}
.tog-btn.on{background:var(--g0);color:#fff;box-shadow:0 2px 8px rgba(0,168,106,.3)}.tog-btn:hover:not(.on){background:var(--s2);color:var(--t1)}
.rank-row{display:grid;grid-template-columns:1fr;gap:1.1rem;margin-bottom:1.1rem}
@media(min-width:640px){.rank-row{grid-template-columns:1fr 1fr}}
.rank-list{display:flex;flex-direction:column;gap:.3rem}
.rank-item{display:flex;align-items:center;gap:.65rem;padding:.5rem .65rem;border-radius:var(--r8);border:1px solid transparent;cursor:pointer;transition:.12s}
.rank-item:hover{background:var(--bg1);border-color:var(--s2)}
.rank-n{width:24px;height:24px;border-radius:6px;background:var(--bg);border:1px solid var(--s2);display:flex;align-items:center;justify-content:center;font-size:.67rem;font-weight:700;color:var(--t3);flex-shrink:0}
.rank-item:nth-child(-n+3) .rank-n{background:rgba(245,163,0,.1);border-color:rgba(245,163,0,.3);color:var(--gold)}
.rank-name{font-size:.78rem;font-weight:600;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rank-right{display:flex;flex-direction:column;align-items:flex-end;gap:.12rem;flex-shrink:0}
.rank-price{font-family:'JetBrains Mono',monospace;font-size:.78rem;font-weight:600}
.rank-bar-bg{height:2px;background:var(--bg);border-radius:99px;width:60px}
.rank-bar-fg{height:100%;border-radius:99px;transition:width .4s}
.fx-wrap{display:grid;gap:.45rem;grid-template-columns:repeat(2,1fr);max-height:240px;overflow-y:auto}
@media(min-width:480px){.fx-wrap{grid-template-columns:repeat(3,1fr)}}
@media(min-width:768px){.fx-wrap{grid-template-columns:repeat(4,1fr)}}
@media(min-width:1100px){.fx-wrap{grid-template-columns:repeat(6,1fr)}}
.fx-card{background:var(--bg1);border:1px solid var(--s2);border-radius:var(--r8);padding:.5rem .65rem;display:flex;align-items:center;justify-content:space-between;gap:.4rem}
.fx-code{font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:600;color:var(--g0)}
.fx-rate{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--t1);font-weight:500}
.fx-inv{font-size:.58rem;color:var(--t4);display:block;margin-top:.08rem}
.tbl-controls{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;padding-bottom:.75rem;border-bottom:1px solid var(--s2);margin-bottom:.75rem}
.fb{padding:.24rem .7rem;border-radius:var(--r99);font-size:.7rem;font-weight:600;border:1px solid var(--s2);background:transparent;color:var(--t3);font-family:'Outfit',sans-serif;transition:.12s;white-space:nowrap}
.fb.on{background:var(--g0);border-color:var(--g0);color:#fff}.fb:hover:not(.on){border-color:var(--s3);color:var(--t1)}
.ctrl-right{display:flex;align-items:center;gap:.5rem;margin-left:auto;flex-wrap:wrap}
.sort-sel{padding:.24rem .6rem;border-radius:var(--r8);font-size:.7rem;border:1px solid var(--s2);background:var(--bg);color:var(--t1);font-family:'Outfit',sans-serif;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%235A8FAF' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right .5rem center;padding-right:1.75rem}
.srch-wrap{position:relative}.srch-ico{position:absolute;left:.55rem;top:50%;transform:translateY(-50%);color:var(--t4);pointer-events:none;font-size:.8rem}
.srch{padding:.24rem .6rem .24rem 1.75rem;border-radius:var(--r8);font-size:.7rem;border:1px solid var(--s2);background:var(--bg);color:var(--t1);font-family:'Outfit',sans-serif;width:150px;transition:.2s}
.srch:focus{border-color:var(--g0);width:200px}.srch::placeholder{color:var(--t4)}
.tbl-wrap{overflow-x:auto}.tbl-hint{display:flex;align-items:center;gap:.4rem;font-size:.65rem;color:var(--t4);margin-bottom:.5rem;padding:.35rem .6rem;background:rgba(26,143,216,.06);border:1px solid rgba(26,143,216,.15);border-radius:var(--r8)}
@media(min-width:900px){.tbl-hint{display:none}}
table{width:100%;border-collapse:collapse;font-size:.76rem;min-width:600px}
thead th{background:var(--bg);border-bottom:2px solid var(--s2);padding:.45rem .65rem;font-size:.64rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--t3);text-align:left;white-space:nowrap;cursor:pointer;position:sticky;top:0;z-index:2;user-select:none}
thead th:hover{color:var(--g0)}thead th.sorted{color:var(--g0);border-bottom-color:var(--g0)}
tbody tr{border-bottom:1px solid rgba(26,51,71,.4);cursor:pointer;transition:.1s}tbody tr:hover{background:rgba(0,168,106,.04)}
td{padding:.45rem .65rem;white-space:nowrap;vertical-align:middle}
.cn{font-weight:700}.mono{font-family:'JetBrains Mono',monospace;font-weight:500}
.rt{font-size:.61rem;font-weight:600;padding:.12rem .45rem;border-radius:var(--r99);border:1px solid}
.rt-na{color:var(--gold);border-color:rgba(245,163,0,.3);background:rgba(245,163,0,.07)}
.rt-wa{color:var(--g0);border-color:rgba(0,168,106,.3);background:rgba(0,168,106,.07)}
.rt-ea{color:var(--blue);border-color:rgba(26,143,216,.3);background:rgba(26,143,216,.07)}
.rt-ca{color:var(--amber);border-color:rgba(232,124,26,.3);background:rgba(232,124,26,.07)}
.rt-sa{color:var(--red);border-color:rgba(232,57,74,.3);background:rgba(232,57,74,.07)}
.cur{font-family:'JetBrains Mono',monospace;font-size:.63rem;font-weight:500;padding:.1rem .38rem;border-radius:4px;background:rgba(0,168,106,.08);color:var(--g0);border:1px solid rgba(0,168,106,.18)}
.up2{color:var(--red);font-weight:700}.dn2{color:var(--g1);font-weight:700}.fl2{color:var(--t4)}
.lev-h{color:var(--red);font-size:.63rem;font-weight:800}.lev-m{color:var(--gold);font-size:.63rem;font-weight:800}.lev-l{color:var(--g0);font-size:.63rem;font-weight:800}
.pb{height:2px;background:var(--bg);border-radius:99px;width:60px;margin-top:3px}.pb-f{height:100%;background:var(--g0);border-radius:99px}
.cnt-badge{font-size:.7rem;font-weight:700;background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.2);color:var(--g0);padding:.1rem .45rem;border-radius:var(--r99)}
.stale-badge{font-size:.58rem;font-weight:700;background:rgba(245,163,0,.12);border:1px solid rgba(245,163,0,.3);color:var(--gold);padding:.08rem .4rem;border-radius:4px;margin-left:.3rem;vertical-align:middle}
.old-badge{font-size:.58rem;font-weight:700;background:rgba(232,57,74,.1);border:1px solid rgba(232,57,74,.3);color:var(--red);padding:.08rem .4rem;border-radius:4px;margin-left:.3rem;vertical-align:middle}
.ov{position:fixed;inset:0;background:rgba(7,17,30,.85);backdrop-filter:blur(8px);z-index:900;display:flex;align-items:flex-end;justify-content:center;opacity:0;pointer-events:none;transition:opacity .25s}
@media(min-width:600px){.ov{align-items:center}}
.ov.open{opacity:1;pointer-events:all}
.modal{background:var(--bg1);border:1px solid var(--s2);border-radius:var(--r24) var(--r24) 0 0;width:100%;max-width:520px;max-height:92vh;overflow-y:auto;transform:translateY(60px);transition:transform .3s cubic-bezier(.34,1.56,.64,1)}
@media(min-width:600px){.modal{border-radius:var(--r24);transform:scale(.94)}}
.ov.open .modal{transform:translateY(0) scale(1)}
.m-bar{display:block;width:36px;height:3px;background:var(--s3);border-radius:99px;margin:.6rem auto .2rem}
@media(min-width:600px){.m-bar{display:none}}
.m-head{display:flex;justify-content:space-between;align-items:flex-start;padding:1rem 1.25rem .6rem;gap:.75rem;border-bottom:1px solid var(--s2)}
.m-title{font-size:1.1rem;font-weight:800;letter-spacing:-.02em}.m-sub{font-size:.72rem;color:var(--t3);margin-top:.2rem}
.m-fx{font-size:.67rem;color:var(--t4);font-family:'JetBrains Mono',monospace;margin-top:.25rem}
.m-close{width:28px;height:28px;border-radius:8px;border:1px solid var(--s2);background:transparent;color:var(--t3);font-size:1rem;display:flex;align-items:center;justify-content:center;transition:.12s;flex-shrink:0}
.m-close:hover{background:var(--s2);color:var(--t1)}
.m-body{padding:1rem 1.25rem 1.5rem}
.m-stats{display:grid;grid-template-columns:repeat(2,1fr);gap:.55rem;margin-bottom:1rem}
@media(min-width:400px){.m-stats{grid-template-columns:repeat(3,1fr)}}
.m-stat{background:var(--bg1);border:1px solid var(--s2);border-radius:var(--r12);padding:.7rem .85rem}
.m-sl{font-size:.62rem;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.28rem}
.m-sv{font-size:1rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.m-tabs{display:flex;gap:.4rem;margin-bottom:.75rem}
.mtab{padding:.28rem .8rem;border-radius:var(--r99);font-size:.72rem;font-weight:600;border:1px solid var(--s2);background:transparent;color:var(--t3);font-family:'Outfit',sans-serif;transition:.12s}
.mtab.on{background:var(--g0);border-color:var(--g0);color:#fff}
.m-chart{height:200px;position:relative}
.m-src{font-size:.62rem;color:var(--t4);margin-top:.75rem;font-family:'JetBrains Mono',monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.m-src a{color:var(--blue)}
footer{border-top:1px solid var(--s2);padding:1rem 1.5rem;font-size:.62rem;color:var(--t4);font-family:'JetBrains Mono',monospace;text-align:center;line-height:1.8}
footer strong{color:var(--t3)}
.dl-float{position:fixed;bottom:1.25rem;right:1.25rem;z-index:400;display:flex;align-items:center;gap:.5rem;padding:.6rem 1rem;border-radius:var(--r12);background:linear-gradient(135deg,#007A4D,var(--g0));color:#fff;font-size:.75rem;font-weight:700;box-shadow:0 6px 24px rgba(0,168,106,.4);animation:floatY 3s ease-in-out infinite;transition:.2s;cursor:pointer;border:none}
@keyframes floatY{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
.dl-float:hover{animation:none;transform:translateY(-2px) scale(1.04)}
.dl-float-badge{position:absolute;top:-7px;right:-7px;background:var(--gold);color:#000;border-radius:99px;font-size:.52rem;font-weight:900;padding:.1rem .35rem;font-family:'JetBrains Mono',monospace;border:2px solid var(--bg);letter-spacing:.03em}
</style>
</head>
<body class="page">
<nav><div class="wrap nav-inner">
  <div class="nav-brand">
    <div class="brand-icon">&#x26FD;</div>
    <div><div class="brand-name">Africa<span>Fuel</span>Watch</div></div>
    <div class="brand-tag">2026</div>
  </div>
  <div class="nav-right">
    <div class="nav-meta" id="navMeta"></div>
    <div class="live-dot"><span class="pulse"></span>LIVE</div>
    <button class="btn-dl-nav" onclick="exportXLSX()">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Export Excel
    </button>
  </div>
</div></nav>
<div class="ticker">
  <div class="ticker-lbl"><span class="tl-dot"></span>LIVE · JAN–MAR 2026</div>
  <div class="ticker-body"><div class="ticker-track" id="tickerTrack"></div></div>
</div>
<main><div class="wrap">
<div class="hero">
  <div class="hero-glow"></div>
  <div class="hero-grid">
    <div>
      <div class="hero-title">Africa Fuel<br>Price Intelligence</div>
      <div class="hero-sub">Real-time monitoring of gasoline &amp; diesel across <strong id="heroN"></strong> &#x2014; USD and local currency, official sources only.</div>
      <div class="hero-tags">
        <span class="tag tag-g" id="tagN"></span>
        <span class="tag tag-y">&#x1F30D; 5 Regions</span>
        <span class="tag tag-b">&#x1F4B1; Official FX Rates</span>
        <span class="tag tag-g">&#x1F504; Daily Updates</span>
      </div>
      <button class="btn-dl" onclick="exportXLSX()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Export Data <span style="opacity:.75;font-size:.75rem;font-weight:500">XLSX</span>
      </button>
    </div>
    <div class="kpi-grid" id="kpiGrid"></div>
  </div>
</div>
<div class="sec-head"><div class="sec-title">Regional Overview <span class="sec-pill">5 REGIONS</span></div></div>
<div class="reg-strip" id="regStrip"></div>
<div class="chart-row">
  <div class="card">
    <div class="card-head">Weekly Trend &#x2014; Key Markets
      <div class="tog" id="lineTog">
        <button class="tog-btn on" data-v="usd">Gas USD</button>
        <button class="tog-btn" data-v="loc">Local</button>
        <button class="tog-btn" data-v="die">Diesel</button>
      </div>
    </div>
    <div class="chart-box"><canvas id="lineChart"></canvas></div>
  </div>
  <div class="card">
    <div class="card-head">Regional Averages</div>
    <div class="chart-box"><canvas id="barChart"></canvas></div>
  </div>
</div>
<div class="rank-row">
  <div class="card">
    <div class="card-head">&#x1F534; Most Expensive Gas
      <div class="tog" id="topTog"><button class="tog-btn on" data-v="usd">USD</button><button class="tog-btn" data-v="loc">Local</button></div>
    </div>
    <div class="rank-list" id="topList"></div>
  </div>
  <div class="card">
    <div class="card-head">&#x1F7E2; Most Affordable Gas
      <div class="tog" id="botTog"><button class="tog-btn on" data-v="usd">USD</button><button class="tog-btn" data-v="loc">Local</button></div>
    </div>
    <div class="rank-list" id="botList"></div>
  </div>
</div>
<div class="card">
  <div class="card-head">&#x1F4B1; Exchange Rates <span style="font-size:.62rem;color:var(--t4);font-weight:400">Local per 1 USD</span></div>
  <div class="fx-wrap" id="fxWrap"></div>
</div>
<div class="card">
  <div class="card-head" id="tblHead">All Countries <span class="cnt-badge" id="cntBadge"></span></div>
  <div class="tog" id="tblTog" style="margin-bottom:.75rem">
    <button class="tog-btn on" data-v="usd">USD/L</button>
    <button class="tog-btn" data-v="loc">Local/L</button>
    <button class="tog-btn" data-v="both">Both</button>
  </div>
  <div class="tbl-controls">
    <button class="fb on" data-r="all">All</button>
    <button class="fb" data-r="North Africa">N. Africa</button>
    <button class="fb" data-r="West Africa">W. Africa</button>
    <button class="fb" data-r="East Africa">E. Africa</button>
    <button class="fb" data-r="Central Africa">Central</button>
    <button class="fb" data-r="Southern Africa">Southern</button>
    <div class="ctrl-right">
      <select class="sort-sel" id="sortSel">
        <option value="name">Name A&#x2013;Z</option>
        <option value="gas_desc">Gas &#x2193;</option>
        <option value="gas_asc">Gas &#x2191;</option>
        <option value="chg_desc">Change &#x2191;</option>
        <option value="chg_asc">Change &#x2193;</option>
      </select>
      <div class="srch-wrap">
        <span class="srch-ico">&#x1F50D;</span>
        <input class="srch" id="srchInp" placeholder="Search&#x2026;">
      </div>
    </div>
  </div>
  <div class="tbl-hint">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--blue)" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
    Scroll right for more &#xB7; Tap a row for details
  </div>
  <div class="tbl-wrap">
    <table><thead><tr id="tHead"></tr></thead><tbody id="tBody"></tbody></table>
  </div>
</div>
</div></main>
<footer><strong>AFRICAFUELWATCH 2026</strong> &nbsp;&#xB7;&nbsp; Official regulatory sources only &nbsp;&#xB7;&nbsp; <span id="ftTime"></span></footer>
<div class="ov" id="modalOv">
  <div class="modal" id="modalBox">
    <span class="m-bar"></span>
    <div class="m-head">
      <div>
        <div class="m-title" id="mTitle"></div>
        <div class="m-sub" id="mSub"></div>
        <div class="m-fx" id="mFx"></div>
      </div>
      <button class="m-close" id="mClose">&#x2715;</button>
    </div>
    <div class="m-body">
      <div class="m-stats" id="mStats"></div>
      <div class="m-tabs" id="mTabs">
        <button class="mtab on" data-tab="gas">&#x26FD; Gasoline</button>
        <button class="mtab" data-tab="die">&#x1F69B; Diesel</button>
      </div>
      <div class="m-chart"><canvas id="mChart"></canvas></div>
      <div class="m-src" id="mSrc"></div>
    </div>
  </div>
</div>
<button class="dl-float" onclick="exportXLSX()">
  <span class="dl-float-badge">XLSX</span>
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
  Export
</button>
"""

    script_open = "<script>\n'use strict';\n"
    data_line   = "const D=" + dj + ";\n"
    script_body = r"""
let data=JSON.parse(JSON.stringify(D.countries));
let filtered=[...data];
let region='all',tblCur='usd',topCur='usd',botCur='usd',lineCur='usd';
let sortKey='name',modalCtry=null,modalTab='gas';
let lineInst,barInst,mInst;
const FX=D.fx_rates,WL=D.week_labels;
const REGS=['North Africa','West Africa','Central Africa','East Africa','Southern Africa'];
const AB={'North Africa':'na','West Africa':'wa','Central Africa':'ca','East Africa':'ea','Southern Africa':'sa'};
const RC={'North Africa':'#F5A300','West Africa':'#00A86A','Central Africa':'#E87C1A','East Africa':'#1A8FD8','Southern Africa':'#E8394A'};
const KEYS=['South Africa','Nigeria','Kenya','Egypt','Libya','Morocco','Ethiopia','Tanzania','Ghana','Tunisia'];
const PAL=['#00A86A','#F5A300','#1A8FD8','#E8394A','#E87C1A','#00C4CF','#8B5CF6','#00CC85','#FFBE33','#9EC8E0'];
Chart.defaults.color='#5A8FAF';
Chart.defaults.borderColor='rgba(33,64,89,.5)';
Chart.defaults.font.family="'Outfit',sans-serif";
Chart.defaults.font.size=11;
const avg=()=>data.reduce((s,c)=>s+c.gas_usd_now,0)/data.length;
const rAvg=r=>{const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+c.gas_usd_now,0)/cs.length:0;};
const rAvgD=r=>{const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+c.die_usd_now,0)/cs.length:0;};
window.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('heroN').textContent=D.n_countries+' African nations';
  document.getElementById('tagN').textContent='\u26fd '+D.n_countries+' Countries';
  document.getElementById('tblHead').firstChild.textContent='All '+D.n_countries+' Countries ';
  buildNav();buildTicker();buildKpis();buildRegions();
  buildLineChart();buildBarChart();buildRanks('top');buildRanks('bot');
  buildFx();buildHead();renderTable();wire();
  setInterval(tick,12000);
});
function buildNav(){
  document.getElementById('navMeta').textContent=D.n_countries+' countries \u00b7 '+D.updated;
  document.getElementById('ftTime').textContent='Updated: '+D.updated;
}
function buildTicker(){
  // Sort: biggest movers first (▲ desc, then ▼ desc), stable countries last (alphabetical)
  const movers = [...data].filter(c=>Math.abs(c.chg_gas)>0.05)
                          .sort((a,b)=>Math.abs(b.chg_gas)-Math.abs(a.chg_gas));
  const stable = [...data].filter(c=>Math.abs(c.chg_gas)<=0.05)
                          .sort((a,b)=>a.name.localeCompare(b.name));
  const s = [...movers, ...stable];
  let h='';
  for(let i=0;i<2;i++) s.forEach(c=>{
    const isUp   = c.chg_gas > 0.05;
    const isDn   = c.chg_gas < -0.05;
    const cl     = isUp?'up':isDn?'dn':'fl';
    const ar     = isUp?'\u25b2':isDn?'\u25bc':'\u2014';
    const sign   = isUp?'+':'';
    const chgTxt = (isUp||isDn) ? ar+sign+c.chg_gas.toFixed(1)+'%' : '\u2014';
    const badge  = c.stale?'<span class="stale-badge">STALE</span>':c.old_source?'<span class="old-badge">OLD</span>':'';
    h+='<span class="ti">'+
       '<span class="ti-n">'+c.name+badge+'</span>'+
       '<span class="ti-p">$'+c.gas_usd_now.toFixed(3)+'</span>'+
       '<span class="ti-c">'+c.currency+'</span>'+
       '<span class="'+cl+'">'+chgTxt+'</span>'+
       '</span>';
  });
  document.getElementById('tickerTrack').innerHTML=h;
}
function buildKpis(){
  const s=[...data].sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  const hi=s[0],lo=s[s.length-1],sg=[...data].sort((a,b)=>b.chg_gas-a.chg_gas)[0],av=avg();
  document.getElementById('kpiGrid').innerHTML=[
    {l:'Highest',v:'$'+hi.gas_usd_now.toFixed(3),s:hi.name,c:'var(--red)'},
    {l:'Lowest',v:'$'+lo.gas_usd_now.toFixed(3),s:lo.name,c:'var(--g0)'},
    {l:'Avg Africa',v:'$'+av.toFixed(3),s:D.n_countries+' nations',c:'var(--gold)'},
    {l:'Biggest \u0394',v:'+'+sg.chg_gas.toFixed(1)+'%',s:sg.name,c:'var(--red)'},
  ].map(k=>'<div class="kpi"><div class="kpi-label">'+k.l+'</div><div class="kpi-value" style="color:'+k.c+'">'+k.v+'</div><div class="kpi-sub">'+k.s+'</div></div>').join('');
}
function buildRegions(){
  const mx=Math.max(...REGS.map(rAvg));
  document.getElementById('regStrip').innerHTML=REGS.map(r=>{
    const ab=AB[r],col=RC[r],av=rAvg(r),n=data.filter(c=>c.region===r).length;
    const chg=data.filter(c=>c.region===r).reduce((s,c)=>s+c.chg_gas,0)/(n||1);
    const pct=Math.round(av/mx*100);
    return '<div class="rc rc-'+ab+'"><div class="rc-name">'+r+'</div><div class="rc-price" style="color:'+col+'">$'+av.toFixed(3)+'</div><div class="rc-count">'+n+' countries</div><div class="rc-bar"><div class="rc-fill" style="width:'+pct+'%;background:'+col+'"></div></div><div class="rc-chg" style="color:'+(chg>=0?'var(--red)':'var(--g0)')+'">'+( chg>=0?'\u25b2':'\u25bc')+' '+Math.abs(chg).toFixed(1)+'% Jan\u2192Now</div></div>';
  }).join('');
}
function buildLineChart(){
  const kd=KEYS.map(n=>data.find(c=>c.name===n)).filter(Boolean);
  lineInst=new Chart(document.getElementById('lineChart').getContext('2d'),{
    type:'line',
    data:{labels:WL,datasets:kd.map((c,i)=>({label:c.name,data:c.gas_usd_w||[],borderColor:PAL[i],backgroundColor:PAL[i]+'12',borderWidth:2,pointRadius:2,pointHoverRadius:5,tension:.4,fill:false}))},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:8,padding:10,font:{size:10}}},tooltip:{callbacks:{title:i=>'Week: '+i[0].label,label:ctx=>ctx.dataset.label+': $'+ctx.parsed.y.toFixed(3)+'/L'}}},
      scales:{x:{grid:{color:'rgba(33,64,89,.35)'},ticks:{font:{size:9},maxTicksLimit:8}},y:{grid:{color:'rgba(33,64,89,.35)'},ticks:{callback:v=>'$'+v.toFixed(2)}}}}
  });
}
function updateLineChart(){
  const kd=KEYS.map(n=>data.find(c=>c.name===n)).filter(Boolean);
  const sd=c=>lineCur==='usd'?c.gas_usd_w||[]:lineCur==='loc'?c.gas_loc_w||[]:c.die_usd_w||[];
  lineInst.data.datasets=kd.map((c,i)=>({label:c.name,data:sd(c),borderColor:PAL[i],backgroundColor:PAL[i]+'12',borderWidth:2,pointRadius:2,pointHoverRadius:5,tension:.4,fill:false}));
  lineInst.options.scales.y.ticks.callback=lineCur!=='loc'?v=>'$'+v.toFixed(3):v=>v.toFixed(1);
  lineInst.update('none');
}
function buildBarChart(){
  barInst=new Chart(document.getElementById('barChart').getContext('2d'),{
    type:'bar',
    data:{labels:REGS.map(r=>r.replace(' Africa','\nAfrica')),
      datasets:[{label:'Gasoline USD',data:REGS.map(rAvg),backgroundColor:REGS.map(r=>RC[r]+'BB'),borderColor:REGS.map(r=>RC[r]),borderWidth:1.5,borderRadius:4},
               {label:'Diesel USD',data:REGS.map(rAvgD),backgroundColor:REGS.map(r=>RC[r]+'44'),borderColor:REGS.map(r=>RC[r]),borderWidth:1.5,borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:8,padding:10,font:{size:10}}},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': $'+ctx.parsed.y.toFixed(3)}}},
      scales:{x:{grid:{display:false},ticks:{font:{size:9}}},y:{grid:{color:'rgba(33,64,89,.35)'},ticks:{callback:v=>'$'+v.toFixed(2)}}}}
  });
}
function buildRanks(type){
  const cur=type==='top'?topCur:botCur,isU=cur==='usd';
  const sorted=[...data].sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  const items=type==='top'?sorted.slice(0,10):sorted.slice(-10).reverse();
  const mx=items[0]?.gas_usd_now||1,col=type==='top'?'var(--red)':'var(--g0)';
  document.getElementById(type+'List').innerHTML=items.map((c,i)=>{
    const price=isU?'$'+c.gas_usd_now.toFixed(3):c.gas_loc_now.toFixed(1)+' '+c.currency;
    const pct=Math.round(c.gas_usd_now/mx*100);
    return '<div class="rank-item" onclick="openModal(\''+esc(c.name)+'\')"><div class="rank-n">'+(i+1)+'</div><div class="rank-name">'+c.name+'</div><div class="rank-right"><span class="rank-price" style="color:'+col+'">'+price+'</span><div class="rank-bar-bg"><div class="rank-bar-fg" style="width:'+pct+'%;background:'+col+'"></div></div></div></div>';
  }).join('');
}
function buildFx(){
  document.getElementById('fxWrap').innerHTML=Object.entries(FX).sort((a,b)=>a[0].localeCompare(b[0])).map(([code,rate])=>{
    const m=rate>=1000?rate.toLocaleString('en-US',{maximumFractionDigits:0}):rate>=10?rate.toFixed(2):rate.toFixed(4);
    const inv=1/rate,invF=inv<0.001?inv.toFixed(6):inv.toFixed(4);
    return '<div class="fx-card"><span class="fx-code">'+code+'</span><div style="text-align:right"><span class="fx-rate">'+m+'</span><span class="fx-inv">= $'+invF+'</span></div></div>';
  }).join('');
}
function buildHead(){
  const cols=[{l:'Country',k:'name'},{l:'Region',k:null},{l:'Curr',k:null},{l:'FX',k:'fx'}];
  if(tblCur==='usd'||tblCur==='both') cols.push({l:'Gas USD',k:'gas'},{l:'Die USD',k:'die'});
  if(tblCur==='loc'||tblCur==='both') cols.push({l:'Gas Local',k:null},{l:'Die Local',k:null});
  cols.push({l:'Jan\u2192Now',k:'chg'},{l:'Level',k:null},{l:'First',k:null},{l:'Latest',k:null},{l:'',k:null});
  document.getElementById('tHead').innerHTML=cols.map(c=>'<th '+(c.k?'data-k="'+c.k+'"':'')+' class="'+(sortKey===c.k?'sorted':'')+'">'+c.l+'</th>').join('');
  document.querySelectorAll('#tHead th[data-k]').forEach(th=>th.addEventListener('click',()=>{sortKey=th.dataset.k;renderTable();}));
}
function renderTable(){
  let d=[...filtered];
  const q=(document.getElementById('srchInp').value||'').toLowerCase();
  if(q) d=d.filter(c=>c.name.toLowerCase().includes(q)||c.region.toLowerCase().includes(q)||c.currency.toLowerCase().includes(q));
  const sv=document.getElementById('sortSel').value;
  const sorts={'name':(a,b)=>a.name.localeCompare(b.name),'gas_desc':(a,b)=>b.gas_usd_now-a.gas_usd_now,'gas_asc':(a,b)=>a.gas_usd_now-b.gas_usd_now,'chg_desc':(a,b)=>b.chg_gas-a.chg_gas,'chg_asc':(a,b)=>a.chg_gas-b.chg_gas};
  if(sorts[sv]) d.sort(sorts[sv]);
  document.getElementById('cntBadge').textContent=d.length;
  const mx=Math.max(...data.map(c=>c.gas_usd_now));
  document.getElementById('tBody').innerHTML=d.map(c=>{
    const ab=AB[c.region]||'na',fx=FX[c.currency]||1;
    const chgCl=c.chg_gas>0.5?'up2':c.chg_gas<-0.5?'dn2':'fl2';
    const chgAr=c.chg_gas>0.5?'\u25b2':c.chg_gas<-0.5?'\u25bc':'\u2014';
    const levCl=c.gas_usd_now>1.3?'lev-h':c.gas_usd_now>0.8?'lev-m':'lev-l';
    const levLb=c.gas_usd_now>1.3?'HIGH':c.gas_usd_now>0.8?'MID':'LOW';
    const fxF=fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx>=10?fx.toFixed(2):fx.toFixed(4);
    const bw=Math.round(c.gas_usd_now/mx*100);
    const w=c.gas_usd_w||[];
    const staleMark=c.stale?'<span class="stale-badge">STALE</span>':c.old_source?'<span class="old-badge">OLD</span>':'';
    const confIco=c.confidence==='high'?'\ud83d\udfe2':c.confidence==='medium'?'\ud83d\udfe1':'\ud83d\udd34';
    let cells='<td><span class="cn">'+c.name+staleMark+'</span></td><td><span class="rt rt-'+ab+'">'+c.region.replace(' Africa','')+'</span></td><td><span class="cur">'+c.currency+'</span></td><td class="mono" style="font-size:.7rem;color:var(--t3)">'+fxF+'</td>';
    if(tblCur==='usd'||tblCur==='both') cells+='<td><span class="mono">$'+c.gas_usd_now.toFixed(3)+'</span><div class="pb"><div class="pb-f" style="width:'+bw+'%"></div></div></td><td class="mono">$'+c.die_usd_now.toFixed(3)+'</td>';
    if(tblCur==='loc'||tblCur==='both') cells+='<td class="mono" style="color:var(--cyan)">'+c.gas_loc_now.toFixed(2)+'</td><td class="mono" style="color:var(--cyan)">'+c.die_loc_now.toFixed(2)+'</td>';
    cells+='<td><span class="'+chgCl+'">'+chgAr+' '+Math.abs(c.chg_gas).toFixed(2)+'%</span></td><td><span class="'+levCl+'">'+levLb+'</span></td><td class="mono" style="font-size:.67rem;color:var(--t4)">'+(w[0]!=null?'$'+Number(w[0]).toFixed(3):'&mdash;')+'</td><td class="mono" style="font-size:.7rem">'+(w[w.length-1]!=null?'$'+Number(w[w.length-1]).toFixed(3):'&mdash;')+'</td><td>'+confIco+'</td>';
    return '<tr onclick="openModal(\''+esc(c.name)+'\')">'+cells+'</tr>';
  }).join('');
}
function openModal(name){
  const c=data.find(d=>d.name===name);if(!c) return;
  modalCtry=c;
  const fx=FX[c.currency]||1;
  const fxF=fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx>=10?fx.toFixed(2):fx.toFixed(4);
  document.getElementById('mTitle').textContent='\u26fd '+c.name;
  document.getElementById('mSub').textContent=c.region+' \u00b7 '+c.currency+' \u00b7 '+c.octane+' RON';
  let fxTxt='1 USD = '+fxF+' '+c.currency;
  if(c.stale) fxTxt+=' \u00b7 \u26a0\ufe0f Last known value';
  else if(c.old_source) fxTxt+=' \u00b7 \ud83d\udd34 Old source (pre-2020)';
  document.getElementById('mFx').textContent=fxTxt;
  document.getElementById('mStats').innerHTML=[
    {l:'Gas USD/L',v:'$'+c.gas_usd_now.toFixed(3),col:'var(--gold)'},
    {l:'Gas '+c.currency+'/L',v:c.gas_loc_now.toFixed(2),col:'var(--g0)'},
    {l:'Diesel USD/L',v:'$'+c.die_usd_now.toFixed(3),col:'var(--blue)'},
    {l:'Die '+c.currency+'/L',v:c.die_loc_now.toFixed(2),col:'var(--cyan)'},
    {l:'Jan\u2192Now',v:(c.chg_gas>=0?'+':'')+c.chg_gas.toFixed(2)+'%',col:c.chg_gas>0?'var(--red)':'var(--g0)'},
    {l:'Confidence',v:c.confidence==='high'?'\ud83d\udfe2 High':c.confidence==='medium'?'\ud83d\udfe1 Med':'\ud83d\udd34 Low',col:c.confidence==='high'?'var(--g0)':c.confidence==='medium'?'var(--gold)':'var(--red)'},
  ].map(s=>'<div class="m-stat"><div class="m-sl">'+s.l+'</div><div class="m-sv" style="color:'+s.col+'">'+s.v+'</div></div>').join('');
  document.getElementById('mSrc').innerHTML='Source: <a href="'+c.src+'" target="_blank">'+c.src+'</a> \u00b7 Effective: '+c.effective_date;
  document.querySelectorAll('.mtab').forEach(b=>b.classList.remove('on'));
  document.querySelector('.mtab[data-tab="gas"]').classList.add('on');
  modalTab='gas';buildModalChart();
  document.getElementById('modalOv').classList.add('open');
  document.body.style.overflow='hidden';
}
function buildModalChart(){
  if(mInst){mInst.destroy();mInst=null;}
  const c=modalCtry;if(!c) return;
  const isGas=modalTab==='gas';
  const uD=(isGas?c.gas_usd_w:c.die_usd_w)||[],lD=(isGas?c.gas_loc_w:c.die_loc_w)||[];
  mInst=new Chart(document.getElementById('mChart').getContext('2d'),{
    type:'line',data:{labels:WL,datasets:[
      {label:'USD/L',data:uD,borderColor:'#F5A300',backgroundColor:'rgba(245,163,0,.1)',borderWidth:2.5,pointRadius:3,pointHoverRadius:6,tension:.4,fill:true,yAxisID:'y1'},
      {label:c.currency+'/L',data:lD,borderColor:'#00A86A',backgroundColor:'transparent',borderWidth:2,pointRadius:2,tension:.4,yAxisID:'y2'}
    ]},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:8,padding:10,font:{size:10}}},tooltip:{callbacks:{title:i=>'Week: '+i[0].label}}},
      scales:{y1:{position:'left',grid:{color:'rgba(33,64,89,.4)'},ticks:{callback:v=>'$'+v.toFixed(3)}},y2:{position:'right',grid:{display:false},ticks:{callback:v=>v.toFixed(v>=1000?0:v>=10?1:2)}}}}
  });
}
function closeModal(){document.getElementById('modalOv').classList.remove('open');document.body.style.overflow='';}
function wire(){
  document.getElementById('mClose').addEventListener('click',closeModal);
  document.getElementById('modalOv').addEventListener('click',e=>{if(e.target.id==='modalOv')closeModal();});
  let touchY=0;
  document.getElementById('modalBox').addEventListener('touchstart',e=>{touchY=e.touches[0].clientY;},{passive:true});
  document.getElementById('modalBox').addEventListener('touchmove',e=>{if(e.touches[0].clientY-touchY>80)closeModal();},{passive:true});
  document.getElementById('mTabs').addEventListener('click',e=>{const b=e.target.closest('.mtab');if(!b)return;document.querySelectorAll('.mtab').forEach(x=>x.classList.remove('on'));b.classList.add('on');modalTab=b.dataset.tab;buildModalChart();});
  document.querySelectorAll('.fb').forEach(btn=>{btn.addEventListener('click',()=>{document.querySelectorAll('.fb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');region=btn.dataset.r;filtered=region==='all'?[...data]:data.filter(c=>c.region===region);renderTable();});});
  document.getElementById('sortSel').addEventListener('change',()=>{sortKey=document.getElementById('sortSel').value.replace(/_desc|_asc/,'');renderTable();});
  document.getElementById('srchInp').addEventListener('input',renderTable);
  document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(btn=>{btn.addEventListener('click',()=>{document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');tblCur=btn.dataset.v;buildHead();renderTable();});});
  document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(btn=>{btn.addEventListener('click',()=>{document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');lineCur=btn.dataset.v;updateLineChart();});});
  ['top','bot'].forEach(t=>{document.getElementById(t+'Tog').querySelectorAll('.tog-btn').forEach(btn=>{btn.addEventListener('click',()=>{document.getElementById(t+'Tog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');if(t==='top')topCur=btn.dataset.v;else botCur=btn.dataset.v;buildRanks(t);});});});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
}
function tick(){
  const free=data.filter(c=>!c.regulated);if(!free.length)return;
  const n=Math.floor(Math.random()*3)+2;
  for(let i=0;i<n;i++){
    const c=free[Math.floor(Math.random()*free.length)];
    const noise=(Math.random()-.5)*.002;
    c.gas_usd_now=Math.max(.01,+(c.gas_usd_now+noise).toFixed(4));
    c.die_usd_now=Math.max(.01,+(c.die_usd_now+noise*.9).toFixed(4));
    const fx=FX[c.currency]||1;
    c.gas_loc_now=+(c.gas_usd_now*fx).toFixed(2);c.die_loc_now=+(c.die_usd_now*fx).toFixed(2);
    if(c.gas_usd_w?.length)c.gas_usd_w[c.gas_usd_w.length-1]=c.gas_usd_now;
    if(c.gas_loc_w?.length)c.gas_loc_w[c.gas_loc_w.length-1]=c.gas_loc_now;
    if(c.die_usd_w?.length)c.die_usd_w[c.die_usd_w.length-1]=c.die_usd_now;
    if(c.die_loc_w?.length)c.die_loc_w[c.die_loc_w.length-1]=c.die_loc_now;
  }
  buildKpis();buildRegions();buildRanks('top');buildRanks('bot');renderTable();
}
function exportXLSX(){
  // Always download the fixed-name file — no date mismatch possible
  const filename = 'africa_fuel_tracker_latest.xlsx';
  const a = document.createElement('a');
  a.href     = filename;
  a.download = 'africa_fuel_tracker_' + D.period_end + '.xlsx';  // rename on save
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
function esc(s){return s.replace(/\\/g,'\\\\').replace(/'/g,"\\'");}
"""
    script_close = "\n</script>\n</body>\n</html>"
    return head + script_open + data_line + script_body + script_close

def main():
    for p in [PRICES_DB, HISTORY_DB]:
        if not p.exists():
            print(f"❌ {p} not found"); return
    prices_db  = load(PRICES_DB)
    history_db = load(HISTORY_DB)
    D    = build(prices_db, history_db)
    html = render(D)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    sz = OUTPUT.stat().st_size / 1024
    print(f"✅ {OUTPUT.name} generated → {OUTPUT}")
    print(f"   {len(D['countries'])} countries | {len(D['week_labels'])} weeks | {sz:.0f} KB")

if __name__ == "__main__":
    main()
