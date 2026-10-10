#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦营养搭配师 —— 餐品组合优化器
=================================
输入（三选一）：
  1) --input PATH   归一化 JSON（默认可用 sample_nutrition.json，离线/演示用）
  2) --mcp-raw PATH 麦当劳 MCP `list-nutrition-foods` 返回的“包装文本”原始输出
  3) --live         直连麦当劳 MCP（需环境变量 MCD_TOKEN），实时拉取营养数据

输出：在满足热量/蛋白目标、规避忌口的前提下，给出 Top-K 餐品组合 + 营养表。

说明：真实 `list-nutrition-foods` 返回体是“API Response Information”包装文本，
内部 `data` 字段是一张表：
  [160]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:
  猪柳麦满分,null,1288,308,16,16,24,781,213
本脚本负责把这种格式解析成归一化记录再优化。
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

MCP_URL = "https://mcp.mcd.cn"
NUMERIC_KEYS = ["energyKj", "energyKcal", "protein", "fat", "carbohydrate", "sodium", "calcium"]
COLS = ["productName", "nutritionDescription"] + NUMERIC_KEYS

# ---------------------------------------------------------------------------
# 1) 解析层：把真实 MCP 返回文本 -> 归一化记录列表
# ---------------------------------------------------------------------------

def extract_json(t: str):
    """从包装文本里抠出 {"success":...} 这个 JSON 对象（data 字段内不含 '}'，故可安全按括号配对）。"""
    start = t.find('{"success"')
    if start < 0:
        start = t.find('{')
    depth = 0
    end = -1
    for i in range(start, len(t)):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    return json.loads(t[start:end])


def parse_table(data_str: str):
    """把 `[160]{...}:` + 行的表解析成归一化 dict 列表。"""
    m = re.search(r'\[(\d+)\]\{([^}]+)\}:', data_str)
    if not m:
        raise ValueError("未在 data 中找到表头 [N]{col1,col2,...}:")
    rest = data_str[m.end():].strip()
    foods = []
    for line in rest.split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(',')]
        name = parts[0]
        nums = parts[-7:]
        desc = ','.join(parts[1:-7]) if len(parts) > 9 else (parts[1] if len(parts) > 1 else '')
        if desc in ('null', 'None', ''):
            desc = ''
        rec = {'productName': name, 'nutritionDescription': desc}
        for k, v in zip(NUMERIC_KEYS, nums):
            try:
                rec[k] = float(v) if ('.' in v or 'e' in v.lower()) else int(v)
            except ValueError:
                rec[k] = None
        foods.append(rec)
    return foods


def parse_mcp_text(text: str):
    obj = extract_json(text)
    return parse_table(obj['data'])


def load_normalized(path: str):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    # 兼容两种格式：已经是归一化列表，或 {"data": "..."} 包装
    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], str):
        return parse_table(data['data'])
    out = []
    for r in data:
        rec = {k: r.get(k) for k in COLS}
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# 2) 实时拉取：Streamable HTTP 握手 + tools/call
# ---------------------------------------------------------------------------

def _post(payload, token, session_id=None):
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': f'Bearer {token}',
    }
    if session_id:
        headers['Mcp-Session-Id'] = session_id
    req = urllib.request.Request(MCP_URL, data=data, headers=headers, method='POST')
    try:
        resp = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"MCP HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    body = resp.read().decode('utf-8', 'replace')
    sid = resp.headers.get('Mcp-Session-Id')
    ct = resp.headers.get('Content-Type', '')
    if not body or not body.strip():
        # 通知类请求(notifications/initialized)服务端通常返回 202 空 body
        return None, sid
    if 'text/event-stream' in ct:
        out = None
        for line in body.splitlines():
            if line.startswith('data:'):
                chunk = line[5:].strip()
                if chunk:
                    try:
                        out = json.loads(chunk)
                    except Exception:
                        pass
        return out, sid
    return json.loads(body), sid


def fetch_mcp_nutrition(token: str):
    init, sid = _post({
        'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
                   'clientInfo': {'name': 'mcd-nutrition-coach', 'version': '1.0'}},
    }, token)
    if not init or 'result' not in init:
        raise RuntimeError(f'initialize 失败: {init}')
    _post({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, token, sid)
    call, _ = _post({
        'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
        'params': {'name': 'list-nutrition-foods', 'arguments': {}},
    }, token, sid)
    content = (call.get('result') or {}).get('content') or []
    text = ''.join(c.get('text', '') for c in content if c.get('type') == 'text')
    return parse_mcp_text(text)


# ---------------------------------------------------------------------------
# 3) 优化层：带剪枝的组合搜索
# ---------------------------------------------------------------------------

def _clean(foods):
    out = []
    for f in foods:
        e = f.get('energyKcal')
        if e is None or e <= 0:
            continue
        rec = {'productName': f.get('productName', '?')}
        for k in NUMERIC_KEYS:
            v = f.get(k)
            rec[k] = v if isinstance(v, (int, float)) else 0
        out.append(rec)
    return out


def _enumerate(pool, max_items, cal_hi):
    """枚举总热量<=cal_hi 的所有不重复组合（大小 1..max_items），带运行和剪枝。"""
    results = []

    def rec(start, chosen, run_cal):
        if chosen:
            results.append(list(chosen))
        if len(chosen) >= max_items:
            return
        for i in range(start, len(pool)):
            c = pool[i]['energyKcal']
            if run_cal + c > cal_hi:
                continue
            rec(i + 1, chosen + [pool[i]], run_cal + c)

    rec(0, [], 0)
    return results


def optimize(foods, mode, target_cal, target_protein, excludes, max_items, top_k):
    foods = _clean(foods)
    ex = [e.strip().lower() for e in (excludes or []) if e.strip()]
    if ex:
        foods = [f for f in foods if not any(e in f['productName'].lower() for e in ex)]

    cal_lo = target_cal * 0.85
    cal_hi = target_cal * 1.15
    pool = [f for f in foods if f['energyKcal'] <= cal_hi]
    raw = _enumerate(pool, max_items, cal_hi)

    rated = []
    for combo in raw:
        t_cal = sum(f['energyKcal'] for f in combo)
        t_prot = sum(f['protein'] for f in combo)
        t_sodium = sum(f['sodium'] for f in combo)
        if not (cal_lo <= t_cal <= cal_hi):
            continue
        if target_protein and t_prot < target_protein * 0.6:
            continue
        cal_err = abs(t_cal - target_cal) / target_cal
        cal_score = max(0.0, 1 - cal_err)
        prot_score = 0.0
        if target_protein:
            prot_err = abs(t_prot - target_protein) / target_protein
            prot_score = max(0.0, 1 - prot_err)
        sodium_pen = t_sodium / 2000.0
        # 减脂更看重热量贴合+高蛋白；增肌更看重蛋白；维持取平衡
        w_cal = 0.55 if mode != 'bulk' else 0.45
        w_prot = 0.35 if mode != 'bulk' else 0.5
        s = 100 * (w_cal * cal_score + w_prot * prot_score) - sodium_pen * 15
        rated.append((max(0.0, round(s, 1)), combo, t_cal, t_prot, t_sodium))

    rated.sort(key=lambda x: x[0], reverse=True)
    return rated[:top_k]


# ---------------------------------------------------------------------------
# 4) 报告
# ---------------------------------------------------------------------------

def build_report(rated, mode, target_cal, target_protein, excludes):
    lines = []
    mode_cn = {'cut': '减脂', 'maintain': '维持', 'bulk': '增肌'}.get(mode, mode)
    lines.append(f"# 麦麦营养搭配师 · {mode_cn}方案")
    lines.append(f"- 目标：热量 ≈ {target_cal:.0f} kcal" +
                 (f"，蛋白 ≈ {target_protein:.0f} g" if target_protein else ""))
    if excludes:
        lines.append(f"- 忌口：{', '.join(excludes)}")
    lines.append("")
    if not rated:
        lines.append("⚠️ 在约束内未找到合适组合，建议放宽热量窗口或忌口。")
        return '\n'.join(lines)
    for rank, (score, combo, t_cal, t_prot, t_sodium) in enumerate(rated, 1):
        lines.append(f"## 方案 {rank}（评分 {score}）")
        lines.append(f"| 餐品 | 热量(kcal) | 蛋白(g) | 脂肪(g) | 碳水(g) | 钠(mg) | 钙(mg) |")
        lines.append(f"|---|---|---|---|---|---|---|")
        for f in combo:
            lines.append(f"| {f['productName']} | {f['energyKcal']:.0f} | {f['protein']:.0f} "
                         f"| {f['fat']:.0f} | {f['carbohydrate']:.0f} | {f['sodium']:.0f} | {f['calcium']:.0f} |")
        lines.append(f"| **合计** | **{t_cal:.0f}** | **{t_prot:.0f}** | "
                     f"**{sum(f['fat'] for f in combo):.0f}** | "
                     f"**{sum(f['carbohydrate'] for f in combo):.0f}** | "
                     f"**{t_sodium:.0f}** | **{sum(f['calcium'] for f in combo):.0f}** |")
        # 一句点评
        tips = []
        if target_protein and t_prot >= target_protein * 0.9:
            tips.append("蛋白达标✅")
        if t_sodium > 1500:
            tips.append("钠偏高⚠️，注意补水")
        if t_cal <= target_cal:
            tips.append("热量控制在目标内👍")
        lines.append("建议：" + ("；".join(tips) if tips else "搭配均衡"))
        lines.append("")
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# 5) CLI
# ---------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="麦麦营养搭配师 餐品组合优化器")
    src = ap.add_mutually_exclusive_group()
    src.add_argument('--input', default=os.path.join(here, 'sample_nutrition.json'),
                     help='归一化营养 JSON 文件（默认 sample_nutrition.json）')
    src.add_argument('--mcp-raw', help='麦当劳 MCP list-nutrition-foods 原始返回文本文件')
    src.add_argument('--live', action='store_true', help='直连麦当劳 MCP 实时拉取（需 MCD_TOKEN 环境变量）')
    ap.add_argument('--mode', choices=['cut', 'maintain', 'bulk'], default='cut')
    ap.add_argument('--target-cal', type=float, help='目标热量(kcal)')
    ap.add_argument('--target-protein', type=float, help='目标蛋白(g)')
    ap.add_argument('--exclude', help='忌口餐品关键词，逗号分隔，如 "薯条,可乐"')
    ap.add_argument('--max-items', type=int, default=3, help='单组合最多餐品数(默认3)')
    ap.add_argument('--top-k', type=int, default=3, help='返回前 K 个组合(默认3)')
    ap.add_argument('--out', help='把报告写到该 UTF-8 文件')
    args = ap.parse_args()

    defaults = {'cut': (500, 35), 'maintain': (700, 40), 'bulk': (900, 60)}
    t_cal = args.target_cal if args.target_cal else defaults[args.mode][0]
    t_prot = args.target_protein if args.target_protein else defaults[args.mode][1]

    if args.live:
        token = os.environ.get('MCD_TOKEN')
        if not token:
            sys.exit('ERROR: --live 需要设置环境变量 MCD_TOKEN')
        foods = fetch_mcp_nutrition(token)
        src_desc = f"实时拉取（{len(foods)} 条）"
    elif args.mcp_raw:
        with open(args.mcp_raw, encoding='utf-8', errors='replace') as f:
            foods = parse_mcp_text(f.read())
        src_desc = f"MCP 原始文本（{len(foods)} 条）"
    else:
        foods = load_normalized(args.input)
        src_desc = f"文件 {os.path.basename(args.input)}（{len(foods)} 条）"

    excludes = [e for e in (args.exclude or '').split(',')] if args.exclude else []
    rated = optimize(foods, args.mode, t_cal, t_prot, excludes, args.max_items, args.top_k)
    report = build_report(rated, args.mode, t_cal, t_prot, excludes)
    header = f"（数据来源：{src_desc}；模式={args.mode}；目标 {t_cal:.0f}kcal"
    if t_prot:
        header += f"/{t_prot:.0f}g"
    header += "）\n"
    full = header + report

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(full + '\n')
        print(f"[已写入报告] {args.out}")
    print(full)


if __name__ == '__main__':
    main()
