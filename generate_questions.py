#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
良質な問題候補を下書きとして生成・検査するツール。

既存の data/questions.json は直接変更しない。まず data/question_drafts.json に
候補を出し、内容を確認してから採用する運用を想定している。

使い方:
  python generate_questions.py --count 120
  python generate_questions.py --check data/question_drafts.json
  python generate_questions.py --promote data/question_drafts.json
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


QUESTIONS_FILE = Path("data/questions.json")
DEFAULT_DRAFT_FILE = Path("data/question_drafts.json")

CATEGORIES = [
    "物質の構成",
    "原子の構造と周期表",
    "化学結合",
    "物質量と濃度",
    "化学反応式と量的関係",
    "酸と塩基",
    "中和反応",
    "酸化還元",
    "実験・グラフ・読解問題",
    "総合問題",
]

DRAFT_ONLY_KEYS = {"reviewStatus", "sourceFamily", "qualityNote"}


def q(category, unit, topic, difficulty, skill, question, choices, answer_index, explanation, point=None, extra=None):
    item = {
        "category": category,
        "unit": unit,
        "topic": topic,
        "difficulty": difficulty,
        "skill": skill,
        "question": question,
        "choices": choices,
        "answerIndex": answer_index,
        "explanation": explanation,
    }
    if point:
        item["point"] = point
    if extra:
        item["extra"] = extra
    return item


def rotate_choices(item, shift):
    choices = item["choices"]
    answer = item["answerIndex"]
    paired = list(enumerate(choices))
    shift %= len(paired)
    rotated = paired[shift:] + paired[:shift]
    item = dict(item)
    item["choices"] = [choice for _, choice in rotated]
    item["answerIndex"] = [old_index for old_index, _ in rotated].index(answer)
    return item


def make_family(name, category, generator, max_variants=6):
    return {
        "name": name,
        "category": category,
        "generator": generator,
        "max_variants": max_variants,
    }


def family_material_classification():
    rows = [
        ("空気", "窒素や酸素など複数の気体が混ざっている", "混合物"),
        ("酸素 O2", "酸素元素だけからなる", "単体"),
        ("水 H2O", "水素と酸素が一定の割合で結びついている", "化合物"),
        ("食塩水", "水と塩化ナトリウムが混ざっている", "混合物"),
        ("銅 Cu", "銅元素だけからなる", "単体"),
        ("二酸化炭素 CO2", "炭素と酸素が一定の割合で結びついている", "化合物"),
    ]
    choices = ["単体", "化合物", "混合物", "同位体", "イオン"]
    return [
        q(
            "物質の構成",
            "物質の分類",
            "単体・化合物・混合物",
            2,
            "判断",
            f"{name} の分類として最も適切なのはどれか。",
            choices,
            choices.index(answer),
            f"{name} は、{reason}ため、{answer}に分類される。",
            "単体・化合物・混合物は、粒子の種類と混ざり方で判断する。",
        )
        for name, reason, answer in rows
    ]


def family_formula_composition():
    rows = [
        ("NH3", "水素", 3),
        ("H2SO4", "酸素", 4),
        ("CaCO3", "酸素", 3),
        ("CH3COOH", "炭素", 2),
        ("C6H12O6", "水素", 12),
        ("NaHCO3", "ナトリウム", 1),
    ]
    items = []
    for formula, element, count in rows:
        choices = [f"{max(1, count - 2)} 個", f"{max(1, count - 1)} 個", f"{count} 個", f"{count + 1} 個", f"{count + 2} 個"]
        choices = list(dict.fromkeys(choices))
        while len(choices) < 5:
            choices.append(f"{len(choices) + count} 個")
        items.append(
            q(
                "物質の構成",
                "化学式",
                "組成",
                2,
                "理解",
                f"{formula} 1分子または1式量中に含まれる {element} 原子の数はいくつか。",
                choices[:5],
                choices[:5].index(f"{count} 個"),
                f"{formula} の添字を読むと、{element} 原子は {count} 個含まれる。",
            )
        )
    return items


def family_atomic_structure():
    rows = [
        (6, 12, 6),
        (8, 16, 8),
        (11, 23, 12),
        (17, 35, 18),
        (20, 40, 20),
        (26, 56, 30),
    ]
    items = []
    for protons, mass_number, neutrons in rows:
        choices = [f"{protons} 個", f"{neutrons} 個", f"{mass_number} 個", f"{mass_number + protons} 個", f"{abs(neutrons - protons)} 個"]
        items.append(
            q(
                "物質の構成",
                "原子の構造",
                "質量数",
                3,
                "計算",
                f"陽子数が {protons}、質量数が {mass_number} の原子の中性子数はいくつか。",
                choices,
                1,
                f"質量数は陽子数と中性子数の和である。したがって {mass_number}-{protons}={neutrons} 個。",
            )
        )
    return items


def family_electron_configuration():
    rows = [
        (11, "ナトリウム", "2-8-1", 1),
        (12, "マグネシウム", "2-8-2", 2),
        (13, "アルミニウム", "2-8-3", 3),
        (16, "硫黄", "2-8-6", 6),
        (17, "塩素", "2-8-7", 7),
        (18, "アルゴン", "2-8-8", 8),
    ]
    items = []
    for atomic_number, name, config, valence in rows:
        choices = ["1 個", "2 個", "3 個", "6 個", "7 個", "8 個"]
        if f"{valence} 個" not in choices:
            choices[0] = f"{valence} 個"
        items.append(
            q(
                "原子の構造と周期表",
                "電子配置",
                "最外殻電子",
                2,
                "理解",
                f"原子番号 {atomic_number} の {name} 原子の最外殻電子数として正しいものはどれか。",
                choices[:5],
                choices[:5].index(f"{valence} 個"),
                f"{name} の電子配置は {config} であり、最外殻電子数は {valence} 個である。",
            )
        )
    return items


def family_periodic_trends():
    return [
        q("原子の構造と周期表", "周期律", "原子半径", 3, "理解",
          "同じ周期の元素で、左から右へ進むと原子半径は一般にどう変化するか。",
          ["大きくなる", "小さくなる", "変化しない", "周期表だけでは判断できない", "必ず2倍になる"], 1,
          "同じ周期では原子番号が大きくなるにつれて原子核の引力が強まり、原子半径は小さくなる傾向がある。"),
        q("原子の構造と周期表", "周期律", "電気陰性度", 3, "理解",
          "周期表で電気陰性度が大きくなりやすい方向として最も適切なのはどれか。",
          ["左下方向", "右上方向", "真下方向のみ", "同じ周期では左方向", "原子番号が小さいほど常に大きい"], 1,
          "電気陰性度は周期表の右上に行くほど大きくなる傾向がある。"),
        q("原子の構造と周期表", "周期表", "族", 2, "知識",
          "同じ族の元素で似ていることが多い性質はどれか。",
          ["化学的性質", "質量数", "中性子数", "同位体の存在比", "原子番号"], 0,
          "同じ族の元素は価電子数が同じことが多く、化学的性質が似ている。"),
        q("原子の構造と周期表", "周期表", "ハロゲン", 2, "知識",
          "次のうち、ハロゲンに属する元素はどれか。",
          ["Na", "Mg", "Al", "Cl", "Ar"], 3,
          "塩素 Cl は17族元素で、ハロゲンに属する。"),
        q("原子の構造と周期表", "周期表", "希ガス", 2, "知識",
          "次のうち、希ガスに属する元素はどれか。",
          ["Li", "C", "O", "Cl", "Ne"], 4,
          "ネオン Ne は18族元素で、希ガスに属する。"),
        q("原子の構造と周期表", "イオン", "イオンの生成", 3, "理解",
          "塩素原子が電子を1個受け取ると、どのようなイオンになるか。",
          ["Cl+", "Cl-", "Cl2+", "Na+", "Ar+"], 1,
          "電子を受け取ると負の電荷をもつ陰イオンになる。塩素は Cl- になりやすい。"),
    ]


def family_bond_type():
    rows = [
        ("NaCl", "イオン結合", "Na+ と Cl- の静電気的な引力でできる"),
        ("H2O", "共有結合", "非金属原子どうしが電子対を共有してできる"),
        ("Cu", "金属結合", "金属陽イオンと自由電子の間の結びつきでできる"),
        ("MgO", "イオン結合", "Mg2+ と O2- の静電気的な引力でできる"),
        ("CO2", "共有結合", "炭素と酸素が電子対を共有してできる"),
        ("Al", "金属結合", "金属結晶中で自由電子が存在する"),
    ]
    choices = ["共有結合", "イオン結合", "金属結合", "水素結合", "分子間力"]
    return [
        q("化学結合", "結合の種類", "結合の判定", 2, "判断",
          f"{substance} に主に見られる結合として最も適切なのはどれか。",
          choices, choices.index(answer),
          f"{substance} は {reason} ため、{answer} と考える。")
        for substance, answer, reason in rows
    ]


def family_molecular_shape():
    rows = [
        ("CO2", "直線形", "中心原子の両側に酸素原子が結合し、分子全体が一直線になる"),
        ("H2O", "折れ線形", "酸素原子上の孤立電子対の影響で折れ線形になる"),
        ("NH3", "三角錐形", "窒素原子上の孤立電子対により三角錐形になる"),
        ("CH4", "正四面体形", "炭素の周囲に4つの結合電子対が正四面体状に配置する"),
    ]
    choices = ["直線形", "折れ線形", "三角錐形", "正四面体形", "平面正方形"]
    return [
        q("化学結合", "共有結合", "分子形状", 3, "理解",
          f"{formula} の分子形状として正しいものはどれか。",
          choices, choices.index(shape),
          f"{formula} は {reason}。")
        for formula, shape, reason in rows
    ]


def family_polarity():
    rows = [
        ("NH3", "極性分子", "三角錐形で分子全体の電荷の偏りが打ち消されない"),
        ("H2O", "極性分子", "折れ線形で O-H 結合の極性が打ち消されない"),
        ("CO2", "無極性分子", "直線形で C=O 結合の極性が左右で打ち消される"),
        ("CH4", "無極性分子", "正四面体形で結合の極性が全体として打ち消される"),
        ("BF3", "無極性分子", "平面三角形で結合の極性が対称に打ち消される"),
    ]
    choices = ["極性分子", "無極性分子", "イオン結晶", "金属結晶", "単原子分子"]
    return [
        q("化学結合", "極性", "極性分子", 3, "判断",
          f"{formula} の分子全体の極性として最も適切なのはどれか。",
          choices, choices.index(answer),
          f"{formula} は {reason} ため、{answer} である。")
        for formula, answer, reason in rows
    ]


def family_mol_mass():
    rows = [
        ("H2O", 18, 18, "1.0 mol"),
        ("CO2", 44, 22, "0.50 mol"),
        ("NaCl", 58.5, 117, "2.0 mol"),
        ("NH3", 17, 51, "3.0 mol"),
        ("O2", 32, 16, "0.50 mol"),
        ("CH4", 16, 32, "2.0 mol"),
    ]
    choices = ["0.25 mol", "0.50 mol", "1.0 mol", "2.0 mol", "3.0 mol"]
    items = []
    for formula, molar_mass, mass, answer in rows:
        items.append(
            q("物質量と濃度", "物質量", "質量と物質量", 3, "計算",
              f"{formula} のモル質量を {molar_mass} g/mol とすると、{mass} g の {formula} は何 mol か。",
              choices, choices.index(answer),
              f"物質量は質量をモル質量で割って求める。{mass}÷{molar_mass}={answer} である。")
        )
    return items


def family_concentration():
    rows = [
        (10, 100, "10 %"),
        (5, 100, "5.0 %"),
        (20, 200, "10 %"),
        (25, 250, "10 %"),
        (15, 300, "5.0 %"),
        (40, 200, "20 %"),
    ]
    choices = ["2.5 %", "5.0 %", "10 %", "20 %", "40 %"]
    return [
        q("物質量と濃度", "濃度", "質量パーセント濃度", 3, "計算",
          f"溶質 {solute} g を含む溶液 {solution} g の質量パーセント濃度は何 % か。",
          choices, choices.index(answer),
          f"質量パーセント濃度は 溶質の質量÷溶液の質量×100 で求める。{solute}÷{solution}×100={answer}。")
        for solute, solution, answer in rows
    ]


def family_molarity_and_dilution():
    return [
        q("物質量と濃度", "濃度", "モル濃度", 3, "計算",
          "0.20 mol の溶質を水に溶かして 500 mL の溶液にした。モル濃度は何 mol/L か。",
          ["0.10 mol/L", "0.20 mol/L", "0.40 mol/L", "1.0 mol/L", "2.5 mol/L"], 2,
          "500 mL = 0.500 L なので、0.20÷0.500=0.40 mol/L である。"),
        q("物質量と濃度", "濃度", "モル濃度", 3, "計算",
          "0.50 mol の溶質を水に溶かして 250 mL の溶液にした。モル濃度は何 mol/L か。",
          ["0.25 mol/L", "0.50 mol/L", "1.0 mol/L", "2.0 mol/L", "4.0 mol/L"], 3,
          "250 mL = 0.250 L なので、0.50÷0.250=2.0 mol/L である。"),
        q("物質量と濃度", "濃度", "希釈", 3, "計算",
          "2.0 mol/L の溶液 100 mL を水で薄めて 400 mL にした。薄めた後の濃度は何 mol/L か。",
          ["0.25 mol/L", "0.50 mol/L", "1.0 mol/L", "2.0 mol/L", "4.0 mol/L"], 1,
          "希釈しても溶質の物質量は変わらない。体積が4倍になるので濃度は 0.50 mol/L になる。"),
        q("物質量と濃度", "物質量", "気体の体積", 2, "計算",
          "標準状態で 0.50 mol の気体の体積は何 L か。ただし 1 mol = 22.4 L とする。",
          ["5.6 L", "11.2 L", "22.4 L", "44.8 L", "56.0 L"], 1,
          "標準状態では気体 1 mol が 22.4 L なので、0.50×22.4=11.2 L である。"),
        q("物質量と濃度", "物質量", "粒子数", 3, "計算",
          "アボガドロ定数を 6.0×10^23 /mol とすると、0.25 mol の粒子数は何個か。",
          ["1.5×10^23 個", "3.0×10^23 個", "6.0×10^23 個", "1.2×10^24 個", "2.4×10^24 個"], 0,
          "0.25×6.0×10^23=1.5×10^23 個である。"),
        q("物質量と濃度", "物質量", "粒子数", 3, "計算",
          "アボガドロ定数を 6.0×10^23 /mol とすると、2.0 mol の粒子数は何個か。",
          ["3.0×10^23 個", "6.0×10^23 個", "1.2×10^24 個", "2.0×10^24 個", "6.0×10^24 個"], 2,
          "2.0×6.0×10^23=1.2×10^24 個である。"),
    ]


def family_stoichiometry():
    rows = [
        ("2H2 + O2 → 2H2O", "H2", "O2", "4.0 mol", "2.0 mol", "H2:O2=2:1"),
        ("N2 + 3H2 → 2NH3", "N2", "NH3", "1.0 mol", "2.0 mol", "N2:NH3=1:2"),
        ("2Na + Cl2 → 2NaCl", "Na", "Cl2", "2.0 mol", "1.0 mol", "Na:Cl2=2:1"),
        ("CH4 + 2O2 → CO2 + 2H2O", "CH4", "O2", "3.0 mol", "6.0 mol", "CH4:O2=1:2"),
        ("2KClO3 → 2KCl + 3O2", "KClO3", "O2", "2.0 mol", "3.0 mol", "KClO3:O2=2:3"),
        ("2Mg + O2 → 2MgO", "Mg", "MgO", "2.0 mol", "2.0 mol", "Mg:MgO=1:1"),
    ]
    choices = ["0.50 mol", "1.0 mol", "2.0 mol", "3.0 mol", "6.0 mol"]
    items = []
    for reaction, from_substance, to_substance, amount, answer, ratio in rows:
        items.append(
            q("化学反応式と量的関係", "量的関係", "物質量の比", 3, "計算",
              f"{reaction} の反応で、{amount} の {from_substance} に対応する {to_substance} は何 mol か。",
              choices, choices.index(answer),
              f"反応式の係数から {ratio} である。したがって {to_substance} は {answer} である。")
        )
    return items


def family_balancing():
    return [
        q("化学反応式と量的関係", "化学反応式", "係数合わせ", 3, "判断",
          "Al + O2 → Al2O3 を係数で正しくそろえたものはどれか。",
          ["Al + O2 → Al2O3", "2Al + O2 → Al2O3", "4Al + 3O2 → 2Al2O3", "Al + 3O2 → Al2O3", "2Al + 3O2 → 2Al2O3"], 2,
          "左右の Al と O の原子数をそろえると、4Al + 3O2 → 2Al2O3 となる。"),
        q("化学反応式と量的関係", "化学反応式", "係数合わせ", 3, "判断",
          "水素と塩素から塩化水素ができる反応式として正しいものはどれか。",
          ["H2 + Cl2 → HCl", "H2 + Cl2 → 2HCl", "2H + Cl → HCl", "H2 + 2Cl2 → 2HCl", "HCl → H2 + Cl2"], 1,
          "H と Cl の原子数が左右で等しくなるようにすると、H2 + Cl2 → 2HCl である。"),
        q("化学反応式と量的関係", "化学反応式", "燃焼", 2, "理解",
          "炭素が完全燃焼するときの反応式として正しいものはどれか。",
          ["C + O2 → CO2", "C + O2 → CO", "CO2 → C + O2", "C + H2 → CH4", "2C + O2 → 2CO2"], 0,
          "炭素が十分な酸素と反応して完全燃焼すると、二酸化炭素 CO2 が生じる。"),
    ]


def family_acid_base():
    return [
        q("酸と塩基", "酸・塩基の定義", "ブレンステッド・ローリー", 2, "知識",
          "ブレンステッド・ローリーの定義で、酸とはどのような物質か。",
          ["H+ を供与する物質", "H+ を受容する物質", "電子対を供与する物質", "電子を失う物質", "OH- を必ず含む物質"], 0,
          "ブレンステッド・ローリーの酸は H+ を供与する物質である。"),
        q("酸と塩基", "酸・塩基の定義", "ブレンステッド・ローリー", 2, "知識",
          "ブレンステッド・ローリーの定義で、塩基とはどのような物質か。",
          ["H+ を供与する物質", "H+ を受容する物質", "酸素を放出する物質", "電子を失う物質", "中性子を受け取る物質"], 1,
          "ブレンステッド・ローリーの塩基は H+ を受容する物質である。"),
        q("酸と塩基", "酸・塩基の性質", "強弱", 2, "知識",
          "次のうち、強酸として扱われるものはどれか。",
          ["CH3COOH", "HCl", "NH3", "NaOH", "H2O"], 1,
          "HCl は水中でほぼ完全に電離するため、強酸として扱われる。"),
        q("酸と塩基", "酸・塩基の性質", "強弱", 2, "知識",
          "次のうち、弱酸として扱われるものはどれか。",
          ["HCl", "HNO3", "H2SO4", "CH3COOH", "NaOH"], 3,
          "酢酸 CH3COOH は水中で一部だけ電離する弱酸である。"),
        q("酸と塩基", "酸・塩基の性質", "電離", 3, "理解",
          "NaOH が水中で電離したときに生じるイオンの組み合わせとして正しいものはどれか。",
          ["Na+ と OH-", "Na- と OH+", "H+ と Cl-", "NH4+ と Cl-", "Na+ と H+"], 0,
          "NaOH は水中で Na+ と OH- に電離する。"),
        q("酸と塩基", "pH", "pOH", 3, "計算",
          "25℃で pH が 11 の水溶液の pOH はいくつか。",
          ["1", "3", "7", "11", "14"], 1,
          "25℃では pH + pOH = 14 なので、pOH = 14-11=3 である。"),
    ]


def family_ph():
    rows = [
        ("1.0×10^-1", "1", "酸性"),
        ("1.0×10^-2", "2", "酸性"),
        ("1.0×10^-4", "4", "酸性"),
        ("1.0×10^-7", "7", "中性"),
        ("1.0×10^-12", "12", "塩基性"),
    ]
    items = []
    for concentration, ph, nature in rows:
        choices = ["1", "2", "4", "7", "12"]
        items.append(
            q("酸と塩基", "pH", "pH の計算", 3, "計算",
              f"水素イオン濃度が {concentration} mol/L の水溶液の pH はいくつか。",
              choices, choices.index(ph),
              f"pH = -log[H+] なので、[H+] = {concentration} mol/L のとき pH は {ph} である。この溶液は{nature}を示す。")
        )
    return items


def family_neutralization():
    return [
        q("中和反応", "中和", "生成物", 2, "知識",
          "酸と塩基の中和反応で一般に生じるものはどれか。",
          ["塩と水", "酸素と水素", "金属と酸素", "電子と陽子", "単体と混合物"], 0,
          "中和反応では、酸と塩基から塩と水が生じる。"),
        q("中和反応", "滴定", "等量点", 3, "理解",
          "中和滴定における等量点とは何を表す点か。",
          ["指示薬を入れ始めた点", "酸と塩基が過不足なく反応した点", "溶液が必ず赤色になる点", "溶液の体積が 1 L になった点", "沈殿が必ず生じる点"], 1,
          "等量点は、酸と塩基が反応式の係数比どおりにちょうど反応し終えた点である。"),
        q("中和反応", "滴定", "指示薬", 2, "知識",
          "フェノールフタレイン溶液が赤色を示すのは、一般にどの性質の溶液か。",
          ["強い酸性", "弱い酸性", "中性", "塩基性", "酸化性"], 3,
          "フェノールフタレインは酸性から中性では無色、塩基性で赤色を示す。"),
        q("中和反応", "滴定", "計算", 4, "計算",
          "0.10 mol/L の HCl 20 mL を中和するのに、0.10 mol/L の NaOH は何 mL 必要か。",
          ["5 mL", "10 mL", "20 mL", "40 mL", "100 mL"], 2,
          "HCl と NaOH は 1:1 で反応し、濃度も同じなので必要な体積も 20 mL である。"),
        q("中和反応", "滴定", "計算", 4, "計算",
          "0.20 mol/L の NaOH 10 mL を中和するのに、0.10 mol/L の HCl は何 mL 必要か。",
          ["5 mL", "10 mL", "20 mL", "40 mL", "100 mL"], 2,
          "NaOH の物質量は 0.20×0.010=0.0020 mol。HCl も 0.0020 mol 必要なので、0.0020÷0.10=0.020 L = 20 mL。"),
        q("中和反応", "中和", "塩の性質", 3, "理解",
          "強酸 HCl と弱塩基 NH3 の中和でできる NH4Cl 水溶液は、おおむねどの性質を示すか。",
          ["強い塩基性", "弱い塩基性", "中性", "弱い酸性", "必ず性質を示さない"], 3,
          "強酸と弱塩基からできる塩の水溶液は、弱塩基由来の陽イオンが加水分解し、弱い酸性を示す。"),
    ]


def family_redox():
    return [
        q("酸化還元", "電子移動", "酸化の定義", 2, "知識",
          "電子の授受で考えたとき、酸化とはどのような変化か。",
          ["電子を失う変化", "電子を受け取る変化", "H+ を受け取る変化", "OH- を放出する変化", "水をつくる変化"], 0,
          "電子を失う変化が酸化である。"),
        q("酸化還元", "電子移動", "還元の定義", 2, "知識",
          "電子の授受で考えたとき、還元とはどのような変化か。",
          ["電子を失う変化", "電子を受け取る変化", "H+ を供与する変化", "中和する変化", "蒸発する変化"], 1,
          "電子を受け取る変化が還元である。"),
        q("酸化還元", "酸化数", "酸化数", 3, "計算",
          "H2O 中の酸素の酸化数として正しいものはどれか。",
          ["-2", "-1", "0", "+1", "+2"], 0,
          "化合物中の水素は通常 +1 であり、H2O 全体は中性なので酸素は -2 になる。"),
        q("酸化還元", "酸化数", "酸化数", 4, "計算",
          "SO4^2- 中の硫黄 S の酸化数はいくつか。",
          ["-2", "0", "+2", "+4", "+6"], 4,
          "酸素を -2 とすると4個で -8、イオン全体が -2 なので S は +6 である。"),
        q("酸化還元", "酸化剤と還元剤", "酸化剤", 3, "理解",
          "酸化剤についての説明として正しいものはどれか。",
          ["相手を酸化し、自身は還元される", "相手を還元し、自身は酸化される", "必ず水素イオンを供与する", "必ず塩基性を示す", "酸化数が変化しない物質である"], 0,
          "酸化剤は相手から電子を奪って相手を酸化し、自身は電子を受け取って還元される。"),
        q("酸化還元", "反応の判定", "酸化数の変化", 4, "判断",
          "酸化還元反応であるかどうかを判断する最も基本的な基準はどれか。",
          ["酸化数が変化するか", "水が生じるか", "沈殿が生じるか", "色が必ず赤くなるか", "pH が7になるか"], 0,
          "酸化還元反応では、反応の前後で酸化数が変化する原子がある。"),
    ]


def family_experiment():
    return [
        q("実験・グラフ・読解問題", "実験操作", "ろ過", 2, "知識",
          "水に溶けない固体と液体を分ける操作として最も適切なのはどれか。",
          ["蒸留", "再結晶", "ろ過", "中和", "電気分解"], 2,
          "水に溶けない固体を液体から分けるには、ろ紙を用いるろ過が適している。"),
        q("実験・グラフ・読解問題", "実験操作", "蒸留", 3, "理解",
          "水とエタノールのように沸点の異なる液体を分ける操作として適切なのはどれか。",
          ["ろ過", "蒸留", "沈殿", "中和", "再結晶"], 1,
          "沸点の違いを利用して液体を分ける操作は蒸留である。"),
        q("実験・グラフ・読解問題", "実験操作", "安全", 2, "判断",
          "酸を水で薄めるときの操作として安全上適切なのはどれか。",
          ["水を酸に一気に加える", "酸を水に少しずつ加える", "加熱しながら密閉する", "素手で混ぜる", "水を使わず蒸発させる"], 1,
          "濃い酸を薄めると発熱するため、酸を水に少しずつ加えて混ぜるのが安全である。"),
        q("実験・グラフ・読解問題", "実験操作", "メスフラスコ", 3, "知識",
          "正確な濃度の溶液を一定体積に調製するとき、最後に標線まで水を加える器具はどれか。",
          ["ビーカー", "メスフラスコ", "蒸発皿", "ろうと", "試験管"], 1,
          "メスフラスコは、溶液を正確な体積に調製するための器具である。"),
        q("実験・グラフ・読解問題", "グラフ解析", "溶解度曲線", 3, "読解",
          "溶解度曲線で、ある温度の点が曲線上にある溶液はどの状態を表すか。",
          ["不飽和溶液", "飽和溶液", "過冷却液体", "純物質", "中和溶液"], 1,
          "溶解度曲線上の点は、その温度で最大量の溶質が溶けている飽和溶液を表す。"),
        q("実験・グラフ・読解問題", "実験操作", "加熱操作", 2, "判断",
          "試験管内の液体を加熱するときの注意として適切なのはどれか。",
          ["試験管の口を人に向ける", "試験管の口を人に向けない", "密栓して強く加熱する", "液体を満杯に入れる", "炎の中に手を入れて支える"], 1,
          "突沸や液体の飛散に備え、試験管の口を自分や周囲の人に向けてはいけない。"),
    ]


def family_integrated():
    return [
        q("総合問題", "総合演習", "分類と結合", 3, "判断",
          "金属ナトリウム、塩化ナトリウム、二酸化炭素の結合や粒子の種類の組み合わせとして最も適切なのはどれか。",
          ["金属結合・イオン結晶・分子", "共有結合・金属結合・イオン結晶", "イオン結晶・分子・金属結合", "分子・共有結合・金属結合", "水素結合・イオン結晶・金属結合"], 0,
          "金属ナトリウムは金属結合、塩化ナトリウムはイオン結晶、二酸化炭素は分子として扱う。"),
        q("総合問題", "総合演習", "反応の分類", 3, "判断",
          "HCl + NaOH → NaCl + H2O は主にどの反応に分類されるか。",
          ["中和反応", "酸化還元反応", "燃焼反応", "沈殿反応", "電気分解"], 0,
          "酸 HCl と塩基 NaOH が反応して塩と水を生じるので、中和反応である。"),
        q("総合問題", "総合演習", "式量と物質量", 3, "計算",
          "二酸化炭素 CO2 の式量を C=12、O=16 とすると、44 g の CO2 は何 mol か。",
          ["0.50 mol", "1.0 mol", "2.0 mol", "12 mol", "44 mol"], 1,
          "CO2 の式量は 12+16×2=44 なので、44 g は 1.0 mol である。"),
        q("総合問題", "総合演習", "pH", 4, "計算",
          "水素イオン濃度が 1.0×10^-2 mol/L の水溶液の pH はいくつか。",
          ["1", "2", "7", "12", "14"], 1,
          "pH = -log[H+] なので、[H+] = 1.0×10^-2 mol/L のとき pH は 2 である。"),
        q("総合問題", "総合演習", "反応式とモル", 4, "計算",
          "2H2 + O2 → 2H2O の反応で、2.0 mol の O2 がすべて反応すると H2O は何 mol 生じるか。",
          ["1.0 mol", "2.0 mol", "3.0 mol", "4.0 mol", "8.0 mol"], 3,
          "係数比は O2:H2O = 1:2 なので、2.0 mol の O2 から 4.0 mol の H2O が生じる。"),
        q("総合問題", "総合演習", "実験と濃度", 4, "計算",
          "5.0 g の食塩を水に溶かして 100 g の食塩水にした。この食塩水の質量パーセント濃度は何 % か。",
          ["0.50 %", "5.0 %", "10 %", "20 %", "50 %"], 1,
          "質量パーセント濃度は 5.0 g÷100 g×100 = 5.0 % である。"),
    ]


FAMILIES = [
    make_family("物質分類", "物質の構成", family_material_classification),
    make_family("化学式の組成", "物質の構成", family_formula_composition),
    make_family("質量数と中性子数", "物質の構成", family_atomic_structure),
    make_family("電子配置", "原子の構造と周期表", family_electron_configuration),
    make_family("周期律", "原子の構造と周期表", family_periodic_trends),
    make_family("結合の種類", "化学結合", family_bond_type),
    make_family("分子形状", "化学結合", family_molecular_shape),
    make_family("分子の極性", "化学結合", family_polarity),
    make_family("モル質量", "物質量と濃度", family_mol_mass),
    make_family("質量パーセント濃度", "物質量と濃度", family_concentration),
    make_family("モル濃度と希釈", "物質量と濃度", family_molarity_and_dilution),
    make_family("反応式の量的関係", "化学反応式と量的関係", family_stoichiometry),
    make_family("係数合わせ", "化学反応式と量的関係", family_balancing, max_variants=3),
    make_family("酸塩基の定義", "酸と塩基", family_acid_base),
    make_family("pH計算", "酸と塩基", family_ph, max_variants=5),
    make_family("中和反応", "中和反応", family_neutralization),
    make_family("酸化還元", "酸化還元", family_redox),
    make_family("実験操作", "実験・グラフ・読解問題", family_experiment),
    make_family("総合演習", "総合問題", family_integrated),
]


def load_json(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")


def next_id(existing):
    max_num = 0
    for item in existing:
        qid = item.get("id", "")
        if qid.startswith("CB-") and qid[3:].isdigit():
            max_num = max(max_num, int(qid[3:]))
    return max_num + 1


def normalize_stem(text):
    text = re.sub(r"\d+(?:\.\d+)?", "N", text)
    text = re.sub(r"[A-Z][a-z]?\d*", "X", text)
    text = re.sub(r"\s+", "", text)
    return text


def validate_items(items):
    errors = []
    seen_ids = set()
    for index, item in enumerate(items, 1):
        label = item.get("id", f"{index}番目")
        if item.get("id") in seen_ids:
            errors.append(f"{label}: id が重複しています")
        seen_ids.add(item.get("id"))
        if item.get("category") not in CATEGORIES:
            errors.append(f"{label}: category が不正です")
        if not isinstance(item.get("difficulty"), int) or not 1 <= item["difficulty"] <= 5:
            errors.append(f"{label}: difficulty は 1〜5 の整数にしてください")
        choices = item.get("choices")
        if not isinstance(choices, list) or not 5 <= len(choices) <= 8:
            errors.append(f"{label}: choices は 5〜8 個にしてください")
            continue
        if len(choices) != len(set(choices)):
            errors.append(f"{label}: choices に重複があります")
        answer = item.get("answerIndex")
        if not isinstance(answer, int) or answer < 0 or answer >= len(choices):
            errors.append(f"{label}: answerIndex が choices の範囲外です")
        for key in ("question", "explanation"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{label}: {key} が空です")
        if len(item.get("explanation", "")) < 20:
            errors.append(f"{label}: explanation が短すぎます")
    return errors


def quality_report(items):
    warnings = []
    categories = Counter(item.get("category") for item in items)
    skills = Counter(item.get("skill", "未設定") for item in items)
    answers = Counter(item.get("answerIndex") for item in items)
    families = Counter(item.get("sourceFamily", "既存") for item in items)

    normalized = defaultdict(list)
    for item in items:
        normalized[normalize_stem(item.get("question", ""))].append(item.get("id", "no-id"))
    similar_groups = {stem: ids for stem, ids in normalized.items() if len(ids) >= 4}
    for ids in similar_groups.values():
        warnings.append(f"類似した問題文が多い可能性: {', '.join(ids[:6])}")

    total = len(items)
    if total:
        for index, count in answers.items():
            if count / total > 0.35:
                warnings.append(f"正解位置 {index} が多めです: {count}/{total}")

    for family, count in families.items():
        if family != "既存" and count > 8:
            warnings.append(f"同じ問題ファミリーが多めです: {family} {count}問")

    return {
        "total": total,
        "categories": dict(categories),
        "skills": dict(skills),
        "answerIndexes": dict(sorted(answers.items())),
        "families": dict(families),
        "warnings": warnings,
    }


def build_candidates():
    candidates = []
    for family in FAMILIES:
        variants = family["generator"]()[:family["max_variants"]]
        for variant_index, item in enumerate(variants):
            item = rotate_choices(item, variant_index % 5)
            item["reviewStatus"] = "draft"
            item["sourceFamily"] = family["name"]
            item["qualityNote"] = "下書き候補。既存問題との重複、授業範囲、選択肢の妥当性を確認してから採用する。"
            candidates.append(item)
    return candidates


def generate_drafts(count, out_path):
    existing = load_json(QUESTIONS_FILE)
    existing_signatures = {(item.get("category"), normalize_stem(item.get("question", ""))) for item in existing}
    candidates = build_candidates()
    selected = []
    next_num = next_id(existing)

    for item in candidates:
        signature = (item.get("category"), normalize_stem(item.get("question", "")))
        if signature in existing_signatures:
            continue
        item = dict(item)
        item["id"] = f"CB-DRAFT-{len(selected) + 1:03d}"
        selected.append(item)
        if len(selected) >= count:
            break

    errors = validate_items(selected)
    if errors:
        raise SystemExit("生成した下書きにエラーがあります:\n" + "\n".join(errors[:20]))

    write_json(out_path, selected)
    report = quality_report(selected)
    print(f"{out_path} に {len(selected)} 問の下書きを作成しました。")
    print_report(report)
    if len(selected) < count:
        print(f"注意: 現在の良問テンプレートでは {len(selected)} 問まで生成できます。テンプレート追加で増やしてください。")
    print(f"採用時の次の本番ID目安: CB-{next_num:03d}")


def print_report(report):
    print("\n[品質レポート]")
    print(f"総数: {report['total']}")
    print("分野:", ", ".join(f"{k}:{v}" for k, v in sorted(report["categories"].items())))
    print("技能:", ", ".join(f"{k}:{v}" for k, v in sorted(report["skills"].items())))
    print("正解位置:", ", ".join(f"{k}:{v}" for k, v in report["answerIndexes"].items()))
    if report["warnings"]:
        print("警告:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    else:
        print("警告: なし")


def check_file(path):
    items = load_json(path)
    errors = validate_items(items)
    report = quality_report(items)
    print_report(report)
    if errors:
        raise SystemExit("形式エラー:\n" + "\n".join(errors[:30]))
    print(f"{path} の形式チェックはOKです。")


def promote_drafts(path):
    existing = load_json(QUESTIONS_FILE)
    drafts = load_json(path)
    approved = [item for item in drafts if item.get("reviewStatus") == "approved"]
    if not approved:
        raise SystemExit("reviewStatus が approved の問題がありません。採用する問題だけ approved にしてください。")

    existing_questions = {(item.get("category"), normalize_stem(item.get("question", ""))) for item in existing}
    next_num = next_id(existing)
    promoted = []
    for draft in approved:
        item = {key: value for key, value in draft.items() if key not in DRAFT_ONLY_KEYS}
        signature = (item.get("category"), normalize_stem(item.get("question", "")))
        if signature in existing_questions:
            continue
        item["id"] = f"CB-{next_num:03d}"
        next_num += 1
        promoted.append(item)
        existing_questions.add(signature)

    merged = existing + promoted
    errors = validate_items(merged)
    if errors:
        raise SystemExit("採用後の問題データにエラーがあります:\n" + "\n".join(errors[:30]))

    write_json(QUESTIONS_FILE, merged)
    print(f"{len(promoted)} 問を {QUESTIONS_FILE} に採用しました。合計 {len(merged)} 問です。")


def main():
    parser = argparse.ArgumentParser(description="化学基礎クイズの良問候補を生成・検査します。")
    parser.add_argument("--count", type=int, default=80, help="生成する下書き問題数")
    parser.add_argument("--out", type=Path, default=DEFAULT_DRAFT_FILE, help="下書きの出力先")
    parser.add_argument("--check", type=Path, help="指定JSONを品質チェックする")
    parser.add_argument("--promote", type=Path, help="approved の下書きだけ questions.json に採用する")
    args = parser.parse_args()

    if args.check:
        check_file(args.check)
        return
    if args.promote:
        promote_drafts(args.promote)
        return
    generate_drafts(args.count, args.out)


if __name__ == "__main__":
    main()
