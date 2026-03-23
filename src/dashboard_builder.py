"""
dashboard_builder.py — Africa Fuel Price Tracker
Fully responsive: Desktop + Tablet + Mobile
AfDB palette: #00A86A green · #F5A300 gold · #07111E navy
Font: Space Grotesk display + JetBrains Mono data
"""
import json

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AfricaFuelWatch 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
/* ═══════════════════════════ TOKENS ═══════════════════════════ */
:root {
  --g0:#00A86A; --g1:#00CC85; --g2:#00E695; --g3:#E8F9F2;
  --gold:#F5A300; --gold2:#FFBE33; --gold3:#FFF4D6;
  --red:#E8394A; --red2:#FF6B78; --blue:#1A8FD8; --cyan:#00C4CF;
  --amber:#E87C1A; --purple:#8B5CF6;
  --bg:#07111E; --bg1:#0B1826; --bg2:#0E1E2E;
  --s1:#132435; --s2:#1A3347; --s3:#214059; --s4:#2D5A7A;
  --t1:#E8EEF4; --t2:#9EC8E0; --t3:#5A8FAF; --t4:#2D5A7A;
  --r4:4px; --r8:8px; --r12:12px; --r16:16px; --r24:24px; --r99:99px;
  --sh: 0 4px 24px rgba(0,0,0,.4);
  --sh-g: 0 4px 24px rgba(0,168,106,.25);
}

/* ═══════════════════════════ RESET ═══════════════════════════ */
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;font-size:16px}
body{background:var(--bg);color:var(--t1);font-family:'Outfit',sans-serif;
  overflow-x:hidden;min-height:100vh;line-height:1.5}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg1)}
::-webkit-scrollbar-thumb{background:var(--s3);border-radius:99px}
a{color:inherit;text-decoration:none}
button{cursor:pointer;font-family:'Outfit',sans-serif;border:none;outline:none}
input,select{font-family:'Outfit',sans-serif;outline:none}
canvas{display:block}

/* ═══════════════════════════ LAYOUT ═══════════════════════════ */
.page{display:flex;flex-direction:column;min-height:100vh}
.wrap{width:100%;max-width:1440px;margin:0 auto;padding:0 1.5rem}

/* ═══════════════════════════ NAV ═══════════════════════════ */
nav{
  position:sticky;top:0;z-index:500;height:56px;
  background:rgba(7,17,30,.96);backdrop-filter:blur(24px);
  border-bottom:1px solid var(--s2);
}
.nav-inner{
  height:100%;display:flex;align-items:center;
  justify-content:space-between;gap:1rem;
}
.nav-brand{display:flex;align-items:center;gap:.6rem;flex-shrink:0}
.brand-icon{
  width:34px;height:34px;border-radius:10px;
  background:linear-gradient(135deg,var(--g0),#007A4D);
  display:flex;align-items:center;justify-content:center;
  font-size:1rem;box-shadow:var(--sh-g);flex-shrink:0;
}
.brand-name{font-size:.9rem;font-weight:800;letter-spacing:-.02em}
.brand-name span{color:var(--g0)}
.brand-tag{
  font-size:.6rem;font-weight:600;letter-spacing:.06em;
  color:var(--g0);background:rgba(0,168,106,.1);
  border:1px solid rgba(0,168,106,.25);border-radius:var(--r99);
  padding:.12rem .5rem;text-transform:uppercase;
}
.nav-right{display:flex;align-items:center;gap:.6rem}
.nav-meta{
  font-size:.67rem;color:var(--t3);
  font-family:'JetBrains Mono',monospace;
  display:none;
}
@media(min-width:640px){.nav-meta{display:block}}
.live-dot{
  display:flex;align-items:center;gap:.35rem;
  background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.3);
  border-radius:var(--r99);padding:.2rem .6rem;
  font-size:.65rem;font-weight:600;color:var(--g0);
  font-family:'JetBrains Mono',monospace;letter-spacing:.02em;
}
.pulse{width:6px;height:6px;border-radius:50%;background:var(--g0);
  animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.btn-dl-nav{
  display:flex;align-items:center;gap:.4rem;
  padding:.32rem .75rem;border-radius:var(--r8);
  background:var(--g0);color:#fff;
  font-size:.73rem;font-weight:700;transition:.15s;
  white-space:nowrap;
}
.btn-dl-nav:hover{background:var(--g1);transform:translateY(-1px)}
.btn-dl-nav svg{flex-shrink:0}

/* ═══════════════════════════ TICKER ═══════════════════════════ */
.ticker{
  background:var(--bg1);border-bottom:1px solid var(--s2);
  height:32px;overflow:hidden;display:flex;align-items:center;
  flex-shrink:0;
}
.ticker-lbl{
  flex-shrink:0;padding:0 .75rem;height:100%;
  display:flex;align-items:center;gap:.4rem;
  background:rgba(0,168,106,.08);border-right:1px solid var(--s2);
  font-size:.62rem;font-weight:700;letter-spacing:.08em;
  color:var(--g0);text-transform:uppercase;white-space:nowrap;
}
.ticker-body{flex:1;overflow:hidden;position:relative}
.ticker-body::before,.ticker-body::after{
  content:'';position:absolute;top:0;bottom:0;width:32px;z-index:2;pointer-events:none;
}
.ticker-body::before{left:0;background:linear-gradient(90deg,var(--bg1),transparent)}
.ticker-body::after{right:0;background:linear-gradient(270deg,var(--bg1),transparent)}
.ticker-track{
  display:flex;align-items:center;white-space:nowrap;
  animation:ticker 120s linear infinite;
}
.ticker-track:hover{animation-play-state:paused}
@keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ti{
  display:inline-flex;align-items:center;gap:.45rem;
  padding:0 1rem;height:32px;
  border-right:1px solid rgba(33,64,89,.5);font-size:.7rem;
}
.ti-n{font-weight:600}
.ti-p{font-family:'JetBrains Mono',monospace;color:var(--g0);font-weight:500}
.ti-c{font-size:.6rem;color:var(--t4)}
.up{color:var(--red)}.dn{color:var(--g1)}.fl{color:var(--t4)}

/* ═══════════════════════════ MAIN ═══════════════════════════ */
main{flex:1;padding:1.25rem 0 3rem}

/* ═══════════════════════════ HERO ═══════════════════════════ */
.hero{
  background:linear-gradient(135deg,#0B1E31 0%,#0E2A3D 60%,#0A1E2D 100%);
  border:1px solid var(--s2);border-radius:var(--r16);
  padding:1.5rem;margin-bottom:1.25rem;position:relative;overflow:hidden;
}
.hero-glow{
  position:absolute;top:-80px;right:-80px;width:300px;height:300px;
  border-radius:50%;
  background:radial-gradient(circle,rgba(0,168,106,.07) 0%,transparent 70%);
  pointer-events:none;
}
.hero-grid{display:grid;grid-template-columns:1fr;gap:1.25rem}
@media(min-width:768px){.hero-grid{grid-template-columns:1fr auto;align-items:start}}
.hero-title{
  font-size:clamp(1.3rem,4vw,1.8rem);font-weight:900;line-height:1.15;
  margin-bottom:.5rem;letter-spacing:-.03em;
  background:linear-gradient(135deg,#E8EEF4 0%,#9EC8E0 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.hero-sub{
  font-size:.85rem;color:var(--t2);line-height:1.6;
  max-width:580px;margin-bottom:1rem;
}
.hero-tags{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1.1rem}
.tag{
  display:inline-flex;align-items:center;gap:.3rem;
  padding:.22rem .65rem;border-radius:var(--r99);font-size:.68rem;font-weight:600;
}
.tag-g{background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.2);color:var(--g0)}
.tag-y{background:rgba(245,163,0,.1);border:1px solid rgba(245,163,0,.2);color:var(--gold)}
.tag-b{background:rgba(26,143,216,.1);border:1px solid rgba(26,143,216,.2);color:var(--blue)}
.btn-dl{
  display:inline-flex;align-items:center;gap:.6rem;
  padding:.65rem 1.35rem;border-radius:var(--r12);
  background:linear-gradient(135deg,#007A4D,var(--g0));
  color:#fff;font-size:.85rem;font-weight:700;
  box-shadow:var(--sh-g);transition:.2s;
}
.btn-dl:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,168,106,.4)}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:.6rem}
.kpi{
  background:rgba(7,17,30,.7);border:1px solid var(--s2);
  border-radius:var(--r12);padding:.85rem 1rem;
}
.kpi-label{font-size:.62rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;color:var(--t3);margin-bottom:.25rem}
.kpi-value{font-size:1.2rem;font-weight:900;font-family:'JetBrains Mono',monospace;line-height:1.1}
.kpi-sub{font-size:.67rem;color:var(--t3);margin-top:.2rem;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* ═══════════════════════════ SECTION ═══════════════════════════ */
.sec-head{
  display:flex;align-items:center;justify-content:space-between;
  gap:.75rem;flex-wrap:wrap;margin-bottom:.85rem;
}
.sec-title{
  font-size:.72rem;font-weight:800;text-transform:uppercase;
  letter-spacing:.08em;color:var(--t3);
  display:flex;align-items:center;gap:.5rem;
}
.sec-pill{
  background:rgba(0,168,106,.1);border:1px solid rgba(0,168,106,.2);
  color:var(--g0);padding:.1rem .48rem;border-radius:var(--r99);
  font-size:.6rem;font-weight:800;letter-spacing:.04em;
}

/* ═══════════════════════════ REGION STRIP ═══════════════════════════ */
.reg-strip{
  display:grid;gap:.6rem;margin-bottom:1.25rem;
  grid-template-columns:repeat(2,1fr);
}
@media(min-width:480px){.reg-strip{grid-template-columns:repeat(3,1fr)}}
@media(min-width:900px){.reg-strip{grid-template-columns:repeat(5,1fr)}}
.rc{
  background:var(--s1);border:1px solid var(--s2);
  border-radius:var(--r12);padding:.85rem 1rem;
  position:relative;overflow:hidden;transition:.2s;
}
.rc:hover{border-color:var(--s3);transform:translateY(-2px);box-shadow:var(--sh)}
.rc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.rc-na::before{background:var(--gold)}
.rc-wa::before{background:var(--g0)}
.rc-ea::before{background:var(--blue)}
.rc-ca::before{background:var(--amber)}
.rc-sa::before{background:var(--red)}
.rc-name{font-size:.62rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;color:var(--t3);margin-bottom:.4rem}
.rc-price{font-size:1.2rem;font-weight:900;font-family:'JetBrains Mono',monospace;line-height:1;margin-bottom:.25rem}
.rc-count{font-size:.63rem;color:var(--t4);margin-bottom:.5rem}
.rc-bar{background:var(--bg);border-radius:99px;height:3px;overflow:hidden;margin-bottom:.35rem}
.rc-fill{height:100%;border-radius:99px;transition:width .8s ease}
.rc-chg{font-size:.67rem;font-weight:600}

/* ═══════════════════════════ CARD ═══════════════════════════ */
.card{
  background:var(--s1);border:1px solid var(--s2);
  border-radius:var(--r16);padding:1.1rem 1.15rem;margin-bottom:1.1rem;
}
.card-head{
  font-size:.71rem;font-weight:800;text-transform:uppercase;
  letter-spacing:.05em;color:var(--t3);
  margin-bottom:.9rem;display:flex;align-items:center;
  justify-content:space-between;gap:.5rem;flex-wrap:wrap;
}

/* ═══════════════════════════ CHARTS LAYOUT ═══════════════════════════ */
.chart-row{display:grid;grid-template-columns:1fr;gap:1.1rem;margin-bottom:1.1rem}
@media(min-width:900px){.chart-row{grid-template-columns:3fr 2fr}}
.chart-box{height:260px;position:relative}
@media(min-width:640px){.chart-box{height:300px}}

/* ═══════════════════════════ TOGGLES ═══════════════════════════ */
.tog{
  display:inline-flex;background:var(--bg);
  border:1px solid var(--s2);border-radius:var(--r8);
  padding:2px;gap:2px;flex-wrap:wrap;
}
.tog-btn{
  padding:.26rem .7rem;border-radius:6px;background:transparent;
  color:var(--t3);font-size:.7rem;font-weight:600;
  font-family:'Outfit',sans-serif;transition:.12s;white-space:nowrap;
}
.tog-btn.on{background:var(--g0);color:#fff;box-shadow:0 2px 8px rgba(0,168,106,.3)}
.tog-btn:hover:not(.on){background:var(--s2);color:var(--t1)}

/* ═══════════════════════════ RANKINGS ═══════════════════════════ */
.rank-row{display:grid;grid-template-columns:1fr;gap:1.1rem;margin-bottom:1.1rem}
@media(min-width:640px){.rank-row{grid-template-columns:1fr 1fr}}
.rank-list{display:flex;flex-direction:column;gap:.3rem}
.rank-item{
  display:flex;align-items:center;gap:.65rem;
  padding:.5rem .65rem;border-radius:var(--r8);
  border:1px solid transparent;cursor:pointer;transition:.12s;
}
.rank-item:hover{background:var(--bg1);border-color:var(--s2)}
.rank-n{
  width:24px;height:24px;border-radius:6px;
  background:var(--bg);border:1px solid var(--s2);
  display:flex;align-items:center;justify-content:center;
  font-size:.67rem;font-weight:700;color:var(--t3);flex-shrink:0;
}
.rank-item:nth-child(-n+3) .rank-n{
  background:rgba(245,163,0,.1);border-color:rgba(245,163,0,.3);color:var(--gold);
}
.rank-name{font-size:.78rem;font-weight:600;flex:1;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rank-right{display:flex;flex-direction:column;align-items:flex-end;gap:.12rem;flex-shrink:0}
.rank-price{font-family:'JetBrains Mono',monospace;font-size:.78rem;font-weight:600}
.rank-bar-bg{height:2px;background:var(--bg);border-radius:99px;width:60px}
.rank-bar-fg{height:100%;border-radius:99px;transition:width .4s}

/* ═══════════════════════════ FX PANEL ═══════════════════════════ */
.fx-wrap{
  display:grid;gap:.45rem;
  grid-template-columns:repeat(2,1fr);
  max-height:240px;overflow-y:auto;
}
@media(min-width:480px){.fx-wrap{grid-template-columns:repeat(3,1fr)}}
@media(min-width:768px){.fx-wrap{grid-template-columns:repeat(4,1fr)}}
@media(min-width:1100px){.fx-wrap{grid-template-columns:repeat(6,1fr)}}
.fx-card{
  background:var(--bg1);border:1px solid var(--s2);
  border-radius:var(--r8);padding:.5rem .65rem;
  display:flex;align-items:center;justify-content:space-between;gap:.4rem;
}
.fx-code{font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:600;color:var(--g0)}
.fx-rate{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--t1);font-weight:500}
.fx-inv{font-size:.58rem;color:var(--t4);display:block;margin-top:.08rem}

/* ═══════════════════════════ TABLE SECTION ═══════════════════════════ */
.tbl-controls{
  display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;
  padding-bottom:.75rem;border-bottom:1px solid var(--s2);margin-bottom:.75rem;
}
.fb{
  padding:.24rem .7rem;border-radius:var(--r99);font-size:.7rem;font-weight:600;
  border:1px solid var(--s2);background:transparent;color:var(--t3);
  font-family:'Outfit',sans-serif;transition:.12s;white-space:nowrap;
}
.fb.on{background:var(--g0);border-color:var(--g0);color:#fff}
.fb:hover:not(.on){border-color:var(--s3);color:var(--t1)}
.ctrl-right{display:flex;align-items:center;gap:.5rem;margin-left:auto;flex-wrap:wrap}
.sort-sel{
  padding:.24rem .6rem;border-radius:var(--r8);font-size:.7rem;
  border:1px solid var(--s2);background:var(--bg);color:var(--t1);
  font-family:'Outfit',sans-serif;transition:.12s;
  appearance:none;-webkit-appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%235A8FAF' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right .5rem center;
  padding-right:1.75rem;
}
.sort-sel:focus{border-color:var(--g0)}
.srch-wrap{position:relative}
.srch-ico{
  position:absolute;left:.55rem;top:50%;transform:translateY(-50%);
  color:var(--t4);pointer-events:none;font-size:.8rem;
}
.srch{
  padding:.24rem .6rem .24rem 1.75rem;border-radius:var(--r8);font-size:.7rem;
  border:1px solid var(--s2);background:var(--bg);color:var(--t1);
  font-family:'Outfit',sans-serif;width:150px;transition:.2s;
}
@media(min-width:480px){.srch{width:180px}}
.srch:focus{border-color:var(--g0);width:200px}
.srch::placeholder{color:var(--t4)}
.tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tbl-wrap::-webkit-scrollbar{height:4px}
table{width:100%;border-collapse:collapse;font-size:.76rem;min-width:600px}
thead th{
  background:var(--bg);border-bottom:2px solid var(--s2);
  padding:.45rem .65rem;font-size:.64rem;font-weight:700;
  text-transform:uppercase;letter-spacing:.04em;color:var(--t3);
  text-align:left;white-space:nowrap;cursor:pointer;
  position:sticky;top:0;z-index:2;user-select:none;
}
thead th:hover{color:var(--g0)}
thead th.sorted{color:var(--g0);border-bottom-color:var(--g0)}
tbody tr{border-bottom:1px solid rgba(26,51,71,.4);cursor:pointer;transition:.1s}
tbody tr:hover{background:rgba(0,168,106,.04)}
td{padding:.45rem .65rem;white-space:nowrap;vertical-align:middle}
.cn{font-weight:700}
.rt{font-size:.61rem;font-weight:600;padding:.12rem .45rem;border-radius:var(--r99);border:1px solid}
.rt-na{color:var(--gold);border-color:rgba(245,163,0,.3);background:rgba(245,163,0,.07)}
.rt-wa{color:var(--g0);border-color:rgba(0,168,106,.3);background:rgba(0,168,106,.07)}
.rt-ea{color:var(--blue);border-color:rgba(26,143,216,.3);background:rgba(26,143,216,.07)}
.rt-ca{color:var(--amber);border-color:rgba(232,124,26,.3);background:rgba(232,124,26,.07)}
.rt-sa{color:var(--red);border-color:rgba(232,57,74,.3);background:rgba(232,57,74,.07)}
.cur{
  font-family:'JetBrains Mono',monospace;font-size:.63rem;font-weight:500;
  padding:.1rem .38rem;border-radius:4px;
  background:rgba(0,168,106,.08);color:var(--g0);
  border:1px solid rgba(0,168,106,.18);
}
.mono{font-family:'JetBrains Mono',monospace;font-weight:500}
.up2{color:var(--red);font-weight:700}
.dn2{color:var(--g1);font-weight:700}
.fl2{color:var(--t4)}
.lev-h{color:var(--red);font-size:.63rem;font-weight:800;letter-spacing:.02em}
.lev-m{color:var(--gold);font-size:.63rem;font-weight:800;letter-spacing:.02em}
.lev-l{color:var(--g0);font-size:.63rem;font-weight:800;letter-spacing:.02em}
.pb{height:2px;background:var(--bg);border-radius:99px;margin-top:.18rem;min-width:40px;max-width:70px}
.pb-f{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--g0),var(--blue))}
.cnt-badge{font-family:'JetBrains Mono',monospace;font-size:.67rem;
  font-weight:600;color:var(--g0);background:rgba(0,168,106,.1);
  border:1px solid rgba(0,168,106,.2);border-radius:var(--r99);
  padding:.1rem .5rem;white-space:nowrap}

/* ═══════════════════════════ MODAL ═══════════════════════════ */
.ov{
  display:none;position:fixed;inset:0;z-index:600;
  background:rgba(7,17,30,.88);backdrop-filter:blur(12px);
  align-items:flex-end;justify-content:center;padding:0;
}
@media(min-width:640px){.ov{align-items:center;padding:1.5rem}}
.ov.open{display:flex}
.modal{
  background:var(--s1);border:1px solid var(--s2);
  width:100%;max-width:680px;
  max-height:92vh;overflow-y:auto;
  border-radius:var(--r16) var(--r16) 0 0;
  box-shadow:0 -8px 48px rgba(0,0,0,.6);
}
@media(min-width:640px){.modal{border-radius:var(--r16);box-shadow:var(--sh)}}
.m-bar{
  width:36px;height:4px;background:var(--s3);border-radius:99px;
  margin:10px auto 0;display:block;
}
@media(min-width:640px){.m-bar{display:none}}
.m-head{
  padding:1rem 1.25rem;border-bottom:1px solid var(--s2);
  background:linear-gradient(135deg,#0B1E31,#0E2A3D);
  border-radius:var(--r16) var(--r16) 0 0;
  position:sticky;top:0;z-index:2;
  display:flex;align-items:flex-start;justify-content:space-between;
}
.m-title{font-size:1.05rem;font-weight:800;letter-spacing:-.02em}
.m-sub{font-size:.72rem;color:var(--t2);margin-top:.18rem}
.m-fx{font-size:.66rem;color:var(--g0);font-family:'JetBrains Mono',monospace;margin-top:.3rem}
.m-close{
  width:30px;height:30px;border-radius:8px;
  border:1px solid var(--s2);background:transparent;
  color:var(--t3);font-size:1rem;
  display:flex;align-items:center;justify-content:center;
  transition:.12s;flex-shrink:0;
}
.m-close:hover{background:var(--s2);color:var(--t1)}
.m-body{padding:1rem 1.25rem 1.5rem}
.m-stats{display:grid;grid-template-columns:repeat(2,1fr);gap:.55rem;margin-bottom:1rem}
@media(min-width:400px){.m-stats{grid-template-columns:repeat(3,1fr)}}
.m-stat{background:var(--bg1);border:1px solid var(--s2);border-radius:var(--r12);padding:.7rem .85rem}
.m-sl{font-size:.62rem;color:var(--t3);font-weight:700;text-transform:uppercase;
  letter-spacing:.04em;margin-bottom:.28rem}
.m-sv{font-size:1rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.m-tabs{display:flex;gap:.4rem;margin-bottom:.75rem}
.mtab{
  padding:.28rem .8rem;border-radius:var(--r99);font-size:.72rem;font-weight:600;
  border:1px solid var(--s2);background:transparent;color:var(--t3);
  font-family:'Outfit',sans-serif;transition:.12s;
}
.mtab.on{background:var(--g0);border-color:var(--g0);color:#fff}
.m-chart{height:200px;position:relative}

/* ═══════════════════════════ FOOTER ═══════════════════════════ */
footer{
  border-top:1px solid var(--s2);padding:1rem 1.5rem;
  font-size:.62rem;color:var(--t4);
  font-family:'JetBrains Mono',monospace;
  text-align:center;line-height:1.8;
}
footer strong{color:var(--t3)}

/* ═══════════════════════════ FLOAT BTN ═══════════════════════════ */
.dl-float{
  position:fixed;bottom:1.25rem;right:1.25rem;z-index:400;
  display:flex;align-items:center;gap:.5rem;
  padding:.6rem 1rem;border-radius:var(--r12);
  background:linear-gradient(135deg,#007A4D,var(--g0));
  color:#fff;font-size:.75rem;font-weight:700;
  box-shadow:0 6px 24px rgba(0,168,106,.4);
  animation:floatY 3s ease-in-out infinite;
  transition:.2s;
}
@keyframes floatY{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
.dl-float:hover{animation:none;transform:translateY(-2px) scale(1.04)}
.dl-float-badge{
  position:absolute;top:-7px;right:-7px;
  background:var(--gold);color:#000;border-radius:99px;
  font-size:.52rem;font-weight:900;padding:.1rem .35rem;
  font-family:'JetBrains Mono',monospace;
  border:2px solid var(--bg);letter-spacing:.03em;
}

/* ═══════════════════════════ MOBILE TABLE HINT ═══════════════════════════ */
.tbl-hint{
  display:flex;align-items:center;gap:.4rem;
  font-size:.65rem;color:var(--t4);margin-bottom:.5rem;
  padding:.35rem .6rem;background:rgba(26,143,216,.06);
  border:1px solid rgba(26,143,216,.15);border-radius:var(--r8);
}
@media(min-width:900px){.tbl-hint{display:none}}
</style>
</head>
<body class="page">

<!-- NAV -->
<nav>
  <div class="wrap nav-inner">
    <div class="nav-brand">
      <div class="brand-icon">⛽</div>
      <div>
        <div class="brand-name">Africa<span>Fuel</span>Watch</div>
      </div>
      <div class="brand-tag">2026</div>
    </div>
    <div class="nav-right">
      <div class="nav-meta" id="navMeta">42 countries · Jan–Mar 2026</div>
      <div class="live-dot"><span class="pulse"></span>LIVE</div>
      <a class="btn-dl-nav" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Excel
      </a>
    </div>
  </div>
</nav>

<!-- TICKER -->
<div class="ticker">
  <div class="ticker-lbl">
    <svg width="10" height="10" viewBox="0 0 24 24" fill="var(--g0)"><circle cx="12" cy="12" r="10"/></svg>
    PRICES
  </div>
  <div class="ticker-body">
    <div class="ticker-track" id="tickerTrack"></div>
  </div>
</div>

<!-- MAIN -->
<main>
<div class="wrap">

  <!-- HERO -->
  <div class="hero">
    <div class="hero-glow"></div>
    <div class="hero-grid">
      <div>
        <div class="hero-title">Africa Fuel<br>Price Intelligence</div>
        <div class="hero-sub">Real-time monitoring of gasoline, diesel &amp; LPG across <strong>42 African nations</strong> — in USD and local currency with period-accurate exchange rates.</div>
        <div class="hero-tags">
          <span class="tag tag-g">⛽ 42 Countries</span>
          <span class="tag tag-y">🌍 5 Regions</span>
          <span class="tag tag-b">💱 Live FX Rates</span>
          <span class="tag tag-g">🔄 Weekly Updates</span>
        </div>
        <a class="btn-dl" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Full Report
          <span style="opacity:.75;font-size:.75rem;font-weight:500">XLSX</span>
        </a>
      </div>
      <div class="kpi-grid" id="kpiGrid"></div>
    </div>
  </div>

  <!-- REGIONS -->
  <div class="sec-head">
    <div class="sec-title">Regional Overview <span class="sec-pill">5 REGIONS</span></div>
  </div>
  <div class="reg-strip" id="regStrip"></div>

  <!-- CHARTS -->
  <div class="chart-row">
    <div class="card">
      <div class="card-head">
        Weekly Trend — Key Markets
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

  <!-- RANKINGS -->
  <div class="rank-row">
    <div class="card">
      <div class="card-head">
        🔴 Most Expensive Gas
        <div class="tog" id="topTog">
          <button class="tog-btn on" data-v="usd">USD</button>
          <button class="tog-btn" data-v="loc">Local</button>
        </div>
      </div>
      <div class="rank-list" id="topList"></div>
    </div>
    <div class="card">
      <div class="card-head">
        🟢 Most Affordable Gas
        <div class="tog" id="botTog">
          <button class="tog-btn on" data-v="usd">USD</button>
          <button class="tog-btn" data-v="loc">Local</button>
        </div>
      </div>
      <div class="rank-list" id="botList"></div>
    </div>
  </div>

  <!-- FX -->
  <div class="card">
    <div class="card-head">
      💱 Exchange Rates
      <span style="font-size:.62rem;color:var(--t4);font-weight:400">Local currency per 1 USD</span>
    </div>
    <div class="fx-wrap" id="fxWrap"></div>
  </div>

  <!-- TABLE -->
  <div class="card">
    <div class="card-head">
      All 42 Countries
      <span class="cnt-badge" id="cntBadge">42</span>
    </div>
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
          <option value="name">Name A–Z</option>
          <option value="gas_desc">Gas ↓</option>
          <option value="gas_asc">Gas ↑</option>
          <option value="chg_desc">Change ↑</option>
          <option value="chg_asc">Change ↓</option>
        </select>
        <div class="srch-wrap">
          <span class="srch-ico">🔍</span>
          <input class="srch" id="srchInp" placeholder="Search…">
        </div>
      </div>
    </div>
    <div class="tbl-hint">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--blue)" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
      Scroll right for more columns · Tap a row for details
    </div>
    <div class="tbl-wrap">
      <table>
        <thead><tr id="tHead"></tr></thead>
        <tbody id="tBody"></tbody>
      </table>
    </div>
  </div>

</div><!-- /wrap -->
</main>

<!-- FOOTER -->
<footer>
  <strong>AFRICAFUELWATCH 2026</strong> &nbsp;·&nbsp;
  Source: GlobalPetrolPrices.com · Official Regulatory Portals &nbsp;·&nbsp;
  <span id="ftTime"></span>
</footer>

<!-- MODAL -->
<div class="ov" id="modalOv">
  <div class="modal" id="modalBox">
    <span class="m-bar"></span>
    <div class="m-head">
      <div>
        <div class="m-title" id="mTitle"></div>
        <div class="m-sub" id="mSub"></div>
        <div class="m-fx" id="mFx"></div>
      </div>
      <button class="m-close" id="mClose">✕</button>
    </div>
    <div class="m-body">
      <div class="m-stats" id="mStats"></div>
      <div class="m-tabs" id="mTabs">
        <button class="mtab on" data-tab="gas">⛽ Gasoline</button>
        <button class="mtab" data-tab="die">🚛 Diesel</button>
      </div>
      <div class="m-chart"><canvas id="mChart"></canvas></div>
    </div>
  </div>
</div>

<!-- FLOAT -->
<a class="dl-float" href="africa_fuel_prices.xlsx" download="Africa_Fuel_Prices_2026.xlsx">
  <span class="dl-float-badge">XLSX</span>
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
  Download
</a>

<script>
'use strict';
const D = __DATA__;
let data = JSON.parse(JSON.stringify(D.countries));
let filtered = [...data];
let region = 'all', tblCur = 'usd', topCur = 'usd', botCur = 'usd', lineCur = 'usd';
let sortKey = 'name', modalCtry = null, modalTab = 'gas';
let lineInst, barInst, mInst;

const FX = D.fx_rates, WL = D.week_labels;
const REGS = ['North Africa','West Africa','East Africa','Central Africa','Southern Africa'];
const AB = {
  'North Africa':'na','West Africa':'wa','East Africa':'ea',
  'Central Africa':'ca','Southern Africa':'sa'
};
const RC = {
  'North Africa':'#F5A300','West Africa':'#00A86A',
  'East Africa':'#1A8FD8','Central Africa':'#E87C1A','Southern Africa':'#E8394A'
};
const KEYS = ['South Africa','Nigeria','Kenya','Egypt','Libya','Morocco',
              'Ethiopia','Tanzania','Ghana','Tunisia'];
const PAL = ['#00A86A','#F5A300','#1A8FD8','#E8394A','#E87C1A',
             '#00C4CF','#8B5CF6','#00CC85','#FFBE33','#9EC8E0'];

Chart.defaults.color = '#5A8FAF';
Chart.defaults.borderColor = 'rgba(33,64,89,.5)';
Chart.defaults.font.family = "'Outfit', sans-serif";
Chart.defaults.font.size = 11;

const avg = () => data.reduce((s,c) => s + c.gas_usd_now, 0) / data.length;
const rAvg = r => { const cs = data.filter(c=>c.region===r); return cs.length ? cs.reduce((s,c)=>s+c.gas_usd_now,0)/cs.length : 0; };
const rAvgF = (r,f) => { const cs = data.filter(c=>c.region===r); return cs.length ? cs.reduce((s,c)=>s+(c[f]||0),0)/cs.length : 0; };

window.addEventListener('DOMContentLoaded', () => {
  buildNav(); buildTicker(); buildKpis(); buildRegions();
  buildLineChart(); buildBarChart();
  buildRanks('top'); buildRanks('bot');
  buildFx(); buildHead(); renderTable();
  wire();
  setInterval(tick, 12000);
});

/* NAV */
function buildNav() {
  document.getElementById('navMeta').textContent = `42 countries · ${D.updated}`;
  document.getElementById('ftTime').textContent = `Updated: ${D.updated}`;
}

/* TICKER */
function buildTicker() {
  const s = [...data].sort((a,b) => a.name.localeCompare(b.name));
  let h = '';
  for (let i = 0; i < 2; i++) s.forEach(c => {
    const cl = c.chg_gas > 0 ? 'up' : c.chg_gas < 0 ? 'dn' : 'fl';
    const ar = c.chg_gas > 0 ? '▲' : c.chg_gas < 0 ? '▼' : '—';
    h += `<span class="ti">
      <span class="ti-n">${c.name}</span>
      <span class="ti-p">$${c.gas_usd_now.toFixed(3)}</span>
      <span class="ti-c">${c.currency}</span>
      <span class="${cl}">${ar}${Math.abs(c.chg_gas).toFixed(1)}%</span>
    </span>`;
  });
  document.getElementById('tickerTrack').innerHTML = h;
}

/* KPIS */
function buildKpis() {
  const s = [...data].sort((a,b) => b.gas_usd_now - a.gas_usd_now);
  const hi = s[0], lo = s[s.length-1];
  const sg = [...data].sort((a,b) => b.chg_gas - a.chg_gas)[0];
  const av = avg();
  document.getElementById('kpiGrid').innerHTML = [
    {l:'Highest',  v:`$${hi.gas_usd_now.toFixed(3)}`, s:hi.name, c:'var(--red)'},
    {l:'Lowest',   v:`$${lo.gas_usd_now.toFixed(3)}`, s:lo.name, c:'var(--g0)'},
    {l:'Avg Africa', v:`$${av.toFixed(3)}`, s:'42 nations', c:'var(--gold)'},
    {l:'Biggest Δ', v:`+${sg.chg_gas.toFixed(1)}%`, s:sg.name, c:'var(--red)'},
  ].map(k=>`<div class="kpi">
    <div class="kpi-label">${k.l}</div>
    <div class="kpi-value" style="color:${k.c}">${k.v}</div>
    <div class="kpi-sub">${k.s}</div>
  </div>`).join('');
}

/* REGIONS */
function buildRegions() {
  const mx = Math.max(...REGS.map(rAvg));
  document.getElementById('regStrip').innerHTML = REGS.map(r => {
    const ab = AB[r], col = RC[r];
    const av = rAvg(r), n = data.filter(c=>c.region===r).length;
    const chg = rAvgF(r,'chg_gas'), pct = Math.round(av/mx*100);
    return `<div class="rc rc-${ab}">
      <div class="rc-name">${r}</div>
      <div class="rc-price" style="color:${col}">$${av.toFixed(3)}</div>
      <div class="rc-count">${n} countries</div>
      <div class="rc-bar"><div class="rc-fill" style="width:${pct}%;background:${col}"></div></div>
      <div class="rc-chg" style="color:${chg>=0?'var(--red)':'var(--g0)'}">
        ${chg>=0?'▲':'▼'} ${Math.abs(chg).toFixed(1)}% Jan→Mar
      </div>
    </div>`;
  }).join('');
}

/* LINE CHART */
function buildLineChart() {
  const kd = KEYS.map(n => data.find(c=>c.name===n)).filter(Boolean);
  lineInst = new Chart(document.getElementById('lineChart').getContext('2d'), {
    type: 'line',
    data: {
      labels: WL,
      datasets: kd.map((c,i) => ({
        label: c.name, data: c.gas_usd_w || [],
        borderColor: PAL[i], backgroundColor: PAL[i]+'12',
        borderWidth: 2, pointRadius: 2, pointHoverRadius: 5,
        tension: .4, fill: false,
      }))
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: {mode:'index', intersect:false},
      plugins: {
        legend: {position:'bottom', labels:{boxWidth:8, padding:10, font:{size:10}}},
        tooltip: {callbacks: {
          title: i => `Week: ${i[0].label}`,
          label: ctx => `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(3)}/L`
        }}
      },
      scales: {
        x: {grid:{color:'rgba(33,64,89,.35)'}, ticks:{font:{size:9}, maxTicksLimit:8}},
        y: {grid:{color:'rgba(33,64,89,.35)'}, ticks:{callback: v=>`$${v.toFixed(2)}`}}
      }
    }
  });
}

function updateLineChart() {
  const kd = KEYS.map(n => data.find(c=>c.name===n)).filter(Boolean);
  const sd = c => lineCur==='usd' ? c.gas_usd_w||[] : lineCur==='loc' ? c.gas_loc_w||[] : c.die_usd_w||[];
  lineInst.data.datasets = kd.map((c,i) => ({
    label:c.name, data:sd(c), borderColor:PAL[i], backgroundColor:PAL[i]+'12',
    borderWidth:2, pointRadius:2, pointHoverRadius:5, tension:.4, fill:false,
  }));
  const isU = lineCur !== 'loc';
  lineInst.options.scales.y.ticks.callback = isU ? v=>`$${v.toFixed(3)}` : v=>v.toFixed(1);
  lineInst.update('none');
}

/* BAR CHART */
function buildBarChart() {
  barInst = new Chart(document.getElementById('barChart').getContext('2d'), {
    type: 'bar',
    data: {
      labels: REGS.map(r => r.replace(' Africa','\nAfrica')),
      datasets: [
        {label:'Gasoline USD',
         data: REGS.map(rAvg),
         backgroundColor: REGS.map(r=>RC[r]+'BB'),
         borderColor: REGS.map(r=>RC[r]),
         borderWidth:1.5, borderRadius:4},
        {label:'Diesel USD',
         data: REGS.map(r=>{const cs=data.filter(c=>c.region===r);return cs.length?cs.reduce((s,c)=>s+c.die_usd_now,0)/cs.length:0;}),
         backgroundColor: REGS.map(r=>RC[r]+'44'),
         borderColor: REGS.map(r=>RC[r]),
         borderWidth:1.5, borderRadius:4},
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins: {
        legend: {position:'bottom', labels:{boxWidth:8,padding:10,font:{size:10}}},
        tooltip: {callbacks: {label: ctx=>`${ctx.dataset.label}: $${ctx.parsed.y.toFixed(3)}`}}
      },
      scales: {
        x: {grid:{display:false}, ticks:{font:{size:9}}},
        y: {grid:{color:'rgba(33,64,89,.35)'}, ticks:{callback:v=>`$${v.toFixed(2)}`}}
      }
    }
  });
}

/* RANKINGS */
function buildRanks(type) {
  const cur = type==='top' ? topCur : botCur, isU = cur==='usd';
  const sorted = [...data].sort((a,b)=>b.gas_usd_now-a.gas_usd_now);
  const items = type==='top' ? sorted.slice(0,10) : sorted.slice(-10).reverse();
  const mx = items[0]?.gas_usd_now || 1;
  const col = type==='top' ? 'var(--red)' : 'var(--g0)';
  document.getElementById(type+'List').innerHTML = items.map((c,i) => {
    const price = isU ? `$${c.gas_usd_now.toFixed(3)}` : `${c.gas_loc_now.toFixed(1)} ${c.currency}`;
    const pct = Math.round(c.gas_usd_now/mx*100);
    return `<div class="rank-item" onclick="openModal('${esc(c.name)}')">
      <div class="rank-n">${i+1}</div>
      <div class="rank-name">${c.name}</div>
      <div class="rank-right">
        <span class="rank-price" style="color:${col}">${price}</span>
        <div class="rank-bar-bg"><div class="rank-bar-fg" style="width:${pct}%;background:${col}"></div></div>
      </div>
    </div>`;
  }).join('');
}

/* FX */
function buildFx() {
  document.getElementById('fxWrap').innerHTML = Object.entries(FX)
    .sort((a,b)=>a[0].localeCompare(b[0]))
    .map(([code,rate]) => {
      const m = rate>=1000 ? rate.toLocaleString('en-US',{maximumFractionDigits:0}) :
                rate>=10 ? rate.toFixed(2) : rate.toFixed(4);
      const inv = 1/rate;
      const invF = inv<0.001 ? inv.toFixed(6) : inv.toFixed(4);
      return `<div class="fx-card">
        <span class="fx-code">${code}</span>
        <div style="text-align:right">
          <span class="fx-rate">${m}</span>
          <span class="fx-inv">= $${invF}</span>
        </div>
      </div>`;
    }).join('');
}

/* TABLE */
function buildHead() {
  const cols = [
    {l:'Country',k:'name'},{l:'Region',k:null},
    {l:'Curr',k:null},{l:'FX',k:'fx'}
  ];
  if (tblCur==='usd'||tblCur==='both')
    cols.push({l:'Gas USD',k:'gas'},{l:'Diesel USD',k:'die'});
  if (tblCur==='loc'||tblCur==='both')
    cols.push({l:'Gas Local',k:null},{l:'Die Local',k:null});
  cols.push({l:'Jan→Mar',k:'chg'},{l:'Level',k:null},{l:'Jan',k:null},{l:'Mar',k:null});
  document.getElementById('tHead').innerHTML = cols.map(c =>
    `<th ${c.k?`data-k="${c.k}"`:''} class="${sortKey===c.k?'sorted':''}">${c.l}</th>`
  ).join('');
  document.querySelectorAll('#tHead th[data-k]').forEach(th =>
    th.addEventListener('click', () => { sortKey=th.dataset.k; renderTable(); })
  );
}

function renderTable() {
  let d = [...filtered];
  const q = (document.getElementById('srchInp').value||'').toLowerCase();
  if (q) d = d.filter(c =>
    c.name.toLowerCase().includes(q) ||
    c.region.toLowerCase().includes(q) ||
    c.currency.toLowerCase().includes(q)
  );
  const sv = document.getElementById('sortSel').value;
  const sorts = {
    'name':(a,b)=>a.name.localeCompare(b.name),
    'gas_desc':(a,b)=>b.gas_usd_now-a.gas_usd_now,
    'gas_asc':(a,b)=>a.gas_usd_now-b.gas_usd_now,
    'chg_desc':(a,b)=>b.chg_gas-a.chg_gas,
    'chg_asc':(a,b)=>a.chg_gas-b.chg_gas,
    'fx_desc':(a,b)=>(FX[b.currency]||1)-(FX[a.currency]||1),
  };
  if (sorts[sv]) d.sort(sorts[sv]);
  document.getElementById('cntBadge').textContent = d.length;
  const mx = Math.max(...data.map(c=>c.gas_usd_now));
  document.getElementById('tBody').innerHTML = d.map(c => {
    const ab = AB[c.region]||'na', fx = FX[c.currency]||1;
    const chgCl = c.chg_gas>0.5?'up2':c.chg_gas<-0.5?'dn2':'fl2';
    const chgAr = c.chg_gas>0.5?'▲':c.chg_gas<-0.5?'▼':'—';
    const levCl = c.gas_usd_now>1.3?'lev-h':c.gas_usd_now>0.8?'lev-m':'lev-l';
    const levLb = c.gas_usd_now>1.3?'HIGH':c.gas_usd_now>0.8?'MID':'LOW';
    const fxF = fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx>=10?fx.toFixed(2):fx.toFixed(4);
    const bw = Math.round(c.gas_usd_now/mx*100);
    const w = c.gas_usd_w||[];
    let cells = `
      <td><span class="cn">${c.name}</span></td>
      <td><span class="rt rt-${ab}">${c.region.replace(' Africa','')}</span></td>
      <td><span class="cur">${c.currency}</span></td>
      <td class="mono" style="font-size:.7rem;color:var(--t3)">${fxF}</td>`;
    if (tblCur==='usd'||tblCur==='both') cells += `
      <td>
        <span class="mono">$${c.gas_usd_now.toFixed(3)}</span>
        <div class="pb"><div class="pb-f" style="width:${bw}%"></div></div>
      </td>
      <td class="mono">$${c.die_usd_now.toFixed(3)}</td>`;
    if (tblCur==='loc'||tblCur==='both') cells += `
      <td class="mono" style="color:var(--cyan)">${c.gas_loc_now.toFixed(2)}</td>
      <td class="mono" style="color:var(--cyan)">${c.die_loc_now.toFixed(2)}</td>`;
    cells += `
      <td><span class="${chgCl}">${chgAr} ${Math.abs(c.chg_gas).toFixed(2)}%</span></td>
      <td><span class="${levCl}">${levLb}</span></td>
      <td class="mono" style="font-size:.67rem;color:var(--t4)">${w[0]!=null?'$'+Number(w[0]).toFixed(3):'—'}</td>
      <td class="mono" style="font-size:.7rem">${w[w.length-1]!=null?'$'+Number(w[w.length-1]).toFixed(3):'—'}</td>`;
    return `<tr onclick="openModal('${esc(c.name)}')">${cells}</tr>`;
  }).join('');
}

/* MODAL */
function openModal(name) {
  const c = data.find(d=>d.name===name); if (!c) return;
  modalCtry = c;
  const fx = FX[c.currency]||1;
  const fxF = fx>=1000?fx.toLocaleString('en-US',{maximumFractionDigits:0}):fx>=10?fx.toFixed(2):fx.toFixed(4);
  document.getElementById('mTitle').textContent = `⛽ ${c.name}`;
  document.getElementById('mSub').textContent = `${c.region} · ${c.currency} · ${c.octane} RON`;
  document.getElementById('mFx').textContent = `1 USD = ${fxF} ${c.currency}  ·  $1 = ${(1/fx).toFixed(fx>=1000?6:4)} ${c.currency}`;
  const av = avg();
  document.getElementById('mStats').innerHTML = [
    {l:`Gas USD/L`,    v:`$${c.gas_usd_now.toFixed(3)}`, col:'var(--gold)'},
    {l:`Gas ${c.currency}/L`, v:`${c.gas_loc_now.toFixed(2)}`, col:'var(--g0)'},
    {l:`Diesel USD/L`, v:`$${c.die_usd_now.toFixed(3)}`, col:'var(--blue)'},
    {l:`Die ${c.currency}/L`, v:`${c.die_loc_now.toFixed(2)}`, col:'var(--cyan)'},
    {l:`LPG USD/kg`,  v:`$${c.lpg_usd_now.toFixed(3)}`, col:'var(--amber)'},
    {l:`Jan→Mar`,     v:`${c.chg_gas>=0?'+':''}${c.chg_gas.toFixed(2)}%`,
     col:c.chg_gas>0?'var(--red)':'var(--g0)'},
  ].map(s=>`<div class="m-stat">
    <div class="m-sl">${s.l}</div>
    <div class="m-sv" style="color:${s.col}">${s.v}</div>
  </div>`).join('');
  document.querySelectorAll('.mtab').forEach(b=>b.classList.remove('on'));
  document.querySelector('.mtab[data-tab="gas"]').classList.add('on');
  modalTab = 'gas'; buildModalChart();
  document.getElementById('modalOv').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function buildModalChart() {
  if (mInst) { mInst.destroy(); mInst = null; }
  const c = modalCtry; if (!c) return;
  const isGas = modalTab === 'gas';
  const uD = (isGas ? c.gas_usd_w : c.die_usd_w) || [];
  const lD = (isGas ? c.gas_loc_w : c.die_loc_w) || [];
  mInst = new Chart(document.getElementById('mChart').getContext('2d'), {
    type: 'line',
    data: {
      labels: WL,
      datasets: [
        {label:'USD/L', data:uD, borderColor:'#F5A300', backgroundColor:'rgba(245,163,0,.1)',
         borderWidth:2.5, pointRadius:3, pointHoverRadius:6, tension:.4, fill:true, yAxisID:'y1'},
        {label:`${c.currency}/L`, data:lD, borderColor:'#00A86A', backgroundColor:'transparent',
         borderWidth:2, pointRadius:2, tension:.4, yAxisID:'y2'},
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{position:'bottom',labels:{boxWidth:8,padding:10,font:{size:10}}},
        tooltip:{callbacks:{title:i=>`Week: ${i[0].label}`}}
      },
      scales:{
        y1:{position:'left',grid:{color:'rgba(33,64,89,.4)'},ticks:{callback:v=>`$${v.toFixed(3)}`}},
        y2:{position:'right',grid:{display:false},ticks:{callback:v=>v.toFixed(v>=1000?0:v>=10?1:2)}}
      }
    }
  });
}

function closeModal() {
  document.getElementById('modalOv').classList.remove('open');
  document.body.style.overflow = '';
}

/* WIRE EVENTS */
function wire() {
  // Modal close
  document.getElementById('mClose').addEventListener('click', closeModal);
  document.getElementById('modalOv').addEventListener('click', e => {
    if (e.target.id==='modalOv') closeModal();
  });
  // Swipe to close on mobile
  let touchY = 0;
  document.getElementById('modalBox').addEventListener('touchstart', e => {
    touchY = e.touches[0].clientY;
  }, {passive:true});
  document.getElementById('modalBox').addEventListener('touchmove', e => {
    if (e.touches[0].clientY - touchY > 80) closeModal();
  }, {passive:true});
  // Modal tabs
  document.getElementById('mTabs').addEventListener('click', e => {
    const b = e.target.closest('.mtab'); if (!b) return;
    document.querySelectorAll('.mtab').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); modalTab = b.dataset.tab; buildModalChart();
  });
  // Region filter
  document.querySelectorAll('.fb').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.fb').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on'); region = btn.dataset.r;
      filtered = region==='all' ? [...data] : data.filter(c=>c.region===region);
      renderTable();
    });
  });
  // Sort
  document.getElementById('sortSel').addEventListener('change', () => {
    sortKey = document.getElementById('sortSel').value.replace(/_desc|_asc/,'');
    renderTable();
  });
  // Search
  document.getElementById('srchInp').addEventListener('input', renderTable);
  // Table toggle
  document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('tblTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on'); tblCur = btn.dataset.v; buildHead(); renderTable();
    });
  });
  // Line toggle
  document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('lineTog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
      btn.classList.add('on'); lineCur = btn.dataset.v; updateLineChart();
    });
  });
  // Rankings toggles
  ['top','bot'].forEach(t => {
    document.getElementById(t+'Tog').querySelectorAll('.tog-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.getElementById(t+'Tog').querySelectorAll('.tog-btn').forEach(b=>b.classList.remove('on'));
        btn.classList.add('on');
        if (t==='top') topCur=btn.dataset.v; else botCur=btn.dataset.v;
        buildRanks(t);
      });
    });
  });
  // Keyboard close
  document.addEventListener('keydown', e => { if (e.key==='Escape') closeModal(); });
}

/* LIVE TICK */
function tick() {
  const n = Math.floor(Math.random()*3)+2;
  for (let i=0; i<n; i++) {
    const c = data[Math.floor(Math.random()*data.length)];
    const noise = (Math.random()-.5)*.002;
    c.gas_usd_now = Math.max(.01, +(c.gas_usd_now+noise).toFixed(4));
    c.die_usd_now = Math.max(.01, +(c.die_usd_now+noise*.9).toFixed(4));
    const fx = FX[c.currency]||1;
    c.gas_loc_now = +(c.gas_usd_now*fx).toFixed(2);
    c.die_loc_now = +(c.die_usd_now*fx).toFixed(2);
    if (c.gas_usd_w?.length) c.gas_usd_w[c.gas_usd_w.length-1]=c.gas_usd_now;
    if (c.gas_loc_w?.length) c.gas_loc_w[c.gas_loc_w.length-1]=c.gas_loc_now;
    if (c.die_usd_w?.length) c.die_usd_w[c.die_usd_w.length-1]=c.die_usd_now;
    if (c.die_loc_w?.length) c.die_loc_w[c.die_loc_w.length-1]=c.die_loc_now;
  }
  buildKpis(); buildRegions(); buildRanks('top'); buildRanks('bot'); renderTable();
}

function esc(s) { return s.replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
</script>
</body>
</html>"""


def build(payload: dict, out_path: str):
    js   = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    html = TEMPLATE.replace('__DATA__', js)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    kb = len(html) // 1024
    print(f"   ✅  Dashboard → {out_path}  ({kb} KB)")
