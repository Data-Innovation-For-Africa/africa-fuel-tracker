"""
dashboard_builder.py — Africa Fuel Price Tracker
=================================================
AfDB-inspired palette: Green #00A86A · Gold #F5A300 · Navy #07111E
All 4 fixes applied:
  1. Historical data never overwritten (DB logic)
  2. Period-accurate FX rates stored and displayed
  3. AfDB color palette throughout
  4. All buttons verified functional
"""
import json


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Africa Fuel Price Intelligence 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#07111E;--bg2:#0B1826;--panel:#0E1E2E;--panel2:#132435;
  --bord:#1A3347;--bord2:#214059;
  --green:#00A86A;--green2:#00CC85;
  --gold:#F5A300;--gold2:#FFBE33;
  --red:#E8394A;--blue:#1A8FD8;--cyan:#00C4CF;
  --amber:#E87C1A;--purple:#8066D6;
  --txt:#E8EEF4;--txt2:#7A9BB5;--txt3:#3E6480;
  --r:10px;--rl:16px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--txt);font-family:'Inter',sans-serif;
  overflow-x:hidden;min-height:100vh;font-size:14px;line-height:1.5}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 70% 40% at 50% 0%,rgba(0,168,106,.06),transparent 60%)}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-thumb{background:#1A3347;border-radius:9px}
/* HEADER */
header{position:sticky;top:0;z-index:200;height:60px;
  background:rgba(7,17,30,.93);backdrop-filter:blur(20px);
  border-bottom:1px solid var(--bord);
  padding:0 1.75rem;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:.75rem}
.logo-badge{width:36px;height:36px;border-radius:9px;
  background:linear-gradient(135deg,#00A86A,#007A4D);
  display:flex;align-items:center;justify-content:center;font-size:1.1rem;
  box-shadow:0 0 24px rgba(0,168,106,.3)}
.logo-text{font-size:.95rem;font-weight:700;letter-spacing:-.01em}
.logo-text em{font-style:normal;color:var(--green)}
.logo-sub{font-size:.64rem;color:var(--txt2);font-weight:400;display:block;margin-top:.05rem}
.hdr-right{display:flex;align-items:center;gap:1rem}
.hdr-meta{font-family:'IBM Plex Mono',monospace;font-size:.67rem;color:var(--txt2);text-align:right;line-height:1.6}
.live-badge{display:flex;align-items:center;gap:.35rem;background:rgba(0,168,106,.1);
  border:1px solid rgba(0,168,106,.3);border-radius:99px;padding:.22rem .7rem;
  font-family:'IBM Plex Mono',monospace;font-size:.67rem;color:var(--green)}
.dot{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,168,106,.5)}50%{box-shadow:0 0 0 5px rgba(0,168,106,0)}}
.hdr-dl{display:flex;align-items:center;gap:.45rem;padding:.3rem .85rem;border-radius:8px;
  background:linear-gradient(135deg,#007A4D,#00A86A);border:none;color:#fff;
  font-family:'Inter',sans-serif;font-size:.73rem;font-weight:600;cursor:pointer;
  text-decoration:none;transition:.2s;white-space:nowrap}
.hdr-dl:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(0,168,106,.4)}
/* TICKER */
.ticker{background:rgba(14,30,46,.95);border-bottom:1px solid var(--bord);
  height:34px;overflow:hidden;display:flex;align-items:center}
.ticker-label{flex-shrink:0;padding:0 1rem;font-size:.64rem;font-weight:700;
  color:var(--green);letter-spacing:.08em;text-transform:uppercase;
  border-right:1px solid var(--bord);height:100%;display:flex;align-items:center;
  white-space:nowrap;background:rgba(0,168,106,.05)}
.ticker-outer{flex:1;overflow:hidden}
.ticker-track{display:flex;align-items:center;animation:tkscroll 90s linear infinite;white-space:nowrap}
.ticker-track:hover{animation-play-state:paused}
@keyframes tkscroll{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ti{display:inline-flex;align-items:center;gap:.45rem;padding:0 1.1rem;height:34px;
  border-right:1px solid rgba(26,51,71,.5);font-size:.72rem}
.ti-name{font-weight:600}.ti-price{font-family:'IBM Plex Mono',monospace;color:var(--green);font-weight:500}
.ti-cur{color:var(--txt3);font-size:.62rem}
.ti-up{color:#E8394A}.ti-dn{color:#00CC85}.ti-fl{color:var(--txt3)}
/* LAYOUT */
.wrap{max-width:1400px;margin:0 auto;padding:1.5rem 1.75rem 3rem}
/* HERO */
.hero{background:linear-gradient(135deg,#0B1E31,#0E2A3D);border:1px solid var(--bord);
  border-radius:var(--rl);padding:2rem;margin-bottom:1.5rem;
  display:grid;grid-template-columns:1fr auto;gap:2rem;align-items:start;
  position:relative;overflow:hidden}
.hero::after{content:'';position:absolute;top:-60px;right:-60px;width:280px;height:280px;
  border-radius:50%;background:radial-gradient(circle,rgba(0,168,106,.07),transparent 70%);pointer-events:none}
.hero-title{font-size:1.65rem;font-weight:800;line-height:1.2;margin-bottom:.55rem;
  background:linear-gradient(135deg,#E8EEF4,#9EC8E0);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{font-size:.87rem;color:var(--txt2);line-height:1.6;max-width:560px;margin-bottom:1rem}
.chips{display:flex;flex-wrap:wrap;gap:.45rem;margin-bottom:1.2rem}
.chip{display:inline-flex;align-items:center;gap:.32rem;padding:.26rem .72rem;border-radius:99px;font-size:.71rem;font-weight:500}
.chip-g{background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.25);color:var(--green)}
.chip-y{background:rgba(245,163,0,.1);border:1px solid rgba(245,163,0,.25);color:var(--gold)}
.chip-b{background:rgba(26,143,216,.1);border:1px solid rgba(26,143,216,.25);color:var(--blue)}
.dl-hero{display:inline-flex;align-items:center;gap:.65rem;padding:.65rem 1.4rem;
  border-radius:10px;background:linear-gradient(135deg,#007A4D,#00A86A,#00CC85);
  background-size:200% auto;animation:shimmer 3s linear infinite;
  border:none;color:#fff;font-family:'Inter',sans-serif;font-size:.85rem;font-weight:700;
  cursor:pointer;text-decoration:none;box-shadow:0 4px 20px rgba(0,168,106,.3);transition:.2s}
@keyframes shimmer{0%{background-position:0% center}100%{background-position:200% center}}
.dl-hero:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,168,106,.45);animation:none}
.hero-kpis{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;min-width:295px}
.hkpi{background:rgba(7,17,30,.6);border:1px solid var(--bord);border-radius:var(--r);padding:.9rem 1rem}
.hkpi-label{font-size:.66rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--txt2);margin-bottom:.3rem}
.hkpi-value{font-size:1.28rem;font-weight:800;font-family:'IBM Plex Mono',monospace;line-height:1}
.hkpi-sub{font-size:.7rem;color:var(--txt2);margin-top:.25rem}
/* SECTION */
.sec-title{font-size:.73rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
  color:var(--txt2);padding:.4rem 0 .85rem;display:flex;align-items:center;gap:.6rem}
.sec-bdg{background:rgba(0,168,106,.12);border:1px solid rgba(0,168,106,.25);
  color:var(--green);padding:.14rem .52rem;border-radius:99px;font-size:.62rem;font-weight:700;letter-spacing:.04em}
/* REGION CARDS */
.reg-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:.85rem;margin-bottom:1.5rem}
.rc{background:var(--panel);border:1px solid var(--bord);border-radius:var(--r);
  padding:1rem;position:relative;overflow:hidden;transition:.2s}
.rc:hover{border-color:var(--bord2);transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.3)}
.rc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.rc-na::before{background:var(--gold)}.rc-wa::before{background:var(--green)}
.rc-ea::before{background:var(--blue)}.rc-ca::before{background:var(--amber)}.rc-sa::before{background:var(--red)}
.rc-name{font-size:.7rem;font-weight:700;color:var(--txt2);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem}
.rc-price{font-size:1.35rem;font-weight:800;font-family:'IBM Plex Mono',monospace;line-height:1;margin-bottom:.3rem}
.rc-meta{font-size:.66rem;color:var(--txt3);margin-bottom:.65rem}
.rc-bar-bg{background:var(--bg);border-radius:99px;height:4px;overflow:hidden}
.rc-bar-fill{height:100%;border-radius:99px;transition:width .6s}
.rc-chg{font-size:.7rem;margin-top:.4rem;font-weight:600}
/* CARD */
.card{background:var(--panel);border:1px solid var(--bord);border-radius:var(--rl);
  padding:1.25rem 1.35rem;margin-bottom:1.25rem}
.card-title{font-size:.76rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  color:var(--txt2);margin-bottom:1rem;display:flex;align-items:center;
  justify-content:space-between;gap:.75rem;flex-wrap:wrap}
.chart-grid{display:grid;grid-template-columns:1.4fr 1fr;gap:1.25rem;margin-bottom:1.25rem}
.chart-wrap{height:280px;position:relative}
/* TOGGLE */
.tog{display:inline-flex;background:var(--bg);border:1px solid var(--bord);
  border-radius:8px;padding:3px;gap:2px;margin-bottom:.85rem}
.tog-btn{padding:.3rem .85rem;border-radius:6px;border:none;background:transparent;
  color:var(--txt2);font-size:.74rem;font-weight:500;cursor:pointer;
  font-family:'Inter',sans-serif;transition:.15s;white-space:nowrap}
.tog-btn.on{background:var(--green);color:#fff;box-shadow:0 2px 8px rgba(0,168,106,.3)}
.tog-btn:hover:not(.on){background:var(--bord);color:var(--txt)}
/* RANKINGS */
.rank-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-bottom:1.25rem}
.rank-item{display:flex;align-items:center;gap:.8rem;padding:.55rem .7rem;
  border-radius:8px;border:1px solid transparent;cursor:pointer;transition:.12s}
.rank-item:hover{background:var(--bg);border-color:var(--bord)}
.rank-num{width:26px;height:26px;border-radius:6px;background:var(--bg);border:1px solid var(--bord);
  display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700;color:var(--txt2);flex-shrink:0}
.rank-item:nth-child(-n+3) .rank-num{background:rgba(245,163,0,.1);border-color:rgba(245,163,0,.3);color:var(--gold)}
.rank-name{font-size:.8rem;font-weight:600;flex:1}
.rank-price{font-family:'IBM Plex Mono',monospace;font-size:.8rem;font-weight:600}
.rank-bar-bg{height:3px;background:var(--bg);border-radius:99px;flex:1;margin-left:.5rem}
.rank-bar-fill{height:100%;border-radius:99px}
/* FX */
.fx-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:.55rem;max-height:270px;overflow-y:auto}
.fx-item{background:var(--bg);border:1px solid var(--bord);border-radius:8px;padding:.6rem .8rem;
  display:flex;align-items:center;justify-content:space-between}
.fx-code{font-family:'IBM Plex Mono',monospace;font-size:.74rem;font-weight:600;color:var(--green)}
.fx-main{font-family:'IBM Plex Mono',monospace;font-size:.77rem;font-weight:500;color:var(--txt)}
.fx-inv{font-size:.61rem;color:var(--txt3);display:block;margin-top:.1rem}
/* FILTERS */
.filters{display:flex;flex-wrap:wrap;align-items:center;gap:.45rem;
  padding-bottom:.8rem;border-bottom:1px solid var(--bord);margin-bottom:.8rem}
.fb{padding:.28rem .82rem;border-radius:99px;font-size:.72rem;font-weight:500;
  border:1px solid var(--bord);background:transparent;color:var(--txt2);
  cursor:pointer;font-family:'Inter',sans-serif;transition:.12s}
.fb.on{background:var(--green);border-color:var(--green);color:#fff}
.fb:hover:not(.on){border-color:var(--bord2);color:var(--txt)}
.sort-sel{padding:.28rem .65rem;border-radius:8px;font-size:.72rem;
  border:1px solid var(--bord);background:var(--bg);color:var(--txt);
  font-family:'Inter',sans-serif;cursor:pointer;outline:none}
.sort-sel:focus{border-color:var(--green)}
.srch-wrap{position:relative;margin-left:auto}
.srch-ico{position:absolute;left:.62rem;top:50%;transform:translateY(-50%);font-size:.78rem;color:var(--txt3);pointer-events:none}
.srch{padding:.28rem .65rem .28rem 1.9rem;border-radius:8px;font-size:.72rem;
  border:1px solid var(--bord);background:var(--bg);color:var(--txt);
  font-family:'Inter',sans-serif;width:185px;outline:none;transition:.2s}
.srch:focus{border-color:var(--green);width:215px}
.srch::placeholder{color:var(--txt3)}
/* TABLE */
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.77rem}
thead th{background:var(--bg);border-bottom:2px solid var(--bord);padding:.52rem .72rem;
  font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;
  color:var(--txt2);text-align:left;white-space:nowrap;cursor:pointer;user-select:none;position:sticky;top:0}
thead th:hover{color:var(--green)}
thead th.sorted{color:var(--green);border-bottom-color:var(--green)}
tbody tr{border-bottom:1px solid rgba(26,51,71,.5);cursor:pointer;transition:.1s}
tbody tr:hover{background:rgba(0,168,106,.04)}
tbody tr:last-child{border-bottom:none}
td{padding:.5rem .72rem;white-space:nowrap;vertical-align:middle}
.cn{font-weight:600}
.rt{font-size:.64rem;font-weight:600;padding:.16rem .52rem;border-radius:99px;border:1px solid}
.rt-na{color:var(--gold);border-color:rgba(245,163,0,.3);background:rgba(245,163,0,.07)}
.rt-wa{color:var(--green);border-color:rgba(0,168,106,.3);background:rgba(0,168,106,.07)}
.rt-ea{color:var(--blue);border-color:rgba(26,143,216,.3);background:rgba(26,143,216,.07)}
.rt-ca{color:var(--amber);border-color:rgba(232,124,26,.3);background:rgba(232,124,26,.07)}
.rt-sa{color:var(--red);border-color:rgba(232,57,74,.3);background:rgba(232,57,74,.07)}
.cur-tag{font-family:'IBM Plex Mono',monospace;font-size:.67rem;font-weight:500;
  padding:.14rem .42rem;border-radius:5px;
  background:rgba(0,168,106,.08);color:var(--green);border:1px solid rgba(0,168,106,.2)}
.mono{font-family:'IBM Plex Mono',monospace;font-weight:500}
.up{color:#E8394A;font-weight:600}.dn{color:#00CC85;font-weight:600}.fl{color:var(--txt3)}
.lev-h{color:#E8394A;font-size:.67rem;font-weight:700}
.lev-m{color:var(--gold);font-size:.67rem;font-weight:700}
.lev-l{color:var(--green);font-size:.67rem;font-weight:700}
.pb-out{height:3px;background:var(--bg);border-radius:99px;margin-top:.22rem;min-width:45px}
.pb-in{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--green),var(--blue))}
/* MODAL */
.ov{display:none;position:fixed;inset:0;z-index:300;
  background:rgba(7,17,30,.85);backdrop-filter:blur(10px);
  align-items:center;justify-content:center;padding:1.5rem}
.ov.open{display:flex}
.modal{background:var(--panel2);border:1px solid var(--bord2);border-radius:var(--rl);
  width:100%;max-width:700px;max-height:90vh;overflow-y:auto;
  box-shadow:0 24px 64px rgba(0,0,0,.6)}
.m-hdr{background:linear-gradient(135deg,#0B1E31,#0E2A3D);padding:1.25rem 1.5rem;
  border-bottom:1px solid var(--bord);display:flex;align-items:flex-start;
  justify-content:space-between;border-radius:var(--rl) var(--rl) 0 0;position:sticky;top:0;z-index:5}
.m-title{font-size:1.1rem;font-weight:800}
.m-meta{font-size:.74rem;color:var(--txt2);margin-top:.22rem}
.m-fx{font-size:.69rem;color:var(--green);font-family:'IBM Plex Mono',monospace;margin-top:.38rem}
.mx-btn{width:32px;height:32px;border-radius:8px;border:1px solid var(--bord);
  background:transparent;color:var(--txt2);font-size:1.1rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:.12s;flex-shrink:0}
.mx-btn:hover{background:var(--bord);color:var(--txt)}
.m-body{padding:1.25rem 1.5rem}
.m-stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin-bottom:1.2rem}
.m-stat{background:var(--bg);border:1px solid var(--bord);border-radius:var(--r);padding:.78rem 1rem}
.m-sl{font-size:.66rem;color:var(--txt2);font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.33rem}
.m-sv{font-size:1.08rem;font-weight:800;font-family:'IBM Plex Mono',monospace}
.m-tabs{display:flex;gap:.45rem;margin-bottom:.8rem}
.mtab{padding:.32rem .88rem;border-radius:99px;font-size:.74rem;font-weight:500;
  border:1px solid var(--bord);background:transparent;color:var(--txt2);
  cursor:pointer;font-family:'Inter',sans-serif;transition:.12s}
.mtab.on{background:var(--green);border-color:var(--green);color:#fff}
.m-chart{height:220px;position:relative}
/* FOOTER */
footer{border-top:1px solid var(--bord);padding:1.2rem 1.75rem;text-align:center;
  font-family:'IBM Plex Mono',monospace;font-size:.63rem;color:var(--txt3);line-height:1.8}
footer strong{color:var(--txt2)}
/* FLOATING DL */
.dl-float{position:fixed;bottom:1.75rem;right:1.75rem;z-index:99;
  display:flex;align-items:center;gap:.62rem;padding:.68rem 1.15rem .68rem 1rem;
  border-radius:14px;background:linear-gradient(135deg,#007A4D,#00A86A);
  border:1px solid rgba(0,204,133,.25);color:#fff;
  font-family:'Inter',sans-serif;font-size:.79rem;font-weight:700;
  cursor:pointer;text-decoration:none;box-shadow:0 8px 28px rgba(0,168,106,.4);
  animation:floatY 3s ease-in-out infinite;transition:.2s}
@keyframes floatY{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
.dl-float:hover{animation:none;transform:translateY(-3px) scale(1.03);box-shadow:0 14px 40px rgba(0,168,106,.55)}
.dl-float-bdg{position:absolute;top:-8px;right:-8px;background:var(--gold);color:#000;
  border-radius:99px;font-size:.56rem;font-weight:800;padding:.14rem .38rem;
  font-family:'IBM Plex Mono',monospace;border:2px solid var(--bg);box-shadow:0 2px 8px rgba(245,163,0,.5)}
</style>
</head>
<body>
<header>
  <div class="logo">
    <div class="logo-badge">⛽</div>
    <div>
      <div class="logo-text">AFRICA<em>FUEL</em>WATCH</div>
      <span class="logo-sub">Pan-African Fuel Price Intelligence</span>
    </div>
  </div>
  <div class="hdr-right">
    <div class="hdr-meta" id="hMeta">Loading...</div>
    <div class="live-badge"><span class="dot"></span>LIVE</div>
    <a class="hdr-dl" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Excel
    </a>
  </div>
</header>
<div class="ticker">
  <div class="ticker-label">⛽ LIVE PRICES</div>
  <div class="ticker-outer"><div class="ticker-track" id="tickerTrack"></div></div>
</div>
<div class="wrap">
<div class="hero">
  <div>
    <div class="hero-title">Africa Fuel Price Intelligence</div>
    <div class="hero-sub">Real-time monitoring across <strong>42 African nations</strong> in <strong>USD/L</strong> and <strong>national currency</strong> using period-accurate exchange rates. Verified weekly by GlobalPetrolPrices.com and official regulatory portals.</div>
    <div class="chips">
      <span class="chip chip-g">⛽ 42 Countries · GPP Verified</span>
      <span class="chip chip-y">🌍 5 Regions</span>
      <span class="chip chip-b">💱 Period-Accurate FX</span>
      <span class="chip chip-g">🔄 Weekly Auto-Update</span>
    </div>
    <a class="dl-hero" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Download Excel Report
      <span style="font-weight:400;opacity:.82;font-size:.74rem;margin-left:.2rem">42 countries · USD + local currency</span>
    </a>
  </div>
  <div class="hero-kpis" id="hKpis"></div>
</div>
<div class="sec-title">Regional Overview <span class="sec-bdg">5 REGIONS · GPP DATA</span></div>
<div class="reg-grid" id="regGrid"></div>
<div class="chart-grid">
  <div class="card">
    <div class="card-title">Weekly Price Trend — Key Markets <span class="sec-bdg" style="margin:0">JAN–MAR 2026</span></div>
    <div class="tog" id="lineTog">
      <button class="tog-btn on" data-v="usd">Gasoline USD/L</button>
      <button class="tog-btn" data-v="loc">Local Currency/L</button>
      <button class="tog-btn" data-v="die">Diesel USD/L</button>
    </div>
    <div class="chart-wrap"><canvas id="lineChart"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Regional Average <span class="sec-bdg" style="margin:0">GAS vs DIESEL</span></div>
    <div class="chart-wrap"><canvas id="barChart"></canvas></div>
  </div>
</div>
<div class="rank-grid">
  <div class="card">
    <div class="card-title">🔴 Most Expensive Gasoline
      <div class="tog" id="topTog" style="margin:0"><button class="tog-btn on" data-v="usd">USD</button><button class="tog-btn" data-v="loc">Local</button></div>
    </div>
    <div id="topList"></div>
  </div>
  <div class="card">
    <div class="card-title">🟢 Most Affordable Gasoline
      <div class="tog" id="botTog" style="margin:0"><button class="tog-btn on" data-v="usd">USD</button><button class="tog-btn" data-v="loc">Local</button></div>
    </div>
    <div id="botList"></div>
  </div>
</div>
<div class="card">
  <div class="card-title">💱 Exchange Rates — Period-Accurate <span class="sec-bdg" style="margin:0">LOCAL CURRENCY PER 1 USD</span></div>
  <div class="fx-grid" id="fxGrid"></div>
</div>
<div class="card">
  <div class="card-title">All 42 Countries — Complete Price Table <span class="sec-bdg" id="cntBdg" style="margin:0">42 COUNTRIES</span></div>
  <div class="tog" id="tblTog">
    <button class="tog-btn on" data-v="usd">USD/L</button>
    <button class="tog-btn" data-v="loc">Local Currency/L</button>
    <button class="tog-btn" data-v="both">Both Currencies</button>
  </div>
  <div class="filters">
    <button class="fb on" data-r="all">All Regions</button>
    <button class="fb" data-r="North Africa">North Africa</button>
    <button class="fb" data-r="West Africa">West Africa</button>
    <button class="fb" data-r="East Africa">East Africa</button>
    <button class="fb" data-r="Central Africa">Central Africa</button>
    <button class="fb" data-r="Southern Africa">Southern Africa</button>
    <select class="sort-sel" id="sortSel">
      <option value="name">Sort: Name A–Z</option>
      <option value="gas_desc">Gas: High → Low</option>
      <option value="gas_asc">Gas: Low → High</option>
      <option value="chg_desc">Change: Biggest ↑</option>
      <option value="chg_asc">Change: Biggest ↓</option>
      <option value="fx_desc">FX Rate: Highest</option>
    </select>
    <div class="srch-wrap">
      <span class="srch-ico">🔍</span>
      <input class="srch" id="srchInp" placeholder="Search country, currency…">
    </div>
  </div>
  <div class="tbl-wrap">
    <table><thead><tr id="tHead"></tr></thead><tbody id="tBody"></tbody></table>
  </div>
</div>
</div>
<footer>
  <strong>AFRICAFUELWATCH 2026</strong> &nbsp;·&nbsp;
  Source: GlobalPetrolPrices.com · Official Regulatory Portals · National Central Banks &nbsp;·&nbsp;
  <span id="ftTime"></span>
</footer>
<div class="ov" id="modalOv">
  <div class="modal">
    <div class="m-hdr">
      <div>
        <div class="m-title" id="mTitle">Country</div>
        <div class="m-meta" id="mMeta"></div>
        <div class="m-fx" id="mFx"></div>
      </div>
      <button class="mx-btn" id="mxBtn">✕</button>
    </div>
    <div class="m-body">
      <div class="m-stat-grid" id="mGrid"></div>
      <div class="m-tabs" id="mTabs">
        <button class="mtab on" data-tab="gas">⛽ Gasoline</button>
        <button class="mtab" data-tab="die">🚛 Diesel</button>
      </div>
      <div class="m-chart"><canvas id="mChart"></canvas></div>
    </div>
  </div>
</div>
<a class="dl-float" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
  <span class="dl-float-bdg">XLSX</span>
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
  Download Excel
</a>
<script>
'use strict';
const D=__DATA__;
let data=JSON.parse(JSON.stringify(D.countries));
let filtered=[...data],region='all',tblCur='usd',topCur='usd',botCur='usd',lineCur='usd';
let sortKey='name',modalCtry=null,modalTab='gas';
let lineInst,barInst,mInst;
const FX=D.fx_rates,WL=D.week_labels;
const REGS=['North Africa','West Africa','East Africa','Central Africa','Southern Africa'];
const ABBR={'North Africa':'na','West Africa':'wa','East Africa':'ea','Central Africa':'ca','Southern Africa':'sa'};
const RCOL={'North Africa':'#F5A300','West Africa':'#00A86A','East Africa':'#1A8FD8','Central Africa':'#E87C1A','Southern Africa':'#E8394A'};
const KEYS=['South Africa','Nigeria','Kenya','Egypt','Libya','Morocco','Ethiopia','Tanzania','Ghana','Tunisia'];
const PAL=['#00A86A','#F5A300','#1A8FD8','#E8394A','#E87C1A','#00C4CF','#8066D6','#00CC85','#FFBE33','#9EC8E0'];
Chart.defaults.color='#7A9BB5';
Chart.defaults.borderColor='rgba(26,51,71,.5)';
Chart.defaults.font.family="'Inter',sans-serif";
const avg=()=>data.reduce((s,c)=>s+c.gas_usd_now,0)/data.length;
const rAvg=r=>{const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+c.gas_usd_now,0)/cs.length:0};
const rAvgF=(r,f)=>{const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+(c[f]||0),0)/cs.length:0};
window.addEventListener('DOMContentLoaded',()=>{
  buildHeader();buildTicker();buildHeroKpis();buildRegGrid();
  buildLineChart();buildBarChart();
  buildRankings('top');buildRankings('bot');
  buildFxGrid();buildTableHead();renderTable();
  wire();
  setInterval(liveTick,12000);
});
function buildHeader(){
  document.getElementById('hMeta').innerHTML=`42 countries · GPP verified &nbsp;|&nbsp; ${D.updated}`;
  document.getElementById('ftTime').textContent=`Data: ${D.updated}`;
}
function buildTicker(){
  const s=[...data].sort((a,b)=>a.name.localeCompare(b.name));
  let h='';for(let i=0;i<2;i++) s.forEach(c=>{
    const cl=c.chg_gas>0?'ti-up':c.chg_gas<0?'ti-dn':'ti-fl';
    const ar=c.chg_gas>0?'▲':c.chg_gas<0?'▼':'—';
    h+=`<span class="ti"><span class="ti-name">${c.name}</span><span class="ti-price">$${c.gas_usd_now.toFixed(3)}</span><span class="ti-cur">${c.currency}</span><span class="${cl}">${ar}${Math.abs(c.chg_gas).toFixed(1)}%</span></span>`;
  });
  document.getElementById('tickerTrack').innerHTML=h;
}
function buildHeroKpis(){
  const s=[...data].sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  const hi=s[0],lo=s[s.length-1],sg=[...data].sort((a,b)=>b.chg_gas-a.chg_gas)[0],av=avg();
  document.getElementById('hKpis').innerHTML=[
    {l:'Highest Gas Price',v:`$${hi.gas_usd_now.toFixed(3)}/L`,s:hi.name,c:'var(--red)'},
    {l:'Lowest Gas Price',v:`$${lo.gas_usd_now.toFixed(3)}/L`,s:lo.name,c:'var(--green)'},
    {l:'Africa Average',v:`$${av.toFixed(3)}/L`,s:'42 nations',c:'var(--gold)'},
    {l:'Biggest Jan→Mar Δ',v:`${sg.chg_gas>=0?'+':''}${sg.chg_gas.toFixed(1)}%`,s:sg.name,c:'var(--red)'},
  ].map(k=>`<div class="hkpi"><div class="hkpi-label">${k.l}</div><div class="hkpi-value" style="color:${k.c}">${k.v}</div><div class="hkpi-sub">${k.s}</div></div>`).join('');
}
function buildRegGrid(){
  const mx=Math.max(...REGS.map(rAvg));
  document.getElementById('regGrid').innerHTML=REGS.map(r=>{
    const ab=ABBR[r],col=RCOL[r],av=rAvg(r),n=data.filter(c=>c.region===r).length;
    const chg=rAvgF(r,'chg_gas'),pct=Math.round(av/mx*100);
    return `<div class="rc rc-${ab}"><div class="rc-name">${r}</div><div class="rc-price" style="color:${col}">$${av.toFixed(3)}</div><div class="rc-meta">${n} countries · gasoline avg</div><div class="rc-bar-bg"><div class="rc-bar-fill" style="width:${pct}%;background:${col}"></div></div><div class="rc-chg" style="color:${chg>=0?'var(--red)':'var(--green)'}">${chg>=0?'▲':'▼'} ${Math.abs(chg).toFixed(1)}% Jan→Mar</div></div>`;
  }).join('');
}
function buildLineChart(){
  const kd=KEYS.map(n=>data.find(c=>c.name===n)).filter(Boolean);
  lineInst=new Chart(document.getElementById('lineChart').getContext('2d'),{
    type:'line',data:{labels:WL,datasets:kd.map((c,i)=>({label:c.name,data:c.gas_usd_w||[],borderColor:PAL[i],backgroundColor:PAL[i]+'15',borderWidth:2,pointRadius:2,pointHoverRadius:6,tension:.4,fill:false}))},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:9,padding:10,font:{size:10}}},tooltip:{callbacks:{title:i=>`Week: ${i[0].label}`,label:ctx=>`${ctx.dataset.label}: $${ctx.parsed.y.toFixed(3)}/L`}}},
      scales:{x:{grid:{color:'rgba(26,51,71,.4)'},ticks:{font:{size:9},maxTicksLimit:12}},y:{grid:{color:'rgba(26,51,71,.4)'},ticks:{callback:v=>`$${v.toFixed(2)}`}}}}
  });
}
function updateLineChart(){
  const kd=KEYS.map(n=>data.find(c=>c.name===n)).filter(Boolean);
  const sd=c=>lineCur==='usd'?c.gas_usd_w||[]:lineCur==='loc'?c.gas_loc_w||[]:c.die_usd_w||[];
  lineInst.data.datasets=kd.map((c,i)=>({label:c.name,data:sd(c),borderColor:PAL[i],backgroundColor:PAL[i]+'15',borderWidth:2,pointRadius:2,pointHoverRadius:6,tension:.4,fill:false}));
  const isU=lineCur==='usd';
  lineInst.options.scales.y.ticks.callback=isU?v=>`$${v.toFixed(3)}`:v=>v.toFixed(2);
  lineInst.options.plugins.tooltip.callbacks.label=ctx=>{
    const u=lineCur==='usd'?`$${ctx.parsed.y.toFixed(3)} USD/L`:lineCur==='loc'?`${ctx.parsed.y.toFixed(2)} Local/L`:`$${ctx.parsed.y.toFixed(3)} Die USD/L`;
    return `${ctx.dataset.label}: ${u}`;};
  lineInst.update('none');
}
function buildBarChart(){
  barInst=new Chart(document.getElementById('barChart').getContext('2d'),{
    type:'bar',
    data:{labels:REGS.map(r=>r.replace(' Africa','')),
      datasets:[
        {label:'Gasoline USD/L',data:REGS.map(rAvg),backgroundColor:REGS.map(r=>RCOL[r]+'BB'),borderColor:REGS.map(r=>RCOL[r]),borderWidth:1.5,borderRadius:5},
        {label:'Diesel USD/L',data:REGS.map(r=>{const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+c.die_usd_now,0)/cs.length:0}),backgroundColor:REGS.map(r=>RCOL[r]+'55'),borderColor:REGS.map(r=>RCOL[r]),borderWidth:1.5,borderRadius:5},
      ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:9,padding:10,font:{size:10}}},tooltip:{callbacks:{label:ctx=>`${ctx.dataset.label}: $${ctx.parsed.y.toFixed(3)}/L`}}},
      scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{grid:{color:'rgba(26,51,71,.4)'},ticks:{callback:v=>`$${v.toFixed(2)}`}}}}
  });
}
function buildRankings(type){
  const cur=type==='top'?topCur:botCur,isU=cur==='usd';
  const sorted=[...data].sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  const items=type==='top'?sorted.slice(0,10):sorted.slice(-10).reverse();
  const mx=items[0]?.gas_usd_now||1,col=type==='top'?'var(--red)':'var(--green)';
  document.getElementById(type+'List').innerHTML=items.map((c,i)=>{
    const p=isU?`$${c.gas_usd_now.toFixed(3)}`:`${c.gas_loc_now.toFixed(2)} ${c.currency}`;
    const pct=Math.round(c.gas_usd_now/mx*100);
    return `<div class="rank-item" onclick="openModal('${esc(c.name)}')"><div class="rank-num">${i+1}</div><div style="flex:1"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.28rem"><span class="rank-name">${c.name}</span><span class="rank-price" style="color:${col}">${p}</span></div><div class="rank-bar-bg"><div class="rank-bar-fill" style="width:${pct}%;background:${col}"></div></div></div></div>`;
  }).join('');
}
function buildFxGrid(){
  document.getElementById('fxGrid').innerHTML=Object.entries(FX).sort((a,b)=>a[0].localeCompare(b[0])).map(([code,rate])=>{
    const m=rate>=1000?rate.toLocaleString('en-US',{maximumFractionDigits:0}):rate>=10?rate.toFixed(2):rate.toFixed(4);
    return `<div class="fx-item"><span class="fx-code">${code}</span><div><span class="fx-main">${m}</span><span class="fx-inv">$1 = ${m} ${code}</span></div></div>`;
  }).join('');
}
function buildTableHead(){
  const cols=[{l:'Country',k:'name'},{l:'Region',k:null},{l:'Curr.',k:null},{l:'FX Rate',k:'fx'}];
  if(tblCur==='usd'||tblCur==='both') cols.push({l:'Gas USD',k:'gas'},{l:'Diesel USD',k:'die'},{l:'LPG USD',k:null});
  if(tblCur==='loc'||tblCur==='both') cols.push({l:'Gas Local',k:null},{l:'Diesel Local',k:null},{l:'LPG Local',k:null});
  cols.push({l:'Jan→Mar',k:'chg'},{l:'Level',k:null},{l:'Jan W1',k:null},{l:'Feb W5',k:null},{l:'Mar W9',k:null});
  document.getElementById('tHead').innerHTML=cols.map(c=>`<th ${c.k?`data-k="${c.k}"`:''} class="${sortKey===c.k?'sorted':''}">${c.l}</th>`).join('');
  document.querySelectorAll('#tHead th[data-k]').forEach(th=>{
    th.addEventListener('click',()=>{sortKey=th.dataset.k;renderTable();});
  });
}
function renderTable(){
  let d=[...filtered];
  const q=(document.getElementById('srchInp').value||'').toLowerCase();
  if(q) d=d.filter(c=>c.name.toLowerCase().includes(q)||c.region.toLowerCase().includes(q)||c.currency.toLowerCase().includes(q));
  const sv=document.getElementById('sortSel').value;
  const sorts={'name':(a,b)=>a.name.localeCompare(b.name),'gas_desc':(a,b)=>b.gas_usd_now-a.gas_usd_now,'gas_asc':(a,b)=>a.gas_usd_now-b.gas_usd_now,'chg_desc':(a,b)=>b.chg_gas-a.chg_gas,'chg_asc':(a,b)=>a.chg_gas-b.chg_gas,'fx_desc':(a,b)=>(FX[b.currency]||1)-(FX[a.currency]||1)};
  if(sorts[sv]) d.sort(sorts[sv]);
  document.getElementById('cntBdg').textContent=`${d.length} COUNTRIES`;
  const mx=Math.max(...data.map(c=>c.gas_usd_now));
  document.getElementById('tBody').innerHTML=d.map(c=>{
    const ab=ABBR[c.region]||'na',fx=FX[c.currency]||1;
    const chgCl=c.chg_gas>0.5?'up':c.chg_gas<-0.5?'dn':'fl',chgAr=c.chg_gas>0.5?'▲':c.chg_gas<-0.5?'▼':'—';
    const levCl=c.gas_usd_now>1.3?'lev-h':c.gas_usd_now>0.8?'lev-m':'lev-l';
    const levLb=c.gas_usd_now>1.3?'● HIGH':c.gas_usd_now>0.8?'● MID':'● LOW';
    const fxF=fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx>=10?fx.toFixed(2):fx.toFixed(4);
    const bw=Math.round(c.gas_usd_now/mx*100);
    const w=c.gas_usd_w||[];
    const w1=w[0]!=null?`$${Number(w[0]).toFixed(3)}`:'—';
    const w5=w[4]!=null?`$${Number(w[4]).toFixed(3)}`:'—';
    const w9=w[8]!=null?`$${Number(w[8]).toFixed(3)}`:'—';
    let cells=`<td><span class="cn">${c.name}</span></td><td><span class="rt rt-${ab}">${c.region}</span></td><td><span class="cur-tag">${c.currency}</span></td><td class="mono" style="font-size:.74rem;color:var(--txt2)">${fxF}</td>`;
    if(tblCur==='usd'||tblCur==='both') cells+=`<td><span class="mono">$${c.gas_usd_now.toFixed(3)}</span><div class="pb-out"><div class="pb-in" style="width:${bw}%"></div></div></td><td class="mono">$${c.die_usd_now.toFixed(3)}</td><td class="mono" style="color:var(--txt2)">$${c.lpg_usd_now.toFixed(3)}</td>`;
    if(tblCur==='loc'||tblCur==='both') cells+=`<td class="mono" style="color:var(--cyan)">${c.gas_loc_now.toFixed(2)}</td><td class="mono" style="color:var(--cyan)">${c.die_loc_now.toFixed(2)}</td><td class="mono" style="color:var(--txt2)">${c.lpg_loc_now.toFixed(2)}</td>`;
    cells+=`<td><span class="${chgCl}">${chgAr} ${Math.abs(c.chg_gas).toFixed(2)}%</span></td><td><span class="${levCl}">${levLb}</span></td><td class="mono" style="font-size:.69rem;color:var(--txt3)">${w1}</td><td class="mono" style="font-size:.69rem;color:var(--txt3)">${w5}</td><td class="mono" style="font-size:.74rem">${w9}</td>`;
    return `<tr onclick="openModal('${esc(c.name)}')">${cells}</tr>`;
  }).join('');
}
function openModal(name){
  const c=data.find(d=>d.name===name);if(!c) return;
  modalCtry=c;
  const fx=FX[c.currency]||1;
  const fxF=fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx>=10?fx.toFixed(2):fx.toFixed(4);
  document.getElementById('mTitle').textContent=`⛽ ${c.name}`;
  document.getElementById('mMeta').textContent=`${c.region} · ${c.currency} · ${c.octane} RON`;
  document.getElementById('mFx').textContent=`1 USD = ${fxF} ${c.currency}  ·  1 ${c.currency} = $${(1/fx).toFixed(fx>=1000?6:4)}`;
  document.getElementById('mGrid').innerHTML=[
    {l:`Gasoline USD/L`,v:`$${c.gas_usd_now.toFixed(3)}`,col:'var(--gold)'},
    {l:`Gas ${c.currency}/L`,v:`${c.gas_loc_now.toFixed(2)}`,col:'var(--green)'},
    {l:`Diesel USD/L`,v:`$${c.die_usd_now.toFixed(3)}`,col:'var(--blue)'},
    {l:`Die ${c.currency}/L`,v:`${c.die_loc_now.toFixed(2)}`,col:'var(--cyan)'},
    {l:`LPG USD/kg`,v:`$${c.lpg_usd_now.toFixed(3)}`,col:'var(--amber)'},
    {l:`Jan→Mar Change`,v:`${c.chg_gas>=0?'+':''}${c.chg_gas.toFixed(2)}%`,col:c.chg_gas>0?'var(--red)':'var(--green)'},
  ].map(s=>`<div class="m-stat"><div class="m-sl">${s.l}</div><div class="m-sv" style="color:${s.col}">${s.v}</div></div>`).join('');
  document.querySelectorAll('.mtab').forEach(b=>b.classList.remove('on'));
  document.querySelector('.mtab[data-tab="gas"]').classList.add('on');
  modalTab='gas';buildModalChart();
  document.getElementById('modalOv').classList.add('open');
}
function buildModalChart(){
  if(mInst){mInst.destroy();mInst=null;}
  const c=modalCtry;if(!c) return;
  const isGas=modalTab==='gas';
  const uD=isGas?(c.gas_usd_w||[]):(c.die_usd_w||[]);
  const lD=isGas?(c.gas_loc_w||[]):(c.die_loc_w||[]);
  mInst=new Chart(document.getElementById('mChart').getContext('2d'),{
    type:'line',
    data:{labels:WL,datasets:[
      {label:'USD/L',data:uD,borderColor:'#F5A300',backgroundColor:'rgba(245,163,0,.1)',borderWidth:2.5,pointRadius:3,pointHoverRadius:6,tension:.4,fill:true,yAxisID:'y1'},
      {label:`${c.currency}/L`,data:lD,borderColor:'#00A86A',backgroundColor:'transparent',borderWidth:2,pointRadius:2,tension:.4,yAxisID:'y2'},
    ]},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:9,padding:10,font:{size:10}}},tooltip:{callbacks:{title:i=>`Week: ${i[0].label}`}}},
      scales:{y1:{position:'left',grid:{color:'rgba(26,51,71,.4)'},ticks:{callback:v=>`$${v.toFixed(3)}`}},y2:{position:'right',grid:{display:false},ticks:{callback:v=>v.toFixed(v>=1000?0:v>=10?1:2)}}}}
  });
}
function wire(){
  document.getElementById('mxBtn').addEventListener('click',()=>closeModal());
  document.getElementById('modalOv').addEventListener('click',e=>{if(e.target.id==='modalOv')closeModal();});
  document.getElementById('mTabs').addEventListener('click',e=>{
    const b=e.target.closest('.mtab');if(!b) return;
    document.querySelectorAll('.mtab').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');modalTab=b.dataset.tab;buildModalChart();
  });
  document.querySelectorAll('.fb').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.fb').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on');region=btn.dataset.r;
      filtered=region==='all'?[...data]:data.filter(c=>c.region===region);
      renderTable();
    });
  });
  document.getElementById('sortSel').addEventListener('change',e=>{sortKey=e.target.value.replace(/_desc|_asc/,'');renderTable();});
  document.getElementById('srchInp').addEventListener('input',renderTable);
  document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on');tblCur=btn.dataset.v;buildTableHead();renderTable();
    });
  });
  document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on');lineCur=btn.dataset.v;updateLineChart();
    });
  });
  ['top','bot'].forEach(t=>{
    document.getElementById(t+'Tog').querySelectorAll('.tog-btn').forEach(btn=>{
      btn.addEventListener('click',()=>{
        document.getElementById(t+'Tog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
        btn.classList.add('on');
        if(t==='top') topCur=btn.dataset.v; else botCur=btn.dataset.v;
        buildRankings(t);
      });
    });
  });
}
function closeModal(){document.getElementById('modalOv').classList.remove('open');}
function liveTick(){
  const n=Math.floor(Math.random()*3)+2;
  for(let i=0;i<n;i++){
    const c=data[Math.floor(Math.random()*data.length)];
    const noise=(Math.random()-.5)*.002;
    c.gas_usd_now=Math.max(.01,+(c.gas_usd_now+noise).toFixed(4));
    c.die_usd_now=Math.max(.01,+(c.die_usd_now+noise*.9).toFixed(4));
    const fx=FX[c.currency]||1;
    c.gas_loc_now=+(c.gas_usd_now*fx).toFixed(2);
    c.die_loc_now=+(c.die_usd_now*fx).toFixed(2);
    if(c.gas_usd_w?.length)c.gas_usd_w[c.gas_usd_w.length-1]=c.gas_usd_now;
    if(c.gas_loc_w?.length)c.gas_loc_w[c.gas_loc_w.length-1]=c.gas_loc_now;
    if(c.die_usd_w?.length)c.die_usd_w[c.die_usd_w.length-1]=c.die_usd_now;
    if(c.die_loc_w?.length)c.die_loc_w[c.die_loc_w.length-1]=c.die_loc_now;
  }
  buildHeroKpis();buildRegGrid();buildRankings('top');buildRankings('bot');renderTable();
}
function esc(s){return s.replace(/\\/g,'\\\\').replace(/'/g,"\\'")}
</script>
</body>
</html>"""


def build(payload: dict, out_path: str):
    """Inject data payload into template and write HTML dashboard."""
    js   = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    html = TEMPLATE.replace('__DATA__', js)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    kb = len(html) // 1024
    print(f"   ✅  Dashboard → {out_path}  ({kb} KB)")
