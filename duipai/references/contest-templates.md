# 赛场对拍手册(给孩子的可默写模板)

对拍是 NOIP/CSP 赛场标准操作:正解写完心里没底时,花 15 分钟搭一套对拍,比裸眼盯代码可靠得多。这份手册里的东西要练到**赛前能默写**——模板是死的,每题只改生成器和暴力。

## 一、暴力三板斧(赛场怎么想出暴力)

暴力的唯一标准:**每行代码都能指着题面读出来,一眼见对**。宁可 O(n!) 也不要任何小聪明——暴力一旦不"显然正确",对拍就失去了裁判。

| 板斧 | 什么时候用 | 写法 |
|---|---|---|
| ① 直译模拟 | 题目描述的是一个过程 | 题目怎么说就怎么做,零优化 |
| ② 全枚举 | 求最优/计数,方案空间是排列、子集或区间 | `next_permutation` / 二进制枚举子集 / 双重循环枚举所有区间 |
| ③ 无脑 DFS | 方案空间不规则(放置、划分、路径) | 搜出每一个完整方案,合法的取最优 |

记住:暴力只需要在 **n≤8** 跑对。复杂度完全不用管——它的工作规模由生成器保证。

## 二、C++ 数据生成器模板

```cpp
#include <bits/stdc++.h>
using namespace std;
int main(int argc, char* argv[]) {
    // 种子从命令行传入:每轮不同,且反例可复现
    mt19937 rnd(atoi(argv[1]));
    // 故意用小规模、小值域:小数据照样拍得出错,且反例能手算复查
    int n = rnd() % 8 + 1;
    printf("%d\n", n);
    for (int i = 0; i < n; i++)
        printf("%d ", (int)(rnd() % 20 + 1));
    printf("\n");
    return 0;
}
```

要点:
- 用 `mt19937`,不用 `rand()`(NOIP 环境下 `rand()` 值域太小且质量差)
- 随机拍了几百轮没事后,改生成器**定向造边界**:n=1、全相同值、数据范围上限(验溢出)、退化结构(树造成链:父节点固定为 i-1)
- 造树:节点 i 的父亲在 1..i-1 里随机选;造区间:l 随机,r 在 l..n 里随机

## 三、对拍脚本模板

### Windows(NOIP 赛场常见).bat

```bat
@echo off
:loop
gen.exe %random% > data.txt
brute.exe < data.txt > out_brute.txt
sol.exe < data.txt > out_sol.txt
fc out_brute.txt out_sol.txt > nul
if errorlevel 1 goto fail
echo AC
goto loop
:fail
echo WA! 反例在 data.txt
pause
```

### Linux / Mac .sh

```bash
#!/bin/bash
i=0
while true; do
  i=$((i+1))
  ./gen $i > data.txt
  ./brute < data.txt > out_brute.txt
  ./sol  < data.txt > out_sol.txt
  if ! diff -w out_brute.txt out_sol.txt > /dev/null; then
    echo "WA on round $i, 反例在 data.txt"; break
  fi
  echo "round $i AC"
done
```

编译三份:`g++ -O2 -o gen gen.cpp` 同理 brute、sol。抓到反例后:先手算这组小数据,确认暴力是对的,再单步排查正解。

## 四、赛场决策清单:什么时候值得对拍

值得(15 分钟投入,可能救回整题):
- 样例太少太弱(只有一两组、没有边界)
- 正解里有分类讨论、边界处理、贪心——这些最容易错
- 这题分值高,且你还剩 ≥40 分钟

不值得:
- 剩余时间 <20 分钟(先把暴力分交了——暴力本身就是部分分!)
- 正解就是模拟/模板题,写挂概率低

对拍抓不到的两类错,单独检查:**读入输出格式**(多组数据?文件结尾?)和**题意理解偏差**(暴力和正解错得一样)。

## 五、训练阶梯

按四级递进,每级一两周、每周两题,卡住就退回上一级多看范例:

1. **L1 看范例**:读 skill 写的暴力和讲解卡,给家长复述"暴力为什么显然正确"
2. **L2 写暴力**:自己写暴力(这同时就是赛场的保底部分分),生成器和对拍交给 skill
3. **L3 写暴力 + 生成器**:重点练结构化数据的造法(随机树、合法区间)
4. **L4 全套(赛前一个月)**:含对拍脚本,模板要能默写;计时,目标 15 分钟搭完

能稳定做到 L4,这个技能才算带进考场了。
