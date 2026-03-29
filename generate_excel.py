"""
generate_excel.py — Africa Fuel Tracker Excel Report Generator
Reads data/prices_db.json + data/history_db.json
Writes africa_fuel_tracker_YYYY-MM-DD.xlsx

Sheets:
  1. Price History  — 54 countries, Jan→Now, USD + local, ▲▼ icons,
                      conditional formatting, data bars
  2. Charts & Analysis — bar chart (regional avg) + line chart (top markets)
                         + top/bottom 10 rankings
"""
import json
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.chart import BarChart, LineChart, Reference

ROOT       = Path(__file__).parent
DATA_DIR   = ROOT / "data"
PRICES_DB  = DATA_DIR / "prices_db.json"
HISTORY_DB = DATA_DIR / "history_db.json"

REGIONS = [
    "North Africa", "West Africa", "Central Africa",
    "East Africa", "Southern Africa",
]
RC_HEX = {
    "North Africa":    "F5A300",
    "West Africa":     "00A86A",
    "Central Africa":  "E87C1A",
    "East Africa":     "1A8FD8",
    "Southern Africa": "E8394A",
}

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK   = "07111E"
BG_SHEET  = "F7F9FC"
BG_HEADER = "1A3347"
TEXT_WHITE = "FFFFFF"
TEXT_DARK  = "0D1B2A"
TEXT_MUTED = "5A7A8F"
CHART_PAL  = [
    "00A86A", "F5A300", "1A8FD8", "E8394A", "E87C1A",
    "8B5CF6", "00C4CF", "FF6B78", "FFBE33", "5A8FAF",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def solid(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)

def thin_border(color: str = "D8E4EF") -> Border:
    s = Side(style="thin", color=color)
    return Border(left=s, right=s, top=s, bottom=s)

def cell(ws, row: int, col: int, value=None, *,
         bold=False, size=10, color=TEXT_DARK, bg=None,
         halign="left", valign="center", wrap=False, num_format=None) -> object:
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name="Arial", size=size, bold=bold, color=color)
    if bg:
        c.fill = solid(bg)
    c.alignment = Alignment(horizontal=halign, vertical=valign, wrap_text=wrap)
    if num_format:
        c.number_format = num_format
    return c

def merge(ws, row: int, c1: int, c2: int, value=None, *,
          bold=False, size=12, color=TEXT_DARK, bg=None,
          halign="center", valign="center", indent=0) -> object:
    ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
    c = ws.cell(row=row, column=c1, value=value)
    c.font = Font(name="Arial", size=size, bold=bold, color=color)
    if bg:
        c.fill = solid(bg)
    c.alignment = Alignment(horizontal=halign, vertical=valign, indent=indent)
    return c

def rh(ws, row: int, height: float):
    ws.row_dimensions[row].height = height

def cw(ws, col: int, width: float):
    ws.column_dimensions[get_column_letter(col)].width = width

def chg_icon(v: float) -> str:
    if v > 0.5:  return f"▲ +{v:.1f}%"
    if v < -0.5: return f"▼ {v:.1f}%"
    return f"— {v:.1f}%"

def chg_fg(v: float) -> str:
    if v > 0.5:  return "C0392B"   # red
    if v < -0.5: return "1A6B3C"   # green
    return "666666"

def chg_bg(v: float, default: str = "FFFFFF") -> str:
    if v > 0.5:  return "FEE2E2"
    if v < -0.5: return "D1FAE5"
    return default

# ── Data preparation ──────────────────────────────────────────────────────────

def load_data():
    p = json.loads(PRICES_DB.read_text(encoding="utf-8"))
    h = json.loads(HISTORY_DB.read_text(encoding="utf-8"))
    meta  = p["meta"]
    pdata = p["data"]

    rows = []
    for country, d in pdata.items():
        hist = h.get(country, [])
        first = next(
            (e for e in hist if e["date"] >= "2026-01-01"), hist[0] if hist else None
        )
        gas_first     = first["gas_usd"]  if first else d["gas_usd"]
        die_first     = first["die_usd"]  if first else d["die_usd"]
        gasloc_first  = first["gas_loc"]  if first else d["gas_loc"]
        dieloc_first  = first["die_loc"]  if first else d["die_loc"]
        chg_gas = round((d["gas_usd"] - gas_first) / gas_first * 100, 2) if gas_first else 0
        chg_die = round((d["die_usd"] - die_first) / die_first * 100, 2) if die_first else 0
        rows.append({
            "country":      country,
            "region":       d["region"],
            "currency":     d["currency"],
            "fx_rate":      d["fx_rate"],
            "gas_usd":      d["gas_usd"],
            "die_usd":      d["die_usd"],
            "gas_loc":      d["gas_loc"],
            "die_loc":      d["die_loc"],
            "gas_first":    gas_first,
            "die_first":    die_first,
            "gasloc_first": gasloc_first,
            "dieloc_first": dieloc_first,
            "chg_gas":      chg_gas,
            "chg_die":      chg_die,
            "confidence":   d["confidence"],
            "eff_date":     d["effective_date"],
            "source":       d["source_url"],
            "hist":         hist,
        })

    rows.sort(key=lambda x: (
        REGIONS.index(x["region"]) if x["region"] in REGIONS else 9,
        x["country"],
    ))
    return meta, rows

# ══════════════════════════════════════════════════════════════════════════════
# SHEET 1 — PRICE HISTORY
# ══════════════════════════════════════════════════════════════════════════════

def build_price_history(wb, meta, rows):
    ws = wb.create_sheet("Price History")
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = "00A86A"

    NCOLS = 14

    # ── Title ─────────────────────────────────────────────────────────────────
    merge(ws, 1, 1, NCOLS,
          "⛽  AFRICA FUEL TRACKER — PRICE HISTORY  |  Jan 2026 → " + meta.get("run_date", ""),
          bold=True, size=15, color=TEXT_WHITE, bg=BG_DARK, halign="left", indent=1)
    rh(ws, 1, 36)

    merge(ws, 2, 1, NCOLS,
          f"Updated: {meta.get('run_date','')}  ·  54 countries, 5 regions  ·  "
          "Sources: official national regulators  ·  FX: central bank references",
          bold=False, size=9, color="9EC8E0", bg=BG_DARK, halign="left", indent=1)
    rh(ws, 2, 18)

    # Spacer
    for c in range(1, NCOLS + 1):
        ws.cell(row=3, column=c).fill = solid(BG_SHEET)
    rh(ws, 3, 8)

    # ── Legend ────────────────────────────────────────────────────────────────
    cell(ws, 4, 1, "LEGEND:", bold=True, size=8, color="444444", bg=BG_SHEET)
    legends = [
        (2,  "▲ = increase vs Jan 2026", "C0392B"),
        (5,  "▼ = decrease vs Jan 2026", "1A6B3C"),
        (8,  "— = no change",            "666666"),
        (11, "Confidence: 🟢 High  🟡 Med  🔴 Low", "444444"),
    ]
    for col_i, txt, clr in legends:
        cell(ws, 4, col_i, txt, size=8, color=clr, bg=BG_SHEET)
    rh(ws, 4, 14)

    # ── Column widths ─────────────────────────────────────────────────────────
    widths = [20, 16, 8, 9, 13, 13, 10, 13, 13, 10, 13, 13, 13, 13]
    for i, w in enumerate(widths, 1):
        cw(ws, i, w)

    # ── Column headers ────────────────────────────────────────────────────────
    HDR = 5
    headers = [
        "Country", "Region", "Cur.", "FX Rate",
        "Gas Jan (USD)", "Gas Now (USD)", "Gas Chg",
        "Die Jan (USD)", "Die Now (USD)", "Die Chg",
        "Gas Jan (Local)", "Gas Now (Local)",
        "Die Jan (Local)", "Die Now (Local)",
    ]
    for i, h_txt in enumerate(headers, 1):
        c = cell(ws, HDR, i, h_txt, bold=True, size=10,
                 color=TEXT_WHITE, bg=BG_HEADER, halign="center")
        c.border = Border(
            bottom=Side(style="medium", color="00A86A"),
            right=Side(style="thin",   color="2D4A6A"),
        )
    rh(ws, HDR, 26)

    # ── Data rows ─────────────────────────────────────────────────────────────
    prev_region = None
    DATA_START = HDR + 1
    r = DATA_START

    for row in rows:
        # Region separator
        if row["region"] != prev_region:
            prev_region = row["region"]
            rc = RC_HEX.get(row["region"], "888888")
            merge(ws, r, 1, NCOLS,
                  f"  {row['region'].upper()}",
                  bold=True, size=9, color=TEXT_WHITE, bg=rc,
                  halign="left", indent=1)
            rh(ws, r, 18)
            r += 1

        # Row background (alternating)
        bg0 = "FFFFFF" if (r - DATA_START) % 2 == 0 else "F0F5FA"
        brd = thin_border()

        cg, cd = row["chg_gas"], row["chg_die"]

        row_vals = [
            # (value, fg_color, bg_color, halign, num_format)
            (row["country"],      TEXT_DARK,        bg0,          "left",   None),
            (row["region"],       TEXT_MUTED,       bg0,          "left",   None),
            (row["currency"],     TEXT_DARK,        bg0,          "center", None),
            (row["fx_rate"],      TEXT_DARK,        bg0,          "right",  "#,##0.00"),
            (row["gas_first"],    TEXT_DARK,        bg0,          "right",  "$#,##0.0000"),
            (row["gas_usd"],      TEXT_DARK,        bg0,          "right",  "$#,##0.0000"),
            (chg_icon(cg),        chg_fg(cg),       chg_bg(cg, bg0), "center", None),
            (row["die_first"],    TEXT_DARK,        bg0,          "right",  "$#,##0.0000"),
            (row["die_usd"],      TEXT_DARK,        bg0,          "right",  "$#,##0.0000"),
            (chg_icon(cd),        chg_fg(cd),       chg_bg(cd, bg0), "center", None),
            (row["gasloc_first"], TEXT_DARK,        bg0,          "right",  "#,##0.00"),
            (row["gas_loc"],      TEXT_DARK,        bg0,          "right",  "#,##0.00"),
            (row["dieloc_first"], TEXT_DARK,        bg0,          "right",  "#,##0.00"),
            (row["die_loc"],      TEXT_DARK,        bg0,          "right",  "#,##0.00"),
        ]

        for col_i, (val, fc, bc, ha, nf) in enumerate(row_vals, 1):
            c = ws.cell(row=r, column=col_i, value=val)
            c.font = Font(name="Arial", size=10, color=fc,
                          bold=(col_i == 1))
            c.fill = solid(bc)
            c.alignment = Alignment(horizontal=ha, vertical="center")
            c.border = brd
            if nf:
                c.number_format = nf

        rh(ws, r, 18)
        r += 1

    DATA_END = r - 1

    # ── Conditional formatting — Gas Now USD (col F) ───────────────────────
    ws.conditional_formatting.add(
        f"F{DATA_START}:F{DATA_END}",
        ColorScaleRule(
            start_type="min",        start_color="63BE7B",
            mid_type="percentile",   mid_value=50, mid_color="FFEB84",
            end_type="max",          end_color="F8696B",
        ),
    )
    # Diesel Now USD (col I)
    ws.conditional_formatting.add(
        f"I{DATA_START}:I{DATA_END}",
        ColorScaleRule(
            start_type="min",        start_color="63BE7B",
            mid_type="percentile",   mid_value=50, mid_color="FFEB84",
            end_type="max",          end_color="F8696B",
        ),
    )
    # Data bars on Gas Now USD
    ws.conditional_formatting.add(
        f"F{DATA_START}:F{DATA_END}",
        DataBarRule(start_type="min", end_type="max",
                    color="1A8FD8", showValue=True),
    )

    ws.freeze_panes = "B6"

    # ── Summary stats ─────────────────────────────────────────────────────────
    r += 1
    merge(ws, r, 1, NCOLS, "SUMMARY STATISTICS",
          bold=True, size=10, color=TEXT_WHITE, bg=BG_HEADER, halign="left", indent=1)
    rh(ws, r, 22)
    r += 1

    stat_hdrs = ["Metric", "Gas USD/L", "Diesel USD/L", "Region", "Country"]
    for i, h_txt in enumerate(stat_hdrs, 1):
        cell(ws, r, i, h_txt, bold=True, size=9,
             color=TEXT_WHITE, bg="2D4A6A", halign="center")
    rh(ws, r, 18)
    r += 1

    gas_vals = [x["gas_usd"] for x in rows]
    die_vals = [x["die_usd"] for x in rows]
    max_r = max(rows, key=lambda x: x["gas_usd"])
    min_r = min(rows, key=lambda x: x["gas_usd"])
    avg_g = round(sum(gas_vals) / len(gas_vals), 4)
    avg_d = round(sum(die_vals) / len(die_vals), 4)

    stats = [
        ("Africa Average (54 nations)", avg_g, avg_d, "All regions", "—"),
        ("Highest gas price",  max_r["gas_usd"], max_r["die_usd"], max_r["region"], max_r["country"]),
        ("Lowest gas price",   min_r["gas_usd"], min_r["die_usd"], min_r["region"], min_r["country"]),
    ]
    for idx, (label, gv, dv, reg, cntry) in enumerate(stats):
        bg = "F7F9FC" if idx % 2 == 0 else "EFF4F8"
        data = [(label, None), (gv, "$#,##0.0000"), (dv, "$#,##0.0000"), (reg, None), (cntry, None)]
        for col_i, (val, nf) in enumerate(data, 1):
            c = ws.cell(row=r, column=col_i, value=val)
            c.font = Font(name="Arial", size=10, bold=(col_i == 1), color=TEXT_DARK)
            c.fill = solid(bg)
            c.alignment = Alignment(
                horizontal="left" if col_i == 1 else "center", vertical="center"
            )
            if nf:
                c.number_format = nf
        rh(ws, r, 18)
        r += 1

    return DATA_START, DATA_END


# ══════════════════════════════════════════════════════════════════════════════
# SHEET 2 — CHARTS & ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def build_charts(wb, meta, rows):
    wc = wb.create_sheet("Charts & Analysis")
    wc.sheet_view.showGridLines = False
    wc.sheet_properties.tabColor = "1A8FD8"

    NCOLS = 22

    # ── Title ─────────────────────────────────────────────────────────────────
    merge(wc, 1, 1, NCOLS,
          "⛽  AFRICA FUEL TRACKER — CHARTS & ANALYSIS",
          bold=True, size=15, color=TEXT_WHITE, bg=BG_DARK, halign="left", indent=1)
    rh(wc, 1, 36)
    merge(wc, 2, 1, NCOLS,
          f"Updated: {meta.get('run_date','')}  ·  Regional averages and key market trends",
          bold=False, size=9, color="9EC8E0", bg=BG_DARK, halign="left", indent=1)
    rh(wc, 2, 18)

    # ── Regional averages data (rows 4-9) ─────────────────────────────────────
    cw(wc, 1, 20); cw(wc, 2, 16); cw(wc, 3, 16); cw(wc, 4, 12)

    for i, hdr in enumerate(["Region", "Avg Gas USD/L", "Avg Diesel USD/L", "Countries"], 1):
        c = cell(wc, 4, i, hdr, bold=True, size=10, color=TEXT_WHITE,
                 bg=BG_HEADER, halign="center")
        c.border = Border(bottom=Side(style="medium", color="00A86A"))
    rh(wc, 4, 24)

    reg_data = {}
    for row in rows:
        reg = row["region"]
        reg_data.setdefault(reg, {"gas": [], "die": [], "n": 0})
        reg_data[reg]["gas"].append(row["gas_usd"])
        reg_data[reg]["die"].append(row["die_usd"])
        reg_data[reg]["n"] += 1

    for i, reg in enumerate(REGIONS, 5):
        d   = reg_data.get(reg, {"gas": [], "die": [], "n": 0})
        avg_g = round(sum(d["gas"]) / len(d["gas"]), 4) if d["gas"] else 0
        avg_d = round(sum(d["die"]) / len(d["die"]), 4) if d["die"] else 0
        bg = "F7F9FC" if i % 2 == 0 else "EFF4F8"
        row_data = [(reg, None), (avg_g, "$#,##0.0000"), (avg_d, "$#,##0.0000"), (d["n"], None)]
        for col_i, (val, nf) in enumerate(row_data, 1):
            c = wc.cell(row=i, column=col_i, value=val)
            c.font = Font(name="Arial", size=10, color=TEXT_DARK)
            c.fill = solid(bg)
            c.alignment = Alignment(
                horizontal="left" if col_i == 1 else "center", vertical="center"
            )
            if nf:
                c.number_format = nf
        rh(wc, i, 18)

    # ── Bar chart — regional averages ─────────────────────────────────────────
    bar = BarChart()
    bar.type = "col"
    bar.grouping = "clustered"
    bar.title = "Average Fuel Price by Region (USD/L)"
    bar.style = 10
    bar.y_axis.title = "USD/L"
    bar.width = 18
    bar.height = 12

    cats    = Reference(wc, min_col=1, min_row=5, max_row=9)
    gas_ref = Reference(wc, min_col=2, min_row=4, max_row=9)
    die_ref = Reference(wc, min_col=3, min_row=4, max_row=9)
    bar.add_data(gas_ref, titles_from_data=True)
    bar.add_data(die_ref, titles_from_data=True)
    bar.set_categories(cats)
    bar.series[0].graphicalProperties.solidFill = "00A86A"
    bar.series[1].graphicalProperties.solidFill = "1A8FD8"
    wc.add_chart(bar, "F4")

    # ── Top markets history data (rows 22+) ───────────────────────────────────
    TOP = ["Kenya","Nigeria","South Africa","Egypt","Morocco",
           "Ethiopia","Ghana","Tanzania","Algeria","Zambia"]

    H_START = 22
    merge(wc, H_START - 1, 1, len(TOP) + 1,
          "TOP MARKETS — GASOLINE HISTORY (USD/L)",
          bold=True, size=10, color=TEXT_WHITE, bg=BG_DARK, halign="left", indent=1)
    rh(wc, H_START - 1, 22)

    cell(wc, H_START, 1, "Date", bold=True, size=10,
         color=TEXT_WHITE, bg=BG_HEADER, halign="center")
    for j, cname in enumerate(TOP, 2):
        cell(wc, H_START, j, cname, bold=True, size=10,
             color=TEXT_WHITE, bg=BG_HEADER, halign="center")
        cw(wc, j, 14)
    rh(wc, H_START, 22)

    # Collect all dates
    hist_map = {row["country"]: row["hist"] for row in rows}
    all_dates = sorted(set(
        e["date"]
        for c in TOP
        for e in hist_map.get(c, [])
        if e["date"] >= "2026-01-01"
    ))

    for di, dt in enumerate(all_dates):
        dr  = H_START + 1 + di
        bg  = "F7F9FC" if di % 2 == 0 else "EFF4F8"
        wc.cell(row=dr, column=1, value=dt).font = Font(name="Arial", size=10)
        wc.cell(row=dr, column=1).fill = solid(bg)
        wc.cell(row=dr, column=1).alignment = Alignment(horizontal="center")
        for j, cname in enumerate(TOP, 2):
            hist_c = hist_map.get(cname, [])
            val = None
            for e in hist_c:
                if e["date"] <= dt:
                    val = e["gas_usd"]
            c = wc.cell(row=dr, column=j, value=val)
            c.fill = solid(bg)
            c.font = Font(name="Arial", size=10)
            c.alignment = Alignment(horizontal="right")
            if val is not None:
                c.number_format = "$#,##0.0000"
        rh(wc, dr, 16)

    H_END = H_START + len(all_dates)

    # ── Line chart — top markets trend ────────────────────────────────────────
    line = LineChart()
    line.title = "Gasoline Price Trend — Top 10 Markets (USD/L)"
    line.style = 10
    line.y_axis.title = "USD/L"
    line.x_axis.title = "Date"
    line.width  = 22
    line.height = 14

    dates_ref = Reference(wc, min_col=1, min_row=H_START + 1, max_row=H_END)
    for j in range(len(TOP)):
        ser_ref = Reference(wc, min_col=j + 2, min_row=H_START, max_row=H_END)
        line.add_data(ser_ref, titles_from_data=True)
        line.series[j].graphicalProperties.line.solidFill = CHART_PAL[j]
        line.series[j].graphicalProperties.line.width = 20000
        line.series[j].smooth = True
    line.set_categories(dates_ref)
    wc.add_chart(line, "F22")

    # ── Rankings (col 18+) ────────────────────────────────────────────────────
    RC = 18
    for c in range(RC, RC + 3):
        cw(wc, c, 16 if c == RC else 12)

    def mini_rank(start_row, title, title_bg, data_rows, row_bg_pair):
        merge(wc, start_row, RC, RC + 2, title,
              bold=True, size=10, color=TEXT_WHITE, bg=title_bg, halign="center")
        rh(wc, start_row, 20)
        for off, lbl in enumerate(["Country", "USD/L", "Region"]):
            cell(wc, start_row + 1, RC + off, lbl, bold=True, size=9,
                 color=TEXT_WHITE, bg=BG_HEADER, halign="center")
        rh(wc, start_row + 1, 18)
        for i, row in enumerate(data_rows):
            dr  = start_row + 2 + i
            bg  = row_bg_pair[i % 2]
            wc.cell(row=dr, column=RC,     value=f"{i+1}. {row['country']}")
            wc.cell(row=dr, column=RC + 1, value=row["gas_usd"])
            wc.cell(row=dr, column=RC + 2, value=row["region"])
            wc.cell(row=dr, column=RC + 1).number_format = "$#,##0.0000"
            for col_off in range(3):
                c = wc.cell(row=dr, column=RC + col_off)
                c.fill = solid(bg)
                c.font = Font(name="Arial", size=9, color=TEXT_DARK)
                c.alignment = Alignment(
                    horizontal="left" if col_off == 0 else "center", vertical="center"
                )
            rh(wc, dr, 16)

    top10 = sorted(rows, key=lambda x: -x["gas_usd"])[:10]
    bot10 = sorted(rows, key=lambda x:  x["gas_usd"])[:10]
    mini_rank(4,  "🔴 TOP 10 MOST EXPENSIVE GAS", "991B1B", top10, ["FEF2F2", "FEE2E2"])
    mini_rank(18, "🟢 TOP 10 MOST AFFORDABLE GAS","065F46", bot10, ["F0FDF4", "DCFCE7"])


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if not PRICES_DB.exists():
        print(f"❌ {PRICES_DB} not found"); return
    if not HISTORY_DB.exists():
        print(f"❌ {HISTORY_DB} not found"); return

    meta, rows = load_data()

    wb = Workbook()
    wb.remove(wb.active)      # remove default blank sheet

    build_price_history(wb, meta, rows)
    build_charts(wb, meta, rows)

    run_date = meta.get("run_date", date.today().isoformat())
    out_path = ROOT / f"africa_fuel_tracker_{run_date}.xlsx"
    wb.save(out_path)

    size_kb = out_path.stat().st_size / 1024
    print(f"✅ Excel generated → {out_path.name}  ({size_kb:.0f} KB)")
    print(f"   Sheets: {wb.sheetnames}")


if __name__ == "__main__":
    main()
