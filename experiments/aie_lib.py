"""E1~E5가 공유하는 헬퍼.

핵심 원칙: Saez 공식·구간세 계산·지니/평등/생산성·효용은 **직접 구현하지 않고**
ai-economist 저장소 함수를 그대로 호출한다. 발표에서 "저자들의 코드로 돌렸다"고
말할 수 있어야 하기 때문이다.
"""

import compat  # noqa: F401  (반드시 foundation보다 먼저)
import numpy as np

from ai_economist import foundation
from ai_economist.foundation.scenarios.utils.rewards import isoelastic_coin_minus_labor
from ai_economist.foundation.scenarios.utils.social_metrics import (
    get_equality,
    get_productivity,
)

# 논문/저장소 기본값: us-federal 구간을 usd_scaling=1000으로 축소한 것
# → cutoffs = [0, 9.7, 39.475, 84.2, 160.725, 204.1, 510.3]
US_FEDERAL_2018 = np.array([0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37])


def make_tax_component(**tax_kwargs):
    """PeriodicBracketTax 컴포넌트를 실제 env에서 꺼내온다.

    컴포넌트는 world를 요구하므로 튜토리얼과 동일한 최소 env를 세운다.
    (env를 step하지는 않는다 — 세율 계산 메서드만 쓴다.)
    """
    kwargs = dict(bracket_spacing="us-federal", period=100)
    kwargs.update(tax_kwargs)
    env_config = {
        "scenario_name": "layout_from_file/simple_wood_and_stone",
        "components": [
            ("Build", {"skill_dist": "pareto", "payment_max_skill_multiplier": 3}),
            ("ContinuousDoubleAuction", {"max_num_orders": 5}),
            ("Gather", {}),
            ("PeriodicBracketTax", kwargs),
        ],
        "env_layout_file": "quadrant_25x25_20each_30clump.txt",
        "starting_agent_coin": 10,
        "fixed_four_skill_and_loc": True,
        "n_agents": 4,
        "world_size": [25, 25],
        "episode_length": 1000,
        "multi_action_mode_agents": False,
        "multi_action_mode_planner": True,
        "flatten_observations": False,
        "flatten_masks": True,
    }
    env = foundation.make_env_instance(**env_config)
    return env.get_component("PeriodicBracketTax")


def saez_schedule(comp, incomes, elas):
    """저장소의 Saez 파이프라인을 그대로 재현해 7구간 한계세율을 낸다.

    redistribution.py:486-506 의 호출 순서와 동일:
      get_binned_saez_welfare_weight_and_pareto_params -> get_saez_marginal_rates
      -> bracketize_schedule -> clip
    """
    gz, az = comp.get_binned_saez_welfare_weight_and_pareto_params(
        population_incomes=np.asarray(incomes, dtype=float)
    )
    binned = comp.get_saez_marginal_rates(gz, az, float(elas))
    rates = comp.bracketize_schedule(
        bin_marginal_rates=binned,
        bin_edges=comp._saez_income_bin_edges,
        bin_sizes=comp._saez_income_bin_sizes,
    )
    return np.clip(rates, comp.rate_min, comp.rate_max)


def taxes_due(comp, rates, income):
    """주어진 구간세율표에서 income에 대한 총 세액. (comp.taxes_due 로직과 동일)"""
    rates = np.asarray(rates, dtype=float)
    past_cutoff = np.maximum(0.0, float(income) - comp.bracket_cutoffs)
    bin_income = np.minimum(comp.bracket_sizes, past_cutoff)
    return float(np.sum(rates * bin_income))


def effective_rate(comp, rates, income):
    """실효세율 = 총세액 / 소득."""
    if income <= 0:
        return 0.0
    return taxes_due(comp, rates, income) / float(income)


# ---------- 합성 소득분포 (평균을 맞춰 '형태'만 비교) ----------


def lognormal_incomes(n=4000, mean=150.0, sigma=0.7, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.lognormal(mean=0.0, sigma=sigma, size=n)
    return x * (mean / x.mean())


def pareto_incomes(n=4000, mean=150.0, alpha=1.5, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.pareto(alpha, size=n) + 1.0  # xm=1
    return x * (mean / x.mean())


# ---------- 후생함수 ----------


def swf_eq_times_prod(incomes):
    """논문의 주 목적함수 swf = eq x prod (저장소 함수 사용)."""
    inc = np.asarray(incomes, dtype=float)
    return float(get_equality(inc) * get_productivity(inc))


def utilities(incomes, labors, isoelastic_eta=0.23, labor_coefficient=1.0):
    """저장소의 등탄력 효용."""
    return np.array(
        [
            isoelastic_coin_minus_labor(
                coin_endowment=max(float(c), 0.0),
                total_labor=float(l),
                isoelastic_eta=isoelastic_eta,
                labor_coefficient=labor_coefficient,
            )
            for c, l in zip(incomes, labors)
        ]
    )


def atkinson(incomes, epsilon):
    """Atkinson 사회후생 (등가균등소득, equally-distributed-equivalent income)."""
    inc = np.maximum(np.asarray(incomes, dtype=float), 1e-9)
    if abs(epsilon - 1.0) < 1e-9:
        return float(np.exp(np.mean(np.log(inc))))
    return float((np.mean(inc ** (1.0 - epsilon))) ** (1.0 / (1.0 - epsilon)))


def bracket_labels(comp):
    """x축용 구간 라벨: '0-10', '10-39', ..., '510+'."""
    cuts = comp.bracket_cutoffs
    labels = []
    for i, lo in enumerate(cuts):
        if i + 1 < len(cuts):
            labels.append(f"{lo:.0f}–{cuts[i+1]:.0f}")
        else:
            labels.append(f"{lo:.0f}+")
    return labels


def describe_shape(rates):
    """세율표가 누진/역진/비단조 중 무엇인지 판정한다."""
    d = np.diff(np.asarray(rates, dtype=float))
    tol = 1e-6
    if np.all(d >= -tol):
        return "누진 progressive"
    if np.all(d <= tol):
        return "역진 regressive"
    return "비단조 non-monotonic"


def trend_summary(rates):
    """엄밀한 단조성 판정 + 전반적 추세를 함께 보고한다.

    구간 1~2에서만 오르고 이후 계속 내려가는 표는 '비단조'지만 실질적으로는
    역진적이다. 그래서 단조성 라벨과 별개로 순위상관(Spearman)과
    최고구간-최저구간 차이를 같이 낸다.
    """
    from scipy.stats import spearmanr

    r = np.asarray(rates, dtype=float)
    if np.ptp(r) < 1e-12:  # 전 구간 동일(예: 무세) -> 순위상관 정의 안 됨
        rho = 0.0
    else:
        rho = float(spearmanr(np.arange(len(r)), r).statistic)
    if rho > 0.5:
        overall = "누진적 progressive"
    elif rho < -0.5:
        overall = "역진적 regressive"
    else:
        overall = "혼합 mixed"
    return {
        "monotonicity": describe_shape(r),
        "overall": overall,
        "spearman": rho,
        "top_minus_bottom": float(r[-1] - r[0]),
        "top_rate": float(r[-1]),
        "mean_rate": float(r.mean()),
    }
