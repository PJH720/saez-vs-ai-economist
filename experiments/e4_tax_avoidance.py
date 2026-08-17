"""E4 — 왜 '소득 교대'가 절세가 되는가: Jensen 부등호가 뒤집히는 지점.

검증 대상 (논문 L1740-1746):
  "agents learn to lower their average effective tax by alternating between
   earning high and low incomes in each period, rather than smoothing...
   which feature lower top tax rates (regressive schedules), making it more
   tax-efficient to earn high incomes."

논리: 누진세(볼록 T)에서는 Jensen 부등식상 소득 평탄화가 세금을 최소화한다.
      세율표가 역진적(오목)이면 부등호가 뒤집혀 '교대'가 유리해진다.
      총소득을 2z로 고정한 두 전략의 실효세율을 직접 계산해 확인한다.

    전략 A 평탄화 smoothing  : (z, z)   -> 세금 2·T(z)
    전략 B 교대   alternating: (2z, 0)  -> 세금 T(2z)

세율표는 전부 '계산된 것'만 쓴다 (임의로 지어낸 표 없음):
  - 미 연방 2018        : 저장소 상수 (누진)
  - Saez @ 로그정규분포 : E1과 동일 계산 (역진)
  - Saez @ 파레토분포   : E1과 동일 계산 (누진)

대응 슬라이드: S21 (창발적 행동 - 조세 회피)
"""

import numpy as np

import aie_lib as L
from compat import save, setup_matplotlib, write_table

ELAS = 0.5
MEAN_INCOME = 150.0
N_POP = 4000
SEED = 0
Z_GRID = [40, 60, 80, 120, 160, 200, 255]  # 총소득 2z = 80 ~ 510


def main():
    plt = setup_matplotlib()
    comp = L.make_tax_component(tax_model="saez", saez_fixed_elas=ELAS)

    ln = L.lognormal_incomes(n=N_POP, mean=MEAN_INCOME, sigma=0.7, seed=SEED)
    pa = L.pareto_incomes(n=N_POP, mean=MEAN_INCOME, alpha=1.5, seed=SEED)

    schedules = {
        "미 연방 2018\nUS Federal": L.US_FEDERAL_2018,
        "Saez @ 로그정규\nSaez (log-normal)": L.saez_schedule(comp, ln, ELAS),
        "Saez @ 파레토\nSaez (Pareto)": L.saez_schedule(comp, pa, ELAS),
    }
    shapes = {k: L.trend_summary(v)["overall"] for k, v in schedules.items()}

    # 전략별 실효세율
    results = {}
    for name, rates in schedules.items():
        smooth, alt = [], []
        for z in Z_GRID:
            tax_smooth = 2.0 * L.taxes_due(comp, rates, z)
            tax_alt = L.taxes_due(comp, rates, 2 * z) + L.taxes_due(comp, rates, 0)
            smooth.append(tax_smooth / (2 * z))
            alt.append(tax_alt / (2 * z))
        results[name] = (np.array(smooth), np.array(alt))

    # --- 그림 ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    totals = [2 * z for z in Z_GRID]
    for ax, (name, (smooth, alt)) in zip(axes, results.items()):
        ax.plot(totals, smooth * 100, "o-", lw=2.4, ms=6, color="#2471a3",
                label="전략 A 평탄화 (z, z)")
        ax.plot(totals, alt * 100, "s--", lw=2.4, ms=6, color="#c0392b",
                label="전략 B 교대 (2z, 0)")
        ax.fill_between(totals, smooth * 100, alt * 100,
                        where=(alt < smooth), alpha=0.18, color="#c0392b")
        ax.fill_between(totals, smooth * 100, alt * 100,
                        where=(alt >= smooth), alpha=0.18, color="#2471a3")
        alt_wins = (alt < smooth - 1e-9).mean()
        verdict = "교대가 유리" if alt_wins > 0.5 else "평탄화가 유리"
        ax.set_title(f"{name}\n({shapes[name]}) → {verdict}", fontsize=10)
        ax.set_xlabel("2기간 총소득 Total income over 2 periods")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8.5)
    axes[0].set_ylabel("실효세율 Effective tax rate (%)")

    fig.suptitle(
        "E4 — 역진 구간이 있으면 Jensen 부등호가 뒤집혀 '교대'가 절세가 된다  "
        "| Regressive segments flip the optimal income-timing strategy",
        fontsize=12.5, y=1.04,
    )
    save(fig, "e4_tax_avoidance")

    # --- 표 ---
    lines = []
    for name, (smooth, alt) in results.items():
        flat = name.replace("\n", " ")
        lines.append(f"\n**{flat}** — {shapes[name]}\n")
        lines.append(
            "| 2기간 총소득 | 전략 A 평탄화 (z,z) | 전략 B 교대 (2z,0) | 유리한 전략 |"
        )
        lines.append("|---|---|---|---|")
        for i, z in enumerate(Z_GRID):
            if alt[i] < smooth[i] - 1e-9:
                better = "**B 교대**"
            elif smooth[i] < alt[i] - 1e-9:
                better = "A 평탄화"
            else:
                better = "동일"
            lines.append(
                f"| {2*z} | {smooth[i]*100:.2f}% | {alt[i]*100:.2f}% | {better} |"
            )
    table = "\n".join(lines)

    us_s, us_a = results["미 연방 2018\nUS Federal"]
    sz_s, sz_a = results["Saez @ 로그정규\nSaez (log-normal)"]
    md = f"""### E4 — 조세회피: 평탄화 vs 교대 (Jensen 부등호 뒤집힘)

**설정:** 총소득을 2z로 고정하고 두 전략의 실효세율을 저장소의 구간세 계산
(`taxes_due`)으로 직접 비교. 세율표는 모두 계산된 것만 사용(임의 작성 없음).

**핵심 논리:** 세금함수 T가 볼록(누진)이면 Jensen 부등식에 의해 2·T(z) ≤ T(2z)+T(0)
→ **평탄화가 유리**. T가 오목(역진)이면 부등호가 뒤집혀 → **교대가 유리**.
{table}

**결론:** 누진세인 미 연방에서는 전 구간에서 평탄화가 유리한 반면,
Saez가 로그정규 분포에서 만들어낸 **역진적** 세율표에서는 교대가 유리해진다.
논문이 관측한 "에이전트가 소득을 평탄화하지 않고 교대로 번다"는 창발적 행동은
세율표에 역진 구간이 있다는 사실에서 **수학적으로 따라나온다**.
(예: 총소득 {2*Z_GRID[3]}일 때 미연방은 평탄화 {us_s[3]*100:.1f}% vs 교대 {us_a[3]*100:.1f}%,
Saez-로그정규는 평탄화 {sz_s[3]*100:.1f}% vs 교대 {sz_a[3]*100:.1f}%)
"""
    write_table("e4_tax_avoidance", md)

    print("\n--- E4 self-check ---")
    for name, (smooth, alt) in results.items():
        n_alt_wins = int((alt < smooth - 1e-9).sum())
        print(
            f"{name.replace(chr(10), ' ')}: {shapes[name]} | "
            f"교대가 이긴 구간 {n_alt_wins}/{len(Z_GRID)}"
        )
    print("기대: 미 연방(누진)=0/7 (평탄화 우세), Saez-로그정규(역진)=대부분 교대 우세")


if __name__ == "__main__":
    main()
