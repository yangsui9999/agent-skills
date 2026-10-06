#!/usr/bin/env python3
"""通用对拍 runner。

用法:
    python3 duipai.py --gen gen.cpp --brute brute.cpp --sol sol.cpp [--rounds 300]
                      [--sizes 1,2,3,5,8] [--tl 2.0] [--checker chk.py] [--outdir .]

约定:
  - 生成器从命令行接收两个参数:种子、规模档位,数据写到 stdout
  - brute / sol 从 stdin 读入,答案写到 stdout
  - checker(可选,用于多解题)接收三个文件参数:输入、暴力输出、正解输出,exit 0 表示一致
  - 找到反例即停止,数据存为 fail_input.txt / fail_brute.txt / fail_sol.txt
"""
import argparse
import subprocess
import sys
from pathlib import Path


STDCPP_SHIM = "\n".join(
    f"#include <{h}>" for h in (
        "iostream cstdio cstring cstdlib cmath string vector algorithm queue "
        "stack map set unordered_map unordered_set deque bitset numeric utility "
        "climits cassert random functional tuple array iomanip sstream"
    ).split()
) + "\n"


def make_shim(workdir: Path) -> Path:
    """macOS 自带的是 clang,没有 bits/stdc++.h;生成一个 shim 头文件目录。"""
    shim_dir = workdir / "_shim_include"
    header = shim_dir / "bits" / "stdc++.h"
    if not header.exists():
        header.parent.mkdir(parents=True, exist_ok=True)
        header.write_text(STDCPP_SHIM)
    return shim_dir


def compile_if_cpp(src: Path, workdir: Path) -> list:
    """返回可执行的命令行前缀;.cpp 先编译,.py 直接用解释器跑。"""
    if src.suffix == ".py":
        return [sys.executable, str(src)]
    if src.suffix in (".cpp", ".cc", ".cxx"):
        exe = (workdir / (src.stem + ".bin")).resolve()
        # 只在源文件比可执行文件新时重新编译
        if not exe.exists() or src.stat().st_mtime > exe.stat().st_mtime:
            print(f"[编译] {src.name} ...")
            cmd = ["g++", "-O2", "-std=c++17", "-o", str(exe), str(src)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0 and "bits/stdc++.h" in r.stderr:
                # clang 环境缺 bits/stdc++.h,用 shim 重试
                shim = make_shim(workdir)
                r = subprocess.run(cmd + ["-I", str(shim)],
                                   capture_output=True, text=True)
            if r.returncode != 0:
                print(f"[错误] {src.name} 编译失败:\n{r.stderr}")
                sys.exit(1)
        return [str(exe)]
    # 无后缀:当作已编译好的可执行文件
    return [str(src.resolve())]


def run(cmd: list, input_text: str, tl: float):
    """返回 (stdout, 状态) 状态: ok / tle / re"""
    try:
        r = subprocess.run(cmd, input=input_text, capture_output=True,
                           text=True, timeout=tl)
    except subprocess.TimeoutExpired:
        return "", "tle"
    if r.returncode != 0:
        return r.stdout, "re"
    return r.stdout, "ok"


def normalize(s: str) -> str:
    """按 token 比较,忽略行末空格和多余空行。"""
    return "\n".join(" ".join(line.split()) for line in s.strip().splitlines())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True, help="数据生成器 (.cpp/.py)")
    ap.add_argument("--brute", required=True, help="暴力解 (.cpp/.py)")
    ap.add_argument("--sol", required=True, help="待验证的正解 (.cpp/.py)")
    ap.add_argument("--rounds", type=int, default=300)
    ap.add_argument("--sizes", default="1,2,3,5,8",
                    help="规模档位,逗号分隔,轮流传给生成器;小档位在前(小数据反例更好查)")
    ap.add_argument("--tl", type=float, default=2.0, help="正解时限(秒)")
    ap.add_argument("--brute-tl", type=float, default=20.0, help="暴力时限(秒)")
    ap.add_argument("--checker", help="可选 checker,多解题用")
    ap.add_argument("--outdir", default=".", help="反例与编译产物的输出目录")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    gen = compile_if_cpp(Path(args.gen), outdir)
    brute = compile_if_cpp(Path(args.brute), outdir)
    sol = compile_if_cpp(Path(args.sol), outdir)
    checker = compile_if_cpp(Path(args.checker), outdir) if args.checker else None
    sizes = args.sizes.split(",")

    for i in range(1, args.rounds + 1):
        size = sizes[(i - 1) % len(sizes)]
        data, st = run(gen + [str(i), size], "", 10.0)
        if st != "ok":
            print(f"[错误] 第 {i} 轮生成器异常 (种子={i}, 规模={size})")
            sys.exit(1)

        out_b, st_b = run(brute, data, args.brute_tl)
        if st_b != "ok":
            print(f"[错误] 暴力解 {st_b.upper()} —— 暴力必须先保证能跑,数据已存 fail_input.txt")
            (outdir / "fail_input.txt").write_text(data)
            sys.exit(1)

        out_s, st_s = run(sol, data, args.tl)
        mismatch = False
        reason = ""
        if st_s == "tle":
            mismatch, reason = True, f"正解超时 (>{args.tl}s)"
        elif st_s == "re":
            mismatch, reason = True, "正解运行时错误 (RE)"
        elif checker:
            fi, fb, fs = (outdir / "chk_in.txt"), (outdir / "chk_brute.txt"), (outdir / "chk_sol.txt")
            fi.write_text(data); fb.write_text(out_b); fs.write_text(out_s)
            _, st_c = run(checker + [str(fi), str(fb), str(fs)], "", 10.0)
            if st_c != "ok":
                mismatch, reason = True, "checker 判定不一致"
        elif normalize(out_b) != normalize(out_s):
            mismatch, reason = True, "输出不一致 (WA)"

        if mismatch:
            (outdir / "fail_input.txt").write_text(data)
            (outdir / "fail_brute.txt").write_text(out_b)
            (outdir / "fail_sol.txt").write_text(out_s)
            print(f"\n{'=' * 40}")
            print(f"[抓到反例] 第 {i} 轮 (种子={i}, 规模档={size}) —— {reason}")
            print(f"{'=' * 40}")
            print(f"--- 输入 ---\n{data.strip()}")
            print(f"--- 暴力输出 ---\n{out_b.strip()}")
            print(f"--- 正解输出 ---\n{out_s.strip() if st_s == 'ok' else '(' + st_s.upper() + ')'}")
            print(f"\n已存到 {outdir}/fail_input.txt 等三个文件")
            sys.exit(2)

        if i % 50 == 0:
            print(f"[进度] {i}/{args.rounds} 轮通过")

    print(f"\n[通过] {args.rounds} 轮对拍全部一致。")
    print("拍不出不等于全对:可以调大 --sizes 和值域、加边界特化数据、用满档规模测 TLE;")
    print("读入格式错误和题意理解偏差是对拍抓不到的,单独检查。")


if __name__ == "__main__":
    main()
