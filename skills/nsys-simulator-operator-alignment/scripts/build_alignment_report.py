#!/usr/bin/env python3
"""Write a KU-style CSV and dependency-free XLSX from an alignment CSV."""

from __future__ import annotations

import argparse
import csv
import html
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


KU_COLUMNS = [
    ("record_type", "记录类型"), ("pp_rank", "PP stage"), ("gpu", "GPU"),
    ("microbatch", "Microbatch"), ("layer_index", "层号"), ("layer_type", "层类型"),
    ("operator_order", "算子序号"), ("logical_operator", "逻辑算子"),
    ("nsys_kernel_name", "Nsys 算子名称"), ("nsys_time_us", "Nsys 数据（us）"),
    ("simulator_ops", "模拟器算子"), ("simulator_time_us", "模拟器数据（us）"),
    ("error_pct_sim_vs_nsys", "误差（%）"), ("notes", "备注"),
]


def safe(v: object) -> str:
    return "" if v is None else str(v)


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return rows, reader.fieldnames or []


def num(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def ku_rows(rows: list[dict[str, str]]) -> tuple[list[str], list[list[str]]]:
    headers = [label for _, label in KU_COLUMNS]
    out: list[list[str]] = []
    for row in rows:
        out.append([safe(row.get(key, "")) for key, _ in KU_COLUMNS])
    return headers, out


def summary_rows(rows: list[dict[str, str]], record_type: str) -> list[dict[str, str]]:
    return [r for r in rows if r.get("record_type") == record_type]


def xml_cell(value: object, style: int = 0) -> str:
    text = safe(value)
    if not text:
        return f'<c s="{style}"/>'
    if re.fullmatch(r"-?(?:\d+\.?\d*|\.\d+)", text):
        return f'<c s="{style}" t="n"><v>{escape(text)}</v></c>'
    return f'<c s="{style}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'


def col_name(n: int) -> str:
    out = ""
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def sheet_xml(rows: list[list[object]], widths: list[int], freeze: str = "A2", autofilter: str | None = None) -> str:
    body = []
    for r_idx, row in enumerate(rows, 1):
        cells = "".join(xml_cell(v, 1 if r_idx == 1 else 0) for v in row)
        body.append(f'<row r="{r_idx}">{cells}</row>')
    cols = "".join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths, 1))
    dim = f"A1:{col_name(max(1, max(len(r) for r in rows)))}{len(rows)}"
    filt = f'<autoFilter ref="{autofilter}"/>' if autofilter else ""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="{dim}"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="{freeze}" state="frozen"/><selection activeCell="A1" sqref="A1"/></sheetView></sheetViews><cols>{cols}</cols><sheetData>{"".join(body)}</sheetData>{filt}</worksheet>'''


def make_xlsx(path: Path, title: str, meta: str, detailed_headers: list[str], detailed: list[list[str]], layers: list[list[str]], stages: list[list[str]], notes: list[list[str]]) -> None:
    sheets = [
        ("算子明细", [title, meta] + [detailed_headers] + detailed, [20] * len(detailed_headers), "A3", f"A3:{col_name(len(detailed_headers))}{len(detailed)+3}"),
        ("层级汇总", [title, meta] + [layers[0]] + layers[1:], [20] * len(layers[0]), "A3", f"A3:{col_name(len(layers[0]))}{len(layers)+2}"),
        ("阶段总览", [title, meta] + [stages[0]] + stages[1:], [24] * len(stages[0]), "A3", f"A3:{col_name(len(stages[0]))}{len(stages)+2}"),
        ("说明", notes, [32, 100], "A1", None),
    ]
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>''' + "".join(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, (name, *_rest) in enumerate(sheets, 1)) + "</sheets></workbook>"
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    wb_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">''' + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, 5)) + "</Relationships>"
    content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>''' + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, 5)) + "</Types>"
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="10"/><name val="Arial"/></font><font><b/><sz val="10"/><name val="Arial"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="solid"><fgColor rgb="D9EAF7"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/><xf numFmtId="0" fontId="1" fillId="1" borderId="0" applyFont="1" applyFill="1"/></cellXfs></styleSheet>'''
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/styles.xml", styles)
        for i, (_name, data, widths, freeze, filt) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(data, widths, freeze, filt))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--csv-out", type=Path, required=True)
    p.add_argument("--xlsx-out", type=Path, required=True)
    p.add_argument("--title", default="模拟器和nsys耗时对比")
    p.add_argument("--meta", default="")
    args = p.parse_args()
    rows, raw_headers = read_rows(args.input)
    headers, data = ku_rows(rows)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(headers); w.writerows(data)

    layer_keys = ["layer_index", "layer_type", "nsys_time_us", "simulator_time_us", "error_pct_sim_vs_nsys", "notes"]
    layer_rows = [["层号", "层类型", "Nsys 总耗时（us）", "模拟器总耗时（us）", "误差（%）", "备注"]] + [[safe(r.get(k, "")) for k in layer_keys] for r in summary_rows(rows, "layer_summary")]
    stage_keys = ["logical_operator", "nsys_time_us", "simulator_time_us", "error_pct_sim_vs_nsys", "notes"]
    stage_rows = [["阶段/指标", "Nsys 数据（us）", "模拟器数据（us）", "误差（%）", "备注"]] + [[safe(r.get(k, "")) for k in stage_keys] for r in summary_rows(rows, "stage_summary")]
    note_rows = [["项目", "内容"], ["标题", args.title], ["参数", args.meta], ["记录数", str(len(rows))], ["对齐规则", "所有 Nsys kernel 保留；无模拟器映射时后两列留空。"], ["重叠规则", "NCCL 持续驻留 kernel 与 host NVTX recv/backpressure 不作为可直接相加的传输耗时；阶段通信采用区间 union/exposed metrics。"]]
    args.xlsx_out.parent.mkdir(parents=True, exist_ok=True)
    make_xlsx(args.xlsx_out, args.title, args.meta, headers, data, layer_rows, stage_rows, note_rows)


if __name__ == "__main__":
    main()
