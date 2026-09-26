# Review (dry run: no API call made)

Model that would be called: `claude-opus-5-5`

## System prompt

```text
You review a paper-trading research rig for a discretionary ICT/SMC trader.
The rig detects rule-based setups (liquidity sweep of the prior session high/low, 5m market
structure shift, entry at an FVG or order block in the 62-79% OTE zone, London and NY AM
killzones only), asks TypeSafe's Jev model a battery of typed questions about each setup, and
compares arm A (every rule-based signal) against arm B (only signals Jev's answers pass).

Hard rules the rig follows, which your suggestions must respect:
- Research and paper trading only. Never suggest live trading, order placement, or exchange keys.
- Every trade has a stop at entry, at least 1.5R, and fixed $25 (or $50) risk.
- No signals within 2 minutes of a high-impact news release. No correlated stacking.
- Nothing is tuned on the holdout. If a holdout result is present, treat it as final and do not
  propose changes justified by it; say what a future, fresh holdout would need instead.

Your role is to suggest. A human decides. Be concrete and honest about sample size: say when a
difference is within noise (use the bootstrap interval and trade counts you are given). If the
data is synthetic or Jev ran in mock mode, say plainly that the numbers only test the pipeline.

Jev primitives, for any new question you propose: Choice (pick one option from a set, returns
probabilities + confidence), Score (ordered rubric levels, returns an expected score +
confidence), Noul (yes/no, returns a probability, no confidence). Jev is weak at arithmetic
and numeric comparison, so questions should be semantic judgements about named fields of the
snapshot, and numbers should be bucketed in code.

Write the review in Markdown with exactly these sections:
## Summary
## What worked
## What didn't
## What's miscalibrated
## Suggested new Jev questions
(for each: name, primitive, instructions, criteria, and what outcome label would grade it)
## Suggested experiments
(each must be testable on train data only, with the expected sign of the effect)
## Caveats
```

## User message (115,490 characters)

```text
Here are this week's eval summaries (JSON) and trade logs (CSV).

<eval_summary split="train">
{
 "split": "train",
 "mode": "mock",
 "data_source": "synthetic",
 "generated_utc": "2026-09-26T21:41:17+00:00",
 "config_hash": "f7e94b4fc34c",
 "period": {
  "data_start": "2026-01-05 00:00:00+00:00",
  "boundary": "2026-10-05 17:00:00+00:00",
  "data_end": "2027-01-04 23:55:00+00:00",
  "embargo": "1 days 01:00:00"
 },
 "signals_in_split": 380,
 "threshold": 0.3,
 "threshold_reason": "best train expectancy with >= 20 trades",
 "threshold_grid": [
  {
   "threshold": 0.3,
   "trades": 24,
   "expectancy_r": 0.10462790273787893
  },
  {
   "threshold": 0.35,
   "trades": 24,
   "expectancy_r": 0.10462790273787893
  },
  {
   "threshold": 0.4,
   "trades": 21,
   "expectancy_r": -0.06197256859027146
  },
  {
   "threshold": 0.45,
   "trades": 18,
   "expectancy_r": 0.15837364403930787
  },
  {
   "threshold": 0.5,
   "trades": 15,
   "expectancy_r": 0.46842621342880963
  },
  {
   "threshold": 0.55,
   "trades": 14,
   "expectancy_r": 0.6100155882639945
  },
  {
   "threshold": 0.6,
   "trades": 14,
   "expectancy_r": 0.6100155882639945
  },
  {
   "threshold": 0.65,
   "trades": 14,
   "expectancy_r": 0.6100155882639945
  },
  {
   "threshold": 0.7,
   "trades": 12,
   "expectancy_r": 0.9619796145485316
  },
  {
   "threshold": 0.75,
   "trades": 11,
   "expectancy_r": 0.7890671236788557
  },
  {
   "threshold": 0.8,
   "trades": 7,
   "expectancy_r": 0.38597050439806646
  }
 ],
 "arm_a": {
  "trades": 172,
  "hit_rate": 0.1686046511627907,
  "expectancy_r": -0.2563848358014526,
  "total_r": -44.09819175784985,
  "pnl_usd": -1102.454793946246,
  "profit_factor": 0.7786078470201657,
  "max_drawdown_r": 60.356896782874756,
  "max_drawdown_usd": 1508.9224195718687
 },
 "arm_b": {
  "trades": 24,
  "hit_rate": 0.20833333333333334,
  "expectancy_r": 0.10462790273787893,
  "total_r": 2.5110696657090945,
  "pnl_usd": 62.7767416427275,
  "profit_factor": 1.094216951312523,
  "max_drawdown_r": 14.556835681724197,
  "max_drawdown_usd": 363.92089204310486
 },
 "expectancy_diff_b_minus_a": {
  "diff": 0.3610127385393315,
  "low": -0.831580110499189,
  "high": 1.8388808700339336,
  "p_b_not_better": 0.3028
 },
 "decisions": {
  "A": {
   "skip: not_traded": 195,
   "take": 172,
   "skip: correlated_open": 13
  },
  "B": {
   "skip: setup_quality": 188,
   "escalate: confidence": 133,
   "take": 24,
   "skip: not_traded": 22,
   "skip: target_before_stop": 13
  }
 },
 "calibration": {
  "direction_agrees": {
   "n": 380,
   "brier": 0.2932451446052632,
   "base_rate": 0.5052631578947369,
   "brier_reference": 0.24997229916897504,
   "skill": -0.1731105629709666,
   "plot": "reliability_direction_agrees_train.png"
  },
  "sweep_is_genuine": {
   "n": 380,
   "brier": 0.28094154944736843,
   "base_rate": 0.44473684210526315,
   "brier_reference": 0.24694598337950147,
   "skill": -0.13766397656131657,
   "plot": "reliability_sweep_is_genuine_train.png"
  },
  "target_before_stop": {
   "n": 375,
   "brier": 0.28870884090666665,
   "base_rate": 0.42133333333333334,
   "brier_reference": 0.24381155555555556,
   "skill": -0.18414748738552178,
   "plot": "reliability_target_before_stop_train.png"
  }
 },
 "jev": {
  "scored": 380,
  "regimes": {
   "volatile_chop": 101,
   "ranging": 98,
   "trending_down": 96,
   "trending_up": 81,
   "crisis": 4
  },
  "mean_confidence": 0.65858,
  "escalation_rate": 0.35,
  "mean_latency_ms": 0.35829024999848597,
  "total_cost_usd": 0.015570912
 },
 "notes": []
}
</eval_summary>

<eval_summary split="holdout">
{
 "split": "holdout",
 "mode": "mock",
 "data_source": "synthetic",
 "generated_utc": "2026-09-26T21:41:18+00:00",
 "config_hash": "f7e94b4fc34c",
 "period": {
  "data_start": "2026-01-05 00:00:00+00:00",
  "boundary": "2026-10-05 17:00:00+00:00",
  "data_end": "2027-01-04 23:55:00+00:00",
  "embargo": "1 days 01:00:00"
 },
 "signals_in_split": 112,
 "threshold": 0.3,
 "threshold_reason": "frozen from train on 2026-09-26T21:41:16.422232+00:00",
 "threshold_grid": null,
 "arm_a": {
  "trades": 54,
  "hit_rate": 0.16666666666666666,
  "expectancy_r": -0.11071357818852055,
  "total_r": -5.9785332221801095,
  "pnl_usd": -149.4633305545027,
  "profit_factor": 0.9030200429594031,
  "max_drawdown_r": 16.465636886897467,
  "max_drawdown_usd": 411.6409221724367
 },
 "arm_b": {
  "trades": 10,
  "hit_rate": 0.1,
  "expectancy_r": -0.31719776165706437,
  "total_r": -3.1719776165706435,
  "pnl_usd": -79.2994404142661,
  "profit_factor": 0.7403669164640849,
  "max_drawdown_r": 10.868926234858305,
  "max_drawdown_usd": 271.7231558714576
 },
 "expectancy_diff_b_minus_a": {
  "diff": -0.2064841834685438,
  "low": -1.855792254343952,
  "high": 2.181781825407939,
  "p_b_not_better": 0.626
 },
 "decisions": {
  "A": {
   "skip: not_traded": 54,
   "take": 54,
   "skip: correlated_open": 4
  },
  "B": {
   "skip: setup_quality": 53,
   "escalate: confidence": 39,
   "take": 10,
   "skip: not_traded": 7,
   "skip: target_before_stop": 3
  }
 },
 "calibration": {
  "direction_agrees": {
   "n": 112,
   "brier": 0.30835805517857146,
   "base_rate": 0.5089285714285714,
   "brier_reference": 0.24992028061224492,
   "skill": -0.23382566001913885,
   "plot": "reliability_direction_agrees_holdout.png"
  },
  "sweep_is_genuine": {
   "n": 112,
   "brier": 0.28087293473214286,
   "base_rate": 0.39285714285714285,
   "brier_reference": 0.23852040816326534,
   "skill": -0.17756353385026724,
   "plot": "reliability_sweep_is_genuine_holdout.png"
  },
  "target_before_stop": {
   "n": 112,
   "brier": 0.28230815526785713,
   "base_rate": 0.42857142857142855,
   "brier_reference": 0.24489795918367344,
   "skill": -0.1527583006770834,
   "plot": "reliability_target_before_stop_holdout.png"
  }
 },
 "jev": {
  "scored": 112,
  "regimes": {
   "trending_down": 31,
   "trending_up": 30,
   "volatile_chop": 29,
   "ranging": 21,
   "crisis": 1
  },
  "mean_confidence": 0.64819375,
  "escalation_rate": 0.3482142857142857,
  "mean_latency_ms": 0.38710625893502637,
  "total_cost_usd": 0.004590096
 },
 "notes": []
}
</eval_summary>

<trade_log split="train">
id,symbol,ts_utc,killzone,direction,zone_kind,reward_risk,outcome,r_multiple,pnl_usd,jev_regime,jev_confidence,jev_setup_quality,jev_direction_agrees,jev_sweep_is_genuine,jev_target_before_stop,label_direction_agrees,label_sweep_is_genuine,label_target_before_stop,arm_a_action,arm_a_reason,arm_b_action,arm_b_reason
BTC-20260105T1000-london-short,BTC,2026-01-05T10:00:00+00:00,london,short,fvg,9.099843760384918,no_fill,,,trending_up,0.581,1.2139,0.3708,0.5659,0.5879,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.58 < 0.60
BTC-20260106T0800-london-short,BTC,2026-01-06T08:00:00+00:00,london,short,ob,4.351248964474069,missed,,,trending_up,0.4044,2.2832,0.9791,0.5662,0.4329,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.40 < 0.60
ETH-20260106T1430-ny_am-long,ETH,2026-01-06T14:30:00+00:00,ny_am,long,fvg,4.770996617691734,no_fill,,,ranging,0.8061,1.0093,0.4152,0.7038,0.2795,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.01 < 2.0
BTC-20260107T0825-london-long,BTC,2026-01-07T08:25:00+00:00,london,long,ob,4.512543275709209,stop,-1.3994413874310316,-34.98603468577579,trending_down,0.8821,2.8888,0.6392,0.6346,0.7823,0,0,0.0,take,,take,
BTC-20260107T1335-ny_am-long,BTC,2026-01-07T13:35:00+00:00,ny_am,long,fvg,3.059318660937109,stop,-1.2216621654961093,-30.541554137402734,trending_up,0.8035,2.0188,0.6155,0.364,0.1093,0,0,0.0,take,,skip,target_before_stop 0.11 < 0.30
ETH-20260109T0755-london-short,ETH,2026-01-09T07:55:00+00:00,london,short,ob,4.787893316230285,missed,,,trending_up,0.4256,0.1361,0.4132,0.6058,0.3392,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.43 < 0.60
ETH-20260109T0950-london-long,ETH,2026-01-09T09:50:00+00:00,london,long,ob,2.9866813127327054,target,2.864017014114968,71.6004253528742,volatile_chop,0.7765,2.9773,0.6168,0.5942,0.7157,0,1,1.0,take,,take,
BTC-20260109T1350-ny_am-short,BTC,2026-01-09T13:50:00+00:00,ny_am,short,ob,4.228057072858068,stop,-1.3692329497740596,-34.23082374435149,trending_up,0.8514,1.8938,0.4556,0.1422,0.7186,1,0,0.0,take,,skip,setup_quality 1.89 < 2.0
ETH-20260111T0805-london-long,ETH,2026-01-11T08:05:00+00:00,london,long,fvg,2.2713135058066705,no_fill,,,trending_down,0.7288,2.4234,0.6528,0.2925,0.2725,0,0,0.0,skip,not_traded: no_fill,skip,target_before_stop 0.27 < 0.30
BTC-20260113T0815-london-long,BTC,2026-01-13T08:15:00+00:00,london,long,ob,1.57352711453079,missed,,,ranging,0.1653,1.813,0.3901,0.5548,0.2449,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.17 < 0.60
BTC-20260113T0955-london-short,BTC,2026-01-13T09:55:00+00:00,london,short,ob,4.8080226262185555,stop,-1.475853183984989,-36.89632959962473,ranging,0.3975,1.9672,0.1315,0.2751,0.1217,0,0,0.0,take,,escalate,confidence 0.40 < 0.60
ETH-20260114T0730-london-long,ETH,2026-01-14T07:30:00+00:00,london,long,fvg,4.050742722555861,no_fill,,,trending_down,0.8461,1.0014,0.7452,0.3954,0.5536,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.00 < 2.0
BTC-20260114T0740-london-long,BTC,2026-01-14T07:40:00+00:00,london,long,ob,3.200581255980193,missed,,,volatile_chop,0.0986,1.6811,0.1127,0.7205,0.5735,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.10 < 0.60
BTC-20260114T1405-ny_am-short,BTC,2026-01-14T14:05:00+00:00,ny_am,short,fvg,5.589116153367014,no_fill,,,trending_down,0.6717,1.881,0.1761,0.5693,0.4784,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.88 < 2.0
BTC-20260115T0925-london-short,BTC,2026-01-15T09:25:00+00:00,london,short,fvg,3.4845889034225697,no_fill,,,ranging,0.7707,0.2865,0.7966,0.7421,0.6916,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.29 < 2.0
BTC-20260115T1405-ny_am-long,BTC,2026-01-15T14:05:00+00:00,ny_am,long,ob,5.915985906401499,no_fill,,,trending_up,0.5912,1.3973,0.5196,0.4889,0.3965,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.59 < 0.60
BTC-20260116T0735-london-short,BTC,2026-01-16T07:35:00+00:00,london,short,ob,5.73290435069934,stop,-1.441419167244634,-36.035479181115846,trending_up,0.7,1.2975,0.5093,0.8137,0.4052,0,0,0.0,take,,skip,setup_quality 1.30 < 2.0
ETH-20260117T0735-london-long,ETH,2026-01-17T07:35:00+00:00,london,long,ob,14.26372784349887,stop,-1.5447565243830588,-38.61891310957647,volatile_chop,0.5341,1.0003,0.2312,0.2465,0.3702,1,0,0.0,take,,escalate,confidence 0.53 < 0.60
BTC-20260117T0920-london-long,BTC,2026-01-17T09:20:00+00:00,london,long,ob,11.106501019261843,no_fill,,,trending_down,0.7126,0.6142,0.3831,0.5593,0.4359,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.61 < 2.0
ETH-20260117T1450-ny_am-long,ETH,2026-01-17T14:50:00+00:00,ny_am,long,ob,5.031981568064967,no_fill,,,trending_up,0.6137,1.1885,0.5699,0.7096,0.4062,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 1.19 < 2.0
BTC-20260118T0720-london-long,BTC,2026-01-18T07:20:00+00:00,london,long,ob,13.41131744497276,target,13.196408992986935,329.9102248246734,trending_down,0.3305,1.9179,0.9285,0.3807,0.7999,1,1,1.0,take,,escalate,confidence 0.33 < 0.60
BTC-20260119T0850-london-short,BTC,2026-01-19T08:50:00+00:00,london,short,ob,12.87088313093486,stop,-1.4439860255007333,-36.09965063751833,trending_down,0.643,1.5272,0.4035,0.6578,0.401,0,0,0.0,take,,skip,setup_quality 1.53 < 2.0
BTC-20260119T1350-ny_am-short,BTC,2026-01-19T13:50:00+00:00,ny_am,short,ob,5.206527944627326,missed,,,volatile_chop,0.6315,2.6728,0.6498,0.3719,0.6102,1,1,1.0,skip,not_traded: missed,skip,not_traded: missed
ETH-20260119T1405-ny_am-short,ETH,2026-01-19T14:05:00+00:00,ny_am,short,fvg,4.56634318344021,no_fill,,,trending_up,0.7559,0.4109,0.1595,0.5629,0.8155,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.41 < 2.0
BTC-20260120T0725-london-long,BTC,2026-01-20T07:25:00+00:00,london,long,ob,12.653012409427344,no_fill,,,trending_down,0.5777,1.1311,0.2437,0.7249,0.7171,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.58 < 0.60
ETH-20260120T0730-london-long,ETH,2026-01-20T07:30:00+00:00,london,long,fvg,12.046852150251237,no_fill,,,trending_down,0.5738,1.4602,0.5978,0.5734,0.1481,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.57 < 0.60
BTC-20260121T0740-london-short,BTC,2026-01-21T07:40:00+00:00,london,short,ob,6.783693423766343,stop,-1.434856653055246,-35.87141632638115,trending_down,0.6344,1.0968,0.3073,0.4846,0.5573,0,0,0.0,take,,skip,setup_quality 1.10 < 2.0
BTC-20260121T1415-ny_am-short,BTC,2026-01-21T14:15:00+00:00,ny_am,short,ob,4.676144884567613,no_fill,,,volatile_chop,0.3681,2.4054,0.2952,0.4823,0.1425,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.37 < 0.60
ETH-20260122T0850-london-long,ETH,2026-01-22T08:50:00+00:00,london,long,ob,3.238162495762769,missed,,,trending_up,0.8915,2.9626,0.6952,0.2134,0.427,1,1,1.0,skip,not_traded: missed,skip,not_traded: missed
BTC-20260122T0855-london-long,BTC,2026-01-22T08:55:00+00:00,london,long,ob,2.332357487327472,missed,,,volatile_chop,0.8076,1.8522,0.4593,0.6455,0.241,1,0,1.0,skip,not_traded: missed,skip,setup_quality 1.85 < 2.0
BTC-20260123T1400-ny_am-short,BTC,2026-01-23T14:00:00+00:00,ny_am,short,fvg,3.5671072302274505,stop,-1.3581281540132,-33.95320385033,ranging,0.897,2.9915,0.6527,0.1205,0.4092,0,0,0.0,take,,take,
ETH-20260124T0835-london-long,ETH,2026-01-24T08:35:00+00:00,london,long,ob,4.597618041683046,stop,-1.4998173719517423,-37.495434298793555,ranging,0.7259,1.0131,0.5506,0.7032,0.3233,0,0,0.0,take,,skip,setup_quality 1.01 < 2.0
BTC-20260125T0905-london-long,BTC,2026-01-25T09:05:00+00:00,london,long,fvg,2.777093403716494,missed,,,trending_down,0.2558,1.0051,0.2699,0.746,0.5093,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.26 < 0.60
ETH-20260125T0905-london-long,ETH,2026-01-25T09:05:00+00:00,london,long,fvg,3.01171327742698,missed,,,ranging,0.2183,1.8856,0.3555,0.9252,0.7518,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.22 < 0.60
BTC-20260125T1305-ny_am-short,BTC,2026-01-25T13:05:00+00:00,ny_am,short,fvg,5.272483978199455,no_fill,,,volatile_chop,0.6805,0.9392,0.2561,0.7752,0.4664,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 0.94 < 2.0
BTC-20260126T1250-ny_am-short,BTC,2026-01-26T12:50:00+00:00,ny_am,short,ob,2.860232901329122,no_fill,,,volatile_chop,0.3056,2.9397,0.6973,0.2583,0.6569,0,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.31 < 0.60
BTC-20260127T1320-ny_am-long,BTC,2026-01-27T13:20:00+00:00,ny_am,long,fvg,3.2677823092234366,no_fill,,,trending_down,0.5427,1.9436,0.6767,0.5959,0.7498,0,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.54 < 0.60
ETH-20260127T1320-ny_am-long,ETH,2026-01-27T13:20:00+00:00,ny_am,long,ob,8.331912174215674,no_fill,,,ranging,0.6396,2.8867,0.5796,0.2412,0.2796,1,1,1.0,skip,not_traded: no_fill,skip,target_before_stop 0.28 < 0.30
ETH-20260128T0805-london-long,ETH,2026-01-28T08:05:00+00:00,london,long,fvg,9.198570425711232,stop,-1.3422665976364931,-33.55666494091233,trending_up,0.4018,2.7924,0.4931,0.7369,0.8326,1,0,0.0,take,,escalate,confidence 0.40 < 0.60
ETH-20260129T0905-london-long,ETH,2026-01-29T09:05:00+00:00,london,long,ob,8.047251682380407,stop,-1.3615682982908988,-34.03920745727247,volatile_chop,0.5273,2.3516,0.0963,0.4063,0.5813,0,0,0.0,take,,escalate,confidence 0.53 < 0.60
ETH-20260130T0720-london-long,ETH,2026-01-30T07:20:00+00:00,london,long,ob,10.745303947808653,no_fill,,,trending_up,0.2876,1.2413,0.2978,0.54,0.4098,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.29 < 0.60
BTC-20260130T0750-london-long,BTC,2026-01-30T07:50:00+00:00,london,long,ob,5.96771724460494,stop,-1.3480827776224638,-33.702069440561594,trending_up,0.278,1.0674,0.3079,0.2539,0.6472,0,1,0.0,take,,escalate,confidence 0.28 < 0.60
ETH-20260130T1435-ny_am-short,ETH,2026-01-30T14:35:00+00:00,ny_am,short,ob,5.984835409092884,stop,-1.3059929189864392,-32.64982297466098,trending_up,0.4809,0.9708,0.2986,0.6971,0.2724,1,0,0.0,take,,escalate,confidence 0.48 < 0.60
BTC-20260201T0905-london-long,BTC,2026-02-01T09:05:00+00:00,london,long,ob,4.34397826358386,target,4.170624948742422,104.26562371856053,volatile_chop,0.3873,0.6338,0.4743,0.6566,0.3854,0,1,1.0,skip,correlated_open: ETH (ETH-20260201T0905-london-long),escalate,confidence 0.39 < 0.60
ETH-20260201T0905-london-long,ETH,2026-02-01T09:05:00+00:00,london,long,ob,8.74458732200332,stop,-1.4822373416073347,-37.05593354018337,trending_down,0.5114,2.2546,0.8023,0.3288,0.4803,1,0,0.0,take,,escalate,confidence 0.51 < 0.60
BTC-20260202T0735-london-short,BTC,2026-02-02T07:35:00+00:00,london,short,ob,5.989663123222433,no_fill,,,volatile_chop,0.7212,0.4893,0.4854,0.438,0.934,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.49 < 2.0
ETH-20260202T0850-london-short,ETH,2026-02-02T08:50:00+00:00,london,short,ob,6.655436859668086,stop,-1.5605725154927899,-39.01431288731975,trending_up,0.8106,0.9852,0.2247,0.4254,0.6654,0,0,0.0,take,,skip,setup_quality 0.99 < 2.0
BTC-20260203T0835-london-long,BTC,2026-02-03T08:35:00+00:00,london,long,ob,3.074498911930575,missed,,,ranging,0.5702,1.6726,0.7861,0.5198,0.1239,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.57 < 0.60
BTC-20260203T1405-ny_am-long,BTC,2026-02-03T14:05:00+00:00,ny_am,long,ob,8.836279828285262,no_fill,,,trending_up,0.8302,1.0249,0.7984,0.0998,0.6831,1,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.02 < 2.0
ETH-20260204T0950-london-long,ETH,2026-02-04T09:50:00+00:00,london,long,fvg,4.008302681964811,no_fill,,,trending_down,0.4813,0.5007,0.5818,0.5066,0.2558,0,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.48 < 0.60
ETH-20260205T1500-ny_am-short,ETH,2026-02-05T15:00:00+00:00,ny_am,short,fvg,8.097203009052418,no_fill,,,volatile_chop,0.7514,2.7183,0.6101,0.4487,0.7943,0,1,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260206T0940-london-long,ETH,2026-02-06T09:40:00+00:00,london,long,ob,3.987248314245395,target,3.7910556908580673,94.77639227145168,trending_down,0.779,2.9513,0.521,0.2036,0.9757,1,1,1.0,take,,take,
ETH-20260206T1300-ny_am-short,ETH,2026-02-06T13:00:00+00:00,ny_am,short,ob,7.388815381814092,no_fill,,,ranging,0.1455,0.9728,0.6957,0.5121,0.4,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.15 < 0.60
BTC-20260206T1450-ny_am-short,BTC,2026-02-06T14:50:00+00:00,ny_am,short,ob,5.868496755064869,target,5.740273210038373,143.50683025095933,trending_up,0.4619,1.6504,0.8258,0.0114,0.2713,1,1,1.0,take,,escalate,confidence 0.46 < 0.60
BTC-20260207T0950-london-long,BTC,2026-02-07T09:50:00+00:00,london,long,ob,2.0030556217380138,stop,-1.3506918370165122,-33.7672959254128,ranging,0.9637,2.0039,0.6653,0.578,0.0772,1,0,0.0,take,,skip,target_before_stop 0.08 < 0.30
ETH-20260210T0740-london-short,ETH,2026-02-10T07:40:00+00:00,london,short,ob,9.389336127880057,no_fill,,,trending_up,0.7446,0.483,0.6005,0.6225,0.5907,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.48 < 2.0
ETH-20260210T1410-ny_am-long,ETH,2026-02-10T14:10:00+00:00,ny_am,long,ob,9.826095133453835,stop,-1.4944042880845052,-37.36010720211263,crisis,0.4168,1.6276,0.0411,0.9175,0.5682,0,0,0.0,take,,escalate,confidence 0.42 < 0.60
ETH-20260211T0745-london-short,ETH,2026-02-11T07:45:00+00:00,london,short,ob,2.8918998265300293,no_fill,,,trending_down,0.5218,0.2001,0.1204,0.421,0.7528,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.52 < 0.60
BTC-20260211T1335-ny_am-long,BTC,2026-02-11T13:35:00+00:00,ny_am,long,ob,6.117282905647171,stop,-1.312928836179053,-32.82322090447632,trending_up,0.7111,2.729,0.1941,0.308,0.4163,1,0,0.0,take,,take,
BTC-20260212T0905-london-short,BTC,2026-02-12T09:05:00+00:00,london,short,ob,7.793320222560299,target,7.624500633948344,190.6125158487086,ranging,0.8665,1.8264,0.802,0.59,0.2732,1,1,1.0,take,,skip,setup_quality 1.83 < 2.0
BTC-20260214T0935-london-long,BTC,2026-02-14T09:35:00+00:00,london,long,ob,7.528638470095232,stop,-1.4935968478391226,-37.339921195978064,ranging,0.8545,1.8378,0.5533,0.441,0.6778,1,0,0.0,take,,skip,setup_quality 1.84 < 2.0
BTC-20260217T0825-london-short,BTC,2026-02-17T08:25:00+00:00,london,short,ob,4.883118888980103,no_fill,,,ranging,0.6786,2.5561,0.4867,0.7279,0.2897,1,1,1.0,skip,not_traded: no_fill,skip,target_before_stop 0.29 < 0.30
BTC-20260218T0900-london-long,BTC,2026-02-18T09:00:00+00:00,london,long,fvg,2.3573800001800507,missed,,,trending_down,0.8208,1.9728,0.1018,0.412,0.6554,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.97 < 2.0
ETH-20260221T0925-london-long,ETH,2026-02-21T09:25:00+00:00,london,long,fvg,6.4110223308437,no_fill,,,volatile_chop,0.6296,1.4461,0.4242,0.6679,0.4794,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 1.45 < 2.0
BTC-20260222T0905-london-short,BTC,2026-02-22T09:05:00+00:00,london,short,ob,6.998075218914879,no_fill,,,volatile_chop,0.4531,1.7228,0.2897,0.6378,0.1677,1,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.45 < 0.60
ETH-20260222T0905-london-short,ETH,2026-02-22T09:05:00+00:00,london,short,fvg,5.036562444671981,no_fill,,,ranging,0.7088,1.8765,0.6841,0.6532,0.3021,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 1.88 < 2.0
ETH-20260224T0805-london-long,ETH,2026-02-24T08:05:00+00:00,london,long,ob,11.127681288575278,stop,-1.5418095228717255,-38.545238071793136,trending_down,0.8934,2.9189,0.2136,0.4907,0.284,0,0,0.0,take,,skip,target_before_stop 0.28 < 0.30
ETH-20260225T0800-london-long,ETH,2026-02-25T08:00:00+00:00,london,long,ob,4.150120076346283,no_fill,,,ranging,0.5253,1.1835,0.6874,0.4704,0.3639,0,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.53 < 0.60
BTC-20260225T0850-london-long,BTC,2026-02-25T08:50:00+00:00,london,long,ob,3.9718629520076343,stop,-1.3186318488259434,-32.965796220648585,volatile_chop,0.9228,0.1419,0.9191,0.573,0.5063,0,0,0.0,take,,skip,setup_quality 0.14 < 2.0
BTC-20260225T1310-ny_am-long,BTC,2026-02-25T13:10:00+00:00,ny_am,long,ob,4.045238426248206,stop,-1.2955087426448428,-32.38771856612107,volatile_chop,0.8687,1.9362,0.3591,0.6211,0.089,1,0,0.0,take,,skip,setup_quality 1.94 < 2.0
ETH-20260226T1420-ny_am-long,ETH,2026-02-26T14:20:00+00:00,ny_am,long,fvg,6.04745347877347,target,5.968954829412046,149.22387073530115,volatile_chop,0.8748,1.9812,0.1683,0.0771,0.5296,1,1,1.0,take,,skip,setup_quality 1.98 < 2.0
BTC-20260227T0820-london-short,BTC,2026-02-27T08:20:00+00:00,london,short,fvg,5.685684328859073,no_fill,,,volatile_chop,0.9179,1.0586,0.5105,0.2097,0.3691,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.06 < 2.0
ETH-20260227T0825-london-short,ETH,2026-02-27T08:25:00+00:00,london,short,ob,7.273835067153095,stop,-1.4671116732443716,-36.67779183110929,trending_down,0.5685,2.9298,0.7216,0.7167,0.6808,0,0,0.0,take,,escalate,confidence 0.57 < 0.60
ETH-20260227T1410-ny_am-short,ETH,2026-02-27T14:10:00+00:00,ny_am,short,ob,10.604003423677874,target,10.455467428663782,261.38668571659457,trending_up,0.6105,2.8184,0.3625,0.5228,0.7867,1,1,1.0,take,,take,
BTC-20260227T1450-ny_am-short,BTC,2026-02-27T14:50:00+00:00,ny_am,short,ob,14.149316157009,no_fill,,,ranging,0.7195,2.1979,0.0519,0.3736,0.5992,1,1,1.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260228T1305-ny_am-long,ETH,2026-02-28T13:05:00+00:00,ny_am,long,ob,7.020977848856051,stop,-1.4213837974325503,-35.53459493581376,trending_up,0.7836,1.9041,0.6519,0.5303,0.6799,0,0,0.0,take,,skip,setup_quality 1.90 < 2.0
ETH-20260303T0720-london-long,ETH,2026-03-03T07:20:00+00:00,london,long,fvg,2.0,target,1.903968651612229,47.599216290305726,ranging,0.619,1.1556,0.546,0.8665,0.4232,1,1,1.0,take,,skip,setup_quality 1.16 < 2.0
BTC-20260303T0750-london-short,BTC,2026-03-03T07:50:00+00:00,london,short,fvg,2.0,target,1.8699056749379588,46.74764187344897,volatile_chop,0.4994,2.8566,0.7826,0.5783,0.22,0,0,1.0,skip,correlated_open: ETH (ETH-20260303T0720-london-long),escalate,confidence 0.50 < 0.60
BTC-20260303T1350-ny_am-short,BTC,2026-03-03T13:50:00+00:00,ny_am,short,ob,9.556939687120984,stop,-1.4928286149583818,-37.320715373959544,trending_up,0.8716,0.9316,0.5665,0.5356,0.6134,0,0,0.0,take,,skip,setup_quality 0.93 < 2.0
BTC-20260308T0720-london-long,BTC,2026-03-08T07:20:00+00:00,london,long,fvg,4.088874164168656,stop,-1.4371629834813242,-35.92907458703311,trending_down,0.7264,0.2044,0.2597,0.6045,0.7527,0,0,0.0,take,,skip,setup_quality 0.20 < 2.0
ETH-20260309T0730-london-long,ETH,2026-03-09T07:30:00+00:00,london,long,ob,9.595057298826472,stop,-1.5364625169315673,-38.41156292328918,trending_up,0.705,1.2582,0.647,0.6907,0.5394,1,0,0.0,take,,skip,setup_quality 1.26 < 2.0
BTC-20260309T0850-london-long,BTC,2026-03-09T08:50:00+00:00,london,long,fvg,7.188107466643028,no_fill,,,ranging,0.8035,2.7329,0.8613,0.8536,0.3671,1,1,1.0,skip,not_traded: no_fill,skip,not_traded: no_fill
BTC-20260309T1350-ny_am-short,BTC,2026-03-09T13:50:00+00:00,ny_am,short,ob,13.51698673117442,no_fill,,,ranging,0.9186,1.9995,0.3408,0.6049,0.1735,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 2.00 < 2.0
BTC-20260310T0820-london-short,BTC,2026-03-10T08:20:00+00:00,london,short,ob,4.105319084489311,missed,,,trending_down,0.6879,1.1645,0.5494,0.5024,0.3381,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.16 < 2.0
ETH-20260310T0825-london-short,ETH,2026-03-10T08:25:00+00:00,london,short,ob,5.719963871448714,missed,,,trending_up,0.3222,1.9162,0.4826,0.0903,0.2527,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.32 < 0.60
BTC-20260312T0800-london-long,BTC,2026-03-12T08:00:00+00:00,london,long,ob,9.981159350015911,no_fill,,,trending_down,0.3622,1.4264,0.7653,0.7284,0.3004,0,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.36 < 0.60
ETH-20260312T0820-london-long,ETH,2026-03-12T08:20:00+00:00,london,long,fvg,8.376078242125194,no_fill,,,volatile_chop,0.5529,1.0449,0.838,0.3722,0.2721,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.55 < 0.60
ETH-20260313T0740-london-short,ETH,2026-03-13T07:40:00+00:00,london,short,fvg,2.894122688295888,no_fill,,,volatile_chop,0.7145,2.9661,0.6002,0.4553,0.5058,0,0,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260313T1250-ny_am-short,ETH,2026-03-13T12:50:00+00:00,ny_am,short,ob,7.590077558294411,no_fill,,,trending_down,0.8463,0.0976,0.233,0.4379,0.5374,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 0.10 < 2.0
BTC-20260313T1350-ny_am-short,BTC,2026-03-13T13:50:00+00:00,ny_am,short,ob,6.649126220269044,no_fill,,,volatile_chop,0.8505,1.8615,0.4103,0.5153,0.1483,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.86 < 2.0
BTC-20260314T0810-london-long,BTC,2026-03-14T08:10:00+00:00,london,long,ob,6.4752124305217755,stop,-1.2815862705904848,-32.03965676476212,ranging,0.637,1.9732,0.5871,0.3602,0.5506,1,1,0.0,take,,skip,setup_quality 1.97 < 2.0
ETH-20260314T1335-ny_am-long,ETH,2026-03-14T13:35:00+00:00,ny_am,long,fvg,2.513160997505423,missed,,,trending_down,0.7783,1.0915,0.711,0.1017,0.79,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.09 < 2.0
BTC-20260315T0835-london-long,BTC,2026-03-15T08:35:00+00:00,london,long,fvg,5.458249353154666,no_fill,,,volatile_chop,0.5185,0.6775,0.9043,0.8376,0.2673,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.52 < 0.60
ETH-20260316T0730-london-short,ETH,2026-03-16T07:30:00+00:00,london,short,fvg,6.525591547555763,no_fill,,,volatile_chop,0.5208,2.2683,0.3163,0.34,0.1165,0,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.52 < 0.60
BTC-20260316T0735-london-short,BTC,2026-03-16T07:35:00+00:00,london,short,ob,8.107776626053091,no_fill,,,trending_down,0.3074,1.1147,0.1975,0.5065,0.7781,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.31 < 0.60
ETH-20260317T0755-london-long,ETH,2026-03-17T07:55:00+00:00,london,long,ob,7.569871819822892,no_fill,,,trending_up,0.3516,1.3116,0.2096,0.4606,0.7977,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.35 < 0.60
BTC-20260317T0800-london-long,BTC,2026-03-17T08:00:00+00:00,london,long,ob,7.26833713981908,no_fill,,,ranging,0.7894,1.1374,0.6058,0.3897,0.0383,1,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.14 < 2.0
BTC-20260318T0750-london-short,BTC,2026-03-18T07:50:00+00:00,london,short,ob,2.6661841969566624,stop,-1.3879433317447571,-34.69858329361893,trending_down,0.7513,0.0116,0.6199,0.7818,0.9267,1,0,0.0,take,,skip,setup_quality 0.01 < 2.0
ETH-20260318T1420-ny_am-short,ETH,2026-03-18T14:20:00+00:00,ny_am,short,fvg,6.95735441305999,no_fill,,,volatile_chop,0.7006,1.1957,0.6311,0.6381,0.6284,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.20 < 2.0
ETH-20260319T0720-london-long,ETH,2026-03-19T07:20:00+00:00,london,long,fvg,4.168587223825921,stop,-1.4952377548106641,-37.380943870266606,crisis,0.4342,1.9771,0.9789,0.5627,0.4702,0,0,0.0,take,,escalate,confidence 0.43 < 0.60
BTC-20260319T1335-ny_am-long,BTC,2026-03-19T13:35:00+00:00,ny_am,long,ob,11.892433312587384,stop,-1.40713365968001,-35.17834149200025,ranging,0.8143,2.0452,0.1044,0.3109,0.1365,0,0,0.0,take,,skip,target_before_stop 0.14 < 0.30
BTC-20260320T1310-ny_am-short,BTC,2026-03-20T13:10:00+00:00,ny_am,short,ob,7.611410447604071,stop,-1.2496787734507628,-31.241969336269072,volatile_chop,0.4015,1.9702,0.631,0.7297,0.3344,0,0,0.0,take,,escalate,confidence 0.40 < 0.60
BTC-20260321T0755-london-short,BTC,2026-03-21T07:55:00+00:00,london,short,ob,6.714707705471595,stop,-1.3721221244684563,-34.30305311171141,trending_down,0.8801,1.1325,0.5237,0.4623,0.8408,0,0,0.0,take,,skip,setup_quality 1.13 < 2.0
ETH-20260321T0755-london-short,ETH,2026-03-21T07:55:00+00:00,london,short,ob,4.620745956480333,no_fill,,,trending_up,0.9454,0.0807,0.7974,0.5031,0.273,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.08 < 2.0
BTC-20260321T1335-ny_am-short,BTC,2026-03-21T13:35:00+00:00,ny_am,short,fvg,8.081768359863725,stop,-1.3595334841062874,-33.988337102657184,trending_up,0.9159,1.1209,0.8821,0.2349,0.9256,0,0,0.0,take,,skip,setup_quality 1.12 < 2.0
BTC-20260322T0900-london-long,BTC,2026-03-22T09:00:00+00:00,london,long,ob,3.082899636185752,stop,-1.3188823241653378,-32.972058104133446,ranging,0.5654,1.5453,0.817,0.1729,0.8229,0,0,0.0,take,,escalate,confidence 0.57 < 0.60
ETH-20260323T1305-ny_am-long,ETH,2026-03-23T13:05:00+00:00,ny_am,long,fvg,7.405181816434939,no_fill,,,volatile_chop,0.4549,1.0953,0.7664,0.7655,0.7753,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.45 < 0.60
BTC-20260324T1405-ny_am-long,BTC,2026-03-24T14:05:00+00:00,ny_am,long,ob,3.994143939135428,no_fill,,,trending_down,0.9152,1.9222,0.4506,0.4018,0.4302,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.92 < 2.0
ETH-20260325T1315-ny_am-short,ETH,2026-03-25T13:15:00+00:00,ny_am,short,ob,3.82473805060511,target,3.7215451431928046,93.03862857982011,ranging,0.7269,1.0217,0.3914,0.8736,0.4305,0,1,1.0,take,,skip,setup_quality 1.02 < 2.0
ETH-20260326T0725-london-short,ETH,2026-03-26T07:25:00+00:00,london,short,ob,3.018692680419618,missed,,,ranging,0.5695,2.0369,0.348,0.534,0.6648,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.57 < 0.60
BTC-20260326T0955-london-short,BTC,2026-03-26T09:55:00+00:00,london,short,ob,7.80476489101114,stop,-1.8078913535963819,-45.197283839909545,trending_up,0.7392,1.7725,0.3915,0.685,0.5209,0,0,0.0,take,,skip,setup_quality 1.77 < 2.0
ETH-20260327T0905-london-short,ETH,2026-03-27T09:05:00+00:00,london,short,ob,4.92457635924921,missed,,,ranging,0.7971,2.7219,0.6037,0.4581,0.4466,0,0,1.0,skip,not_traded: missed,skip,not_traded: missed
BTC-20260327T0950-london-short,BTC,2026-03-27T09:50:00+00:00,london,short,fvg,3.166294364784669,stop,-1.2313830091024676,-30.78457522756169,ranging,0.8432,2.0708,0.6728,0.1208,0.3725,0,0,0.0,take,,take,
ETH-20260327T1500-ny_am-short,ETH,2026-03-27T15:00:00+00:00,ny_am,short,ob,9.872415555435913,target,9.69036502032886,242.2591255082215,ranging,0.6323,1.521,0.5874,0.4473,0.9559,1,1,1.0,take,,skip,setup_quality 1.52 < 2.0
ETH-20260328T0850-london-short,ETH,2026-03-28T08:50:00+00:00,london,short,ob,2.836851227842979,stop,-1.4310800098042948,-35.777000245107374,volatile_chop,0.7829,2.7813,0.3276,0.6976,0.4994,1,0,0.0,take,,take,
BTC-20260330T1305-ny_am-short,BTC,2026-03-30T13:05:00+00:00,ny_am,short,ob,5.249654222303816,stop,-1.3482573512098894,-33.70643378024724,trending_down,0.8552,1.0857,0.6976,0.382,0.7525,0,0,0.0,take,,skip,setup_quality 1.09 < 2.0
BTC-20260401T0835-london-short,BTC,2026-04-01T08:35:00+00:00,london,short,ob,3.9299405690200127,stop,-1.2873326853093574,-32.18331713273393,volatile_chop,0.814,1.0676,0.4108,0.1628,0.8164,0,0,0.0,take,,skip,setup_quality 1.07 < 2.0
BTC-20260402T1450-ny_am-short,BTC,2026-04-02T14:50:00+00:00,ny_am,short,fvg,4.826884683636098,stop,-1.237562772704416,-30.939069317610404,ranging,0.7345,2.8427,0.5194,0.6542,0.3886,1,0,0.0,take,,take,
ETH-20260402T1450-ny_am-short,ETH,2026-04-02T14:50:00+00:00,ny_am,short,fvg,6.115932962421252,stop,-1.324539116058249,-33.11347790145622,volatile_chop,0.2583,2.4816,0.5154,0.2478,0.2262,0,0,0.0,skip,correlated_open: BTC (BTC-20260402T1450-ny_am-short),escalate,confidence 0.26 < 0.60
BTC-20260404T0920-london-long,BTC,2026-04-04T09:20:00+00:00,london,long,ob,13.019878435481553,stop,-1.3959354786297964,-34.89838696574491,trending_down,0.622,1.0429,0.6831,0.8475,0.745,0,0,0.0,take,,skip,setup_quality 1.04 < 2.0
BTC-20260405T1450-ny_am-short,BTC,2026-04-05T14:50:00+00:00,ny_am,short,ob,14.653607206879276,stop,-1.452038357757865,-36.300958943946625,trending_down,0.2602,1.7301,0.7296,0.2912,0.2233,1,0,0.0,take,,escalate,confidence 0.26 < 0.60
ETH-20260406T0720-london-short,ETH,2026-04-06T07:20:00+00:00,london,short,ob,4.190511436339824,stop,-1.5726807360212218,-39.31701840053054,ranging,0.9178,1.9428,0.2672,0.5736,0.7836,1,0,0.0,take,,skip,setup_quality 1.94 < 2.0
BTC-20260406T0850-london-short,BTC,2026-04-06T08:50:00+00:00,london,short,ob,8.325278824988597,stop,-1.5234357684220199,-38.0858942105505,ranging,0.8295,1.9748,0.5597,0.699,0.194,1,1,0.0,take,,skip,setup_quality 1.97 < 2.0
BTC-20260406T1345-ny_am-long,BTC,2026-04-06T13:45:00+00:00,ny_am,long,ob,3.839443011492201,no_fill,,,volatile_chop,0.8655,1.9699,0.7687,0.5545,0.846,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.97 < 2.0
ETH-20260406T1350-ny_am-long,ETH,2026-04-06T13:50:00+00:00,ny_am,long,fvg,5.37427006843689,no_fill,,,trending_down,0.6926,0.4545,0.3947,0.4448,0.8275,1,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.45 < 2.0
ETH-20260407T1435-ny_am-short,ETH,2026-04-07T14:35:00+00:00,ny_am,short,fvg,4.584461381453648,stop,-1.246532254879741,-31.163306371993528,ranging,0.7437,1.05,0.9426,0.1548,0.4471,0,0,0.0,take,,skip,setup_quality 1.05 < 2.0
ETH-20260409T0800-london-short,ETH,2026-04-09T08:00:00+00:00,london,short,ob,4.947186798755621,stop,-1.3437693668828168,-33.59423417207042,volatile_chop,0.8981,1.9598,0.5713,0.4973,0.5237,0,0,0.0,take,,skip,setup_quality 1.96 < 2.0
BTC-20260413T0820-london-short,BTC,2026-04-13T08:20:00+00:00,london,short,fvg,2.663406254494554,no_fill,,,volatile_chop,0.8011,0.1649,0.1179,0.1137,0.4972,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.16 < 2.0
ETH-20260413T0925-london-short,ETH,2026-04-13T09:25:00+00:00,london,short,ob,4.6728775494910275,target,4.503638462396355,112.59096155990886,trending_up,0.5798,2.3662,0.4747,0.9073,0.3781,1,0,1.0,take,,escalate,confidence 0.58 < 0.60
BTC-20260413T1320-ny_am-long,BTC,2026-04-13T13:20:00+00:00,ny_am,long,fvg,1.748642720651594,stop,-1.202307929077973,-30.057698226949327,trending_down,0.3275,1.2602,0.6483,0.6832,0.7122,0,0,0.0,take,,escalate,confidence 0.33 < 0.60
BTC-20260414T0805-london-short,BTC,2026-04-14T08:05:00+00:00,london,short,ob,10.509667789909425,stop,-1.5155300139669197,-37.88825034917299,volatile_chop,0.2919,2.6802,0.576,0.9813,0.255,1,0,0.0,take,,escalate,confidence 0.29 < 0.60
ETH-20260414T0805-london-short,ETH,2026-04-14T08:05:00+00:00,london,short,ob,8.849514848010706,stop,-1.435376119706769,-35.88440299266922,trending_up,0.7292,1.0142,0.5863,0.172,0.3808,1,0,0.0,skip,correlated_open: BTC (BTC-20260414T0805-london-short),skip,setup_quality 1.01 < 2.0
BTC-20260415T0905-london-short,BTC,2026-04-15T09:05:00+00:00,london,short,fvg,3.099915444220731,missed,,,ranging,0.7554,0.8718,0.5791,0.5254,0.594,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.87 < 2.0
ETH-20260415T0905-london-short,ETH,2026-04-15T09:05:00+00:00,london,short,fvg,4.7268154961126605,no_fill,,,volatile_chop,0.2488,1.9839,0.935,0.3149,0.9534,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.25 < 0.60
BTC-20260415T1430-ny_am-long,BTC,2026-04-15T14:30:00+00:00,ny_am,long,ob,5.557180052407892,no_fill,,,ranging,0.4168,0.7063,0.7941,0.1593,0.2276,1,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.42 < 0.60
ETH-20260415T1500-ny_am-long,ETH,2026-04-15T15:00:00+00:00,ny_am,long,ob,4.070014806546554,no_fill,,,ranging,0.4216,1.0648,0.7361,0.3629,0.6486,1,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.42 < 0.60
BTC-20260416T0830-london-long,BTC,2026-04-16T08:30:00+00:00,london,long,ob,3.395155967400975,stop,-1.3775327185861905,-34.438317964654765,volatile_chop,0.6735,1.7617,0.5592,0.9023,0.868,1,0,0.0,take,,skip,setup_quality 1.76 < 2.0
ETH-20260416T0850-london-long,ETH,2026-04-16T08:50:00+00:00,london,long,fvg,4.655734764210281,stop,-1.357365965717775,-33.93414914294438,volatile_chop,0.6344,1.1321,0.8988,0.5315,0.6229,1,0,0.0,take,,skip,setup_quality 1.13 < 2.0
BTC-20260417T0850-london-short,BTC,2026-04-17T08:50:00+00:00,london,short,ob,10.79555852434041,stop,-1.5166748145675881,-37.916870364189705,trending_up,0.8958,0.1622,0.6716,0.7652,0.5449,0,0,0.0,take,,skip,setup_quality 0.16 < 2.0
ETH-20260417T0850-london-short,ETH,2026-04-17T08:50:00+00:00,london,short,ob,13.525565423362876,stop,-1.521379015958341,-38.03447539895852,trending_down,0.5061,0.7016,0.0623,0.5181,0.5228,0,0,0.0,skip,correlated_open: BTC (BTC-20260417T0850-london-short),escalate,confidence 0.51 < 0.60
ETH-20260417T1435-ny_am-short,ETH,2026-04-17T14:35:00+00:00,ny_am,short,ob,5.873543511902428,target,5.771084617848601,144.27711544621502,volatile_chop,0.9176,2.9259,0.2774,0.7846,0.8042,1,1,1.0,take,,take,
BTC-20260418T1420-ny_am-short,BTC,2026-04-18T14:20:00+00:00,ny_am,short,fvg,6.279260824303106,no_fill,,,trending_up,0.9039,1.9935,0.819,0.7223,0.175,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.99 < 2.0
BTC-20260419T0805-london-short,BTC,2026-04-19T08:05:00+00:00,london,short,ob,2.9358076306494034,target,2.77992621131944,69.49815528298599,volatile_chop,0.4147,1.9617,0.0821,0.1124,0.4583,0,0,1.0,take,,escalate,confidence 0.41 < 0.60
ETH-20260419T0850-london-short,ETH,2026-04-19T08:50:00+00:00,london,short,fvg,1.5175622618229567,stop,-1.2713767680256738,-31.784419200641842,trending_up,0.7847,1.8846,0.5881,0.661,0.3812,0,0,0.0,take,,skip,setup_quality 1.88 < 2.0
BTC-20260419T0945-london-long,BTC,2026-04-19T09:45:00+00:00,london,long,ob,1.6108031405546515,missed,,,trending_up,0.7351,1.2211,0.5965,0.6801,0.2805,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.22 < 2.0
BTC-20260419T1435-ny_am-short,BTC,2026-04-19T14:35:00+00:00,ny_am,short,ob,7.785999598699692,stop,-1.330565271378253,-33.264131784456325,trending_down,0.9586,0.9994,0.3196,0.3631,0.3619,0,0,0.0,take,,skip,setup_quality 1.00 < 2.0
ETH-20260420T0725-london-long,ETH,2026-04-20T07:25:00+00:00,london,long,ob,7.192669436609104,no_fill,,,trending_up,0.3564,0.1146,0.9324,0.0105,0.3401,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.36 < 0.60
BTC-20260420T1000-london-long,BTC,2026-04-20T10:00:00+00:00,london,long,fvg,4.712453493231383,no_fill,,,ranging,0.3762,1.2649,0.8674,0.4536,0.2152,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.38 < 0.60
ETH-20260421T0935-london-long,ETH,2026-04-21T09:35:00+00:00,london,long,ob,4.280539201592649,stop,-1.3714924272213176,-34.28731068053294,trending_down,0.8103,1.8617,0.5439,0.0641,0.4566,0,0,0.0,take,,skip,setup_quality 1.86 < 2.0
ETH-20260422T0850-london-short,ETH,2026-04-22T08:50:00+00:00,london,short,ob,4.107924847219354,missed,,,trending_up,0.7593,1.0089,0.489,0.7666,0.4992,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.01 < 2.0
BTC-20260422T1345-ny_am-long,BTC,2026-04-22T13:45:00+00:00,ny_am,long,ob,11.792857246406797,stop,-1.3786262169174,-34.465655422935,volatile_chop,0.7336,1.9662,0.2474,0.3221,0.689,0,0,0.0,take,,skip,setup_quality 1.97 < 2.0
ETH-20260423T1335-ny_am-long,ETH,2026-04-23T13:35:00+00:00,ny_am,long,ob,5.642195436829883,stop,-1.3710502794845032,-34.27625698711258,volatile_chop,0.6001,1.5937,0.8036,0.3608,0.5431,0,0,0.0,take,,skip,setup_quality 1.59 < 2.0
BTC-20260423T1435-ny_am-long,BTC,2026-04-23T14:35:00+00:00,ny_am,long,fvg,2.7997344506513233,stop,-1.2572777355001132,-31.43194338750283,ranging,0.777,1.0195,0.5121,0.938,0.6191,0,0,0.0,take,,skip,setup_quality 1.02 < 2.0
BTC-20260424T0825-london-long,BTC,2026-04-24T08:25:00+00:00,london,long,ob,4.578482209926006,missed,,,trending_up,0.8505,1.2096,0.8535,0.2279,0.8513,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.21 < 2.0
ETH-20260424T0840-london-long,ETH,2026-04-24T08:40:00+00:00,london,long,ob,2.589535659821738,missed,,,ranging,0.8546,2.7776,0.0887,0.7966,0.4956,1,1,1.0,skip,not_traded: missed,skip,not_traded: missed
BTC-20260425T0905-london-short,BTC,2026-04-25T09:05:00+00:00,london,short,ob,6.848134495643685,stop,-1.5291110111653279,-38.2277752791332,volatile_chop,0.4672,0.9853,0.6937,0.0657,0.5767,1,0,0.0,take,,escalate,confidence 0.47 < 0.60
ETH-20260426T0755-london-short,ETH,2026-04-26T07:55:00+00:00,london,short,fvg,3.86134585181942,no_fill,,,volatile_chop,0.8015,0.1104,0.348,0.7217,0.8492,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.11 < 2.0
ETH-20260426T1305-ny_am-long,ETH,2026-04-26T13:05:00+00:00,ny_am,long,fvg,13.113974105870541,stop,-1.2982949754560877,-32.45737438640219,volatile_chop,0.8165,1.1351,0.7082,0.51,0.4674,1,0,0.0,take,,skip,setup_quality 1.14 < 2.0
BTC-20260427T0800-london-short,BTC,2026-04-27T08:00:00+00:00,london,short,ob,9.307470848823403,no_fill,,,trending_up,0.5522,0.7088,0.5691,0.8018,0.4499,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.55 < 0.60
ETH-20260428T0835-london-short,ETH,2026-04-28T08:35:00+00:00,london,short,ob,3.538164932403869,missed,,,volatile_chop,0.6917,1.9547,0.3754,0.4407,0.0475,0,0,1.0,skip,not_traded: missed,skip,setup_quality 1.95 < 2.0
BTC-20260428T0930-london-short,BTC,2026-04-28T09:30:00+00:00,london,short,fvg,4.157673500655047,stop,-1.4055528558680483,-35.13882139670121,trending_down,0.4994,2.0101,0.637,0.5466,0.296,0,0,0.0,take,,escalate,confidence 0.50 < 0.60
BTC-20260502T1305-ny_am-short,BTC,2026-05-02T13:05:00+00:00,ny_am,short,ob,12.478960721881982,no_fill,,,trending_down,0.7051,1.147,0.9335,0.9784,0.047,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.15 < 2.0
ETH-20260502T1325-ny_am-short,ETH,2026-05-02T13:25:00+00:00,ny_am,short,ob,12.480139456687589,no_fill,,,trending_down,0.9509,1.0235,0.5654,0.2218,0.7812,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.02 < 2.0
BTC-20260504T0815-london-long,BTC,2026-05-04T08:15:00+00:00,london,long,fvg,7.0138933590436565,no_fill,,,trending_down,0.7806,2.7593,0.1056,0.2096,0.353,0,0,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260507T0745-london-long,ETH,2026-05-07T07:45:00+00:00,london,long,ob,10.449452689919672,no_fill,,,trending_up,0.4471,1.0326,0.3037,0.4385,0.2842,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.45 < 0.60
ETH-20260508T0815-london-long,ETH,2026-05-08T08:15:00+00:00,london,long,ob,3.728504769690447,no_fill,,,trending_up,0.5641,2.6567,0.8575,0.7613,0.3787,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.56 < 0.60
ETH-20260510T1300-ny_am-short,ETH,2026-05-10T13:00:00+00:00,ny_am,short,fvg,4.830257086296145,no_fill,,,volatile_chop,0.6096,1.2464,0.2193,0.6574,0.6706,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.25 < 2.0
ETH-20260511T1400-ny_am-short,ETH,2026-05-11T14:00:00+00:00,ny_am,short,fvg,5.809551922604565,no_fill,,,ranging,0.7462,0.8825,0.9305,0.7161,0.4667,1,1,0.0,skip,not_traded: no_fill,skip,setup_quality 0.88 < 2.0
BTC-20260512T1455-ny_am-short,BTC,2026-05-12T14:55:00+00:00,ny_am,short,fvg,10.224817979889146,no_fill,,,ranging,0.7617,2.6432,0.5171,0.6469,0.7055,1,1,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
BTC-20260513T1435-ny_am-long,BTC,2026-05-13T14:35:00+00:00,ny_am,long,ob,6.567324174858364,no_fill,,,volatile_chop,0.5894,1.4448,0.2393,0.1664,0.3567,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.59 < 0.60
ETH-20260514T1300-ny_am-long,ETH,2026-05-14T13:00:00+00:00,ny_am,long,ob,9.204525572948345,stop,-1.336931597933551,-33.42328994833878,volatile_chop,0.6448,0.2989,0.5275,0.4164,0.6916,1,1,0.0,take,,skip,setup_quality 0.30 < 2.0
BTC-20260515T0835-london-long,BTC,2026-05-15T08:35:00+00:00,london,long,fvg,18.456284376980477,no_fill,,,volatile_chop,0.4868,1.7698,0.6811,0.7575,0.5368,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.49 < 0.60
ETH-20260515T0835-london-long,ETH,2026-05-15T08:35:00+00:00,london,long,ob,19.76560585353221,no_fill,,,ranging,0.9261,0.1134,0.7322,0.4503,0.1413,1,1,,skip,not_traded: no_fill,skip,setup_quality 0.11 < 2.0
ETH-20260515T1455-ny_am-short,ETH,2026-05-15T14:55:00+00:00,ny_am,short,fvg,4.309746706157693,stop,-1.241353857455956,-31.033846436398896,volatile_chop,0.3119,1.0485,0.3067,0.3543,0.2521,0,1,0.0,take,,escalate,confidence 0.31 < 0.60
ETH-20260516T0720-london-short,ETH,2026-05-16T07:20:00+00:00,london,short,ob,5.22716005047295,stop,-1.463379438709457,-36.58448596773643,trending_down,0.5155,2.022,0.5452,0.7215,0.503,1,0,0.0,take,,escalate,confidence 0.52 < 0.60
ETH-20260516T1355-ny_am-long,ETH,2026-05-16T13:55:00+00:00,ny_am,long,ob,6.6880110965741135,stop,-1.3554409998275307,-33.88602499568827,ranging,0.4729,1.9991,0.4176,0.689,0.2901,0,0,0.0,take,,escalate,confidence 0.47 < 0.60
BTC-20260518T1435-ny_am-short,BTC,2026-05-18T14:35:00+00:00,ny_am,short,fvg,3.955538680638095,missed,,,ranging,0.7765,1.9894,0.5962,0.64,0.5903,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.99 < 2.0
ETH-20260520T0720-london-short,ETH,2026-05-20T07:20:00+00:00,london,short,ob,4.812606935043837,no_fill,,,trending_down,0.4896,1.5951,0.3647,0.6729,0.7243,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.49 < 0.60
BTC-20260520T1435-ny_am-long,BTC,2026-05-20T14:35:00+00:00,ny_am,long,fvg,6.256643153424733,stop,-1.246706606053598,-31.16766515133995,trending_down,0.505,2.9672,0.5536,0.5386,0.4317,0,0,0.0,take,,escalate,confidence 0.51 < 0.60
BTC-20260521T0755-london-short,BTC,2026-05-21T07:55:00+00:00,london,short,fvg,2.0,missed,,,ranging,0.8154,0.1185,0.1413,0.5758,0.8398,0,0,1.0,skip,not_traded: missed,skip,setup_quality 0.12 < 2.0
ETH-20260521T0755-london-short,ETH,2026-05-21T07:55:00+00:00,london,short,ob,2.0,missed,,,ranging,0.9113,2.8559,0.4624,0.6251,0.3423,0,0,1.0,skip,not_traded: missed,skip,not_traded: missed
BTC-20260521T0905-london-long,BTC,2026-05-21T09:05:00+00:00,london,long,ob,2.0,missed,,,trending_down,0.8492,0.9791,0.6583,0.328,0.9495,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.98 < 2.0
ETH-20260521T0910-london-long,ETH,2026-05-21T09:10:00+00:00,london,long,ob,2.0,target,1.8969594574235595,47.423986435588986,trending_down,0.8058,2.9328,0.3364,0.2498,0.2953,1,1,1.0,take,,skip,target_before_stop 0.30 < 0.30
ETH-20260522T1320-ny_am-long,ETH,2026-05-22T13:20:00+00:00,ny_am,long,ob,6.3250462488296835,no_fill,,,trending_down,0.6675,2.1352,0.5888,0.5436,0.8287,0,1,1.0,skip,not_traded: no_fill,skip,not_traded: no_fill
BTC-20260523T0925-london-long,BTC,2026-05-23T09:25:00+00:00,london,long,fvg,4.747863359289653,no_fill,,,volatile_chop,0.7436,0.0489,0.6846,0.526,0.2888,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.05 < 2.0
ETH-20260526T0805-london-short,ETH,2026-05-26T08:05:00+00:00,london,short,ob,4.327827615219083,no_fill,,,volatile_chop,0.5999,2.7891,0.5163,0.5638,0.414,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.60 < 0.60
BTC-20260526T0955-london-long,BTC,2026-05-26T09:55:00+00:00,london,long,ob,7.87791524335155,stop,-1.494738959326686,-37.36847398316715,trending_down,0.5293,2.2172,0.7643,0.5946,0.1107,0,0,0.0,take,,escalate,confidence 0.53 < 0.60
ETH-20260527T1350-ny_am-long,ETH,2026-05-27T13:50:00+00:00,ny_am,long,ob,7.455634789155029,no_fill,,,trending_up,0.6144,2.2767,0.99,0.8541,0.1178,1,1,0.0,skip,not_traded: no_fill,skip,target_before_stop 0.12 < 0.30
ETH-20260528T0800-london-long,ETH,2026-05-28T08:00:00+00:00,london,long,fvg,3.626703913851234,stop,-1.3064186813787049,-32.66046703446762,ranging,0.8382,1.7849,0.712,0.4764,0.2629,0,0,0.0,take,,skip,setup_quality 1.78 < 2.0
BTC-20260528T1305-ny_am-short,BTC,2026-05-28T13:05:00+00:00,ny_am,short,ob,4.039068743475367,stop,-1.2586937463558772,-31.46734365889693,trending_down,0.7187,1.8397,0.1327,0.8252,0.7969,0,0,0.0,take,,skip,setup_quality 1.84 < 2.0
ETH-20260529T0925-london-long,ETH,2026-05-29T09:25:00+00:00,london,long,ob,11.699570195993344,stop,-1.4771367227572478,-36.928418068931194,volatile_chop,0.9168,1.012,0.3378,0.5101,0.5083,0,0,0.0,take,,skip,setup_quality 1.01 < 2.0
ETH-20260530T0750-london-short,ETH,2026-05-30T07:50:00+00:00,london,short,ob,2.5193282069716916,target,2.365090261659213,59.12725654148032,ranging,0.8492,0.0364,0.7616,0.1554,0.6394,1,1,1.0,take,,skip,setup_quality 0.04 < 2.0
ETH-20260530T0950-london-long,ETH,2026-05-30T09:50:00+00:00,london,long,ob,4.9811253064135,stop,-1.587729635374889,-39.69324088437223,trending_down,0.6363,1.9114,0.62,0.4549,0.4074,0,0,0.0,take,,skip,setup_quality 1.91 < 2.0
ETH-20260530T1305-ny_am-long,ETH,2026-05-30T13:05:00+00:00,ny_am,long,ob,3.9332426112272554,target,3.8023608193019647,95.05902048254912,trending_down,0.6726,0.2516,0.5444,0.86,0.6929,1,1,1.0,take,,skip,setup_quality 0.25 < 2.0
BTC-20260531T0720-london-short,BTC,2026-05-31T07:20:00+00:00,london,short,fvg,6.455546986017189,stop,-1.4189705750867043,-35.47426437716761,trending_down,0.3256,1.9201,0.4081,0.2057,0.681,0,0,0.0,take,,escalate,confidence 0.33 < 0.60
BTC-20260531T1435-ny_am-short,BTC,2026-05-31T14:35:00+00:00,ny_am,short,ob,9.929262693142107,stop,-1.338131670348999,-33.45329175872497,trending_down,0.163,0.3059,0.6611,0.2122,0.431,1,0,0.0,take,,escalate,confidence 0.16 < 0.60
BTC-20260601T0725-london-long,BTC,2026-06-01T07:25:00+00:00,london,long,ob,1.7090448602707355,missed,,,volatile_chop,0.6036,1.5273,0.6857,0.4269,0.1627,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.53 < 2.0
ETH-20260601T0730-london-long,ETH,2026-06-01T07:30:00+00:00,london,long,fvg,5.261202410896927,stop,-1.4866793491202985,-37.166983728007466,ranging,0.9144,2.9076,0.2012,0.2386,0.6724,0,0,0.0,take,,take,
ETH-20260601T1355-ny_am-long,ETH,2026-06-01T13:55:00+00:00,ny_am,long,ob,6.9334594894506445,no_fill,,,ranging,0.3071,1.4752,0.2447,0.8719,0.5443,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.31 < 0.60
BTC-20260601T1400-ny_am-long,BTC,2026-06-01T14:00:00+00:00,ny_am,long,ob,3.225717847081654,missed,,,ranging,0.6425,0.0103,0.8304,0.649,0.8025,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.01 < 2.0
ETH-20260603T0905-london-long,ETH,2026-06-03T09:05:00+00:00,london,long,ob,3.46941527758281,missed,,,volatile_chop,0.6979,1.2345,0.2657,0.7244,0.311,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.23 < 2.0
BTC-20260603T0920-london-long,BTC,2026-06-03T09:20:00+00:00,london,long,fvg,2.031292424539189,missed,,,volatile_chop,0.6254,2.6341,0.3254,0.6085,0.8721,1,1,1.0,skip,not_traded: missed,skip,not_traded: missed
ETH-20260603T1455-ny_am-short,ETH,2026-06-03T14:55:00+00:00,ny_am,short,ob,3.129393295514932,stop,-1.1946403782294872,-29.866009455737178,ranging,0.815,1.8266,0.433,0.6829,0.2375,0,0,0.0,take,,skip,setup_quality 1.83 < 2.0
ETH-20260604T1305-ny_am-short,ETH,2026-06-04T13:05:00+00:00,ny_am,short,ob,6.740529941636791,target,6.5934545110483045,164.8363627762076,volatile_chop,0.662,1.8529,0.1447,0.1116,0.7424,1,1,1.0,take,,skip,setup_quality 1.85 < 2.0
BTC-20260604T1350-ny_am-short,BTC,2026-06-04T13:50:00+00:00,ny_am,short,ob,4.258384991791528,stop,-1.2491596647323215,-31.22899161830804,trending_up,0.6698,1.9983,0.0916,0.629,0.4617,1,0,0.0,skip,correlated_open: ETH (ETH-20260604T1305-ny_am-short),skip,setup_quality 2.00 < 2.0
ETH-20260605T0830-london-long,ETH,2026-06-05T08:30:00+00:00,london,long,ob,2.8253611818811146,target,2.6748320067871614,66.87080016967903,ranging,0.4809,1.7554,0.4083,0.4796,0.7251,0,0,1.0,take,,escalate,confidence 0.48 < 0.60
ETH-20260606T0930-london-long,ETH,2026-06-06T09:30:00+00:00,london,long,ob,6.614131268373491,no_fill,,,volatile_chop,0.4335,1.7773,0.4183,0.7244,0.3227,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.43 < 0.60
BTC-20260607T0820-london-long,BTC,2026-06-07T08:20:00+00:00,london,long,fvg,2.520623459767702,target,2.3942616505360066,59.85654126340017,trending_up,0.6932,1.6949,0.3736,0.9913,0.9366,1,1,1.0,take,,skip,setup_quality 1.69 < 2.0
BTC-20260607T1310-ny_am-short,BTC,2026-06-07T13:10:00+00:00,ny_am,short,ob,7.3079530307200296,no_fill,,,trending_up,0.6307,1.0193,0.7649,0.959,0.2468,0,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.02 < 2.0
ETH-20260607T1400-ny_am-short,ETH,2026-06-07T14:00:00+00:00,ny_am,short,ob,7.075023073319569,target,6.937846442575151,173.44616106437877,trending_up,0.5483,2.8642,0.608,0.8723,0.7938,1,1,1.0,take,,escalate,confidence 0.55 < 0.60
ETH-20260608T0840-london-short,ETH,2026-06-08T08:40:00+00:00,london,short,ob,3.7011777944688875,no_fill,,,trending_up,0.6329,2.4955,0.3138,0.5872,0.6529,0,0,1.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260609T0810-london-short,ETH,2026-06-09T08:10:00+00:00,london,short,ob,3.9353184885871606,stop,-1.5560126924133206,-38.900317310333016,trending_down,0.764,0.2362,0.4548,0.4881,0.3565,0,0,0.0,take,,skip,setup_quality 0.24 < 2.0
ETH-20260609T1340-ny_am-short,ETH,2026-06-09T13:40:00+00:00,ny_am,short,fvg,6.019715738388335,no_fill,,,volatile_chop,0.7789,0.0732,0.6581,0.8501,0.5177,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.07 < 2.0
BTC-20260609T1350-ny_am-short,BTC,2026-06-09T13:50:00+00:00,ny_am,short,fvg,6.5622264125395855,target,6.442458976594598,161.06147441486496,ranging,0.8899,1.0411,0.9225,0.2984,0.3022,1,1,1.0,take,,skip,setup_quality 1.04 < 2.0
BTC-20260610T0745-london-long,BTC,2026-06-10T07:45:00+00:00,london,long,ob,14.90824701900612,stop,-1.4557155158374153,-36.39288789593538,trending_down,0.5409,2.9889,0.9628,0.4147,0.2449,0,0,0.0,take,,escalate,confidence 0.54 < 0.60
BTC-20260611T0720-london-long,BTC,2026-06-11T07:20:00+00:00,london,long,ob,4.3480408729632325,stop,-1.3535972991151146,-33.839932477877866,ranging,0.4714,1.0762,0.5833,0.4676,0.3986,0,0,0.0,skip,correlated_open: ETH (ETH-20260611T0730-london-long),escalate,confidence 0.47 < 0.60
ETH-20260611T0730-london-long,ETH,2026-06-11T07:30:00+00:00,london,long,fvg,5.607923399221356,stop,-1.3261342950852884,-33.15335737713221,trending_up,0.6661,0.4619,0.7645,0.5438,0.3338,0,0,0.0,take,,skip,setup_quality 0.46 < 2.0
BTC-20260612T1445-ny_am-long,BTC,2026-06-12T14:45:00+00:00,ny_am,long,ob,6.464397929070225,stop,-1.3827053801753129,-34.56763450438282,volatile_chop,0.3597,0.7496,0.4811,0.7772,0.6825,0,0,0.0,take,,escalate,confidence 0.36 < 0.60
BTC-20260613T0735-london-short,BTC,2026-06-13T07:35:00+00:00,london,short,ob,8.065511971720653,stop,-1.3266781808247758,-33.1669545206194,trending_down,0.7553,2.0609,0.6587,0.3388,0.8514,0,0,0.0,take,,take,
BTC-20260614T1255-ny_am-long,BTC,2026-06-14T12:55:00+00:00,ny_am,long,fvg,7.462252589125218,no_fill,,,ranging,0.5776,1.0613,0.4227,0.6056,0.2704,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.58 < 0.60
BTC-20260615T0720-london-short,BTC,2026-06-15T07:20:00+00:00,london,short,ob,6.516972976953856,missed,,,trending_up,0.8574,1.133,0.4109,0.4032,0.2516,0,0,1.0,skip,not_traded: missed,skip,setup_quality 1.13 < 2.0
BTC-20260616T1405-ny_am-long,BTC,2026-06-16T14:05:00+00:00,ny_am,long,ob,4.290099059932224,no_fill,,,trending_up,0.461,0.5072,0.3038,0.8207,0.5611,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.46 < 0.60
BTC-20260617T1315-ny_am-short,BTC,2026-06-17T13:15:00+00:00,ny_am,short,ob,4.778027298092623,stop,-1.2451720336210024,-31.12930084052506,trending_down,0.3117,1.5796,0.357,0.8596,0.4525,0,0,0.0,take,,escalate,confidence 0.31 < 0.60
ETH-20260617T1435-ny_am-short,ETH,2026-06-17T14:35:00+00:00,ny_am,short,ob,5.345276725560791,stop,-1.2472525175496236,-31.18131293874059,ranging,0.7443,0.4381,0.7585,0.5759,0.6066,0,0,0.0,skip,correlated_open: BTC (BTC-20260617T1315-ny_am-short),skip,setup_quality 0.44 < 2.0
BTC-20260618T0805-london-long,BTC,2026-06-18T08:05:00+00:00,london,long,fvg,2.5997082134627463,missed,,,trending_down,0.3741,1.4577,0.0746,0.4829,0.5124,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.37 < 0.60
BTC-20260618T0925-london-short,BTC,2026-06-18T09:25:00+00:00,london,short,ob,3.334911149831722,missed,,,ranging,0.7747,0.1974,0.3093,0.8269,0.5748,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.20 < 2.0
ETH-20260619T0735-london-short,ETH,2026-06-19T07:35:00+00:00,london,short,ob,7.936856955452669,stop,-1.5088975406738923,-37.722438516847305,volatile_chop,0.8593,0.1103,0.2889,0.3278,0.0482,1,0,0.0,take,,skip,setup_quality 0.11 < 2.0
BTC-20260619T0815-london-short,BTC,2026-06-19T08:15:00+00:00,london,short,ob,3.7694684706467796,missed,,,trending_down,0.7112,1.8332,0.2333,0.6181,0.5278,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.83 < 2.0
BTC-20260620T0845-london-long,BTC,2026-06-20T08:45:00+00:00,london,long,fvg,6.131912846882618,no_fill,,,trending_up,0.7644,1.8126,0.4291,0.6289,0.6334,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.81 < 2.0
ETH-20260620T0845-london-long,ETH,2026-06-20T08:45:00+00:00,london,long,ob,10.166958701083729,target,9.987299830473983,249.6824957618496,trending_down,0.7929,0.329,0.7083,0.8781,0.5923,1,1,1.0,take,,skip,setup_quality 0.33 < 2.0
ETH-20260621T0740-london-short,ETH,2026-06-21T07:40:00+00:00,london,short,ob,3.0576021824183144,no_fill,,,trending_up,0.7437,1.9315,0.1923,0.3065,0.516,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.93 < 2.0
BTC-20260621T0815-london-short,BTC,2026-06-21T08:15:00+00:00,london,short,fvg,3.0461208009262633,missed,,,ranging,0.925,1.9456,0.377,0.4163,0.3572,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.95 < 2.0
BTC-20260621T1400-ny_am-long,BTC,2026-06-21T14:00:00+00:00,ny_am,long,fvg,9.856964054601727,stop,-1.3112770927842683,-32.78192731960671,trending_down,0.7392,2.023,0.4401,0.5021,0.8532,0,0,0.0,take,,take,
ETH-20260623T1300-ny_am-short,ETH,2026-06-23T13:00:00+00:00,ny_am,short,ob,8.798218088835911,no_fill,,,trending_down,0.9462,0.9678,0.47,0.2511,0.12,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.97 < 2.0
BTC-20260623T1430-ny_am-short,BTC,2026-06-23T14:30:00+00:00,ny_am,short,ob,8.314891430236697,no_fill,,,trending_up,0.8417,1.826,0.1355,0.3545,0.4802,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.83 < 2.0
ETH-20260624T0735-london-long,ETH,2026-06-24T07:35:00+00:00,london,long,ob,15.321307312525747,stop,-1.5453910281726326,-38.634775704315814,trending_down,0.8208,1.136,0.244,0.8604,0.2497,0,0,0.0,take,,skip,setup_quality 1.14 < 2.0
BTC-20260625T0950-london-long,BTC,2026-06-25T09:50:00+00:00,london,long,fvg,3.0816005855913815,stop,-1.2879323318790932,-32.19830829697733,ranging,0.6568,0.9435,0.186,0.525,0.5948,0,0,0.0,take,,skip,setup_quality 0.94 < 2.0
BTC-20260625T1325-ny_am-long,BTC,2026-06-25T13:25:00+00:00,ny_am,long,ob,2.823598334577653,no_fill,,,trending_down,0.8214,1.9606,0.1485,0.2501,0.0802,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.96 < 2.0
BTC-20260626T0750-london-long,BTC,2026-06-26T07:50:00+00:00,london,long,fvg,1.8534666813113079,missed,,,trending_down,0.8538,1.9256,0.2052,0.6901,0.8821,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.93 < 2.0
BTC-20260627T0935-london-short,BTC,2026-06-27T09:35:00+00:00,london,short,ob,6.198252343922838,no_fill,,,volatile_chop,0.7235,2.5865,0.6168,0.8779,0.0611,1,1,0.0,skip,not_traded: no_fill,skip,target_before_stop 0.06 < 0.30
ETH-20260627T1335-ny_am-long,ETH,2026-06-27T13:35:00+00:00,ny_am,long,fvg,2.746836383075549,missed,,,trending_down,0.9539,0.0843,0.6408,0.3186,0.1037,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.08 < 2.0
ETH-20260628T1405-ny_am-long,ETH,2026-06-28T14:05:00+00:00,ny_am,long,ob,15.079884033150686,no_fill,,,trending_down,0.4824,2.3538,0.862,0.0911,0.4454,0,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.48 < 0.60
BTC-20260629T0720-london-short,BTC,2026-06-29T07:20:00+00:00,london,short,ob,5.235365310074888,no_fill,,,volatile_chop,0.2492,1.2902,0.5547,0.5537,0.3557,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.25 < 0.60
BTC-20260630T0920-london-short,BTC,2026-06-30T09:20:00+00:00,london,short,ob,2.9809293196770064,target,2.8517487622011157,71.29371905502789,ranging,0.612,0.6316,0.5913,0.616,0.4245,1,1,1.0,take,,skip,setup_quality 0.63 < 2.0
ETH-20260630T1330-ny_am-short,ETH,2026-06-30T13:30:00+00:00,ny_am,short,ob,6.458335122960045,target,6.257856799658233,156.44641999145583,volatile_chop,0.5032,1.3251,0.3837,0.6722,0.4583,1,1,1.0,take,,escalate,confidence 0.50 < 0.60
ETH-20260701T0905-london-short,ETH,2026-07-01T09:05:00+00:00,london,short,ob,7.459746050378949,stop,-1.4001840168406183,-35.00460042101546,ranging,0.5348,1.6909,0.4225,0.7034,0.5413,0,0,0.0,take,,escalate,confidence 0.53 < 0.60
ETH-20260701T1325-ny_am-short,ETH,2026-07-01T13:25:00+00:00,ny_am,short,fvg,3.4144957294454663,missed,,,trending_up,0.7195,2.0096,0.3481,0.638,0.5831,0,1,1.0,skip,not_traded: missed,skip,not_traded: missed
BTC-20260703T0835-london-long,BTC,2026-07-03T08:35:00+00:00,london,long,fvg,2.6261263043817547,no_fill,,,volatile_chop,0.5888,2.6398,0.2669,0.8221,0.8346,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.59 < 0.60
ETH-20260703T1425-ny_am-short,ETH,2026-07-03T14:25:00+00:00,ny_am,short,ob,10.262020502601697,no_fill,,,trending_up,0.5508,2.1855,0.1886,0.47,0.5636,1,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.55 < 0.60
BTC-20260706T1435-ny_am-short,BTC,2026-07-06T14:35:00+00:00,ny_am,short,fvg,11.359901858360574,no_fill,,,volatile_chop,0.3489,1.4884,0.483,0.2677,0.1173,1,1,,skip,not_traded: no_fill,escalate,confidence 0.35 < 0.60
ETH-20260708T0810-london-long,ETH,2026-07-08T08:10:00+00:00,london,long,ob,5.365936798526241,no_fill,,,trending_down,0.1752,0.7049,0.7584,0.8612,0.6594,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.18 < 0.60
ETH-20260709T0905-london-long,ETH,2026-07-09T09:05:00+00:00,london,long,fvg,3.3991018087777984,stop,-1.2809995457547336,-32.02498864386834,crisis,0.5786,0.071,0.8769,0.274,0.2032,0,0,0.0,take,,escalate,confidence 0.58 < 0.60
ETH-20260709T1350-ny_am-long,ETH,2026-07-09T13:50:00+00:00,ny_am,long,ob,2.687874273940561,no_fill,,,volatile_chop,0.8671,1.0126,0.7745,0.2492,0.173,0,0,1.0,skip,not_traded: no_fill,skip,setup_quality 1.01 < 2.0
BTC-20260710T1420-ny_am-long,BTC,2026-07-10T14:20:00+00:00,ny_am,long,fvg,8.341488966826452,stop,-1.3151997915374969,-32.87999478843742,trending_up,0.8394,0.0884,0.4353,0.3578,0.5449,0,0,0.0,take,,skip,setup_quality 0.09 < 2.0
BTC-20260711T1300-ny_am-long,BTC,2026-07-11T13:00:00+00:00,ny_am,long,ob,6.404166627687074,target,6.281439387911682,157.03598469779206,volatile_chop,0.945,2.0057,0.1516,0.7747,0.3908,1,1,1.0,take,,take,
ETH-20260712T0805-london-long,ETH,2026-07-12T08:05:00+00:00,london,long,fvg,5.520921037994538,no_fill,,,ranging,0.8803,0.0141,0.9591,0.9338,0.6274,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.01 < 2.0
BTC-20260713T0805-london-long,BTC,2026-07-13T08:05:00+00:00,london,long,fvg,7.883596857492332,no_fill,,,ranging,0.7607,2.9711,0.7019,0.4147,0.6731,1,1,1.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260713T0815-london-long,ETH,2026-07-13T08:15:00+00:00,london,long,fvg,4.056588625833215,stop,-1.2215749939279454,-30.539374848198634,volatile_chop,0.6473,1.9472,0.276,0.3055,0.6836,0,0,0.0,take,,skip,setup_quality 1.95 < 2.0
ETH-20260713T1320-ny_am-long,ETH,2026-07-13T13:20:00+00:00,ny_am,long,ob,9.202892052441442,no_fill,,,crisis,0.5239,0.8593,0.3071,0.236,0.2,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.52 < 0.60
ETH-20260714T1340-ny_am-short,ETH,2026-07-14T13:40:00+00:00,ny_am,short,ob,4.965537849605453,no_fill,,,trending_down,0.8206,0.1503,0.2862,0.0573,0.1289,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.15 < 2.0
ETH-20260715T1305-ny_am-short,ETH,2026-07-15T13:05:00+00:00,ny_am,short,ob,6.521751035537488,no_fill,,,volatile_chop,0.7799,1.16,0.3327,0.0723,0.2284,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.16 < 2.0
BTC-20260715T1350-ny_am-short,BTC,2026-07-15T13:50:00+00:00,ny_am,short,fvg,4.898579723134835,missed,,,trending_up,0.8262,0.3317,0.6627,0.4092,0.5976,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.33 < 2.0
ETH-20260716T0750-london-short,ETH,2026-07-16T07:50:00+00:00,london,short,ob,6.761126912999581,no_fill,,,volatile_chop,0.6569,1.245,0.4285,0.554,0.1204,1,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.25 < 2.0
ETH-20260717T1420-ny_am-short,ETH,2026-07-17T14:20:00+00:00,ny_am,short,fvg,3.588657949737828,stop,-1.2261189053669117,-30.652972634172794,ranging,0.4647,1.4366,0.2928,0.2309,0.4798,0,0,0.0,take,,escalate,confidence 0.46 < 0.60
ETH-20260718T0835-london-short,ETH,2026-07-18T08:35:00+00:00,london,short,ob,7.948112586743253,no_fill,,,trending_up,0.7716,1.9328,0.399,0.3895,0.3093,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.93 < 2.0
ETH-20260719T1350-ny_am-short,ETH,2026-07-19T13:50:00+00:00,ny_am,short,fvg,1.9486173419815367,missed,,,trending_down,0.8978,2.8547,0.7157,0.7437,0.5969,1,0,1.0,skip,not_traded: missed,skip,not_traded: missed
ETH-20260719T1435-ny_am-long,ETH,2026-07-19T14:35:00+00:00,ny_am,long,fvg,1.764380448667215,missed,,,ranging,0.6584,1.297,0.5828,0.222,0.0836,0,0,1.0,skip,not_traded: missed,skip,setup_quality 1.30 < 2.0
BTC-20260720T0720-london-short,BTC,2026-07-20T07:20:00+00:00,london,short,ob,7.141652469637304,no_fill,,,trending_up,0.9026,0.1519,0.527,0.5294,0.9518,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.15 < 2.0
ETH-20260720T0925-london-long,ETH,2026-07-20T09:25:00+00:00,london,long,fvg,5.145462749881415,stop,-1.3000902351030004,-32.50225587757501,trending_up,0.5225,0.1454,0.6504,0.428,0.5005,0,0,0.0,take,,escalate,confidence 0.52 < 0.60
ETH-20260721T0935-london-long,ETH,2026-07-21T09:35:00+00:00,london,long,ob,10.694196004563384,stop,-1.489653781028788,-37.2413445257197,trending_up,0.8437,2.0491,0.5287,0.5474,0.4698,1,0,0.0,take,,take,
BTC-20260722T0750-london-long,BTC,2026-07-22T07:50:00+00:00,london,long,ob,9.31613663510517,stop,-1.5818999144794652,-39.54749786198663,trending_up,0.919,1.9347,0.2281,0.7245,0.4254,1,0,0.0,take,,skip,setup_quality 1.93 < 2.0
ETH-20260722T0755-london-long,ETH,2026-07-22T07:55:00+00:00,london,long,ob,8.756483855534457,stop,-1.4621427418416717,-36.553568546041795,ranging,0.5873,1.8899,0.2172,0.611,0.286,0,0,0.0,take,,escalate,confidence 0.59 < 0.60
BTC-20260723T0945-london-long,BTC,2026-07-23T09:45:00+00:00,london,long,ob,6.940038929357187,stop,-1.4300379770619214,-35.75094942654803,volatile_chop,0.7249,1.9881,0.834,0.0882,0.5862,0,0,0.0,take,,skip,setup_quality 1.99 < 2.0
BTC-20260724T0725-london-short,BTC,2026-07-24T07:25:00+00:00,london,short,ob,2.2744866357197395,stop,-1.4293129676402094,-35.732824191005236,volatile_chop,0.8481,1.8997,0.0661,0.2269,0.3057,0,0,0.0,take,,skip,setup_quality 1.90 < 2.0
ETH-20260724T0920-london-short,ETH,2026-07-24T09:20:00+00:00,london,short,ob,6.508128351353951,stop,-1.555077806832492,-38.8769451708123,trending_down,0.8597,1.1015,0.1934,0.2321,0.568,0,0,0.0,take,,skip,setup_quality 1.10 < 2.0
ETH-20260724T1305-ny_am-short,ETH,2026-07-24T13:05:00+00:00,ny_am,short,ob,6.589695964785472,missed,,,trending_up,0.8074,1.8918,0.3716,0.1433,0.4517,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.89 < 2.0
BTC-20260724T1320-ny_am-short,BTC,2026-07-24T13:20:00+00:00,ny_am,short,fvg,4.057073730779742,no_fill,,,trending_down,0.8449,1.9483,0.195,0.4378,0.4584,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.95 < 2.0
BTC-20260725T0735-london-long,BTC,2026-07-25T07:35:00+00:00,london,long,ob,3.1334410575721523,missed,,,trending_up,0.8563,2.918,0.9354,0.3907,0.6736,1,1,1.0,skip,not_traded: missed,skip,not_traded: missed
ETH-20260725T0735-london-long,ETH,2026-07-25T07:35:00+00:00,london,long,ob,4.779409537880114,no_fill,,,ranging,0.8623,1.025,0.6999,0.7888,0.5218,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.02 < 2.0
ETH-20260725T1425-ny_am-short,ETH,2026-07-25T14:25:00+00:00,ny_am,short,fvg,5.710002734337025,no_fill,,,trending_down,0.8726,0.9735,0.7281,0.8396,0.6432,1,1,0.0,skip,not_traded: no_fill,skip,setup_quality 0.97 < 2.0
BTC-20260726T0800-london-long,BTC,2026-07-26T08:00:00+00:00,london,long,ob,3.012253479569782,stop,-1.2660429137296392,-31.65107284324098,ranging,0.5559,2.4167,0.2543,0.2602,0.6318,0,0,0.0,take,,escalate,confidence 0.56 < 0.60
ETH-20260726T0800-london-long,ETH,2026-07-26T08:00:00+00:00,london,long,ob,2.690647100081314,no_fill,,,trending_down,0.8143,0.0521,0.747,0.7464,0.1322,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.05 < 2.0
BTC-20260727T0850-london-short,BTC,2026-07-27T08:50:00+00:00,london,short,ob,4.467304880436466,stop,-1.4587162633754513,-36.467906584386284,trending_up,0.7414,1.9427,0.3925,0.4838,0.2831,0,0,0.0,take,,skip,setup_quality 1.94 < 2.0
ETH-20260728T0920-london-short,ETH,2026-07-28T09:20:00+00:00,london,short,ob,6.126523784052261,no_fill,,,volatile_chop,0.5919,2.3826,0.4528,0.3995,0.5163,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.59 < 0.60
BTC-20260728T0935-london-short,BTC,2026-07-28T09:35:00+00:00,london,short,ob,7.2254269634917065,stop,-1.4413176656205495,-36.03294164051374,trending_down,0.6799,0.9786,0.6067,0.5258,0.9192,0,0,0.0,take,,skip,setup_quality 0.98 < 2.0
BTC-20260729T1355-ny_am-long,BTC,2026-07-29T13:55:00+00:00,ny_am,long,ob,7.966264624119973,stop,-1.414663327163945,-35.366583179098626,trending_down,0.8046,1.0772,0.5952,0.3865,0.164,0,0,0.0,take,,skip,setup_quality 1.08 < 2.0
BTC-20260731T0725-london-short,BTC,2026-07-31T07:25:00+00:00,london,short,ob,7.121937403965305,missed,,,trending_up,0.8488,1.8634,0.2602,0.7377,0.7024,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.86 < 2.0
ETH-20260801T0955-london-short,ETH,2026-08-01T09:55:00+00:00,london,short,ob,4.188113737438666,no_fill,,,ranging,0.5353,2.2424,0.8977,0.3782,0.4202,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.54 < 0.60
ETH-20260802T0935-london-short,ETH,2026-08-02T09:35:00+00:00,london,short,ob,4.6549856011636415,stop,-1.4300958782687963,-35.752396956719906,volatile_chop,0.577,1.5993,0.5227,0.5453,0.0927,0,0,0.0,take,,escalate,confidence 0.58 < 0.60
ETH-20260802T1300-ny_am-short,ETH,2026-08-02T13:00:00+00:00,ny_am,short,ob,3.1737562674368722,no_fill,,,volatile_chop,0.7481,0.3158,0.6472,0.7696,0.4048,1,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.32 < 2.0
BTC-20260805T0920-london-long,BTC,2026-08-05T09:20:00+00:00,london,long,ob,4.885301934691273,missed,,,ranging,0.5563,1.6653,0.5846,0.3468,0.3253,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.56 < 0.60
ETH-20260805T1350-ny_am-short,ETH,2026-08-05T13:50:00+00:00,ny_am,short,fvg,2.653550475362656,stop,-1.2749622118518067,-31.874055296295168,trending_up,0.4941,0.3542,0.7837,0.6792,0.1348,0,0,0.0,take,,escalate,confidence 0.49 < 0.60
ETH-20260806T0850-london-short,ETH,2026-08-06T08:50:00+00:00,london,short,fvg,2.268577033870607,no_fill,,,volatile_chop,0.5287,1.0629,0.7323,0.1866,0.5575,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.53 < 0.60
BTC-20260807T0750-london-long,BTC,2026-08-07T07:50:00+00:00,london,long,fvg,4.476265256771008,target,4.321485860517929,108.03714651294823,trending_down,0.5099,0.3103,0.7566,0.9528,0.0733,1,1,1.0,take,,escalate,confidence 0.51 < 0.60
BTC-20260807T1440-ny_am-short,BTC,2026-08-07T14:40:00+00:00,ny_am,short,ob,7.5232728918474105,target,7.291665843618583,182.29164609046458,volatile_chop,0.3141,1.0253,0.1364,0.4103,0.7461,1,1,1.0,take,,escalate,confidence 0.31 < 0.60
ETH-20260808T0950-london-long,ETH,2026-08-08T09:50:00+00:00,london,long,fvg,3.3424468284122693,no_fill,,,trending_down,0.8086,1.0534,0.2513,0.2937,0.291,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.05 < 2.0
ETH-20260808T1420-ny_am-long,ETH,2026-08-08T14:20:00+00:00,ny_am,long,fvg,2.289342900891036,missed,,,ranging,0.8514,0.9276,0.6512,0.8193,0.4527,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.93 < 2.0
BTC-20260810T0745-london-long,BTC,2026-08-10T07:45:00+00:00,london,long,ob,6.456093986916385,target,6.299972902613791,157.49932256534478,trending_down,0.8223,1.8955,0.6464,0.1714,0.7041,1,1,1.0,take,,skip,setup_quality 1.90 < 2.0
ETH-20260810T0835-london-long,ETH,2026-08-10T08:35:00+00:00,london,long,fvg,3.3185233688444393,stop,-1.3480568856938304,-33.70142214234576,ranging,0.5558,1.0131,0.7244,0.3633,0.5603,1,0,0.0,skip,correlated_open: BTC (BTC-20260810T0745-london-long),escalate,confidence 0.56 < 0.60
ETH-20260810T1405-ny_am-short,ETH,2026-08-10T14:05:00+00:00,ny_am,short,fvg,3.461554126139552,missed,,,ranging,0.8124,0.2542,0.805,0.7584,0.5895,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.25 < 2.0
BTC-20260812T0735-london-short,BTC,2026-08-12T07:35:00+00:00,london,short,ob,5.827743472611219,stop,-1.4645377357243579,-36.613443393108945,volatile_chop,0.8425,2.6698,0.3299,0.6607,0.75,1,0,0.0,take,,take,
ETH-20260812T0735-london-short,ETH,2026-08-12T07:35:00+00:00,london,short,ob,7.331187623501104,no_fill,,,trending_up,0.4597,2.1867,0.5695,0.7617,0.1898,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.46 < 0.60
BTC-20260813T0850-london-short,BTC,2026-08-13T08:50:00+00:00,london,short,fvg,5.5753718517513455,stop,-1.3440584473748087,-33.601461184370216,volatile_chop,0.7191,1.0289,0.1791,0.6114,0.7277,0,0,0.0,take,,skip,setup_quality 1.03 < 2.0
BTC-20260814T0820-london-long,BTC,2026-08-14T08:20:00+00:00,london,long,ob,5.954039822693541,stop,-1.6088085703863382,-40.220214259658455,trending_up,0.672,2.0379,0.7305,0.574,0.8098,0,0,0.0,take,,take,
ETH-20260814T0935-london-long,ETH,2026-08-14T09:35:00+00:00,london,long,ob,1.7215510240675274,stop,-1.3161263325997634,-32.90315831499409,trending_up,0.7614,1.961,0.1838,0.6647,0.2848,0,0,0.0,take,,skip,setup_quality 1.96 < 2.0
BTC-20260816T1345-ny_am-short,BTC,2026-08-16T13:45:00+00:00,ny_am,short,fvg,5.718938342306775,no_fill,,,volatile_chop,0.6026,2.8828,0.3458,0.4509,0.5037,1,1,,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260816T1400-ny_am-short,ETH,2026-08-16T14:00:00+00:00,ny_am,short,fvg,6.600576876729754,no_fill,,,volatile_chop,0.476,1.5211,0.4224,0.6678,0.8817,1,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.48 < 0.60
ETH-20260817T0810-london-short,ETH,2026-08-17T08:10:00+00:00,london,short,ob,2.6304446077265164,missed,,,trending_up,0.3447,1.141,0.138,0.2121,0.5804,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.34 < 0.60
BTC-20260817T0820-london-short,BTC,2026-08-17T08:20:00+00:00,london,short,fvg,2.4771518072987644,stop,-1.316746483556895,-32.918662088922375,trending_up,0.8013,0.0217,0.4388,0.1355,0.7371,0,0,0.0,take,,skip,setup_quality 0.02 < 2.0
ETH-20260817T0905-london-long,ETH,2026-08-17T09:05:00+00:00,london,long,ob,3.0115079816583687,missed,,,volatile_chop,0.6321,0.2163,0.0853,0.6139,0.0227,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.22 < 2.0
ETH-20260819T0720-london-short,ETH,2026-08-19T07:20:00+00:00,london,short,ob,4.725075514594668,stop,-1.3585260039253533,-33.96315009813383,volatile_chop,0.7024,0.505,0.688,0.5652,0.2594,0,0,0.0,skip,correlated_open: BTC (BTC-20260819T0730-london-short),skip,setup_quality 0.51 < 2.0
BTC-20260819T0730-london-short,BTC,2026-08-19T07:30:00+00:00,london,short,ob,2.841442858452065,stop,-1.3035628022697154,-32.589070056742884,volatile_chop,0.8942,0.9652,0.7775,0.0975,0.1142,0,0,0.0,take,,skip,setup_quality 0.97 < 2.0
BTC-20260820T1340-ny_am-short,BTC,2026-08-20T13:40:00+00:00,ny_am,short,ob,5.5767503453278255,no_fill,,,volatile_chop,0.5632,0.9947,0.656,0.8965,0.3732,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.56 < 0.60
ETH-20260821T1355-ny_am-short,ETH,2026-08-21T13:55:00+00:00,ny_am,short,ob,12.101390948535196,stop,-1.3022511520318523,-32.556278800796306,trending_down,0.8979,1.8727,0.3161,0.493,0.483,0,0,0.0,skip,correlated_open: BTC (BTC-20260821T1400-ny_am-short),skip,setup_quality 1.87 < 2.0
BTC-20260821T1400-ny_am-short,BTC,2026-08-21T14:00:00+00:00,ny_am,short,ob,19.39075101530463,stop,-1.413081141043007,-35.327028526075175,trending_down,0.6287,1.3808,0.3759,0.6408,0.6552,0,0,0.0,take,,skip,setup_quality 1.38 < 2.0
ETH-20260822T1355-ny_am-short,ETH,2026-08-22T13:55:00+00:00,ny_am,short,ob,7.746218138822285,no_fill,,,ranging,0.5758,1.1997,0.3249,0.8648,0.4319,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.58 < 0.60
BTC-20260822T1425-ny_am-short,BTC,2026-08-22T14:25:00+00:00,ny_am,short,ob,2.1762907532753912,stop,-1.2860906688738976,-32.15226672184744,trending_down,0.964,1.9705,0.5607,0.6912,0.2206,0,0,0.0,take,,skip,setup_quality 1.97 < 2.0
BTC-20260823T0750-london-long,BTC,2026-08-23T07:50:00+00:00,london,long,ob,8.563086841644802,stop,-1.4294395281749865,-35.735988204374664,trending_up,0.8765,0.9243,0.4962,0.7712,0.5765,1,0,0.0,take,,skip,setup_quality 0.92 < 2.0
ETH-20260823T0925-london-long,ETH,2026-08-23T09:25:00+00:00,london,long,ob,5.737176865380665,stop,-1.3593264009704216,-33.98316002426054,trending_down,0.8474,1.1895,0.2855,0.3029,0.4139,0,0,0.0,take,,skip,setup_quality 1.19 < 2.0
BTC-20260823T1310-ny_am-short,BTC,2026-08-23T13:10:00+00:00,ny_am,short,ob,7.259104457412534,stop,-1.4584565133063279,-36.4614128326582,volatile_chop,0.3875,1.9435,0.6341,0.7006,0.7895,1,0,0.0,take,,escalate,confidence 0.39 < 0.60
ETH-20260824T1345-ny_am-short,ETH,2026-08-24T13:45:00+00:00,ny_am,short,ob,6.226924941133515,no_fill,,,ranging,0.8656,2.0635,0.175,0.3628,0.3291,0,0,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
BTC-20260825T0850-london-long,BTC,2026-08-25T08:50:00+00:00,london,long,fvg,3.937957873137389,no_fill,,,ranging,0.6543,1.0721,0.7728,0.8332,0.8935,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.07 < 2.0
ETH-20260825T0850-london-long,ETH,2026-08-25T08:50:00+00:00,london,long,ob,4.8778724871384025,missed,,,volatile_chop,0.4506,0.6912,0.6931,0.5067,0.435,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.45 < 0.60
BTC-20260826T0730-london-long,BTC,2026-08-26T07:30:00+00:00,london,long,ob,4.538847022127031,stop,-1.3628641342359016,-34.07160335589754,volatile_chop,0.5007,2.1677,0.4963,0.6337,0.3339,0,0,0.0,take,,escalate,confidence 0.50 < 0.60
ETH-20260826T0920-london-long,ETH,2026-08-26T09:20:00+00:00,london,long,ob,3.8366400198769037,stop,-1.4666081222420195,-36.66520305605049,trending_up,0.9032,2.9293,0.3274,0.5022,0.2605,1,0,0.0,take,,skip,target_before_stop 0.26 < 0.30
BTC-20260826T1320-ny_am-short,BTC,2026-08-26T13:20:00+00:00,ny_am,short,ob,7.6972766419411345,stop,-1.6135434758274463,-40.338586895686156,trending_down,0.6913,2.5278,0.4648,0.5508,0.7739,1,0,0.0,take,,take,
ETH-20260826T1450-ny_am-short,ETH,2026-08-26T14:50:00+00:00,ny_am,short,ob,6.080775576709169,stop,-1.3885147995282014,-34.712869988205036,ranging,0.7089,0.3869,0.6464,0.8121,0.7153,0,0,0.0,take,,skip,setup_quality 0.39 < 2.0
BTC-20260827T0820-london-long,BTC,2026-08-27T08:20:00+00:00,london,long,fvg,2.0,stop,-1.1812745066459636,-29.53186266614909,trending_up,0.3631,1.471,0.7668,0.7915,0.6741,0,0,0.0,take,,escalate,confidence 0.36 < 0.60
BTC-20260827T1435-ny_am-short,BTC,2026-08-27T14:35:00+00:00,ny_am,short,ob,5.063783452727078,stop,-1.3046147774617467,-32.615369436543666,ranging,0.6839,1.9827,0.7082,0.261,0.8199,0,0,0.0,skip,correlated_open: ETH (ETH-20260827T1435-ny_am-short),skip,setup_quality 1.98 < 2.0
ETH-20260827T1435-ny_am-short,ETH,2026-08-27T14:35:00+00:00,ny_am,short,ob,5.694045192655672,stop,-1.2830218142909926,-32.07554535727481,ranging,0.8838,1.1554,0.5303,0.6227,0.3748,0,0,0.0,take,,skip,setup_quality 1.16 < 2.0
BTC-20260829T0805-london-long,BTC,2026-08-29T08:05:00+00:00,london,long,fvg,4.3051511741535125,no_fill,,,trending_down,0.8144,1.863,0.3445,0.4202,0.3861,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.86 < 2.0
BTC-20260901T1350-ny_am-long,BTC,2026-09-01T13:50:00+00:00,ny_am,long,fvg,6.71134775129325,no_fill,,,trending_down,0.4619,0.9893,0.825,0.4326,0.4083,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.46 < 0.60
ETH-20260903T0950-london-short,ETH,2026-09-03T09:50:00+00:00,london,short,ob,4.098373406351302,no_fill,,,trending_down,0.7317,1.0026,0.7059,0.4489,0.1953,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.00 < 2.0
BTC-20260904T1355-ny_am-long,BTC,2026-09-04T13:55:00+00:00,ny_am,long,ob,6.496526575639158,stop,-1.2610388206502956,-31.525970516257388,trending_up,0.5073,1.0154,0.357,0.7631,0.6715,0,0,0.0,take,,escalate,confidence 0.51 < 0.60
ETH-20260906T0735-london-short,ETH,2026-09-06T07:35:00+00:00,london,short,fvg,10.055610439405928,no_fill,,,ranging,0.8562,0.0787,0.3369,0.3873,0.2008,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.08 < 2.0
BTC-20260906T0835-london-short,BTC,2026-09-06T08:35:00+00:00,london,short,ob,19.107627025956802,stop,-1.5188803625206646,-37.972009063016614,volatile_chop,0.4405,1.4555,0.3174,0.3682,0.4402,1,0,0.0,take,,escalate,confidence 0.44 < 0.60
BTC-20260907T0725-london-long,BTC,2026-09-07T07:25:00+00:00,london,long,fvg,13.775796049773954,stop,-1.6541069672868187,-41.35267418217047,ranging,0.7704,1.1594,0.8166,0.615,0.7612,1,0,0.0,take,,skip,setup_quality 1.16 < 2.0
ETH-20260907T0820-london-long,ETH,2026-09-07T08:20:00+00:00,london,long,fvg,11.108474058926754,no_fill,,,volatile_chop,0.7027,1.007,0.2466,0.4261,0.8553,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.01 < 2.0
ETH-20260908T0930-london-long,ETH,2026-09-08T09:30:00+00:00,london,long,fvg,8.337307852203537,stop,-1.3109385601714783,-32.77346400428696,trending_down,0.9011,1.0074,0.8141,0.6876,0.7852,0,0,0.0,take,,skip,setup_quality 1.01 < 2.0
BTC-20260908T1435-ny_am-long,BTC,2026-09-08T14:35:00+00:00,ny_am,long,ob,5.596685020245259,no_fill,,,volatile_chop,0.6463,1.9342,0.3272,0.3971,0.6298,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.93 < 2.0
BTC-20260909T1450-ny_am-short,BTC,2026-09-09T14:50:00+00:00,ny_am,short,fvg,3.950886975677377,no_fill,,,ranging,0.3371,1.4,0.782,0.3845,0.1939,0,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.34 < 0.60
BTC-20260910T0855-london-short,BTC,2026-09-10T08:55:00+00:00,london,short,fvg,4.068515544753548,missed,,,volatile_chop,0.6361,1.8474,0.7983,0.237,0.4056,0,0,1.0,skip,not_traded: missed,skip,setup_quality 1.85 < 2.0
ETH-20260911T0835-london-long,ETH,2026-09-11T08:35:00+00:00,london,long,ob,4.62209967218891,stop,-1.3193907509633345,-32.98476877408336,trending_down,0.3757,2.6669,0.7352,0.5073,0.5767,1,0,0.0,take,,escalate,confidence 0.38 < 0.60
ETH-20260912T0735-london-short,ETH,2026-09-12T07:35:00+00:00,london,short,fvg,3.902471053010784,stop,-1.3058221747512675,-32.64555436878169,trending_down,0.9024,2.8479,0.3374,0.5857,0.8102,0,0,0.0,take,,take,
ETH-20260912T1420-ny_am-long,ETH,2026-09-12T14:20:00+00:00,ny_am,long,ob,3.076701547076279,missed,,,trending_down,0.4182,0.9239,0.5173,0.2751,0.7965,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.42 < 0.60
BTC-20260913T0835-london-short,BTC,2026-09-13T08:35:00+00:00,london,short,ob,7.012066743292974,no_fill,,,trending_down,0.6376,1.4647,0.7201,0.4458,0.2245,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.46 < 2.0
ETH-20260913T0945-london-long,ETH,2026-09-13T09:45:00+00:00,london,long,ob,5.222850564096327,stop,-1.4372927693449407,-35.93231923362352,volatile_chop,0.4298,1.9017,0.5492,0.4107,0.2467,0,0,0.0,take,,escalate,confidence 0.43 < 0.60
ETH-20260914T1425-ny_am-long,ETH,2026-09-14T14:25:00+00:00,ny_am,long,ob,6.093247604283642,no_fill,,,trending_down,0.7512,2.9838,0.2827,0.3297,0.3513,1,1,1.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20260915T0945-london-long,ETH,2026-09-15T09:45:00+00:00,london,long,ob,6.38887705702038,stop,-1.3839772476079575,-34.599431190198935,ranging,0.8586,1.9143,0.7233,0.5095,0.3985,0,0,0.0,take,,skip,setup_quality 1.91 < 2.0
ETH-20260915T1320-ny_am-short,ETH,2026-09-15T13:20:00+00:00,ny_am,short,ob,2.337619519165829,missed,,,trending_up,0.9054,2.8912,0.6393,0.2242,0.4468,1,1,1.0,skip,not_traded: missed,skip,not_traded: missed
ETH-20260916T0800-london-long,ETH,2026-09-16T08:00:00+00:00,london,long,ob,6.48698414070719,stop,-1.516857789766159,-37.92144474415397,trending_down,0.7504,2.8923,0.1517,0.6577,0.6985,0,0,0.0,take,,take,
BTC-20260916T0850-london-long,BTC,2026-09-16T08:50:00+00:00,london,long,ob,3.5008630562330714,no_fill,,,ranging,0.8637,0.0814,0.8752,0.8043,0.4933,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.08 < 2.0
ETH-20260917T0835-london-short,ETH,2026-09-17T08:35:00+00:00,london,short,ob,9.137617307133297,stop,-1.513825034263778,-37.84562585659445,ranging,0.8451,2.8014,0.1656,0.7017,0.522,0,0,0.0,take,,take,
BTC-20260917T1300-ny_am-short,BTC,2026-09-17T13:00:00+00:00,ny_am,short,fvg,4.64127773621346,no_fill,,,volatile_chop,0.0923,1.225,0.2475,0.528,0.6005,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.09 < 0.60
ETH-20260918T0850-london-long,ETH,2026-09-18T08:50:00+00:00,london,long,fvg,1.544421966090092,missed,,,volatile_chop,0.5536,1.9953,0.3604,0.4392,0.4985,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.55 < 0.60
ETH-20260919T0900-london-long,ETH,2026-09-19T09:00:00+00:00,london,long,ob,1.959080449695098,missed,,,volatile_chop,0.8217,0.0341,0.9457,0.6995,0.6469,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.03 < 2.0
BTC-20260919T0905-london-long,BTC,2026-09-19T09:05:00+00:00,london,long,ob,4.550307172983693,stop,-1.5375878796808087,-38.43969699202022,ranging,0.8164,1.1297,0.3986,0.6635,0.5492,1,0,0.0,take,,skip,setup_quality 1.13 < 2.0
BTC-20260920T0740-london-long,BTC,2026-09-20T07:40:00+00:00,london,long,ob,4.534562685397678,stop,-1.4810925429109885,-37.02731357277471,ranging,0.6537,2.9763,0.4388,0.4238,0.4109,0,0,0.0,take,,take,
ETH-20260920T1405-ny_am-long,ETH,2026-09-20T14:05:00+00:00,ny_am,long,fvg,9.584556577914602,stop,-1.3781494197111877,-34.45373549277969,ranging,0.6679,1.8231,0.335,0.026,0.6691,0,0,0.0,take,,skip,setup_quality 1.82 < 2.0
BTC-20260921T1315-ny_am-long,BTC,2026-09-21T13:15:00+00:00,ny_am,long,ob,10.83027770481182,timeout,0.6777530749935817,16.943826874839544,ranging,0.7803,1.0841,0.6352,0.5765,0.2668,1,1,,take,,skip,setup_quality 1.08 < 2.0
BTC-20260922T1435-ny_am-long,BTC,2026-09-22T14:35:00+00:00,ny_am,long,ob,3.5241412886101835,missed,,,ranging,0.2773,1.2947,0.742,0.7507,0.6242,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.28 < 0.60
BTC-20260923T1350-ny_am-short,BTC,2026-09-23T13:50:00+00:00,ny_am,short,ob,9.795802947238542,no_fill,,,ranging,0.7159,1.97,0.4442,0.653,0.67,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.97 < 2.0
BTC-20260924T0810-london-long,BTC,2026-09-24T08:10:00+00:00,london,long,ob,3.3930958548337267,no_fill,,,volatile_chop,0.417,0.8745,0.2763,0.5847,0.0439,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.42 < 0.60
ETH-20260924T1410-ny_am-short,ETH,2026-09-24T14:10:00+00:00,ny_am,short,ob,7.527377808027186,stop,-1.3085941390537308,-32.71485347634327,ranging,0.7685,2.8109,0.7069,0.7751,0.2606,0,0,0.0,take,,skip,target_before_stop 0.26 < 0.30
BTC-20260924T1420-ny_am-short,BTC,2026-09-24T14:20:00+00:00,ny_am,short,fvg,5.611531524136798,stop,-1.2481025119893103,-31.20256279973276,trending_down,0.7447,1.6587,0.4678,0.7665,0.5192,0,0,0.0,take,,skip,setup_quality 1.66 < 2.0
ETH-20260926T0820-london-short,ETH,2026-09-26T08:20:00+00:00,london,short,ob,2.7059376455095876,missed,,,volatile_chop,0.6333,1.9106,0.2181,0.5891,0.7468,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.91 < 2.0
BTC-20260926T0825-london-short,BTC,2026-09-26T08:25:00+00:00,london,short,ob,2.247596520977921,stop,-1.2645223169285544,-31.61305792321386,trending_up,0.2808,2.0076,0.1086,0.1137,0.2564,0,0,0.0,take,,escalate,confidence 0.28 < 0.60
ETH-20260927T0815-london-short,ETH,2026-09-27T08:15:00+00:00,london,short,fvg,3.6204892133386966,stop,-1.307760759173553,-32.69401897933882,ranging,0.8711,2.0628,0.5468,0.2916,0.9018,0,0,0.0,take,,take,
BTC-20260927T0820-london-short,BTC,2026-09-27T08:20:00+00:00,london,short,fvg,3.8308536041073094,stop,-1.3680458449152977,-34.20114612288244,trending_down,0.7959,1.8571,0.926,0.6015,0.5226,0,0,0.0,take,,skip,setup_quality 1.86 < 2.0
BTC-20260927T1250-ny_am-short,BTC,2026-09-27T12:50:00+00:00,ny_am,short,ob,4.038823104671675,no_fill,,,volatile_chop,0.3199,0.5965,0.8544,0.1576,0.6567,0,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.32 < 0.60
ETH-20260927T1435-ny_am-short,ETH,2026-09-27T14:35:00+00:00,ny_am,short,ob,3.712251527084963,stop,-1.2549338178915197,-31.373345447287992,ranging,0.7005,2.6565,0.0882,0.5281,0.4817,0,0,0.0,take,,take,
BTC-20260929T0955-london-short,BTC,2026-09-29T09:55:00+00:00,london,short,ob,3.8840493765082984,no_fill,,,ranging,0.6589,1.1202,0.6229,0.0646,0.1669,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.12 < 2.0
ETH-20260930T0835-london-long,ETH,2026-09-30T08:35:00+00:00,london,long,ob,12.806198962255959,no_fill,,,volatile_chop,0.8688,0.2016,0.5655,0.546,0.4202,1,0,0.0,skip,not_traded: no_fill,skip,setup_quality 0.20 < 2.0
BTC-20260930T1350-ny_am-short,BTC,2026-09-30T13:50:00+00:00,ny_am,short,ob,6.712558298764299,no_fill,,,trending_up,0.431,1.8789,0.4642,0.5432,0.5281,0,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.43 < 0.60
BTC-20261001T0935-london-short,BTC,2026-10-01T09:35:00+00:00,london,short,fvg,2.6130156099348345,stop,-1.3662647200303994,-34.156618000759984,ranging,0.3064,0.9891,0.2056,0.7214,0.2963,1,0,0.0,take,,escalate,confidence 0.31 < 0.60
ETH-20261002T0720-london-short,ETH,2026-10-02T07:20:00+00:00,london,short,ob,9.199223835312843,stop,-1.540235025217652,-38.5058756304413,trending_up,0.597,0.7188,0.3387,0.3852,0.2351,0,0,0.0,take,,escalate,confidence 0.60 < 0.60
BTC-20261002T1335-ny_am-short,BTC,2026-10-02T13:35:00+00:00,ny_am,short,fvg,10.688921279895826,no_fill,,,trending_up,0.3464,1.9893,0.2303,0.4692,0.5122,0,1,,skip,not_traded: no_fill,escalate,confidence 0.35 < 0.60
ETH-20261003T1405-ny_am-long,ETH,2026-10-03T14:05:00+00:00,ny_am,long,ob,6.219390368854084,no_fill,,,trending_up,0.7255,2.7318,0.2962,0.3773,0.2943,0,0,0.0,skip,not_traded: no_fill,skip,target_before_stop 0.29 < 0.30
BTC-20261004T0720-london-long,BTC,2026-10-04T07:20:00+00:00,london,long,ob,5.538243852522504,stop,-1.4962726815020124,-37.40681703755031,ranging,0.6373,1.1956,0.1888,0.4323,0.4662,0,0,0.0,take,,skip,setup_quality 1.20 < 2.0
ETH-20261004T0720-london-long,ETH,2026-10-04T07:20:00+00:00,london,long,ob,5.776199289856021,stop,-1.574268667941685,-39.35671669854213,trending_down,0.8081,1.1476,0.1763,0.4197,0.1947,0,0,0.0,skip,correlated_open: BTC (BTC-20261004T0720-london-long),skip,setup_quality 1.15 < 2.0
</trade_log>

<trade_log split="holdout">
id,symbol,ts_utc,killzone,direction,zone_kind,reward_risk,outcome,r_multiple,pnl_usd,jev_regime,jev_confidence,jev_setup_quality,jev_direction_agrees,jev_sweep_is_genuine,jev_target_before_stop,label_direction_agrees,label_sweep_is_genuine,label_target_before_stop,arm_a_action,arm_a_reason,arm_b_action,arm_b_reason
BTC-20261006T1250-ny_am-short,BTC,2026-10-06T12:50:00+00:00,ny_am,short,ob,5.841122460468981,no_fill,,,volatile_chop,0.6815,0.9917,0.3955,0.1467,0.3111,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.99 < 2.0
BTC-20261008T1435-ny_am-long,BTC,2026-10-08T14:35:00+00:00,ny_am,long,ob,10.46082742755716,stop,-1.3690566748207822,-34.22641687051956,trending_up,0.6976,2.01,0.7061,0.1139,0.1179,1,0,0.0,take,,skip,target_before_stop 0.12 < 0.30
BTC-20261009T0720-london-short,BTC,2026-10-09T07:20:00+00:00,london,short,ob,6.596391021786352,no_fill,,,volatile_chop,0.7017,1.9812,0.2922,0.6423,0.34,0,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.98 < 2.0
BTC-20261009T0950-london-long,BTC,2026-10-09T09:50:00+00:00,london,long,ob,5.330335957596187,target,5.166523917339557,129.16309793348893,trending_down,0.4209,2.7705,0.5185,0.2389,0.3618,0,0,1.0,take,,escalate,confidence 0.42 < 0.60
BTC-20261010T0840-london-long,BTC,2026-10-10T08:40:00+00:00,london,long,ob,3.461099181957094,missed,,,volatile_chop,0.8707,1.9074,0.6143,0.5108,0.6998,1,0,1.0,skip,not_traded: missed,skip,setup_quality 1.91 < 2.0
ETH-20261010T0925-london-short,ETH,2026-10-10T09:25:00+00:00,london,short,ob,4.008513475187161,stop,-1.4573829032267698,-36.43457258066925,volatile_chop,0.6111,1.0992,0.4941,0.4715,0.369,0,0,0.0,take,,skip,setup_quality 1.10 < 2.0
ETH-20261011T0745-london-short,ETH,2026-10-11T07:45:00+00:00,london,short,fvg,5.5173486656736275,no_fill,,,ranging,0.5213,0.4748,0.364,0.2443,0.8814,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.52 < 0.60
ETH-20261011T0925-london-long,ETH,2026-10-11T09:25:00+00:00,london,long,ob,5.62128657228706,stop,-1.422870835691219,-35.571770892280476,ranging,0.5844,2.2569,0.4946,0.191,0.3189,0,0,0.0,take,,escalate,confidence 0.58 < 0.60
BTC-20261011T1400-ny_am-short,BTC,2026-10-11T14:00:00+00:00,ny_am,short,fvg,5.121241218554472,stop,-1.29405693648931,-32.35142341223275,ranging,0.677,2.0071,0.4665,0.3132,0.425,0,0,0.0,take,,take,
BTC-20261012T0840-london-long,BTC,2026-10-12T08:40:00+00:00,london,long,ob,17.969875491812186,stop,-1.3511815430218335,-33.779538575545835,trending_down,0.7548,2.6239,0.2339,0.3233,0.4769,1,0,0.0,take,,take,
BTC-20261014T1430-ny_am-short,BTC,2026-10-14T14:30:00+00:00,ny_am,short,ob,7.66276234708539,no_fill,,,ranging,0.9112,2.8747,0.4032,0.8194,0.5075,0,0,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
BTC-20261015T1305-ny_am-short,BTC,2026-10-15T13:05:00+00:00,ny_am,short,ob,5.954697546948173,stop,-1.2785275033264438,-31.963187583161094,trending_down,0.7186,2.5708,0.5817,0.3304,0.3209,1,0,0.0,take,,take,
ETH-20261016T0950-london-short,ETH,2026-10-16T09:50:00+00:00,london,short,fvg,6.296700931779107,no_fill,,,trending_up,0.9232,1.9744,0.5355,0.6616,0.7411,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.97 < 2.0
ETH-20261016T1405-ny_am-long,ETH,2026-10-16T14:05:00+00:00,ny_am,long,fvg,3.7039329775739747,stop,-1.1545931260583806,-28.864828151459513,ranging,0.4855,1.4781,0.7725,0.4785,0.5092,1,0,0.0,take,,escalate,confidence 0.49 < 0.60
ETH-20261017T1405-ny_am-long,ETH,2026-10-17T14:05:00+00:00,ny_am,long,ob,5.447621588578488,stop,-1.4047735477174104,-35.11933869293526,volatile_chop,0.7145,1.9751,0.3828,0.7806,0.4034,1,0,0.0,take,,skip,setup_quality 1.98 < 2.0
BTC-20261018T0720-london-short,BTC,2026-10-18T07:20:00+00:00,london,short,fvg,2.904381392327473,missed,,,trending_down,0.8995,0.951,0.1483,0.6293,0.5505,1,0,1.0,skip,not_traded: missed,skip,setup_quality 0.95 < 2.0
ETH-20261018T0720-london-short,ETH,2026-10-18T07:20:00+00:00,london,short,ob,5.671579859699921,stop,-1.4250666697637282,-35.62666674409321,trending_down,0.8228,1.8771,0.6016,0.6702,0.4655,0,0,0.0,take,,skip,setup_quality 1.88 < 2.0
BTC-20261018T0815-london-long,BTC,2026-10-18T08:15:00+00:00,london,long,fvg,2.0,missed,,,trending_up,0.7989,1.888,0.7964,0.6811,0.3993,0,0,1.0,skip,not_traded: missed,skip,setup_quality 1.89 < 2.0
BTC-20261018T1355-ny_am-long,BTC,2026-10-18T13:55:00+00:00,ny_am,long,ob,10.505073546871518,stop,-1.4782890678063005,-36.957226695157516,trending_up,0.5001,2.7756,0.7513,0.6817,0.9545,1,0,0.0,take,,escalate,confidence 0.50 < 0.60
ETH-20261019T0835-london-short,ETH,2026-10-19T08:35:00+00:00,london,short,fvg,8.23882302648483,stop,-1.354517233647911,-33.86293084119777,volatile_chop,0.7099,0.235,0.4285,0.5602,0.4691,0,0,0.0,take,,skip,setup_quality 0.23 < 2.0
ETH-20261020T0920-london-long,ETH,2026-10-20T09:20:00+00:00,london,long,fvg,7.436333939249158,stop,-1.3931638190957563,-34.829095477393906,trending_down,0.6885,1.091,0.6683,0.8184,0.4574,1,0,0.0,take,,skip,setup_quality 1.09 < 2.0
BTC-20261021T0730-london-short,BTC,2026-10-21T07:30:00+00:00,london,short,fvg,5.666608612193572,stop,-1.4512137010524047,-36.280342526310115,trending_down,0.796,1.1848,0.2191,0.4735,0.2973,0,0,0.0,take,,skip,setup_quality 1.18 < 2.0
ETH-20261021T0735-london-short,ETH,2026-10-21T07:35:00+00:00,london,short,ob,7.241549054631377,target,7.053381731945051,176.33454329862627,ranging,0.635,1.321,0.1933,0.799,0.5505,0,1,1.0,take,,skip,setup_quality 1.32 < 2.0
BTC-20261022T1355-ny_am-short,BTC,2026-10-22T13:55:00+00:00,ny_am,short,fvg,7.662801851173942,no_fill,,,ranging,0.5485,1.3773,0.3201,0.1409,0.376,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.55 < 0.60
BTC-20261023T1415-ny_am-long,BTC,2026-10-23T14:15:00+00:00,ny_am,long,fvg,3.658274366459408,no_fill,,,trending_up,0.7556,2.0135,0.3715,0.5282,0.5605,0,0,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
BTC-20261024T1310-ny_am-long,BTC,2026-10-24T13:10:00+00:00,ny_am,long,fvg,4.22678955709127,stop,-1.2566735695058313,-31.416839237645785,trending_down,0.5363,0.0595,0.3979,0.5524,0.3928,0,0,0.0,take,,escalate,confidence 0.54 < 0.60
BTC-20261028T0835-london-short,BTC,2026-10-28T08:35:00+00:00,london,short,fvg,5.394713307070088,no_fill,,,ranging,0.6432,1.9354,0.9067,0.6064,0.5057,1,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.94 < 2.0
BTC-20261029T1335-ny_am-long,BTC,2026-10-29T13:35:00+00:00,ny_am,long,ob,20.408323148321166,stop,-1.515057851208509,-37.876446280212726,trending_down,0.9033,2.8384,0.8024,0.3709,0.3985,0,0,0.0,take,,take,
ETH-20261030T0755-london-short,ETH,2026-10-30T07:55:00+00:00,london,short,ob,3.7039978655757646,stop,-1.4050915323213655,-35.12728830803414,volatile_chop,0.5466,1.5662,0.8785,0.4204,0.4747,0,0,0.0,take,,escalate,confidence 0.55 < 0.60
BTC-20261030T0935-london-long,BTC,2026-10-30T09:35:00+00:00,london,long,ob,7.748917320108302,stop,-1.6599027744373849,-41.49756936093462,volatile_chop,0.7649,1.1346,0.2079,0.605,0.097,1,0,0.0,skip,correlated_open: ETH (ETH-20261030T0755-london-short),skip,setup_quality 1.13 < 2.0
BTC-20261030T1430-ny_am-short,BTC,2026-10-30T14:30:00+00:00,ny_am,short,ob,4.751342229136219,stop,-1.2441198682903465,-31.10299670725866,trending_down,0.3561,1.8633,0.3314,0.5548,0.5089,0,0,0.0,take,,escalate,confidence 0.36 < 0.60
ETH-20261031T1430-ny_am-short,ETH,2026-10-31T14:30:00+00:00,ny_am,short,ob,7.52981260236827,target,7.3850368465017375,184.62592116254345,trending_up,0.4483,2.5599,0.6265,0.4882,0.8095,1,1,1.0,take,,escalate,confidence 0.45 < 0.60
ETH-20261102T0720-london-short,ETH,2026-11-02T07:20:00+00:00,london,short,ob,9.12884676305329,no_fill,,,trending_up,0.5657,1.3809,0.4847,0.3031,0.8182,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.57 < 0.60
BTC-20261102T0935-london-short,BTC,2026-11-02T09:35:00+00:00,london,short,ob,6.328076582508588,stop,-1.3995893330757392,-34.98973332689348,volatile_chop,0.2362,2.0043,0.6758,0.6686,0.8652,0,0,0.0,take,,escalate,confidence 0.24 < 0.60
ETH-20261103T0935-london-long,ETH,2026-11-03T09:35:00+00:00,london,long,ob,7.199211426812878,target,6.970517828345219,174.26294570863047,trending_up,0.8949,0.0203,0.2527,0.6281,0.8508,1,0,1.0,take,,skip,setup_quality 0.02 < 2.0
BTC-20261104T1435-ny_am-short,BTC,2026-11-04T14:35:00+00:00,ny_am,short,fvg,2.306798691815924,no_fill,,,ranging,0.5128,1.9274,0.4468,0.2944,0.397,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.51 < 0.60
ETH-20261104T1435-ny_am-short,ETH,2026-11-04T14:35:00+00:00,ny_am,short,fvg,2.104816086837275,target,2.032517808361307,50.812945209032684,ranging,0.4046,0.7823,0.5588,0.6077,0.6118,0,1,1.0,take,,escalate,confidence 0.40 < 0.60
ETH-20261105T0725-london-long,ETH,2026-11-05T07:25:00+00:00,london,long,ob,8.074443428515327,stop,-1.4362153424695772,-35.90538356173943,trending_up,0.9516,1.0697,0.5972,0.1121,0.6936,0,0,0.0,skip,correlated_open: BTC (BTC-20261105T0750-london-long),skip,setup_quality 1.07 < 2.0
BTC-20261105T0750-london-long,BTC,2026-11-05T07:50:00+00:00,london,long,ob,7.256249141271885,stop,-1.4037755468037634,-35.094388670094084,trending_up,0.8208,0.8904,0.7675,0.4275,0.5671,0,0,0.0,take,,skip,setup_quality 0.89 < 2.0
ETH-20261106T0740-london-short,ETH,2026-11-06T07:40:00+00:00,london,short,ob,2.91400588637357,missed,,,trending_up,0.4016,2.5142,0.5975,0.4323,0.6959,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.40 < 0.60
BTC-20261106T0745-london-short,BTC,2026-11-06T07:45:00+00:00,london,short,fvg,1.9657684179599402,missed,,,trending_up,0.6367,1.1504,0.3573,0.3803,0.7153,0,0,1.0,skip,not_traded: missed,skip,setup_quality 1.15 < 2.0
ETH-20261106T0845-london-long,ETH,2026-11-06T08:45:00+00:00,london,long,fvg,2.0493325161686506,missed,,,ranging,0.5557,0.8507,0.3647,0.4805,0.4162,1,0,1.0,skip,not_traded: missed,escalate,confidence 0.56 < 0.60
ETH-20261107T1350-ny_am-short,ETH,2026-11-07T13:50:00+00:00,ny_am,short,fvg,9.851484358715469,stop,-1.2928423380691931,-32.321058451729826,trending_up,0.6424,2.1708,0.4771,0.4238,0.324,0,0,0.0,take,,take,
ETH-20261109T0815-london-short,ETH,2026-11-09T08:15:00+00:00,london,short,fvg,6.99684345605258,no_fill,,,trending_down,0.8914,1.9491,0.3669,0.1115,0.5023,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.95 < 2.0
BTC-20261109T1345-ny_am-short,BTC,2026-11-09T13:45:00+00:00,ny_am,short,ob,8.36845044854798,no_fill,,,volatile_chop,0.5694,2.9774,0.3811,0.4183,0.4624,1,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.57 < 0.60
BTC-20261110T0805-london-short,BTC,2026-11-10T08:05:00+00:00,london,short,fvg,3.436244385075112,stop,-1.3226566979739118,-33.066417449347796,volatile_chop,0.7367,0.1412,0.4566,0.3835,0.8444,0,0,0.0,take,,skip,setup_quality 0.14 < 2.0
ETH-20261111T0720-london-long,ETH,2026-11-11T07:20:00+00:00,london,long,ob,5.1532088688554625,stop,-1.5620437926779551,-39.051094816948876,volatile_chop,0.5955,1.6021,0.734,0.6473,0.7952,0,0,0.0,take,,escalate,confidence 0.60 < 0.60
BTC-20261111T1255-ny_am-long,BTC,2026-11-11T12:55:00+00:00,ny_am,long,fvg,3.8854385413247923,no_fill,,,trending_down,0.8931,1.8915,0.601,0.5092,0.938,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.89 < 2.0
ETH-20261111T1255-ny_am-long,ETH,2026-11-11T12:55:00+00:00,ny_am,long,fvg,4.161217490372437,target,4.056397272872584,101.40993182181458,trending_up,0.7767,1.6657,0.3574,0.3698,0.6687,1,1,1.0,take,,skip,setup_quality 1.67 < 2.0
ETH-20261112T0740-london-long,ETH,2026-11-12T07:40:00+00:00,london,long,fvg,5.401927246728005,no_fill,,,trending_down,0.8165,0.261,0.5735,0.4746,0.7956,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.26 < 2.0
BTC-20261113T0950-london-long,BTC,2026-11-13T09:50:00+00:00,london,long,ob,8.403482928389092,stop,-1.3457601047210679,-33.6440026180267,volatile_chop,0.3238,1.3167,0.8672,0.6211,0.8308,1,0,0.0,skip,correlated_open: ETH (ETH-20261113T0950-london-long),escalate,confidence 0.32 < 0.60
ETH-20261113T0950-london-long,ETH,2026-11-13T09:50:00+00:00,london,long,ob,7.099258087257242,stop,-1.319847542366371,-32.99618855915927,trending_up,0.4456,1.6213,0.4444,0.4664,0.3062,1,0,0.0,take,,escalate,confidence 0.45 < 0.60
ETH-20261114T0835-london-long,ETH,2026-11-14T08:35:00+00:00,london,long,ob,4.5237693779526,stop,-1.3952081916799717,-34.88020479199929,trending_down,0.354,1.7499,0.6984,0.534,0.5405,1,0,0.0,take,,escalate,confidence 0.35 < 0.60
ETH-20261117T1450-ny_am-short,ETH,2026-11-17T14:50:00+00:00,ny_am,short,fvg,8.018760337699009,stop,-1.2998961060823768,-32.49740265205942,trending_down,0.7824,1.9753,0.3239,0.8951,0.4679,0,0,0.0,take,,skip,setup_quality 1.98 < 2.0
ETH-20261118T1255-ny_am-long,ETH,2026-11-18T12:55:00+00:00,ny_am,long,ob,6.586011523439339,target,6.4762385541107195,161.905963852768,volatile_chop,0.5212,2.9929,0.6791,0.7667,0.4734,0,1,1.0,take,,escalate,confidence 0.52 < 0.60
BTC-20261119T1335-ny_am-short,BTC,2026-11-19T13:35:00+00:00,ny_am,short,fvg,11.721606281153026,no_fill,,,trending_down,0.3251,0.6622,0.225,0.7636,0.1684,1,1,1.0,skip,not_traded: no_fill,escalate,confidence 0.33 < 0.60
BTC-20261120T0915-london-short,BTC,2026-11-20T09:15:00+00:00,london,short,fvg,2.0044132439121687,missed,,,ranging,0.6129,0.7116,0.1166,0.752,0.4267,1,1,1.0,skip,not_traded: missed,skip,setup_quality 0.71 < 2.0
ETH-20261120T0950-london-short,ETH,2026-11-20T09:50:00+00:00,london,short,ob,2.5193797330203593,missed,,,volatile_chop,0.8026,1.0745,0.4493,0.6351,0.4552,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.07 < 2.0
BTC-20261120T1450-ny_am-long,BTC,2026-11-20T14:50:00+00:00,ny_am,long,ob,11.544418450740507,no_fill,,,volatile_chop,0.6526,1.4817,0.1032,0.6568,0.7272,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.48 < 2.0
BTC-20261121T0740-london-short,BTC,2026-11-21T07:40:00+00:00,london,short,ob,3.3084582854226583,stop,-1.3869032761051157,-34.67258190262789,trending_up,0.626,2.7987,0.6783,0.8382,0.8782,0,0,0.0,take,,take,
ETH-20261121T0855-london-long,ETH,2026-11-21T08:55:00+00:00,london,long,fvg,2.416085532252374,missed,,,ranging,0.7821,1.7696,0.5884,0.3809,0.7932,1,1,1.0,skip,not_traded: missed,skip,setup_quality 1.77 < 2.0
ETH-20261121T1310-ny_am-short,ETH,2026-11-21T13:10:00+00:00,ny_am,short,ob,12.533877259622884,stop,-1.3918248769015873,-34.79562192253968,trending_up,0.7627,1.9875,0.3047,0.4082,0.5447,1,0,0.0,take,,skip,setup_quality 1.99 < 2.0
ETH-20261122T0935-london-short,ETH,2026-11-22T09:35:00+00:00,london,short,fvg,2.1814882184750357,missed,,,crisis,0.5872,0.0941,0.6142,0.4555,0.5501,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.59 < 0.60
ETH-20261123T0935-london-long,ETH,2026-11-23T09:35:00+00:00,london,long,fvg,4.5846808231563845,no_fill,,,volatile_chop,0.6661,0.9769,0.9111,0.6084,0.1282,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.98 < 2.0
BTC-20261123T1405-ny_am-long,BTC,2026-11-23T14:05:00+00:00,ny_am,long,ob,8.901581748694095,no_fill,,,trending_up,0.8225,1.8709,0.3377,0.8863,0.1865,1,1,0.0,skip,not_traded: no_fill,skip,setup_quality 1.87 < 2.0
ETH-20261124T0730-london-short,ETH,2026-11-24T07:30:00+00:00,london,short,ob,5.548045904024841,stop,-1.4043290918412603,-35.10822729603151,trending_down,0.8046,2.8387,0.2185,0.2397,0.8887,0,0,0.0,take,,take,
ETH-20261125T1420-ny_am-long,ETH,2026-11-25T14:20:00+00:00,ny_am,long,ob,6.750546357079018,stop,-1.2970119692017232,-32.42529923004308,volatile_chop,0.8206,1.0601,0.273,0.7098,0.5655,0,0,0.0,take,,skip,setup_quality 1.06 < 2.0
BTC-20261128T0945-london-long,BTC,2026-11-28T09:45:00+00:00,london,long,fvg,6.347320524055061,no_fill,,,trending_down,0.7279,1.6599,0.0578,0.354,0.6055,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.66 < 2.0
BTC-20261128T1420-ny_am-short,BTC,2026-11-28T14:20:00+00:00,ny_am,short,ob,6.986810981132713,no_fill,,,ranging,0.2088,0.1207,0.2438,0.5703,0.8083,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.21 < 0.60
ETH-20261129T0855-london-long,ETH,2026-11-29T08:55:00+00:00,london,long,fvg,1.7305084765014414,stop,-1.3263390055748898,-33.15847513937224,trending_down,0.2098,1.1246,0.3671,0.0698,0.3879,0,0,0.0,take,,escalate,confidence 0.21 < 0.60
BTC-20261201T1425-ny_am-short,BTC,2026-12-01T14:25:00+00:00,ny_am,short,ob,8.577513835716395,no_fill,,,trending_down,0.8048,2.1424,0.8629,0.6275,0.5128,1,1,1.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20261201T1440-ny_am-short,ETH,2026-12-01T14:40:00+00:00,ny_am,short,ob,4.574490817283183,stop,-1.2580551552992403,-31.45137888248101,trending_up,0.4387,1.9962,0.278,0.5841,0.9085,0,0,0.0,take,,escalate,confidence 0.44 < 0.60
BTC-20261203T0735-london-short,BTC,2026-12-03T07:35:00+00:00,london,short,ob,9.091082228551715,stop,-1.4751985823741658,-36.87996455935414,trending_down,0.842,0.2982,0.557,0.6017,0.4438,1,1,0.0,take,,skip,setup_quality 0.30 < 2.0
ETH-20261203T0820-london-short,ETH,2026-12-03T08:20:00+00:00,london,short,ob,11.382802066480796,stop,-1.525221807333203,-38.13054518333007,volatile_chop,0.6737,0.108,0.571,0.6039,0.7442,0,0,0.0,skip,correlated_open: BTC (BTC-20261203T0735-london-short),skip,setup_quality 0.11 < 2.0
BTC-20261204T0740-london-long,BTC,2026-12-04T07:40:00+00:00,london,long,ob,8.961054257736334,no_fill,,,trending_up,0.6484,0.4923,0.3777,0.6115,0.213,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 0.49 < 2.0
BTC-20261206T0950-london-short,BTC,2026-12-06T09:50:00+00:00,london,short,ob,17.50729113418822,stop,-1.6435753396778496,-41.08938349194624,volatile_chop,0.4962,1.8227,0.7534,0.1828,0.5159,0,0,0.0,take,,escalate,confidence 0.50 < 0.60
ETH-20261207T1320-ny_am-long,ETH,2026-12-07T13:20:00+00:00,ny_am,long,fvg,7.156170612795151,no_fill,,,trending_down,0.6013,1.4717,0.106,0.1729,0.6517,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.47 < 2.0
BTC-20261207T1335-ny_am-long,BTC,2026-12-07T13:35:00+00:00,ny_am,long,fvg,5.35119572301819,no_fill,,,trending_up,0.6914,1.9852,0.4869,0.4589,0.7057,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.99 < 2.0
ETH-20261210T0835-london-long,ETH,2026-12-10T08:35:00+00:00,london,long,fvg,5.766774925970467,no_fill,,,trending_up,0.6373,1.7645,0.6823,0.7891,0.2372,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.76 < 2.0
BTC-20261211T1335-ny_am-short,BTC,2026-12-11T13:35:00+00:00,ny_am,short,fvg,4.525269272545531,no_fill,,,trending_up,0.6956,1.7513,0.7789,0.287,0.4131,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 1.75 < 2.0
BTC-20261212T0905-london-long,BTC,2026-12-12T09:05:00+00:00,london,long,ob,7.108464087729259,no_fill,,,volatile_chop,0.5871,1.0011,0.6824,0.561,0.6604,1,1,0.0,skip,not_traded: no_fill,escalate,confidence 0.59 < 0.60
ETH-20261212T1310-ny_am-short,ETH,2026-12-12T13:10:00+00:00,ny_am,short,ob,9.409213543492374,no_fill,,,volatile_chop,0.6811,0.9225,0.3476,0.1653,0.232,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 0.92 < 2.0
BTC-20261213T0850-london-long,BTC,2026-12-13T08:50:00+00:00,london,long,ob,4.662596564339861,no_fill,,,volatile_chop,0.8932,1.9008,0.9199,0.2598,0.3596,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.90 < 2.0
BTC-20261213T1320-ny_am-short,BTC,2026-12-13T13:20:00+00:00,ny_am,short,fvg,4.655134411841364,no_fill,,,ranging,0.6345,1.9949,0.087,0.4251,0.5397,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.99 < 2.0
BTC-20261215T1320-ny_am-short,BTC,2026-12-15T13:20:00+00:00,ny_am,short,fvg,15.069295791383265,stop,-1.3460276947966385,-33.650692369915966,trending_down,0.6624,2.6076,0.2116,0.8384,0.6288,0,0,0.0,take,,take,
ETH-20261217T0735-london-long,ETH,2026-12-17T07:35:00+00:00,london,long,ob,2.7016446926618545,stop,-1.3590206731503043,-33.975516828757605,volatile_chop,0.4821,1.0546,0.0975,0.6448,0.5115,0,0,0.0,take,,escalate,confidence 0.48 < 0.60
BTC-20261217T1255-ny_am-long,BTC,2026-12-17T12:55:00+00:00,ny_am,long,ob,3.837700712684102,missed,,,trending_up,0.3992,2.3099,0.7636,0.3382,0.1613,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.40 < 0.60
ETH-20261217T1255-ny_am-long,ETH,2026-12-17T12:55:00+00:00,ny_am,long,ob,4.594842859919953,no_fill,,,ranging,0.9152,2.8722,0.7411,0.7612,0.6118,0,0,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
BTC-20261217T1410-ny_am-short,BTC,2026-12-17T14:10:00+00:00,ny_am,short,ob,9.231179922671096,target,9.04517735217148,226.129433804287,trending_up,0.8991,2.924,0.7742,0.4682,0.9281,1,1,1.0,take,,take,
ETH-20261218T0840-london-long,ETH,2026-12-18T08:40:00+00:00,london,long,fvg,4.076555654619994,stop,-1.3241559978337454,-33.10389994584364,trending_down,0.8255,1.9117,0.3792,0.2335,0.4131,0,0,0.0,take,,skip,setup_quality 1.91 < 2.0
BTC-20261219T0720-london-short,BTC,2026-12-19T07:20:00+00:00,london,short,ob,3.3760477010273475,missed,,,ranging,0.205,1.0217,0.6987,0.4157,0.618,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.20 < 0.60
BTC-20261220T0815-london-long,BTC,2026-12-20T08:15:00+00:00,london,long,ob,1.8942866875024296,missed,,,trending_up,0.3768,2.0562,0.2803,0.2029,0.4527,1,1,1.0,skip,not_traded: missed,escalate,confidence 0.38 < 0.60
ETH-20261220T0820-london-long,ETH,2026-12-20T08:20:00+00:00,london,long,ob,4.624099031759218,missed,,,volatile_chop,0.8488,2.8205,0.6962,0.609,0.2459,1,1,1.0,skip,not_traded: missed,skip,target_before_stop 0.25 < 0.30
ETH-20261220T1310-ny_am-short,ETH,2026-12-20T13:10:00+00:00,ny_am,short,fvg,6.490286164008772,stop,-1.1715491969557947,-29.28872992389487,trending_up,0.7222,1.0647,0.618,0.5244,0.6469,0,0,0.0,take,,skip,setup_quality 1.06 < 2.0
BTC-20261220T1435-ny_am-short,BTC,2026-12-20T14:35:00+00:00,ny_am,short,fvg,7.591883557411183,target,7.482776626233715,187.06941565584287,trending_down,0.6802,1.1066,0.2381,0.64,0.8139,1,1,1.0,take,,skip,setup_quality 1.11 < 2.0
ETH-20261222T0755-london-long,ETH,2026-12-22T07:55:00+00:00,london,long,ob,7.289977359222186,no_fill,,,ranging,0.6445,1.9168,0.3747,0.3056,0.5097,0,0,0.0,skip,not_traded: no_fill,skip,setup_quality 1.92 < 2.0
BTC-20261222T0800-london-long,BTC,2026-12-22T08:00:00+00:00,london,long,ob,8.068986730818876,stop,-1.3362444629780628,-33.40611157445157,ranging,0.6728,1.0003,0.3748,0.9355,0.5741,0,0,0.0,take,,skip,setup_quality 1.00 < 2.0
ETH-20261224T0800-london-short,ETH,2026-12-24T08:00:00+00:00,london,short,fvg,3.5232890260189795,missed,,,trending_down,0.7968,2.9874,0.3287,0.9461,0.3233,1,1,1.0,skip,not_traded: missed,skip,not_traded: missed
BTC-20261225T0835-london-short,BTC,2026-12-25T08:35:00+00:00,london,short,ob,5.809578396737338,stop,-1.4791551505159704,-36.97887876289926,trending_down,0.8502,2.8799,0.2965,0.2825,0.136,1,0,0.0,take,,skip,target_before_stop 0.14 < 0.30
BTC-20261225T1415-ny_am-long,BTC,2026-12-25T14:15:00+00:00,ny_am,long,ob,5.429468198438077,stop,-1.260032162189996,-31.5008040547499,trending_up,0.5098,2.0243,0.309,0.1398,0.2695,0,0,0.0,take,,escalate,confidence 0.51 < 0.60
BTC-20261227T0910-london-long,BTC,2026-12-27T09:10:00+00:00,london,long,ob,3.854364594518503,missed,,,volatile_chop,0.3505,1.0325,0.536,0.4448,0.796,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.35 < 0.60
ETH-20261227T0935-london-short,ETH,2026-12-27T09:35:00+00:00,london,short,ob,5.376220561379128,no_fill,,,trending_down,0.7908,1.2923,0.5427,0.6654,0.9512,0,1,0.0,skip,not_traded: no_fill,skip,setup_quality 1.29 < 2.0
BTC-20261229T0720-london-long,BTC,2026-12-29T07:20:00+00:00,london,long,ob,8.518315914582127,stop,-1.6079235220541888,-40.198088051354716,ranging,0.6752,1.9372,0.6409,0.0735,0.4869,0,0,0.0,take,,skip,setup_quality 1.94 < 2.0
ETH-20261229T1415-ny_am-long,ETH,2026-12-29T14:15:00+00:00,ny_am,long,ob,1.5661189434082827,missed,,,volatile_chop,0.4527,1.0298,0.728,0.3374,0.8828,0,0,1.0,skip,not_traded: missed,escalate,confidence 0.45 < 0.60
ETH-20261231T0950-london-long,ETH,2026-12-31T09:50:00+00:00,london,long,ob,9.917345843892717,no_fill,,,trending_up,0.5956,0.9757,0.2585,0.7997,0.5411,0,0,0.0,skip,not_traded: no_fill,escalate,confidence 0.60 < 0.60
ETH-20261231T1335-ny_am-long,ETH,2026-12-31T13:35:00+00:00,ny_am,long,fvg,3.3347564563085257,no_fill,,,volatile_chop,0.6689,1.5363,0.6526,0.6387,0.6206,1,1,1.0,skip,not_traded: no_fill,skip,setup_quality 1.54 < 2.0
BTC-20270101T0835-london-short,BTC,2027-01-01T08:35:00+00:00,london,short,fvg,3.7148813609674227,missed,,,trending_down,0.6477,2.998,0.4055,0.2607,0.8468,0,0,1.0,skip,not_traded: missed,skip,not_traded: missed
ETH-20270101T0920-london-short,ETH,2027-01-01T09:20:00+00:00,london,short,fvg,2.733389233395127,no_fill,,,volatile_chop,0.7949,2.0453,0.6205,0.6641,0.4314,1,1,0.0,skip,not_traded: no_fill,skip,not_traded: no_fill
ETH-20270101T1425-ny_am-long,ETH,2027-01-01T14:25:00+00:00,ny_am,long,fvg,2.658028458944389,stop,-1.1770707266810807,-29.426768167027017,trending_up,0.8163,1.1294,0.6287,0.3688,0.8572,0,0,0.0,take,,skip,setup_quality 1.13 < 2.0
ETH-20270103T0720-london-short,ETH,2027-01-03T07:20:00+00:00,london,short,ob,5.388603799556698,stop,-1.34822873388382,-33.7057183470955,trending_down,0.6093,2.1075,0.1298,0.7502,0.4449,1,0,0.0,take,,take,
BTC-20270104T0720-london-short,BTC,2027-01-04T07:20:00+00:00,london,short,fvg,7.481090382479203,stop,-1.4661213240053235,-36.65303310013309,trending_down,0.4557,1.4235,0.1812,0.8683,0.8559,1,1,0.0,take,,escalate,confidence 0.46 < 0.60
BTC-20270104T1405-ny_am-short,BTC,2027-01-04T14:05:00+00:00,ny_am,short,ob,6.0049445371016645,stop,-1.33683828626714,-33.4209571566785,ranging,0.5559,1.6292,0.2494,0.5944,0.2881,1,0,0.0,take,,escalate,confidence 0.56 < 0.60
</trade_log>

Write the review.
```
