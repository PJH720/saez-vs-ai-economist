"""E1 — Saez 세율표의 형태는 소득분포의 형태가 결정한다.

검증 대상 (논문 L1259-1261):
  "The resulting tax schedule depends sharply on the shape of the income
   distribution. A log-normal-like income distribution leads to regressive
   taxes... while a Pareto-like distribution leads to progressive taxes."

방법: ai-economist 저장소의 Saez 구현(get_binned_saez_welfare_weight_and_pareto_params
      -> get_saez_marginal_rates -> bracketize_schedule)에 평균이 동일한 두 분포를
      각각 통과시킨다. 분포의 '수준'이 아니라 '형태'만 다르게 한 통제 비교다.

대응 슬라이드: S19 (왜 Saez가 졌는가 - 기계적 효과)
"""

import numpy as np

import aie_lib as L
from compat import save, setup_matplotlib, write_table

ELAS = 0.5  # 저장소 기본 탄력성 초기값 (redistribution.py: elas_tm1 = 0.5)
MEAN_INCOME = 150.0
N_POP = 4000
SEED = 0


def main():
    plt = setup_matplotlib()
    comp = L.make_tax_component(tax_model="saez", saez_fixed_elas=ELAS)

    dists = {
        "로그정규 Log-normal (σ=0.7)": L.lognormal_incomes(
            n=N_POP, mean=MEAN_INCOME, sigma=0.7, seed=SEED
        ),
        "파레토 Pareto (α=1.5)": L.pareto_incomes(
            n=N_POP, mean=MEAN_INCOME, alpha=1.5, seed=SEED
        ),
    }

    schedules, summaries = {}, {}
    for name, inc in dists.items():
        schedules[name] = L.saez_schedule(comp, inc, ELAS)
        summaries[name] = L.trend_summary(schedules[name])

    labels = L.bracket_labels(comp)
    x = np.arange(len(labels))

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))

    # --- (좌) 소득분포 자체 ---
    # 우측 패널과 색을 일치시킨다. clip 대신 range로 잘라 가짜 스파이크를 만들지 않는다.
    colors = ["#c0392b", "#2471a3"]
    ax = axes[0]
    for (name, inc), color in zip(dists.items(), colors):
        ax.hist(
            inc, bins=60, range=(0, 600), alpha=0.5, label=name,
            density=True, color=color,
        )
    ax.set_xlabel("소득 Income (coin)  ※ 600 초과 꼬리는 표시 생략")
    ax.set_ylabel("밀도 Density")
    ax.set_title(f"① 입력: 평균이 같은 두 소득분포\n(both mean = {MEAN_INCOME:.0f})")
    ax.legend(fontsize=9)

    # --- (우) Saez가 산출한 세율표 ---
    ax = axes[1]
    for (name, rates), color in zip(schedules.items(), colors):
        ax.step(
            x, rates * 100, where="mid", lw=2.4, color=color,
            label=f"{name} → {summaries[name]['overall']}",
        )
        ax.plot(x, rates * 100, "o", ms=5, color=color)
    ax.step(
        x, L.US_FEDERAL_2018 * 100, where="mid", lw=1.6, ls="--", color="gray",
        label="참고: 미 연방 2018 US Federal (누진)",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.set_xlabel("소득 구간 Income bracket (coin)")
    ax.set_ylabel("한계세율 Marginal tax rate (%)")
    ax.set_title(f"② 출력: 저장소의 Saez 공식이 낸 세율표\n(탄력성 elasticity e = {ELAS})")
    ax.legend(fontsize=8.5, loc="upper center")
    ax.grid(alpha=0.3)
    ax.set_ylim(-3, 100)

    fig.suptitle(
        "E1 — Saez 세율표의 누진/역진은 소득분포 '형태'가 결정한다  "
        "| Saez schedule shape is driven by the income distribution",
        fontsize=12.5, y=1.03,
    )
    save(fig, "e1_saez_distribution")

    # --- 표 ---
    rows = [
        "| 소득 구간 (coin) | " + " | ".join(dists.keys()) + " | 미 연방 2018 |",
        "|---|" + "---|" * (len(dists) + 1),
    ]
    for i, lab in enumerate(labels):
        cells = [f"{schedules[n][i]*100:.1f}%" for n in dists]
        rows.append(
            f"| {lab} | " + " | ".join(cells) + f" | {L.US_FEDERAL_2018[i]*100:.0f}% |"
        )
    rows.append(
        "| **형태 판정** | "
        + " | ".join(f"**{summaries[n]['overall']}**" for n in dists)
        + " | 누진 |"
    )
    rows.append(
        "| 순위상관 ρ (구간↑ vs 세율) | "
        + " | ".join(f"{summaries[n]['spearman']:+.2f}" for n in dists)
        + " | +1.00 |"
    )
    table = "\n".join(rows)

    first, second = list(dists)
    md = f"""### E1 — Saez 세율표 vs 소득분포 형태

**설정:** 저장소 `PeriodicBracketTax(tax_model="saez", bracket_spacing="us-federal")`,
탄력성 e={ELAS} 고정, 인구 N={N_POP}, 두 분포 모두 평균소득 {MEAN_INCOME:.0f} coin으로 정규화(seed={SEED}).
세율은 저장소의 `get_saez_marginal_rates` → `bracketize_schedule`를 그대로 호출해 산출.

{table}

**결과:** 평균이 동일한데도 분포 *형태*만 바꾸면 Saez 공식의 결론이 뒤집힌다.
로그정규에서는 최저구간 {schedules[first][0]*100:.0f}% → 최고구간 {schedules[first][-1]*100:.0f}%로 **떨어지고**(역진),
파레토에서는 {schedules[second][0]*100:.0f}% → {schedules[second][-1]*100:.0f}%로 **올라간다**(누진).
논문 L1259–1261의 서술과 부호가 일치한다.
"""
    write_table("e1_saez_distribution", md)

    print("\n--- E1 self-check ---")
    for name, s in summaries.items():
        print(f"{name}: {s}")
    print("기대: 로그정규=역진적, 파레토=누진적 (논문 L1259-1261)")


if __name__ == "__main__":
    main()
