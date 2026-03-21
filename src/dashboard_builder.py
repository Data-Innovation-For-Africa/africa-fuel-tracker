"""
dashboard_builder.py — generates the complete standalone HTML dashboard.
All features verified: ticker, KPIs, region cards, charts, currency toggle,
filters, sort, search, rankings, FX panel, modal, live simulation.
"""
import json


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Africa Fuel Price Tracker 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=IBM+Plex+Mono:wght@400;600&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#07090f;--bg2:#0d1117;--bg3:#111827;
  --panel:#151d2b;--panel2:#1a2438;
  --bord:#1e2d42;--bord2:#253347;
  --acc:#f59e0b;--acc2:#fbbf24;
  --grn:#10b981;--red:#ef4444;
  --blu:#3b82f6;--pur:#8b5cf6;--cyn:#06b6d4;
  --txt:#f1f5f9;--txt2:#94a3b8;--txt3:#475569;
  --r:10px;--rl:16px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--txt);font-family:'DM Sans',sans-serif;overflow-x:hidden;min-height:100vh;font-size:14px}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(245,158,11,.07),transparent 65%);pointer-events:none;z-index:0}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-thumb{background:#1e2d42;border-radius:9px}

/* ── HEADER ── */
header{position:sticky;top:0;z-index:100;background:rgba(7,9,15,.9);backdrop-filter:blur(18px);
  border-bottom:1px solid var(--bord);height:56px;padding:0 1.5rem;
  display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:.65rem}
.logo-ico{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,var(--acc),#d97706);
  display:flex;align-items:center;justify-content:center;font-size:.95rem;box-shadow:0 0 20px rgba(245,158,11,.2)}
.logo-txt{font-family:'Syne',sans-serif;font-size:.95rem;font-weight:800;letter-spacing:-.01em}
.logo-txt em{font-style:normal;color:var(--acc)}
.hdr-r{display:flex;align-items:center;gap:1.2rem}
.hdr-meta{font-family:'IBM Plex Mono',monospace;font-size:.68rem;color:var(--txt2);text-align:right;line-height:1.5}
.live-pill{display:flex;align-items:center;gap:.35rem;background:rgba(16,185,129,.1);
  border:1px solid rgba(16,185,129,.3);border-radius:99px;padding:.22rem .65rem;
  font-family:'IBM Plex Mono',monospace;font-size:.68rem;color:var(--grn)}
.dot{width:6px;height:6px;background:var(--grn);border-radius:50%;animation:blink 2s infinite}
@keyframes blink{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.5)}50%{box-shadow:0 0 0 5px rgba(16,185,129,0)}}

/* ── TICKER ── */
.ticker{height:32px;background:var(--bg3);border-bottom:1px solid var(--bord);
  display:flex;align-items:center;overflow:hidden}
.ticker-lbl{background:var(--acc);color:#000;font-family:'IBM Plex Mono',monospace;
  font-size:.66rem;font-weight:700;letter-spacing:.06em;padding:0 .85rem;height:100%;
  display:flex;align-items:center;flex-shrink:0;white-space:nowrap}
.ticker-inner{overflow:hidden;flex:1}
.ticker-track{display:flex;gap:2.5rem;white-space:nowrap;padding:0 1.5rem;
  animation:scroll-left 90s linear infinite}
@keyframes scroll-left{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ti{font-family:'IBM Plex Mono',monospace;font-size:.68rem;display:flex;align-items:center;gap:.4rem}
.ti-n{color:var(--txt);font-weight:600}
.ti-p{color:var(--txt2)}
.ti-up{color:var(--red)}.ti-dn{color:var(--grn)}.ti-fl{color:var(--txt3)}

/* ── WRAPPER ── */
.wrap{max-width:1700px;margin:0 auto;padding:1.4rem 1.5rem 5rem;position:relative;z-index:1}

/* ── HERO ── */
.hero{background:linear-gradient(135deg,var(--bg3),var(--panel));border:1px solid var(--bord);
  border-radius:var(--rl);padding:1.75rem 2rem;margin-bottom:1.4rem;
  display:flex;align-items:flex-start;justify-content:space-between;gap:1.5rem;
  overflow:hidden;position:relative}
.hero::after{content:'🌍';position:absolute;right:.5rem;bottom:-1.5rem;font-size:9rem;opacity:.04;pointer-events:none}
.hero-h{font-family:'Syne',sans-serif;font-size:1.85rem;font-weight:800;line-height:1.1;
  background:linear-gradient(120deg,#fff 15%,var(--acc));-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.45rem}
.hero-s{color:var(--txt2);font-size:.85rem;line-height:1.65;max-width:540px}
.hero-chips{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.9rem}
.chip{padding:.24rem .65rem;border-radius:99px;font-size:.68rem;font-weight:600;letter-spacing:.02em;border:1px solid}
.ca{background:rgba(245,158,11,.1);border-color:rgba(245,158,11,.35);color:var(--acc2)}
.cg{background:rgba(16,185,129,.1);border-color:rgba(16,185,129,.3);color:var(--grn)}
.cb{background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.3);color:var(--blu)}
.cp{background:rgba(139,92,246,.1);border-color:rgba(139,92,246,.3);color:var(--pur)}
.hero-kpis{display:grid;grid-template-columns:repeat(2,1fr);gap:.75rem;flex-shrink:0}
.hkpi{background:var(--bg3);border:1px solid var(--bord);border-radius:var(--r);
  padding:.9rem 1.1rem;min-width:140px}
.hkpi-l{font-size:.64rem;text-transform:uppercase;letter-spacing:.07em;color:var(--txt3);margin-bottom:.3rem}
.hkpi-v{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;line-height:1}
.hkpi-s{font-size:.65rem;color:var(--txt3);margin-top:.2rem;font-family:'IBM Plex Mono',monospace}

/* ── SECTION TITLE ── */
.st{font-family:'Syne',sans-serif;font-size:.88rem;font-weight:700;
  display:flex;align-items:center;gap:.55rem;margin-bottom:.9rem}
.st::after{content:'';flex:1;height:1px;background:var(--bord)}
.st .bdg{font-size:.6rem;font-weight:400;background:var(--panel2);border:1px solid var(--bord2);
  border-radius:99px;padding:.15rem .48rem;color:var(--txt3);font-family:'IBM Plex Mono',monospace;font-weight:400}

/* ── REGION STRIP ── */
.reg-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:.9rem;margin-bottom:1.4rem}
.rc{background:var(--panel);border:1px solid var(--bord);border-radius:var(--r);
  padding:1rem 1.1rem;position:relative;overflow:hidden;transition:transform .2s,border-color .2s}
.rc:hover{transform:translateY(-2px);border-color:var(--bord2)}
.rc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.rc-na::before{background:linear-gradient(90deg,var(--grn),#34d399)}
.rc-wa::before{background:linear-gradient(90deg,var(--blu),#60a5fa)}
.rc-ea::before{background:linear-gradient(90deg,var(--acc),var(--acc2))}
.rc-ca::before{background:linear-gradient(90deg,var(--pur),#a78bfa)}
.rc-sa::before{background:linear-gradient(90deg,var(--red),#f87171)}
.rc-l{font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;color:var(--txt3);margin-bottom:.3rem}
.rc-p{font-family:'Syne',sans-serif;font-size:1.35rem;font-weight:800;line-height:1}
.rc-m{font-size:.67rem;color:var(--txt3);margin-top:.28rem}
.rc-bar{height:2px;border-radius:99px;margin-top:.65rem;background:var(--bord2)}
.rc-bf{height:2px;border-radius:99px;transition:.5s}

/* ── CARDS + GRID ── */
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem;margin-bottom:1.4rem}
.grid-ch{display:grid;grid-template-columns:3fr 2fr;gap:1.1rem;margin-bottom:1.4rem}
.card{background:var(--panel);border:1px solid var(--bord);border-radius:var(--r);padding:1.2rem}

/* ── TOGGLE BUTTONS ── */
.tog{display:flex;background:var(--bg3);border:1px solid var(--bord);border-radius:99px;
  padding:.22rem;gap:.3rem;margin-bottom:.85rem;width:fit-content}
.tog-btn{padding:.28rem .8rem;border-radius:99px;font-size:.73rem;font-weight:600;
  cursor:pointer;transition:.15s;border:none;background:transparent;
  color:var(--txt2);font-family:'DM Sans',sans-serif}
.tog-btn.on{background:var(--acc);color:#000}

/* ── FILTERS ── */
.filters{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;margin-bottom:.9rem}
.fb{padding:.3rem .8rem;border-radius:99px;border:1px solid var(--bord);background:var(--panel);
  color:var(--txt2);font-size:.73rem;font-weight:500;cursor:pointer;transition:.15s;
  font-family:'DM Sans',sans-serif}
.fb:hover{border-color:var(--acc);color:var(--txt)}
.fb.on{background:rgba(245,158,11,.12);border-color:var(--acc);color:var(--acc)}
.srch-w{margin-left:auto;position:relative}
.srch{background:var(--panel);border:1px solid var(--bord);color:var(--txt);
  border-radius:99px;padding:.3rem .85rem .3rem 2rem;font-size:.73rem;width:180px;
  outline:none;transition:.2s;font-family:'DM Sans',sans-serif}
.srch:focus{border-color:var(--acc);width:220px}
.srch-ic{position:absolute;left:.68rem;top:50%;transform:translateY(-50%);color:var(--txt3);font-size:.78rem}
.sort-sel{background:var(--panel);border:1px solid var(--bord);color:var(--txt);
  border-radius:99px;padding:.3rem .85rem;font-size:.73rem;outline:none;cursor:pointer;
  font-family:'DM Sans',sans-serif}
.sort-sel option{background:var(--bg3)}

/* ── TABLE ── */
.tbl-w{overflow-x:auto}
table{width:100%;border-collapse:collapse}
thead th{padding:.55rem .75rem;text-align:left;font-size:.65rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.07em;color:var(--txt3);
  border-bottom:1px solid var(--bord);cursor:pointer;user-select:none;white-space:nowrap;
  transition:color .15s}
thead th:hover{color:var(--acc)}
thead th.sorted{color:var(--acc)}
tbody td{padding:.5rem .75rem;border-bottom:1px solid rgba(30,45,66,.45);
  font-size:.78rem;line-height:1.4;white-space:nowrap}
tbody tr{cursor:pointer;transition:background .12s}
tbody tr:hover td{background:rgba(20,30,50,.55)}
tbody tr:last-child td{border-bottom:none}
.cn{font-weight:600;color:var(--txt)}
.rt{font-size:.61rem;font-weight:600;padding:.1rem .4rem;border-radius:99px;border:1px solid}
.rt-na{color:#34d399;border-color:rgba(52,211,153,.3);background:rgba(52,211,153,.08)}
.rt-wa{color:#60a5fa;border-color:rgba(96,165,250,.3);background:rgba(96,165,250,.08)}
.rt-ea{color:#fbbf24;border-color:rgba(251,191,36,.3);background:rgba(251,191,36,.08)}
.rt-ca{color:#c084fc;border-color:rgba(192,132,252,.3);background:rgba(192,132,252,.08)}
.rt-sa{color:#f87171;border-color:rgba(248,113,113,.3);background:rgba(248,113,113,.08)}
.mono{font-family:'IBM Plex Mono',monospace;font-weight:600}
.pbar-w{width:64px;background:var(--bg2);border-radius:99px;height:3px;margin-top:3px}
.pbar{height:3px;border-radius:99px;background:linear-gradient(90deg,var(--acc),var(--acc2));transition:.4s}
.up{color:var(--red);font-family:'IBM Plex Mono',monospace;font-size:.72rem;font-weight:600}
.dn{color:var(--grn);font-family:'IBM Plex Mono',monospace;font-size:.72rem;font-weight:600}
.fl{color:var(--txt3);font-family:'IBM Plex Mono',monospace;font-size:.72rem}
.lev-h{color:var(--red);font-size:.68rem;font-weight:700}
.lev-m{color:var(--acc);font-size:.68rem;font-weight:700}
.lev-l{color:var(--grn);font-size:.68rem;font-weight:700}
.fx-tag{font-family:'IBM Plex Mono',monospace;font-size:.7rem;color:var(--cyn)}
.cur-tag{font-size:.64rem;background:rgba(6,182,212,.09);border:1px solid rgba(6,182,212,.25);
  color:var(--cyn);padding:.08rem .38rem;border-radius:4px;font-family:'IBM Plex Mono',monospace}
.ch-wrap{position:relative;height:300px}
.ch-wrap-lg{position:relative;height:350px}

/* ── RANKINGS ── */
.rlist{display:flex;flex-direction:column;gap:.42rem}
.ri{display:flex;align-items:center;gap:.65rem;padding:.58rem .72rem;border-radius:8px;
  background:var(--bg3);border:1px solid var(--bord);cursor:pointer;transition:.15s}
.ri:hover{border-color:var(--acc)}
.ri-n{font-family:'Syne',sans-serif;font-weight:800;font-size:.88rem;width:1.4rem;
  text-align:center;color:var(--txt3)}
.r1 .ri-n{color:var(--acc)}.r2 .ri-n{color:var(--txt2)}.r3 .ri-n{color:var(--acc2)}
.ri-info{flex:1}
.ri-nm{font-weight:600;font-size:.78rem}
.ri-sub{font-size:.63rem;color:var(--txt3);margin-top:.08rem}
.ri-right{text-align:right}
.ri-price{font-family:'IBM Plex Mono',monospace;font-weight:700;font-size:.82rem}
.ri-local{font-family:'IBM Plex Mono',monospace;font-size:.66rem;color:var(--txt3);margin-top:.08rem}

/* ── FX GRID ── */
.fx-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(195px,1fr));gap:.55rem;
  max-height:300px;overflow-y:auto;padding-right:.3rem}
.fx-item{background:var(--bg3);border:1px solid var(--bord);border-radius:8px;
  padding:.6rem .75rem;display:flex;align-items:center;justify-content:space-between}
.fx-code{font-family:'IBM Plex Mono',monospace;font-weight:700;font-size:.78rem;color:var(--cyn)}
.fx-val{text-align:right}
.fx-rate{font-family:'IBM Plex Mono',monospace;font-size:.76rem;color:var(--txt2)}
.fx-inv{font-size:.6rem;color:var(--txt3);display:block;margin-top:.05rem;font-family:'IBM Plex Mono',monospace}

/* ── MODAL ── */
.ov{position:fixed;inset:0;background:rgba(0,0,0,.78);z-index:200;
  display:none;align-items:center;justify-content:center;backdrop-filter:blur(8px)}
.ov.open{display:flex}
.modal{background:var(--bg2);border:1px solid var(--bord);border-radius:var(--rl);
  padding:1.75rem;width:min(640px,95vw);max-height:90vh;overflow-y:auto;position:relative}
.mx{position:absolute;top:.85rem;right:.85rem;background:var(--panel);border:1px solid var(--bord);
  color:var(--txt2);border-radius:7px;padding:.25rem .55rem;cursor:pointer;font-size:.8rem;
  transition:.15s;font-family:'DM Sans',sans-serif}
.mx:hover{color:var(--txt);background:var(--panel2)}
.m-title{font-family:'Syne',sans-serif;font-size:1.45rem;font-weight:800;margin-bottom:.22rem}
.m-meta{font-size:.76rem;color:var(--txt2);margin-bottom:.15rem}
.m-fx{font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:var(--cyn);margin-bottom:1.1rem}
.m-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem;margin-bottom:1.1rem}
.m-stat{background:var(--panel);border:1px solid var(--bord);border-radius:9px;
  padding:.8rem;text-align:center}
.m-sl{font-size:.6rem;text-transform:uppercase;letter-spacing:.07em;color:var(--txt3);margin-bottom:.28rem}
.m-sv{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800}
.m-tabs{display:flex;gap:.38rem;margin-bottom:.7rem}
.mtab{padding:.25rem .65rem;border-radius:99px;font-size:.7rem;font-weight:600;cursor:pointer;
  border:1px solid var(--bord);background:var(--panel2);color:var(--txt2);transition:.15s;
  font-family:'DM Sans',sans-serif}
.mtab.on{background:var(--acc);color:#000;border-color:var(--acc)}
.m-ch{position:relative;height:210px}

footer{border-top:1px solid var(--bord);padding:1.2rem 1.5rem;text-align:center;
  font-family:'IBM Plex Mono',monospace;font-size:.65rem;color:var(--txt3)}

/* ── DOWNLOAD BUTTON ── */
@keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes float-pulse{0%,100%{transform:translateY(0);box-shadow:0 8px 32px rgba(16,185,129,.4),0 2px 8px rgba(0,0,0,.4)}50%{transform:translateY(-5px);box-shadow:0 16px 48px rgba(16,185,129,.6),0 4px 16px rgba(0,0,0,.4)}}
@keyframes glow-ring{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.6),0 8px 32px rgba(16,185,129,.3)}60%{box-shadow:0 0 0 12px rgba(16,185,129,0),0 8px 32px rgba(16,185,129,.2)}}
/* Header compact button */
.dl-hdr{display:flex;align-items:center;gap:.45rem;padding:.32rem .85rem;border-radius:99px;
  background:linear-gradient(135deg,#064e3b,#065f46);border:1px solid rgba(16,185,129,.4);
  color:#6ee7b7;font-family:'DM Sans',sans-serif;font-size:.72rem;font-weight:600;
  cursor:pointer;text-decoration:none;transition:.2s;white-space:nowrap;
  box-shadow:0 0 16px rgba(16,185,129,.18)}
.dl-hdr:hover{background:linear-gradient(135deg,#065f46,#047857);border-color:rgba(16,185,129,.7);
  color:#a7f3d0;box-shadow:0 0 28px rgba(16,185,129,.45);transform:translateY(-1px)}
/* Hero large button */
.dl-hero-wrap{margin-top:1.4rem}
.dl-hero{display:inline-flex;align-items:center;gap:.8rem;padding:.8rem 1.75rem;border-radius:14px;
  background:linear-gradient(120deg,#047857 0%,#059669 30%,#34d399 55%,#10b981 75%,#047857 100%);
  background-size:250% auto;animation:shimmer 3s linear infinite,glow-ring 2.5s ease-out infinite;
  border:1px solid rgba(110,231,183,.3);color:#fff;
  font-family:'Syne',sans-serif;font-size:.95rem;font-weight:800;
  cursor:pointer;text-decoration:none;letter-spacing:.01em;position:relative;overflow:hidden}
.dl-hero::after{content:'';position:absolute;inset:0;
  background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,.18) 50%,transparent 65%);
  background-size:300% auto;animation:shimmer 2.2s linear infinite}
.dl-hero:hover{animation:shimmer 1.2s linear infinite;transform:translateY(-2px) scale(1.02);filter:brightness(1.1)}
.dl-hero-ico{width:40px;height:40px;background:rgba(255,255,255,.2);border-radius:10px;
  display:flex;align-items:center;justify-content:center;font-size:1.25rem;flex-shrink:0;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.25)}
.dl-hero-txt{text-align:left;line-height:1.25}
.dl-hero-txt strong{display:block;font-size:.95rem}
.dl-hero-txt span{font-size:.7rem;opacity:.82;font-family:'DM Sans',sans-serif;font-weight:400}
/* Floating button */
.dl-float{position:fixed;bottom:2rem;right:2rem;z-index:99;
  display:flex;align-items:center;gap:.7rem;padding:.8rem 1.35rem .8rem 1.1rem;border-radius:16px;
  background:linear-gradient(135deg,#047857 0%,#059669 50%,#10b981 100%);
  border:1px solid rgba(110,231,183,.25);color:#fff;
  font-family:'Syne',sans-serif;font-size:.82rem;font-weight:700;
  cursor:pointer;text-decoration:none;
  animation:float-pulse 3s ease-in-out infinite;transition:filter .2s}
.dl-float:hover{animation:none;transform:translateY(-4px) scale(1.04);filter:brightness(1.12);
  box-shadow:0 20px 56px rgba(16,185,129,.6),0 4px 16px rgba(0,0,0,.5) !important}
.dl-float-ico{width:36px;height:36px;background:rgba(255,255,255,.2);border-radius:10px;
  display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0}
.dl-float-bdg{position:absolute;top:-8px;right:-8px;background:var(--acc);color:#000;
  border-radius:99px;font-size:.57rem;font-weight:800;padding:.16rem .4rem;
  font-family:'IBM Plex Mono',monospace;letter-spacing:.03em;border:2px solid var(--bg);
  box-shadow:0 2px 10px rgba(245,158,11,.6)}
.dl-float-txt{line-height:1.2}
.dl-float-txt strong{display:block}
.dl-float-txt span{font-size:.62rem;opacity:.82;font-family:'DM Sans',sans-serif;font-weight:400}

@media(max-width:1280px){.reg-strip{grid-template-columns:repeat(3,1fr)}.grid-ch{grid-template-columns:1fr}}
@media(max-width:900px){.reg-strip{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}.hero-kpis{display:none}}
@media(max-width:600px){.wrap{padding:.9rem}.hero-h{font-size:1.3rem}.reg-strip{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-ico">⛽</div>
    <div class="logo-txt">AFRICA<em>FUEL</em>WATCH</div>
  </div>
  <div class="hdr-r">
    <div class="hdr-meta" id="hMeta">Loading...</div>
    <div class="live-pill"><span class="dot"></span>LIVE</div>
    <a class="dl-hdr" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Download Excel
    </a>
  </div>
</header>

<div class="ticker">
  <div class="ticker-lbl">LIVE · JAN–MAR 2026</div>
  <div class="ticker-inner"><div class="ticker-track" id="tickerTrack"></div></div>
</div>

<div class="wrap">

<!-- HERO -->
<div class="hero">
  <div>
    <div class="hero-h">Africa Fuel Price Intelligence<br>01 January – 20 March 2026</div>
    <div class="hero-s">
      Real-time monitoring of gasoline, diesel &amp; LPG across all <strong>54 African nations</strong>.
      Every price shown in <strong>USD/L</strong> and the country's <strong>local national currency/L</strong>
      via live central bank exchange rates. Updated automatically every day.
    </div>
    <div class="hero-chips">
      <span class="chip ca">⛽ 54 Countries</span>
      <span class="chip cg">🌍 5 Regions</span>
      <span class="chip cb">💱 41 Currencies · Live FX</span>
      <span class="chip cp">📅 01 Jan – 20 Mar 2026 · 12 weeks</span>
      <span class="chip ca">🔄 Daily Auto-Update</span>
    </div>
    <div class="dl-hero-wrap">
      <a class="dl-hero" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
        <div class="dl-hero-ico">📊</div>
        <div class="dl-hero-txt">
          <strong>Download Excel Report</strong>
          <span>7 sheets · 54 countries · USD + Local Currency · Updated daily</span>
        </div>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;opacity:.9"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      </a>
    </div>
  </div>
  <div class="hero-kpis" id="hKpis"></div>
</div>

<!-- REGION CARDS -->
<div class="st">Regional Overview <span class="bdg">5 REGIONS · MARCH 2026</span></div>
<div class="reg-strip" id="regStrip"></div>

<!-- CHARTS -->
<div class="grid-ch">
  <div class="card">
    <div class="st" style="margin-bottom:.5rem">Weekly Trend — 10 Key Markets <span class="bdg">01 JAN → 20 MAR 2026 · 12 WEEKS</span></div>
    <div class="tog" id="lineTog">
      <button class="tog-btn on" data-v="usd">USD / L</button>
      <button class="tog-btn" data-v="loc">Local Currency / L</button>
      <button class="tog-btn" data-v="die">Diesel USD / L</button>
    </div>
    <div class="ch-wrap-lg"><canvas id="lineChart"></canvas></div>
  </div>
  <div class="card">
    <div class="st" style="margin-bottom:.5rem">Regional Comparison <span class="bdg">GAS vs DIESEL</span></div>
    <div class="ch-wrap-lg"><canvas id="barChart"></canvas></div>
  </div>
</div>

<!-- RANKINGS -->
<div class="grid2">
  <div class="card">
    <div class="st" style="margin-bottom:.55rem">🔴 Most Expensive Gasoline <span class="bdg">TOP 10 · MAR 2026</span></div>
    <div class="tog" id="topTog">
      <button class="tog-btn on" data-v="usd">USD</button>
      <button class="tog-btn" data-v="loc">Local Currency</button>
    </div>
    <div class="rlist" id="topList"></div>
  </div>
  <div class="card">
    <div class="st" style="margin-bottom:.55rem">🟢 Most Affordable Gasoline <span class="bdg">TOP 10 · MAR 2026</span></div>
    <div class="tog" id="botTog">
      <button class="tog-btn on" data-v="usd">USD</button>
      <button class="tog-btn" data-v="loc">Local Currency</button>
    </div>
    <div class="rlist" id="botList"></div>
  </div>
</div>

<!-- FX RATES -->
<div class="card" style="margin-bottom:1.4rem">
  <div class="st" style="margin-bottom:.7rem">💱 Exchange Rates — Local Currency per 1 USD <span class="bdg">MARCH 2026 · CENTRAL BANK REFERENCE</span></div>
  <div class="fx-grid" id="fxGrid"></div>
</div>

<!-- MAIN TABLE -->
<div class="card">
  <div class="st">All 54 Countries — 01 Jan → 20 Mar 2026 <span class="bdg" id="cntBadge">54 COUNTRIES</span></div>
  <div class="tog" id="tblTog">
    <button class="tog-btn on" data-v="usd">USD / L</button>
    <button class="tog-btn" data-v="loc">Local Currency / L</button>
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
      <option value="gas_desc">Gas Price: High → Low</option>
      <option value="gas_asc">Gas Price: Low → High</option>
      <option value="chg_desc">Change: Biggest ↑</option>
      <option value="chg_asc">Change: Biggest ↓</option>
      <option value="fx_desc">FX Rate: Highest</option>
    </select>
    <div class="srch-w">
      <span class="srch-ic">🔍</span>
      <input class="srch" id="srchInp" placeholder="Search country...">
    </div>
  </div>
  <div class="tbl-w">
    <table>
      <thead><tr id="tHead"></tr></thead>
      <tbody id="tBody"></tbody>
    </table>
  </div>
</div>

</div>

<footer>AFRICAFUELWATCH 2026 &nbsp;·&nbsp; Sources: GlobalPetrolPrices.com · OPEC · World Bank · National Central Banks · Energy Regulatory Portals &nbsp;·&nbsp; <span id="ftTime"></span></footer>

<!-- FLOATING DOWNLOAD BUTTON -->
<a class="dl-float" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
  <span class="dl-float-bdg">XLSX</span>
  <div class="dl-float-ico">📊</div>
  <div class="dl-float-txt">
    <strong>Download Excel</strong>
    <span>54 countries · 7 sheets</span>
  </div>
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
</a>

<!-- MODAL -->
<div class="ov" id="modalOv">
  <div class="modal">
    <button class="mx" id="mxBtn">✕ Close</button>
    <div class="m-title" id="mTitle"></div>
    <div class="m-meta" id="mMeta"></div>
    <div class="m-fx" id="mFx"></div>
    <div class="m-grid" id="mGrid"></div>
    <div class="m-tabs" id="mTabs">
      <button class="mtab on" data-tab="gas">Gasoline</button>
      <button class="mtab" data-tab="die">Diesel</button>
    </div>
    <div class="m-ch"><canvas id="mChart"></canvas></div>
  </div>
</div>

<script>
// ── DATA (injected by dashboard_builder.py) ──────────────────────────────────
const D = __DATA__;

// ── STATE ────────────────────────────────────────────────────────────────────
let data      = JSON.parse(JSON.stringify(D.countries));  // deep copy for live mutation
let filtered  = [...data];
let region    = 'all';
let tblCur    = 'usd';    // table currency mode
let topCur    = 'usd';
let botCur    = 'usd';
let lineCur   = 'usd';
let sortKey   = 'name';
let modalCtry = null;
let modalTab  = 'gas';
let lineInst, barInst, mInst;

const FX          = D.fx_rates;
const MONTHS      = D.week_labels;   // kept for backward compat
const WEEK_LABELS = D.week_labels;   // 12-week labels
const REGIONS = ['North Africa','West Africa','East Africa','Central Africa','Southern Africa'];
const KEY     = ['South Africa','Nigeria','Kenya','Egypt','Libya','Morocco','Ethiopia','Tanzania','Ghana','Tunisia'];
const R_ABR   = {'North Africa':'na','West Africa':'wa','East Africa':'ea','Central Africa':'ca','Southern Africa':'sa'};
const R_COL   = {'North Africa':'#10b981','West Africa':'#3b82f6','East Africa':'#f59e0b','Central Africa':'#8b5cf6','Southern Africa':'#ef4444'};
const PAL     = ['#f59e0b','#10b981','#3b82f6','#8b5cf6','#ef4444','#06b6d4','#ec4899','#a3e635','#f97316','#14b8a6'];

Chart.defaults.color        = '#94a3b8';
Chart.defaults.borderColor  = 'rgba(30,45,66,.5)';
Chart.defaults.font.family  = "'DM Sans', sans-serif";

const afAvg = () => data.reduce((s,c)=>s+c.gas_usd_now,0)/data.length;

// ── BOOTSTRAP ────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  updateHeader();
  buildTicker();
  buildHeroKpis();
  buildRegCards();
  buildLineChart();
  buildBarChart();
  buildRankings('top'); buildRankings('bot');
  buildFxGrid();
  buildTableHead();
  renderTable();
  wire();
  setInterval(liveTick, 10000);
});

// ── HEADER ───────────────────────────────────────────────────────────────────
function updateHeader(){
  const t = new Date().toLocaleTimeString('en-US',{hour12:false});
  document.getElementById('hMeta').innerHTML =
    `Period: Jan–Mar 2026&nbsp; | &nbsp;Updated: ${t} UTC&nbsp; | &nbsp;${D.updated}`;
  document.getElementById('ftTime').textContent = `Last data update: ${D.updated}`;
}

// ── TICKER ───────────────────────────────────────────────────────────────────
function buildTicker(){
  const sorted = [...data].sort((a,b)=>a.name.localeCompare(b.name));
  let html = '';
  for(let i=0;i<2;i++) sorted.forEach(c=>{
    const cl = c.chg_gas>0?'ti-up':c.chg_gas<0?'ti-dn':'ti-fl';
    const ar = c.chg_gas>0?'▲':c.chg_gas<0?'▼':'—';
    html += `<span class="ti"><span class="ti-n">${c.name}</span>`+
            `<span class="ti-p">$${c.gas_usd_now.toFixed(3)}</span>`+
            `<span style="color:var(--txt3);font-size:.62rem">${c.currency}</span>`+
            `<span class="${cl}">${ar}${Math.abs(c.chg_gas).toFixed(1)}%</span></span>`;
  });
  document.getElementById('tickerTrack').innerHTML = html;
}

// ── HERO KPIS ────────────────────────────────────────────────────────────────
function buildHeroKpis(){
  const sorted = [...data].sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  const hi = sorted[0], lo = sorted[sorted.length-1];
  const sg = [...data].sort((a,b)=>b.chg_gas-a.chg_gas)[0];
  const av = afAvg();
  document.getElementById('hKpis').innerHTML = [
    {l:'Highest Gas',v:`$${hi.gas_usd_now.toFixed(3)}`,s:hi.name,c:'var(--red)'},
    {l:'Lowest Gas', v:`$${lo.gas_usd_now.toFixed(3)}`,s:lo.name,c:'var(--grn)'},
    {l:'Africa Avg', v:`$${av.toFixed(3)}`,s:'54 nations USD/L',c:'var(--acc)'},
    {l:'Biggest Surge',v:`+${sg.chg_gas.toFixed(1)}%`,s:sg.name,c:'var(--red)'},
  ].map(k=>`<div class="hkpi">
    <div class="hkpi-l">${k.l}</div>
    <div class="hkpi-v" style="color:${k.c}">${k.v}</div>
    <div class="hkpi-s">${k.s}</div>
  </div>`).join('');
}

// ── REGION CARDS ─────────────────────────────────────────────────────────────
function buildRegCards(){
  const maxA = Math.max(...REGIONS.map(r=>rAvg(r)));
  document.getElementById('regStrip').innerHTML = REGIONS.map(r=>{
    const abbr=R_ABR[r], col=R_COL[r];
    const avg=rAvg(r), n=data.filter(c=>c.region===r).length;
    const avgChg=rAvgF(r,'chg_gas');
    const pct=(avg/maxA*100).toFixed(0);
    return `<div class="rc rc-${abbr}">
      <div class="rc-l">${r}</div>
      <div class="rc-p" style="color:${col}">$${avg.toFixed(3)}</div>
      <div class="rc-m">${n} countries · gasoline avg · ${avgChg>=0?'+':''}${avgChg.toFixed(1)}% Jan→Mar</div>
      <div class="rc-bar"><div class="rc-bf" style="width:${pct}%;background:${col}"></div></div>
    </div>`;
  }).join('');
}
function rAvg(r){const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+c.gas_usd_now,0)/cs.length:0}
function rAvgF(r,f){const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+c[f],0)/cs.length:0}

// ── LINE CHART ───────────────────────────────────────────────────────────────
function buildLineChart(){
  const kd = KEY.map(n=>data.find(c=>c.name===n)).filter(Boolean);
  const ctx = document.getElementById('lineChart').getContext('2d');
  lineInst = new Chart(ctx,{
    type:'line',
    data:{
      labels:D.week_labels,   // full 12-week labels Jan 01 → Mar 20
      datasets:kd.map((c,i)=>({
        label:c.name,
        data:c.gas_usd_w,     // full weekly series
        borderColor:PAL[i],
        backgroundColor:PAL[i]+'18',
        borderWidth:2, pointRadius:2, pointHoverRadius:6, tension:.45,
        fill:false,
      }))
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{position:'bottom',labels:{boxWidth:10,padding:12,font:{size:10}}},
        tooltip:{callbacks:{
          title: items => `Week of ${items[0].label}`,
          label: ctx  => `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(3)}/L`
        }}
      },
      scales:{
        x:{grid:{color:'rgba(30,45,66,.3)'},ticks:{font:{size:9},maxTicksLimit:13}},
        y:{grid:{color:'rgba(30,45,66,.3)'},ticks:{callback:v=>`$${v.toFixed(3)}`}}
      }
    }
  });
}

function updateLineChart(){
  const kd = KEY.map(n=>data.find(c=>c.name===n)).filter(Boolean);
  const isUsd = lineCur==='usd';
  const seriesData = c => lineCur==='usd' ? c.gas_usd_w : lineCur==='loc' ? c.gas_loc_w : c.die_usd_w;
  lineInst.data.datasets = kd.map((c,i)=>({
    label:c.name,
    data: seriesData(c),
    borderColor:PAL[i], backgroundColor:PAL[i]+'18',
    borderWidth:2, pointRadius:2, pointHoverRadius:6, tension:.45, fill:false,
  }));
  lineInst.options.scales.y.ticks.callback = isUsd
    ? v=>`$${v.toFixed(3)}`
    : v=>v.toFixed(2);
  lineInst.options.plugins.tooltip.callbacks = {
    title: items => `Week of ${items[0].label}`,
    label: ctx => {
      return isUsd
        ? `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(3)} USD/L`
        : `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)} Local/L`;
    }
  };
  lineInst.update('none');
}

// ── BAR CHART ────────────────────────────────────────────────────────────────
function buildBarChart(){
  const ctx = document.getElementById('barChart').getContext('2d');
  barInst = new Chart(ctx,{
    type:'bar',
    data:{
      labels:REGIONS.map(r=>r.replace(' Africa','')),
      datasets:[
        {label:'Gasoline USD/L',data:REGIONS.map(r=>+rAvg(r).toFixed(3)),
         backgroundColor:REGIONS.map((_,i)=>PAL[i]),borderRadius:5},
        {label:'Diesel USD/L', data:REGIONS.map(r=>+rAvgF(r,'die_usd_now').toFixed(3)),
         backgroundColor:REGIONS.map((_,i)=>PAL[i]+'60'),borderRadius:5}
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:12,font:{size:10}}}},
      scales:{
        x:{grid:{color:'rgba(30,45,66,.4)'},ticks:{font:{size:10}}},
        y:{grid:{color:'rgba(30,45,66,.4)'},ticks:{callback:v=>`$${v.toFixed(3)}`}}
      }
    }
  });
}

// ── RANKINGS ─────────────────────────────────────────────────────────────────
function buildRankings(type){
  const sorted=[...data].sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  const list  = type==='top' ? sorted.slice(0,10) : sorted.slice(-10).reverse();
  const cur   = type==='top' ? topCur : botCur;
  const col   = type==='top' ? 'var(--red)' : 'var(--grn)';
  document.getElementById(type+'List').innerHTML = list.map((c,i)=>`
    <div class="ri r${i+1}" onclick="openModal('${esc(c.name)}')">
      <span class="ri-n">${i+1}</span>
      <div class="ri-info">
        <div class="ri-nm">${c.name}</div>
        <div class="ri-sub">${c.region}</div>
      </div>
      <div class="ri-right">
        <div class="ri-price" style="color:${col}">
          ${cur==='loc'?`${c.gas_loc_now.toFixed(2)} ${c.currency}` : `$${c.gas_usd_now.toFixed(3)}`}
        </div>
        <div class="ri-local">
          ${cur==='loc'?`$${c.gas_usd_now.toFixed(3)}`:`${c.gas_loc_now.toFixed(2)} ${c.currency}`}
        </div>
      </div>
    </div>`).join('');
}

// ── FX GRID ──────────────────────────────────────────────────────────────────
function buildFxGrid(){
  const entries = Object.entries(FX).sort((a,b)=>a[0].localeCompare(b[0]));
  document.getElementById('fxGrid').innerHTML = entries.map(([code,rate])=>{
    const fmt = rate>=1000?'0,0':rate>=10?'0.00':'0.0000';
    const inv  = (1/rate);
    const invFmt = inv<0.001?inv.toFixed(6):inv<0.1?inv.toFixed(4):inv.toFixed(4);
    return `<div class="fx-item">
      <span class="fx-code">${code}</span>
      <div class="fx-val">
        <span class="fx-rate">${rate.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:rate>=1000?0:4})}</span>
        <span class="fx-inv">$1 = ${invFmt} ${code}</span>
      </div>
    </div>`;
  }).join('');
}

// ── TABLE ────────────────────────────────────────────────────────────────────
function buildTableHead(){
  const cols=[];
  cols.push({l:'Country',k:'name'},{l:'Region',k:null},{l:'Currency',k:null},{l:'FX Rate',k:'fx'});
  if(tblCur==='usd'||tblCur==='both'){
    cols.push({l:'Gas USD/L',k:'gas'},{l:'Die USD/L',k:'die'},{l:'LPG USD/kg',k:null});
  }
  if(tblCur==='loc'||tblCur==='both'){
    cols.push({l:'Gas Local/L',k:null},{l:'Die Local/L',k:null},{l:'LPG Local/kg',k:null});
  }
  cols.push({l:'Jan→Mar %',k:'chg'},{l:'Level',k:null},
            {l:'Jan',k:null},{l:'Feb',k:null},{l:'Mar',k:null});

  document.getElementById('tHead').innerHTML = cols.map(c=>`
    <th ${c.k?`data-k="${c.k}"`:''} class="${sortKey===c.k?'sorted':''}">${c.l}</th>`
  ).join('');

  document.querySelectorAll('#tHead th[data-k]').forEach(th=>{
    th.addEventListener('click',()=>{
      sortKey=th.dataset.k;
      document.getElementById('sortSel').value=sortKey+'_desc';
      renderTable();
    });
  });
}

function renderTable(){
  let d=[...filtered];
  const q=document.getElementById('srchInp').value.toLowerCase();
  if(q) d=d.filter(c=>c.name.toLowerCase().includes(q)||c.region.toLowerCase().includes(q)||c.currency.toLowerCase().includes(q));

  const sv=document.getElementById('sortSel').value;
  if(sv==='name')     d.sort((a,b)=>a.name.localeCompare(b.name));
  if(sv==='gas_desc') d.sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  if(sv==='gas_asc')  d.sort((a,b)=>a.gas_usd_now-b.gas_usd_now);
  if(sv==='chg_desc') d.sort((a,b)=>b.chg_gas-a.chg_gas);
  if(sv==='chg_asc')  d.sort((a,b)=>a.chg_gas-b.chg_gas);
  if(sv==='fx_desc')  d.sort((a,b)=>(FX[b.currency]||1)-(FX[a.currency]||1));

  document.getElementById('cntBadge').textContent=`${d.length} COUNTRIES`;
  const maxP=Math.max(...data.map(c=>c.gas_usd_now));
  const av=afAvg();

  document.getElementById('tBody').innerHTML=d.map(c=>{
    const abrv=R_ABR[c.region]||'na';
    const fx=FX[c.currency]||1;
    const chgCl=c.chg_gas>0.5?'up':c.chg_gas<-0.5?'dn':'fl';
    const chgAr=c.chg_gas>0.5?'▲':c.chg_gas<-0.5?'▼':'—';
    const levCl=c.gas_usd_now>1.3?'lev-h':c.gas_usd_now>0.8?'lev-m':'lev-l';
    const levLb=c.gas_usd_now>1.3?'● HIGH':c.gas_usd_now>0.8?'● MID':'● LOW';
    const bw=Math.round(c.gas_usd_now/maxP*100);
    const diff=c.gas_usd_now-av;
    const fxFmt=fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx.toFixed(fx>=10?2:4);

    let cells=`
      <td><span class="cn">${c.name}</span></td>
      <td><span class="rt rt-${abrv}">${c.region}</span></td>
      <td><span class="cur-tag">${c.currency}</span></td>
      <td><span class="fx-tag">${fxFmt}</span></td>`;

    if(tblCur==='usd'||tblCur==='both') cells+=`
      <td><span class="mono">$${c.gas_usd_now.toFixed(3)}</span>
          <div class="pbar-w"><div class="pbar" style="width:${bw}%"></div></div></td>
      <td><span class="mono">$${c.die_usd_now.toFixed(3)}</span></td>
      <td><span class="mono">$${c.lpg_usd_now.toFixed(3)}</span></td>`;

    if(tblCur==='loc'||tblCur==='both') cells+=`
      <td><span class="mono" style="color:var(--cyn)">${c.gas_loc_now.toFixed(2)}</span></td>
      <td><span class="mono" style="color:var(--cyn)">${c.die_loc_now.toFixed(2)}</span></td>
      <td><span class="mono" style="color:var(--cyn)">${c.lpg_loc_now.toFixed(2)}</span></td>`;

    cells+=`
      <td><span class="${chgCl}">${chgAr} ${Math.abs(c.chg_gas).toFixed(2)}%</span></td>
      <td><span class="${levCl}">${levLb}</span></td>
      <td class="mono" style="font-size:.7rem;color:var(--txt3)">$${c.gas_usd[0].toFixed(3)}</td>
      <td class="mono" style="font-size:.7rem;color:var(--txt3)">$${c.gas_usd[1].toFixed(3)}</td>
      <td class="mono" style="font-size:.75rem">$${c.gas_usd[2].toFixed(3)}</td>`;

    return `<tr onclick="openModal('${esc(c.name)}')">${cells}</tr>`;
  }).join('');
}

// ── MODAL ────────────────────────────────────────────────────────────────────
function openModal(name){
  const c=data.find(d=>d.name===name); if(!c) return;
  modalCtry=c;
  const fx=FX[c.currency]||1;
  const av=afAvg(); const diff=c.gas_usd_now-av;
  document.getElementById('mTitle').textContent=`⛽ ${c.name}`;
  document.getElementById('mMeta').textContent=`${c.region} · ${c.currency} · ${c.octane} RON Octane`;
  const fxFmt=fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx.toFixed(4);
  document.getElementById('mFx').textContent=
    `Exchange Rate: 1 USD = ${fxFmt} ${c.currency}  ·  1 ${c.currency} = $${(1/fx).toFixed(fx>=1000?6:4)}`;

  document.getElementById('mGrid').innerHTML=[
    {l:`Gasoline USD/L`,  v:`$${c.gas_usd_now.toFixed(3)}`,     col:'var(--acc)'},
    {l:`Gas ${c.currency}/L`, v:`${c.gas_loc_now.toFixed(2)}`,  col:'var(--cyn)'},
    {l:`Diesel USD/L`,   v:`$${c.die_usd_now.toFixed(3)}`,      col:'var(--blu)'},
    {l:`Die ${c.currency}/L`,v:`${c.die_loc_now.toFixed(2)}`,   col:'var(--cyn)'},
    {l:`LPG USD/kg`,     v:`$${c.lpg_usd_now.toFixed(3)}`,      col:'var(--pur)'},
    {l:`Jan→Mar Change`, v:`${c.chg_gas>=0?'+':''}${c.chg_gas.toFixed(2)}%`,
     col:c.chg_gas>0?'var(--red)':'var(--grn)'},
  ].map(s=>`<div class="m-stat">
    <div class="m-sl">${s.l}</div>
    <div class="m-sv" style="color:${s.col}">${s.v}</div>
  </div>`).join('');

  // reset tabs
  document.querySelectorAll('.mtab').forEach(b=>{b.classList.toggle('on',b.dataset.tab==='gas')});
  modalTab='gas';
  buildModalChart();
  document.getElementById('modalOv').classList.add('open');
}

function buildModalChart(){
  if(mInst){mInst.destroy();mInst=null;}
  const c=modalCtry; if(!c) return;
  const isGas=modalTab==='gas';
  const usdData = isGas ? c.gas_usd_w : c.die_usd_w;   // full 12-week series
  const locData = isGas ? c.gas_loc_w : c.die_loc_w;
  const ctx=document.getElementById('mChart').getContext('2d');
  mInst=new Chart(ctx,{
    type:'line',
    data:{
      labels: WEEK_LABELS,
      datasets:[
        {label:`USD/L`,data:usdData,
         borderColor:'#f59e0b',backgroundColor:'rgba(245,158,11,.1)',
         borderWidth:2.5,pointRadius:3,pointHoverRadius:6,
         tension:.4,fill:true,yAxisID:'y1'},
        {label:`${c.currency}/L`,data:locData,
         borderColor:'#06b6d4',backgroundColor:'transparent',
         borderWidth:2,pointRadius:2,pointHoverRadius:5,
         tension:.4,yAxisID:'y2'},
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{position:'bottom',labels:{boxWidth:10,padding:10,font:{size:10}}},
        tooltip:{callbacks:{
          title: items => `Week of ${items[0].label}`,
        }}
      },
      scales:{
        y1:{position:'left',grid:{color:'rgba(30,45,66,.4)'},
            ticks:{callback:v=>`$${v.toFixed(3)}`}},
        y2:{position:'right',grid:{display:false},
            ticks:{callback:v=>v.toFixed(v>=1000?0:v>=10?1:2)}}
      }
    }
  });
}

function closeModal(){document.getElementById('modalOv').classList.remove('open')}
document.getElementById('mxBtn').addEventListener('click',closeModal);
document.getElementById('modalOv').addEventListener('click',e=>{if(e.target.id==='modalOv')closeModal()});
document.getElementById('mTabs').addEventListener('click',e=>{
  const btn=e.target.closest('.mtab'); if(!btn) return;
  document.querySelectorAll('.mtab').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on'); modalTab=btn.dataset.tab; buildModalChart();
});

// ── WIRE EVENTS ──────────────────────────────────────────────────────────────
function wire(){
  // Region filter buttons
  document.querySelectorAll('.fb').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.fb').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on');
      region=btn.dataset.r;
      filtered=region==='all'?[...data]:data.filter(c=>c.region===region);
      renderTable();
    });
  });

  // Search & sort
  document.getElementById('srchInp').addEventListener('input',renderTable);
  document.getElementById('sortSel').addEventListener('change',e=>{
    sortKey=e.target.value.replace('_desc','').replace('_asc','');
    renderTable();
  });

  // Table currency toggle
  document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on'); tblCur=btn.dataset.v;
      buildTableHead(); renderTable();
    });
  });

  // Line chart toggle
  document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on'); lineCur=btn.dataset.v; updateLineChart();
    });
  });

  // Rankings toggles
  ['top','bot'].forEach(type=>{
    document.getElementById(type+'Tog').querySelectorAll('.tog-btn').forEach(btn=>{
      btn.addEventListener('click',()=>{
        document.getElementById(type+'Tog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
        btn.classList.add('on');
        if(type==='top') topCur=btn.dataset.v; else botCur=btn.dataset.v;
        buildRankings(type);
      });
    });
  });
}

// ── LIVE SIMULATION ──────────────────────────────────────────────────────────
function liveTick(){
  // Nudge 2–4 countries slightly to simulate real-time price changes
  const n=Math.floor(Math.random()*3)+2;
  for(let i=0;i<n;i++){
    const c=data[Math.floor(Math.random()*data.length)];
    const noise=(Math.random()-.5)*.003;
    c.gas_usd_now=Math.max(.01,+(c.gas_usd_now+noise).toFixed(4));
    c.die_usd_now=Math.max(.01,+(c.die_usd_now+noise*.9).toFixed(4));
    const fx=FX[c.currency]||1;
    c.gas_loc_now=+(c.gas_usd_now*fx).toFixed(2);
    c.die_loc_now=+(c.die_usd_now*fx).toFixed(2);
    // Keep last weekly point in sync with live value
    if(c.gas_usd_w) c.gas_usd_w[c.gas_usd_w.length-1]=c.gas_usd_now;
    if(c.gas_loc_w) c.gas_loc_w[c.gas_loc_w.length-1]=c.gas_loc_now;
    if(c.die_usd_w) c.die_usd_w[c.die_usd_w.length-1]=c.die_usd_now;
    if(c.die_loc_w) c.die_loc_w[c.die_loc_w.length-1]=c.die_loc_now;
  }
  buildHeroKpis(); buildRegCards();
  buildRankings('top'); buildRankings('bot');
  renderTable(); updateHeader();
}

// ── UTILITY ──────────────────────────────────────────────────────────────────
function esc(s){return s.replace(/'/g,"\\'")}
</script>
</body>
</html>"""


def build(payload: dict, out_path: str):
    """Inject data payload into template and write HTML file."""
    js = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    html = TEMPLATE.replace('__DATA__', js)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    kb = len(html) // 1024
    print(f"   ✅  Dashboard → {out_path}  ({kb} KB)")
