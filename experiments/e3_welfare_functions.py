"""E3 — "16% 개선"의 분모를 바꾸면 순위가 뒤집히는가.

검증 대상:
  논문의 주 목적함수는 swf = eq x prod (곱셈형)이다. 이는 표준 공리주의(sum u)도,
  롤스(min u)도, Atkinson/CES 족도 아니다. 곱셈형은 "평등과 생산성이 완전보완재"
  라는 강한 규범적 가정을 깐다. 즉 "16% 개선"은 중립적 측정이 아니라 이 특정
  후생함수를 받아들일 때만 성립하는 값이다.

방법: E5가 실제로 만들어낸 네 정책의 배분(세후 coin, 노동시간)을 그대로 가져와
      여러 후생함수로 점수를 매기고 순위가 바뀌는지 본다. 소득 벡터를 임의로
      지어내지 않는다 — E5의 실제 균형 결과만 쓴다.

포함한 후생함수:
  - 논문: eq x prod                       (social_metrics 그대로)
  - 공리주의: sum u_i                     (rewards.coin_minus_labor_cost 그대로)
  - 롤스: min u_i
  - Atkinson: eps = 0.5 / 1 / 2           (등가균등소득)
  - 역소득가중: sum u_i / z_i             (논문이 MTurk에서 우위를 주장한 바로 그 지표)

대응 슬라이드: S22 ("16%"의 분모를 의심하기)
"""

import numpy as np

import aie_lib as L
from compat import RESULT_DIR, save, setup_matplotlib, write_table

LABOR_COST = 0.012  # E5와 동일
LABOR_EXPONENT = 2.0

KEY_PAPER = "논문: eq × prod\n(paper)"
KEY_UTIL = "공리주의 Σu_i\n(utilitarian)"
KEY_RAWLS = "롤스 min u_i\n(Rawlsian)"
KEY_ATK2 = "Atkinson ε=2"


def main():
    plt = setup_matplotlib()
    # allow_pickle 불필요: 저장된 배열은 float64와 고정폭 유니코드(<U23)뿐이다.
    data = np.load(RESULT_DIR / "e5_incomes.npz")
    names = [str(n) for n in data["policy_names"]]
    coins = data["coins"]      # (정책, 에이전트) 세후 coin
    incomes = data["incomes"]  # 세전 소득
    labors = data["labors"]    # 노동시간

    from ai_economist.foundation.scenarios.utils.rewards import coin_minus_labor_cost

    def utils_of(i):
        return np.array([
            coin_minus_labor_cost(
                coin_endowment=max(float(c), 0.0),
                total_labor=float(l),
                labor_exponent=LABOR_EXPONENT,
                labor_coefficient=LABOR_COST,
            )
            for c, l in zip(coins[i], labors[i])
        ])

    swfs = {
        KEY_PAPER: lambda i: L.swf_eq_times_prod(coins[i]),
        KEY_UTIL: lambda i: float(utils_of(i).sum()),
        KEY_RAWLS: lambda i: float(utils_of(i).min()),
        "Atkinson ε=0.5": lambda i: L.atkinson(coins[i], 0.5),
        "Atkinson ε=1": lambda i: L.atkinson(coins[i], 1.0),
        KEY_ATK2: lambda i: L.atkinson(coins[i], 2.0),
        "역소득가중 Σu_i/z_i\n(inv-income wtd)": lambda i: float(
            np.sum(utils_of(i) / np.maximum(incomes[i], 1.0))
        ),
    }

    scores = {k: np.array([f(i) for i in range(len(names))]) for k, f in swfs.items()}
    # 순위: 1등이 가장 높은 점수
    ranks = {k: (len(names) - np.argsort(np.argsort(v))) for k, v in scores.items()}

    # --- 그림 ---
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.9))

    ax = axes[0]
    mat = np.array([ranks[k] for k in swfs]).T  # (정책, 후생함수)
    im = ax.imshow(mat, cmap="RdYlGn_r", vmin=1, vmax=len(names), aspect="auto")
    ax.set_xticks(range(len(swfs)))
    ax.set_xticklabels(list(swfs), fontsize=7.5, rotation=30, ha="right")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8.5)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]}위", ha="center", va="center",
                    fontsize=10, fontweight="bold")
    ax.set_title("① 후생함수를 바꾸면 정책 순위가 바뀐다\nPolicy rank under different SWFs")
    fig.colorbar(im, ax=ax, label="순위 Rank (1=최선)")

    ax = axes[1]
    width = 0.8 / len(names)
    xs = np.arange(len(swfs))
    palette = ["#7f8c8d", "#27ae60", "#c0392b", "#2471a3"]
    for i, name in enumerate(names):
        norm = np.array([
            (scores[k][i] - scores[k].min()) / (np.ptp(scores[k]) + 1e-12)
            for k in swfs
        ])
        ax.bar(xs + i * width, norm, width, label=name, color=palette[i % len(palette)])
    ax.set_xticks(xs + 0.4 - width / 2)
    ax.set_xticklabels(list(swfs), fontsize=7.5, rotation=30, ha="right")
    ax.set_ylabel("정규화 점수 (0=최하, 1=최상)")
    ax.set_title("② 후생함수별 상대 점수\nNormalised score per SWF")
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.3, axis="y")

    fig.suptitle(
        "E3 — '개선 16%'의 개선은 후생함수 선택에 의존한다  "
        "| The winner depends on which social welfare function you pick",
        fontsize=12.5, y=1.05,
    )
    save(fig, "e3_welfare_functions")

    # --- 표 ---
    tbl = ["| 후생함수 | " + " | ".join(names) + " | 1위 |",
           "|---|" + "---|" * (len(names) + 1)]
    for k in swfs:
        flat = k.replace("\n", " ")
        best = names[int(np.argmax(scores[k]))]
        cells = []
        for i in range(len(names)):
            mark = "**" if ranks[k][i] == 1 else ""
            cells.append(f"{mark}{scores[k][i]:.3g}{mark}")
        tbl.append(f"| {flat} | " + " | ".join(cells) + f" | {best} |")
    table = "\n".join(tbl)

    winners = {k: names[int(np.argmax(scores[k]))] for k in swfs}
    distinct = sorted(set(winners.values()))

    md = f"""### E3 — 후생함수를 바꾸면 승자가 바뀌는가

**설정:** E5가 실제로 만들어낸 네 정책의 균형 배분(세후 coin, 노동시간)을 그대로 사용.
소득 벡터를 임의로 만들지 않았다. 효용은 저장소의 `coin_minus_labor_cost`
(labor_coefficient={LABOR_COST}, exponent={LABOR_EXPONENT:.0f}), 평등·생산성은 `social_metrics` 그대로.

{table}

**결과:** 서로 다른 후생함수에서 1위가 **{len(distinct)}종류**로 갈렸다 → {", ".join(distinct)}

논문의 지표(eq × prod)에서는 **{winners[KEY_PAPER]}**가 1위지만,
공리주의(Σu_i)에서는 **{winners[KEY_UTIL]}**,
롤스(min u_i)에서는 **{winners[KEY_RAWLS]}**,
불평등 회피가 강한 Atkinson ε=2에서는 **{winners[KEY_ATK2]}**가 1위다.

**발표에서 할 말:** "16% 개선"의 *개선*은 `eq × prod`라는 곱셈형 후생함수를
전제할 때만 성립한다. 곱셈형은 평등과 생산성을 완전보완재로 취급하는 강한 규범적
선택이며, 공리주의도 롤스도 Atkinson도 아니다. 즉 이 논문의 성과 지표는
**중립적 측정이 아니라 하나의 가치판단**이다. (논문도 이를 의식해 linear-weighted
sum of utilities 계열을 별도로 언급한다, L910~)

특히 `역소득가중 Σu_i/z_i`는 논문이 **MTurk 인간 실험에서 우위를 주장한 바로 그 지표**다.
지표를 바꿔가며 우위를 주장할 수 있다는 점 자체가 이 비판의 요지다.
"""
    write_table("e3_welfare_functions", md)

    print("\n--- E3 self-check ---")
    for k in swfs:
        print(f"{k.replace(chr(10), ' '):34s} 1위 = {winners[k]}")
    print(f"서로 다른 1위 개수: {len(distinct)} (2 이상이면 순위 역전 존재)")


if __name__ == "__main__":
    main()
