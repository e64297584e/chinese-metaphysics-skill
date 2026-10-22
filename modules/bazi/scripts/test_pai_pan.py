#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pai_pan.py 回归：用 stdout 断言黄金用例与日界/大运/农历/流年。"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "pai_pan.py")
PY = sys.executable


def run_pai(*args):
    proc = subprocess.run(
        [PY, SCRIPT] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def section(stdout, title):
    """截取 '## title' 到下一个 '##'（不含）。"""
    marker = "## " + title
    start = stdout.find(marker)
    if start < 0:
        return ""
    rest = stdout[start + len(marker) :]
    nxt = rest.find("\n## ")
    if nxt < 0:
        return rest
    return rest[:nxt]


def table_row(stdout, cell0):
    for line in stdout.splitlines():
        if line.startswith("| " + cell0 + " |"):
            return [p.strip() for p in line.strip().strip("|").split("|")]
    return []


def pillars(stdout):
    gan = table_row(stdout, "天干")
    zhi = table_row(stdout, "地支")
    # gan/zhi: ['天干', 年, 月, 日, 时]
    return {
        "year": (gan[1] if gan else "") + (zhi[1] if zhi else ""),
        "month": (gan[2] if gan else "") + (zhi[2] if zhi else ""),
        "day": (gan[3] if gan else "") + (zhi[3] if zhi else ""),
        "hour": (gan[4] if gan else "") + (zhi[4] if zhi else ""),
        "gan": gan[1:] if gan else [],
        "zhi": zhi[1:] if zhi else [],
    }


def field(stdout, name):
    m = re.search(r"^- %s：(.+)$" % re.escape(name), stdout, re.M)
    return m.group(1).strip() if m else ""


class PaiPanTests(unittest.TestCase):
    def test_golden_1990_wushi_male(self):
        """1990-05-15 午时男：庚午 / 辛巳 / 庚辰 / 壬午，顺排，神煞已计算。"""
        code, out, err = run_pai("--solar", "1990-05-15", "--shichen", "午", "--sex", "男")
        self.assertEqual(code, 0, err)
        p = pillars(out)
        self.assertEqual(p["year"], "庚午")
        self.assertEqual(p["month"], "辛巳")
        self.assertEqual(p["day"], "庚辰")
        self.assertEqual(p["hour"], "壬午")
        self.assertIn("方向：顺排", out)
        shensha = section(out, "神煞").strip()
        self.assertNotEqual(shensha, "未计算")
        self.assertTrue(shensha)
        self.assertNotIn("天乙贵人", shensha)
        self.assertNotIn("Traceback", out)
        self.assertNotIn("Traceback", err)

    def test_before_lichun_year_is_jisi(self):
        """1990-02-03 10:00 在立春前，年柱己巳，不是庚午。"""
        code, out, err = run_pai("--solar", "1990-02-03", "--hour", "10:00", "--sex", "男")
        self.assertEqual(code, 0, err)
        p = pillars(out)
        self.assertEqual(p["year"], "己巳")
        self.assertNotEqual(p["year"], "庚午")

    def test_precise_lichun_boundary(self):
        """2048 立春约 12:04:44；边界前后不能被简式黄经的分钟误差混同。"""
        code_a, out_a, err_a = run_pai("--solar", "2048-02-04", "--hour", "12:00", "--sex", "男")
        code_b, out_b, err_b = run_pai("--solar", "2048-02-04", "--hour", "12:10", "--sex", "男")
        self.assertEqual(code_a, 0, err_a)
        self.assertEqual(code_b, 0, err_b)
        self.assertEqual(pillars(out_a)["year"], "丁卯")
        self.assertEqual(pillars(out_b)["year"], "戊辰")

    def test_official_2026_lichun_minute_boundary(self):
        """PMO anchors 04:02; pillar assertions are this repo's fixed-UTC+8 profile."""
        code_a, out_a, err_a = run_pai("--solar", "2026-02-04", "--hour", "04:01", "--sex", "男")
        code_b, out_b, err_b = run_pai("--solar", "2026-02-04", "--hour", "04:03", "--sex", "男")
        self.assertEqual(code_a, 0, err_a)
        self.assertEqual(code_b, 0, err_b)
        self.assertEqual(pillars(out_a)["year"], "乙巳")
        self.assertEqual(pillars(out_a)["month"], "己丑")
        self.assertEqual(pillars(out_b)["year"], "丙午")
        self.assertEqual(pillars(out_b)["month"], "庚寅")

    def test_gbt_reference_day_is_jiazi(self):
        """GB/T 33661-2017 section 6.3.2 anchors 1949-10-01 as 甲子日."""
        code, out, err = run_pai("--solar", "1949-10-01", "--hour", "12:00", "--sex", "男")
        self.assertEqual(code, 0, err)
        self.assertEqual(pillars(out)["day"], "甲子")

    def test_late_zi_uses_next_day_pillar(self):
        """23:30 夜子时：日柱用次日辛巳，时支子。"""
        code, out, err = run_pai("--solar", "1990-05-15", "--hour", "23:30", "--sex", "男")
        self.assertEqual(code, 0, err)
        p = pillars(out)
        self.assertEqual(p["day"], "辛巳")
        self.assertEqual(p["zhi"][3], "子")
        self.assertEqual(field(out, "子时"), "夜子时")

    def test_early_zi_keeps_same_day_pillar(self):
        """00:30 早子时：日柱仍庚辰，时支子。"""
        code, out, err = run_pai("--solar", "1990-05-15", "--hour", "00:30", "--sex", "男")
        self.assertEqual(code, 0, err)
        p = pillars(out)
        self.assertEqual(p["day"], "庚辰")
        self.assertEqual(p["zhi"][3], "子")
        self.assertEqual(field(out, "子时"), "早子时")

    def test_yin_year_male_dayun_reverse(self):
        """1991-06-15 辛未阴年男，大运逆排。"""
        code, out, err = run_pai("--solar", "1991-06-15", "--shichen", "午", "--sex", "男")
        self.assertEqual(code, 0, err)
        p = pillars(out)
        self.assertEqual(p["year"], "辛未")
        self.assertIn("方向：逆排", out)

    def test_yang_year_female_dayun_reverse(self):
        """1990-05-15 阳年女，大运逆排。"""
        code, out, err = run_pai("--solar", "1990-05-15", "--shichen", "午", "--sex", "女")
        self.assertEqual(code, 0, err)
        p = pillars(out)
        self.assertEqual(p["year"], "庚午")
        self.assertIn("方向：逆排", out)

    def test_unknown_hour_keeps_ymd(self):
        """无 hour/shichen：时柱未知，年月日柱完整。"""
        code, out, err = run_pai("--solar", "1990-05-15", "--sex", "男")
        self.assertEqual(code, 0, err)
        p = pillars(out)
        self.assertEqual(p["year"], "庚午")
        self.assertEqual(p["month"], "辛巳")
        self.assertEqual(p["day"], "庚辰")
        self.assertEqual(p["gan"][3], "未知")
        self.assertEqual(p["zhi"][3], "未知")
        self.assertEqual(field(out, "时辰"), "未知")
        self.assertEqual(field(out, "子时"), "无")
        self.assertIn("时辰未知", section(out, "警告"))

    def test_lunar_non_leap_matches_solar(self):
        """农历 1990-04-21（非闰四月廿一）与阳历 1990-05-15 四柱一致。"""
        code_l, out_l, err_l = run_pai("--lunar", "1990-04-21", "--shichen", "午", "--sex", "男")
        code_s, out_s, err_s = run_pai("--solar", "1990-05-15", "--shichen", "午", "--sex", "男")
        self.assertEqual(code_l, 0, err_l)
        self.assertEqual(code_s, 0, err_s)
        self.assertEqual(pillars(out_l), pillars(out_s))

    def test_leap_month_when_major_term_and_new_moon_share_date(self):
        """Use Beijing civil dates for leap-month placement, not instant order.

        These month starts are independently published in the Hong Kong
        Observatory's Gregorian-Lunar conversion tables.
        """
        sys.path.insert(0, HERE)
        import pai_pan

        cases = (
            ((1903, 6, 25), (1903, 5, 1, True)),
            ((1955, 4, 22), (1955, 3, 1, True)),
            ((2001, 5, 23), (2001, 4, 1, True)),
        )
        for solar, expected in cases:
            with self.subTest(solar=solar):
                self.assertEqual(pai_pan.solar_to_lunar(*solar), expected)

    def test_hko_2033_leap_eleventh_month(self):
        """HKO's 2033 table catches new-year, month-eight, and leap-month errors."""
        sys.path.insert(0, HERE)
        import pai_pan

        self.assertEqual(pai_pan.solar_to_lunar(2033, 1, 31), (2033, 1, 1, False))
        self.assertEqual(pai_pan.solar_to_lunar(2033, 8, 25), (2033, 8, 1, False))
        self.assertEqual(pai_pan.solar_to_lunar(2033, 12, 22), (2033, 11, 1, True))

    def test_deceased_year_stops_liunian(self):
        """--deceased-year 2010：流年不出现 2011 及更晚。"""
        code, out, err = run_pai(
            "--solar",
            "1990-05-15",
            "--hour",
            "12:00",
            "--sex",
            "男",
            "--deceased-year",
            "2010",
        )
        self.assertEqual(code, 0, err)
        liunian = section(out, "流年")
        self.assertIn("2010", liunian)
        self.assertNotIn("2011", liunian)
        self.assertNotIn("2012", liunian)
        self.assertNotIn("2020", liunian)
        self.assertNotIn("2026", liunian)

    def test_dayun_ranges_keep_qiyun_months(self):
        """交运不是整岁时，每一步大运的起止月不能被丢掉。"""
        code, out, err = run_pai("--solar", "1990-05-15", "--hour", "12:00", "--sex", "男")
        self.assertEqual(code, 0, err)
        qiyun = field(out, "起运")
        self.assertRegex(qiyun, r"\d+岁\d+个月")
        self.assertIn(qiyun + "起至", out)

    def test_qiyun_classical_five_days_three_shichen_is_twenty_one_months(self):
        """《三命通会》五日三时：一日十二时，所以是 5.25 日、21 个月。"""
        sys.path.insert(0, HERE)
        import pai_pan

        self.assertEqual(pai_pan.qiyun_from_days(5 + 3 / 12), (1, 9))
        self.assertEqual(pai_pan.qiyun_from_days(-(5 + 3 / 12)), (1, 9))

    def test_qiyun_synthetic_half_month_uses_profile_half_up_policy(self):
        """5.125 日是合成量化边界；验证本 profile，不冒充古籍例。"""
        sys.path.insert(0, HERE)
        import pai_pan

        self.assertEqual(pai_pan.qiyun_from_days(5 + 3 / 24), (1, 9))
        self.assertEqual(pai_pan.qiyun_from_days(-(5 + 3 / 24)), (1, 9))
        self.assertEqual(pai_pan.qiyun_from_days(3), (1, 0))

    def test_rejects_inconsistent_solar_and_lunar_inputs(self):
        code, out, err = run_pai(
            "--solar", "1990-05-16", "--lunar", "1990-04-21", "--shichen", "午", "--sex", "男"
        )
        self.assertEqual(code, 2)
        self.assertIn("阳历与农历输入不一致", err)


class ShenshaTests(unittest.TestCase):
    def test_golden_shensha_hits_and_misses(self):
        """1990-05-15 午时男：庚不以午为天乙；有将星，无驿马、桃花。"""
        code, out, err = run_pai("--solar", "1990-05-15", "--shichen", "午", "--sex", "男")
        self.assertEqual(code, 0, err)
        shensha = section(out, "神煞")
        self.assertNotEqual(shensha.strip(), "未计算")
        self.assertNotIn("天乙贵人", shensha)
        self.assertIn("将星", shensha)
        self.assertNotIn("驿马", shensha)
        self.assertNotIn("桃花", shensha)

    def test_shensha_table_driven(self):
        """日干甲见丑为天乙；日柱甲子旬空戌亥。"""
        sys.path.insert(0, HERE)
        import pai_pan

        cases = (
            {
                "name": "日干甲+地支丑→天乙",
                "args": ("乙", "亥", "戊", "丑", "甲", "寅", None, None, "男"),
                "has": ("天乙贵人",),
            },
            {
                "name": "日柱甲子→空亡戌亥",
                "args": ("甲", "戌", "乙", "亥", "甲", "子", None, None, "男"),
                "has": ("空亡",),
            },
        )
        for case in cases:
            with self.subTest(case["name"]):
                text = "\n".join(pai_pan.compute_shensha(*case["args"]))
                for name in case["has"]:
                    self.assertIn(name, text)

    def test_tianyi_geng_uses_ox_goat_not_tiger_horse(self):
        """《协纪辨方书》卷七：庚贵人在丑未，寅午只属于辛。"""
        sys.path.insert(0, HERE)
        import pai_pan

        no_hit = "\n".join(
            pai_pan.compute_shensha("乙", "寅", "丁", "午", "庚", "寅", None, None, "男")
        )
        hit = "\n".join(
            pai_pan.compute_shensha("乙", "寅", "丁", "午", "庚", "未", None, None, "男")
        )
        self.assertNotIn("天乙贵人", no_hit)
        self.assertIn("天乙贵人", hit)

    def test_yangren_profile_is_five_yang_stems(self):
        """《三命通会》卷五 profile：阴干不报阳刃，庚酉仍命中。"""
        sys.path.insert(0, HERE)
        import pai_pan

        old_yin_entries = (("乙", "寅"), ("丁", "巳"), ("己", "巳"), ("辛", "子"), ("癸", "亥"))
        for day_stem, old_branch in old_yin_entries:
            with self.subTest(day_stem=day_stem, old_branch=old_branch):
                yin_stem = "\n".join(
                    pai_pan.compute_shensha(
                        "甲", old_branch, "丙", "辰", day_stem, "申", None, None, "女"
                    )
                )
                self.assertNotIn("羊刃", yin_stem)
        yang_stem = "\n".join(
            pai_pan.compute_shensha("甲", "申", "丁", "巳", "庚", "酉", None, None, "男")
        )
        self.assertIn("羊刃", yang_stem)


if __name__ == "__main__":
    unittest.main(verbosity=2)
