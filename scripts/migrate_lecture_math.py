#!/usr/bin/env python3
"""One-time, idempotent correction of 15 SQLite lecture fields to explicit KaTeX syntax."""
import json,sqlite3
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
db=sqlite3.connect(ROOT/"data"/"curriculum.sqlite3")
overrides={
  "T003": {
    "definition": "ベイズの定理は \\(P(A\\mid B)=\\frac{P(B\\mid A)P(A)}{P(B)}\\)。分母は全確率 \\(P(B)=\\sum_i P(B\\mid A_i)P(A_i)\\)。",
    "derivation": "条件付き確率から \\(P(A\\cap B)=P(B\\mid A)P(A)=P(A\\mid B)P(B)\\) と二通りに表し、\\(P(B)>0\\) で割る。",
    "example": "有病率 \\(0.1\\)、感度 \\(0.8\\)、偽陽性率 \\(0.1\\) なら \\(P(\\text{罹患}\\mid\\text{陽性})=\\frac{0.08}{0.08+0.09}=\\frac8{17}\\approx0.471\\)。",
    "conditions": "\\(P(B)>0\\) が必要。\\(A_i\\) は互いに排反で全体を覆う。"
  },
  "T023": {
    "definition": "\\(X\\sim\\operatorname{Bin}(n,p)\\) の確率関数は \\(P(X=k)=\\binom nk p^k(1-p)^{n-k}\\)。期待値 \\(E[X]=np\\)、分散 \\(\\operatorname{Var}(X)=np(1-p)\\)。",
    "derivation": "指定した成功・失敗の並びの確率は \\(p^k(1-p)^{n-k}\\)。成功位置の組合せ \\(\\binom nk\\) 通りを掛ける。",
    "example": "\\(n=5,\\ p=0.2\\) で \\(P(X=1)=\\binom51(0.2)(0.8)^4=0.4096\\)。"
  },
  "T042": {
    "definition": "最尤推定量は \\(\\hat\\theta=\\operatorname*{arg\\,max}_\\theta L(\\theta)\\)、独立標本なら \\(L(\\theta)=\\prod_{i=1}^n f(x_i\\mid\\theta)\\)。対数尤度は \\(\\ell(\\theta)=\\sum_i\\log f(x_i\\mid\\theta)\\)。",
    "derivation": "ベルヌーイ標本で成功数 \\(s\\) のとき \\(L(p)=p^s(1-p)^{n-s}\\)。\\(\\ell'(p)=\\frac{s}{p}-\\frac{n-s}{1-p}=0\\) より \\(\\hat p=s/n\\)（境界も確認）。",
    "example": "成功7回・失敗3回なら \\(\\hat p=\\frac7{10}=0.7\\)。"
  },
  "T054": {
    "definition": "\\(p\\) 値は帰無仮説 \\(H_0\\) の下で、観測値以上に極端な統計量を得る確率。\\(p\\leq\\alpha\\) なら棄却。",
    "example": "\\(p=0.03\\)、有意水準 \\(\\alpha=0.05\\) なら \\(H_0\\) を棄却。",
    "conditions": "\\(p\\) 値は帰無分布と片側／両側の定義に依存する。"
  },
  "T077": {
    "definition": "線形回帰モデルは \\(y_i=\\beta_0+\\sum_j\\beta_j x_{ij}+\\varepsilon_i\\)。列フルランクならOLS推定量は \\(\\hat\\beta=(X^{\\mathsf T}X)^{-1}X^{\\mathsf T}y\\)。",
    "derivation": "残差平方和 \\((y-X\\beta)^{\\mathsf T}(y-X\\beta)\\) の微分をゼロにすると、正規方程式 \\(X^{\\mathsf T}X\\hat\\beta=X^{\\mathsf T}y\\) が得られる。",
    "example": "\\(\\hat y=4+2x_1-3x_2\\) で \\(x_1\\) が3増加、\\(x_2\\) 一定なら \\(\\Delta\\hat y=2\\times3=6\\)。"
  },
  "T001": {
    "definition": "条件付き確率は \\(P(A\\mid B)=\\frac{P(A\\cap B)}{P(B)}\\)。",
    "example": "\\(P(A\\cap B)=0.12\\)、\\(P(B)=0.3\\) のとき \\(P(A\\mid B)=0.12/0.3=0.4\\)。",
    "conditions": "分母 \\(P(B)>0\\) が必要。"
  },
  "T025": {
    "definition": "\\(X\\sim\\operatorname{Pois}(\\lambda)\\) なら \\(P(X=k)=e^{-\\lambda}\\lambda^k/k!\\)、\\(E[X]=\\operatorname{Var}(X)=\\lambda\\)。",
    "derivation": "\\(X_n\\sim\\operatorname{Bin}(n,\\lambda/n)\\) として \\(n\\to\\infty\\) の極限をとると \\(P(X=k)=e^{-\\lambda}\\lambda^k/k!\\)。",
    "example": "\\(\\lambda=2\\) のとき \\(P(X=0)=e^{-2}\\)。"
  },
  "T043": {
    "definition": "母集団の理論モーメント \\(E_\\theta[X^r]\\) と標本モーメント \\(\\frac1n\\sum_{i=1}^n X_i^r\\) を等置する。",
    "derivation": "ポアソン分布で \\(E[X]=\\lambda\\) なので \\(\\hat\\lambda=\\bar X\\)。",
    "example": "\\(\\bar X=4\\) なら \\(\\hat\\lambda=4\\)。"
  },
  "T057": {
    "definition": "検出力は対立仮説下で棄却する確率で、\\(1-\\beta=P_\\theta(\\text{棄却})\\)。",
    "derivation": "第二種過誤は \\(\\beta=P_\\theta(\\text{棄却しない})\\) なので、補事象の確率は \\(1-\\beta\\)。",
    "example": "\\(\\beta=0.2\\) なら検出力 \\(1-\\beta=0.8\\)。",
    "pitfalls": "有意水準 \\(\\alpha\\) と第二種過誤 \\(\\beta\\) を混同しない。"
  },
  "T094": {
    "definition": "一元配置分散分析の検定統計量は \\(F=MS_{\\mathrm{between}}/MS_{\\mathrm{within}}\\)。群間自由度 \\(k-1\\)、群内自由度 \\(N-k\\)。",
    "example": "3群で各5観測なら \\(N=15\\)、自由度は \\(k-1=2\\) と \\(N-k=12\\)。"
  },
  "T007": {
    "definition": "離散変数では \\(E[X]=\\sum_x xP(X=x)\\)、連続変数では \\(E[X]=\\int_{-\\infty}^{\\infty}xf(x)\\,dx\\)。線形性 \\(E[aX+bY]=aE[X]+bE[Y]\\)。",
    "derivation": "和・積分の線形性から期待値の線形性が従う。独立性は不要。",
    "example": "\\(E[X]=3\\)、\\(E[Y]=-1\\) なら \\(E[2X-Y]=2\\times3-(-1)=7\\)。"
  },
  "T030": {
    "definition": "\\(X\\sim N(\\mu,\\sigma^2)\\) なら \\(Z=\\frac{X-\\mu}{\\sigma}\\sim N(0,1)\\)。",
    "derivation": "\\(X=\\mu+\\sigma Z\\) の変数変換から標準正規分布が得られる。",
    "example": "\\(X\\sim N(10,4)\\) なら標準偏差は2なので \\(Z=(X-10)/2\\)。"
  },
  "T051": {
    "definition": "母標準偏差 \\(\\sigma\\) 既知の母平均に対する両側信頼区間は \\(\\bar X\\pm z_{1-\\alpha/2}\\frac{\\sigma}{\\sqrt n}\\)。",
    "derivation": "\\(Z=\\frac{\\bar X-\\mu}{\\sigma/\\sqrt n}\\) の両側確率不等式を \\(\\mu\\) について解く。",
    "example": "\\(\\bar X=10\\)、\\(\\sigma=4\\)、\\(n=16\\) の95%信頼区間は \\(10\\pm1.96=(8.04,11.96)\\)。"
  },
  "T062": {
    "definition": "尤度比 \\(\\Lambda=\\frac{L(\\hat\\theta_0)}{L(\\hat\\theta)}\\) の値域は \\(0\\leq\\Lambda\\leq1\\)。通常は \\(-2\\log\\Lambda\\) を使用する。",
    "derivation": "帰無仮説の許容母数集合は制約なしの集合の部分集合なので \\(L(\\hat\\theta_0)\\leq L(\\hat\\theta)\\)。",
    "example": "制約による適合悪化が大きいほど \\(\\Lambda\\) は小さく、\\(-2\\log\\Lambda\\) は大きい。"
  },
  "T104": {
    "definition": "非復元単純無作為抽出では、分母 \\(N-1\\) の有限母集団分散 \\(S^2\\) を用いて \\(\\operatorname{Var}(\\bar X)=\\left(1-\\frac nN\\right)\\frac{S^2}{n}\\)。別の分散定義では \\((N-n)/(N-1)\\) の修正係数を使う。",
    "example": "\\(N=101,n=11\\) なら \\(\\frac{N-n}{N-1}=\\frac{90}{100}=0.9\\)。",
    "pitfalls": "標準誤差への修正は分散の修正係数の平方根 \\(\\sqrt{(N-n)/(N-1)}\\) を用いる。"
  }
}
with db:
    already=db.execute("SELECT 1 FROM metadata WHERE key='lecture_math_v1'").fetchone()
    if not already:
        for tid,fields in overrides.items():
            assert db.execute("SELECT 1 FROM lectures WHERE topic_id=?",(tid,)).fetchone(),tid
            for col,value in fields.items():
                assert col in {"intuition","definition","derivation","example","conditions","pitfalls","exam_criteria"}
                db.execute(f"UPDATE lectures SET {col}=? WHERE topic_id=?",(value,tid))
            db.execute("UPDATE lectures SET revised_at=?, review_status='draft' WHERE topic_id=?",(datetime.now(timezone.utc).isoformat(),tid))
        db.execute("INSERT INTO metadata(key,json_value) VALUES(?,?)",("lecture_math_v1",json.dumps({"topics":list(overrides),"version":1})))
        print("Migrated 15 SQLite lectures to explicit KaTeX delimiters")
    else:print("Math migration already applied, skipping")
db.close()
