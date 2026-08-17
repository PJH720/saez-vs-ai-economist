### E3 — 후생함수를 바꾸면 승자가 바뀌는가

**설정:** E5가 실제로 만들어낸 네 정책의 균형 배분(세후 coin, 노동시간)을 그대로 사용.
소득 벡터를 임의로 만들지 않았다. 효용은 저장소의 `coin_minus_labor_cost`
(labor_coefficient=0.012, exponent=2), 평등·생산성은 `social_metrics` 그대로.

| 후생함수 | 자유시장 Free market | 미 연방 2018 US Federal | Saez (고정점) | 미니-AI Mini AI Economist | 1위 |
|---|---|---|---|---|---|
| 논문: eq × prod (paper) | 279 | 246 | 266 | **295** | 미니-AI Mini AI Economist |
| 공리주의 Σu_i (utilitarian) | **226** | 213 | 225 | 222 | 자유시장 Free market |
| 롤스 min u_i (Rawlsian) | 26.5 | 35.5 | 30.2 | **35.5** | 미니-AI Mini AI Economist |
| Atkinson ε=0.5 | **105** | 82.9 | 99 | 101 | 자유시장 Free market |
| Atkinson ε=1 | **98.2** | 79.9 | 92.8 | 96.6 | 자유시장 Free market |
| Atkinson ε=2 | 86.7 | 74.6 | 82.8 | **89.8** | 미니-AI Mini AI Economist |
| 역소득가중 Σu_i/z_i (inv-income wtd) | 2 | **2.72** | 2.23 | 2.4 | 미 연방 2018 US Federal |

**결과:** 서로 다른 후생함수에서 1위가 **3종류**로 갈렸다 → 미 연방 2018 US Federal, 미니-AI Mini AI Economist, 자유시장 Free market

논문의 지표(eq × prod)에서는 **미니-AI Mini AI Economist**가 1위지만,
공리주의(Σu_i)에서는 **자유시장 Free market**,
롤스(min u_i)에서는 **미니-AI Mini AI Economist**,
불평등 회피가 강한 Atkinson ε=2에서는 **미니-AI Mini AI Economist**가 1위다.

**발표에서 할 말:** "16% 개선"의 *개선*은 `eq × prod`라는 곱셈형 후생함수를
전제할 때만 성립한다. 곱셈형은 평등과 생산성을 완전보완재로 취급하는 강한 규범적
선택이며, 공리주의도 롤스도 Atkinson도 아니다. 즉 이 논문의 성과 지표는
**중립적 측정이 아니라 하나의 가치판단**이다. (논문도 이를 의식해 linear-weighted
sum of utilities 계열을 별도로 언급한다, L910~)

특히 `역소득가중 Σu_i/z_i`는 논문이 **MTurk 인간 실험에서 우위를 주장한 바로 그 지표**다.
지표를 바꿔가며 우위를 주장할 수 있다는 점 자체가 이 비판의 요지다.
