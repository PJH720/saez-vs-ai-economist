# References

Source PDFs are deliberately not included in this repository — several are
subscription content. Identifiers are given so you can retrieve each from the
publisher or preprint server.

## The paper under examination

**Zheng, S., Trott, A., Srinivasa, S., Naik, N., Gruesbeck, M., Parkes, D. C.,
& Socher, R. (2020).** *The AI Economist: Improving Equality and Productivity
with AI-Driven Tax Policies.*
arXiv:[2004.13332](https://arxiv.org/abs/2004.13332)

Line numbers cited throughout `experiments/RESULTS.md` and
[`docs/RESULTS.en.md`](docs/RESULTS.en.md) (e.g. "L1259–1261") refer to the
arXiv preprint text.

**Zheng, S., Trott, A., Srinivasa, S., Parkes, D. C., & Socher, R. (2021).**
*The AI Economist: Optimal Economic Policy Design via Two-level Deep
Reinforcement Learning.*
arXiv:[2108.02755](https://arxiv.org/abs/2108.02755)

The follow-up paper. Source of the `OneStepEconomy` simplified economy that
E5 optimizes over.

## The economics baseline

**Saez, E. (2001).** *Using Elasticities to Derive Optimal Income Tax Rates.*
*Review of Economic Studies*, 68(1), 205–229.
doi:[10.1111/1467-937X.00166](https://doi.org/10.1111/1467-937X.00166)

The baseline the paper's 16% is measured against. E1 and E2 probe how sensitive
this formula is to inputs the paper holds fixed.

**Mirrlees, J. A. (1971).** *An Exploration in the Theory of Optimum Income
Taxation.* *Review of Economic Studies*, 38(2), 175–208.
doi:[10.2307/2296779](https://doi.org/10.2307/2296779)

**Gruber, J., & Saez, E. (2002).** *The elasticity of taxable income: evidence
and implications.* *Journal of Public Economics*, 84(1), 1–32.
doi:[10.1016/S0047-2727(01)00085-8](https://doi.org/10.1016/S0047-2727(01)00085-8)

Source of the constant-elasticity assumption the paper adopts, and which E2
shows carries a 38.9 pp swing in the resulting mean marginal rate.

**Mankiw, N. G., Weinzierl, M., & Yagan, D. (2009).** *Optimal Taxation in
Theory and Practice.* *Journal of Economic Perspectives*, 23(4), 147–174.
doi:[10.1257/jep.23.4.147](https://doi.org/10.1257/jep.23.4.147)

## Welfare functions

**Atkinson, A. B. (1970).** *On the measurement of inequality.*
*Journal of Economic Theory*, 2(3), 244–263.
doi:[10.1016/0022-0531(70)90039-6](https://doi.org/10.1016/0022-0531(70)90039-6)

The inequality-aversion family E3 re-scores the four policies against, alongside
utilitarian, Rawlsian, and the paper's own `eq × prod`.

## Reinforcement learning

**Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O. (2017).**
*Proximal Policy Optimization Algorithms.*
arXiv:[1707.06347](https://arxiv.org/abs/1707.06347)

All five policy networks in the paper are trained with PPO.

**Schulman, J., Levine, S., Abbeel, P., Jordan, M., & Moritz, P. (2015).**
*Trust Region Policy Optimization.*
arXiv:[1502.05477](https://arxiv.org/abs/1502.05477)

**Mnih, V., Badia, A. P., Mirza, M., Graves, A., Lillicrap, T., Harley, T.,
Silver, D., & Kavukcuoglu, K. (2016).** *Asynchronous Methods for Deep
Reinforcement Learning.*
arXiv:[1602.01783](https://arxiv.org/abs/1602.01783)

Source of the entropy regularization the paper repurposes to keep the planner
exploring tax schedules early in training.

**Mnih, V., Kavukcuoglu, K., Silver, D., Graves, A., Antonoglou, I.,
Wierstra, D., & Riedmiller, M. (2013).** *Playing Atari with Deep Reinforcement
Learning.* arXiv:[1312.5602](https://arxiv.org/abs/1312.5602)

## Reference implementation

**salesforce/ai-economist** — <https://github.com/salesforce/ai-economist>
BSD 3-Clause. Pinned here at `a84d5f3fdcabb207d9fde7754d34906903b3e184`.
See [NOTICE.md](NOTICE.md).
