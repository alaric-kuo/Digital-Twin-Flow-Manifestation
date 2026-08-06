# Digital Twin Flow Manifestation

## 高科技廠房冷卻系統的雙重流向時間動態 POC

> **Digital Twin = Digital Topology Manifesting Twin Information Flow**

本儲存庫展示一個可執行的數位孿生方法論概念驗證（Proof of Concept, POC）。  
案例以高科技廠房冷卻系統為背景，將物理風險、告警理解、授權形成與實體介入放入同一個時間動態模型，觀察兩股流向如何演化：

- **Risk Failure Flow**：風險失效流
- **Decision Response Flow**：決策響應流

POC提供兩個相互核對的實作：

| 實作 | 主要技術 | 用途 |
|---|---|---|
| Pure NumPy | 手寫密度矩陣、`Ry`、controlled-`Ry`、Kraus振幅耗散 | 透明的參考實作，可逐步檢查每一項矩陣運算 |
| Qiskit | `DensityMatrix`、`RYGate`、`CRYGate`、`Kraus`、`sample_counts` | 將相同語意模型建成Qiskit量子狀態與有限shots量測 |

兩個版本的精確密度矩陣結果應一致。Qiskit圖中的細微波動來自固定為8192 shots的有限量測取樣，不是另一套物理模型，也不是IBM Quantum硬體雜訊。

---

## 一、理論來源與實作對應

本Repo整合四篇既有文章的觀念，順序如下。

| 理論來源 | 原始問題 | 本POC的實作位置 |
|---|---|---|
| [I Ching Quantum Dynamics（IQD）](https://aj-consulting.net/iching-quantum-dynamics/) | 如何讓語意狀態、張力與作用關係進入可計算的量子動態系統 | 語意狀態轉成量子位元機率；作用關係轉成`Ry`、`CRY`與Kraus耗散通道 |
| [Architecture Graph Evolution（AGE）](https://aj-consulting.net/architecture-graph-evolution/) | 真實場域的痕跡、角色與視角如何逐步生成節點及關係 | 本POC先以人工定義的八個節點與作用關係，建立最小可運算圖場 |
| [Fractal Field Data Model Ontology（FFDM）](https://aj-consulting.net/fractal-field-data-model-ontology/) | 資料如何以痕跡、權重、時間與版本推動模型演化 | 每分鐘的外部輸入、狀態機率與觀測結果都寫入CSV，形成可追溯時間資料痕跡 |
| [Digital Topology](https://aj-consulting.net/digital-topology/) | 關係如何成為承載物理、資訊、風險、授權與實體作用的動態通道 | 風險失效流與決策響應流在同一拓撲與同一時間軸上被共同推演 |

**Digital Twin Flow Manifestation**不是第五篇理論來源，而是將上述四項觀念整合成可執行POC的Repo名稱。

---

## 二、核心命題

傳統數位孿生通常先呈現設備、模型、感測值與告警。本POC進一步追問：

> 異常被看見之後，是否已經形成理解、授權、資源與實體介入？

因此，數位孿生在此不只顯示物件狀態，也同時顯化兩股流：

```text
Risk Failure Flow
熱負載／冷卻劣化
→ 備援餘裕受壓
→ 電力限制
→ 製程熱風險
```

```text
Decision Response Flow
異常證據
→ 告警被理解
→ 授權形成
→ 實體介入
→ 備援壓力與製程熱風險耗散
```

主要觀測量定義如下：

| 觀測量 | 定義 | 說明 |
|---|---|---|
| Physical Risk | `P(q4 = 1)` | 製程熱風險本身的邊際機率 |
| Decision Response | `P(q7 = 1)` | 實體介入已形成的邊際機率 |
| Uncontained Risk | `P(q4 = 1, q7 = 0)` | 風險存在且介入尚未形成 |
| Contained / Avoided | `P(q4 = 0, q7 = 1)` | 介入已形成且製程熱風險未顯化 |

---

## 三、八個語意狀態

| Qubit | 程式欄位 | 中文語意 | 所屬流向 |
|---|---|---|---|
| `q0` | `thermal_load_high` | 熱負載偏高 | 外部擾動 |
| `q1` | `primary_cooling_degraded` | 主冷卻能力劣化 | 外部擾動 |
| `q2` | `backup_reserve_stressed` | 備援餘裕受壓 | Risk Failure Flow |
| `q3` | `power_constraint` | 電力／EMS約束 | Risk Failure Flow |
| `q4` | `process_thermal_risk` | 製程熱風險 | Risk Failure Flow |
| `q5` | `alarm_interpreted` | 告警已形成可理解意義 | Decision Response Flow |
| `q6` | `authorization_ready` | 授權已形成 | Decision Response Flow |
| `q7` | `intervention_executed` | 實體介入已執行 | Decision Response Flow |

初始語意機率 `p` 透過下式編碼為Y軸旋轉角：

```math
\theta = 2\arcsin\sqrt{p}
```

因此：

```math
P(q=1)=\sin^2\left(\frac{\theta}{2}\right)=p
```

---

## 四、時間軸與事件設定

模擬範圍為 `0–120` 分鐘，時間步長為 `1` 分鐘，共121個時間點。

| 事件 | 時間 | 模型意義 |
|---|---:|---|
| Heat rise | 8 min | 熱負載開始升高 |
| Cooling degradation | 15 min | 主冷卻能力開始劣化 |
| Detection | 25 min | 異常開始進入告警理解 |
| Fast authorization | 38 min | Accelerated-response開始形成授權 |
| Fast intervention | 50 min | Accelerated-response開始形成介入 |
| Delayed authorization | 75 min | Sensor-only延遲形成授權 |
| Delayed intervention | 95 min | Sensor-only延遲形成介入 |
| Heat-load easing | 85–105 min | 外部熱負載逐步回落 |

兩個情境使用相同的物理擾動與風險耦合，差異集中在決策響應能力。

| 參數 | Sensor-only | Accelerated-response |
|---|---:|---:|
| Detection | 25 min | 25 min |
| Authorization | 75 min | 38 min |
| Intervention | 95 min | 50 min |
| Alarm gain | 0.065 | 0.065 |
| Authorization gain | 0.018 | 0.100 |
| Intervention gain | 0.022 | 0.140 |
| Mitigation gain | 0.050 | 0.280 |

---

## 五、Qiskit代表性線路

以下線路圖由Qiskit單檔程式中的Matplotlib函式直接生成。它呈現的是**單一分鐘更新的代表性結構**，並未將121個時間步全部展開。

![Qiskit representative circuit](outputs/dtfm_qiskit_circuit_explainer.png)

線路由六個階段構成：

| 階段 | 實作 |
|---|---|
| 1. Initial probability encoding | 八個`RYGate`將初始語意機率編碼至`q0–q7` |
| 2. External disturbances | `q0`與`q1`接受隨時間變化的局部`Ry`擾動 |
| 3. Risk Failure Flow | `q0/q1 → q2 → q3/q4`以`CRYGate`表達物理與功能作用 |
| 4. Decision Response Flow | `q1/q2/q3 → q5 → q6 → q7`表達理解、授權與介入 |
| 5. Mitigation / Dissipation | `q7`形成後，對`q2`與`q4`施加Kraus振幅耗散 |
| 6. Measurement | 量測八個狀態並計算四項主要觀測量 |

---

## 六、NumPy時間響應

![NumPy time response](outputs/dtfm_numpy_time_response.png)

NumPy版本以精確密度矩陣顯示時間演化。第120分鐘結果如下：

| Scenario | Physical Risk | Decision Response | Uncontained Risk | Contained / Avoided | Trace |
|---|---:|---:|---:|---:|---:|
| Sensor-only | 0.2401 | 0.0040 | 0.2389 | 0.0028 | 1.000000 |
| Accelerated-response | 0.0134 | 0.3236 | 0.0071 | 0.3174 | 1.000000 |

結果顯示：

- **Sensor-only**雖然在第25分鐘開始取得異常資訊，但授權與介入延遲，物理風險持續升高。
- **Accelerated-response**在第38分鐘形成授權、第50分鐘形成實體介入後，物理風險於中段形成峰值，隨後透過耗散通道下降。
- `Trace = 1.000000`表示密度矩陣正規化在時間演化中維持。

---

## 七、Qiskit有限shots時間響應

![Qiskit time response](outputs/dtfm_qiskit_time_response.png)

Qiskit版本同時保留：

1. `exact`：由`DensityMatrix`直接計算的精確值。
2. `sampled`：由8192 shots取得的有限量測頻率。

第120分鐘結果如下：

| Scenario | Physical Risk sampled | Decision Response sampled | Physical Risk exact | Decision Response exact | Shots |
|---|---:|---:|---:|---:|---:|
| Sensor-only | 0.2405 | 0.0050 | 0.2401 | 0.0040 | 8192 |
| Accelerated-response | 0.0151 | 0.3208 | 0.0134 | 0.3236 | 8192 |

NumPy與Qiskit的`exact`值一致，這是預期結果，因為兩者實作的是同一套密度矩陣模型。Qiskit的`sampled`值在精確值附近波動，呈現有限shots的量測差異。

---

## 八、成果解讀

| 情境 | 資訊可見度 | 授權／介入 | 第120分鐘結果 | 方法論意義 |
|---|---|---|---|---|
| Sensor-only | 已形成告警理解 | 明顯延遲 | Physical Risk約0.24，Decision Response接近0 | 看見異常仍未取得改變實體狀態的作用能力 |
| Accelerated-response | 已形成告警理解 | 較早且較強 | Physical Risk降至約0.013，Decision Response升至約0.324 | 響應流穿過理解、授權與行動邊界後，開始改寫風險演化 |

POC的核心結果不是宣稱已預測特定工廠事故，而是展示：

> **資訊可見度與系統響應能力是兩件不同的事。**

當Decision Response Flow只停留在感測與告警，物理風險仍可能持續累積。只有當響應取得授權並形成實體介入，風險失效流的後續演化才開始改變。

---

## 九、Repository結構

```text
Digital-Twin-Flow-Manifestation/
├─ README.md
├─ requirements-numpy.txt
├─ requirements-qiskit.txt
├─ .gitignore
├─ scripts/
│  ├─ dtfm_cooling_numpy_standalone.py
│  └─ dtfm_cooling_qiskit_standalone.py
├─ outputs/
│  ├─ dtfm_numpy_time_response.png
│  ├─ dtfm_numpy_time_series.csv
│  ├─ dtfm_qiskit_circuit_explainer.png
│  ├─ dtfm_qiskit_time_response.png
│  └─ dtfm_qiskit_time_series.csv
└─ docs/
```

---

## 十、執行方式

### A. Pure NumPy

```powershell
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements-numpy.txt
python scripts/dtfm_cooling_numpy_standalone.py
```

輸出：

```text
outputs/dtfm_numpy_time_series.csv
outputs/dtfm_numpy_time_response.png
```

### B. Qiskit

```powershell
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements-qiskit.txt
python scripts/dtfm_cooling_qiskit_standalone.py
```

輸出：

```text
outputs/dtfm_qiskit_time_series.csv
outputs/dtfm_qiskit_time_response.png
outputs/dtfm_qiskit_circuit_explainer.png
```

macOS或Linux啟用虛擬環境時，改用：

```bash
source .venv/bin/activate
```

---

## 十一、CSV欄位

### NumPy CSV

| 欄位群組 | 內容 |
|---|---|
| Metadata | `engine`, `scenario`, `minute` |
| External inputs | `thermal_load_input`, `degradation_input` |
| Semantic states | `thermal_load_high`至`intervention_executed` |
| Observations | `physical_risk_probability`, `decision_response_probability`, `uncontained_risk_probability`, `contained_or_avoided_probability` |
| Validation | `trace` |

### Qiskit CSV

Qiskit CSV在相同欄位之外，另外保存：

| 欄位 | 說明 |
|---|---|
| `measurement_shots` | 每一時間點的量測次數，固定為8192 |
| `*_exact` | 由DensityMatrix直接計算的精確機率 |
| `*_sampled` | 由有限shots得到的量測頻率 |

---

## 十二、可重複性

本POC採用下列固定條件：

| 項目 | 設定 |
|---|---|
| Simulation duration | 120 min |
| Time step | 1 min |
| Qubits | 8 |
| Qiskit shots | 8192 |
| Random seed | 20260806 |
| Qiskit version | 2.5.1 |
| Main outputs | CSV + PNG |

在相同Python與套件版本下，Qiskit有限shots輸出可由固定seed重現。

---

## 十三、研究邊界

本Repo目前證明的是：

- 語意狀態可以轉成量子位元機率。
- 作用關係可以轉成旋轉、受控旋轉與耗散通道。
- 風險失效流與決策響應流可以放入同一個時間動態模型。
- NumPy參考實作與Qiskit精確密度矩陣實作可以相互核對。
- 有限shots可以形成可重複的量測輸出。

本Repo尚未證明：

- 目前參數已對真實高科技廠房完成工程校準。
- 這些數值可直接視為事故發生機率。
- 模型已整合實際BMS、EMS、工單、權限與事件紀錄。
- 量子硬體相較經典演算法已具有運算優勢。

---

## 十四、後續研究方向

1. 由真實BMS／EMS時間序列校準外部擾動與耦合參數。
2. 由事件報告、工單及權限紀錄校準Decision Response Flow。
3. 讓AGE與FFDM由真實痕跡生成節點、邊與版本，而非由程式預先固定。
4. 建立動態貝氏網路、常微分方程或Monte Carlo經典基準。
5. 比較不同介入時間、權限配置與備援策略的結果分布。
6. 評估更大狀態空間、電路深度、雜訊與量子硬體條件。
