# Digital Twin Flow Manifestation

## 高科技廠房冷卻系統的風險失效流與決策響應流時間動態 POC

**理論提出者與作者：** Dr. Han-Jung (Alaric) Kuo（郭瀚嶸 博士）  
**所屬機構：** A&J Management Consulting Limited Company（瀚菱管理顧問有限公司）  
**實作狀態：** 可重現方法論概念驗證（Reproducible Methodological POC）  
**文件版本：** README V2，2026-08-06

> **Digital Twin = Digital Topology Manifesting Twin Information Flow**

本Repository觀測的核心問題是：

> **當高科技廠房的冷卻風險開始傳播，決策響應流能否在風險失效流完成關鍵傳播之前，穿過告警理解、授權與實體介入節點，真正改變後續狀態？**

整體實作可以濃縮為一條鏈：

```text
語意狀態
→ 量子位元機率
→ 作用關係與動態拓樸
→ 風險失效流／決策響應流共同演化
→ 介入後耗散
→ 數位孿生顯化
```

本POC使用相同的物理擾動與風險耦合，比較兩種響應情境。第120分鐘的精確密度矩陣結果如下：

| 情境 | Physical Risk | Decision Response | Uncontained Risk | Contained / Avoided |
|---|---:|---:|---:|---:|
| Sensor-only | 0.2401 | 0.0040 | 0.2389 | 0.0028 |
| Accelerated-response | 0.0134 | 0.3236 | 0.0071 | 0.3174 |

在本POC固定參數下，Accelerated-response相較Sensor-only呈現：

- Physical Risk降低 **94.4%**
- Uncontained Risk降低 **97.0%**
- Decision Response為 **81.7倍**
- Contained / Avoided為 **114.6倍**

這些數字是模型內部的情境比較，用來顯示響應拓樸改變後的演化差異；尚未經真實廠房事故資料校準。

---

## 如何閱讀這個Repository

第一次閱讀時，可先讀：

- **第1章**：研究問題與主要發現
- **第5章**：Qiskit線路究竟實作了什麼
- **第6章**：NumPy精確時間演化如何解讀
- **第7章**：Qiskit有限shots結果如何驗證

若要理解完整方法論，可接著閱讀第2至第4章。  
若要重現、檢查邊界或延伸研究，可閱讀第9至第12章。

## 章節目錄

1. [從這裡開始：本POC在觀測什麼](#1-從這裡開始本poc在觀測什麼)
2. [理論來源、順序與目前實作範圍](#2-理論來源順序與目前實作範圍)
3. [語意狀態、量子位元與觀測量](#3-語意狀態量子位元與觀測量)
4. [時間動態、雙重流向與情境設定](#4-時間動態雙重流向與情境設定)
5. [Qiskit代表性線路的完整解讀](#5-qiskit代表性線路的完整解讀)
6. [NumPy精確時間響應的分段解讀](#6-numpy精確時間響應的分段解讀)
7. [Qiskit有限shots結果與數值驗證](#7-qiskit有限shots結果與數值驗證)
8. [跨情境發現與Digital Twin Flow Manifestation](#8-跨情境發現與digital-twin-flow-manifestation)
9. [雙實作架構與Repository結構](#9-雙實作架構與repository結構)
10. [重現方式、輸出檔案與資料欄位](#10-重現方式輸出檔案與資料欄位)
11. [目前證據、可檢查條件與研究邊界](#11-目前證據可檢查條件與研究邊界)
12. [研究定位、後續演化、引用與權利](#12-研究定位後續演化引用與權利)

---

# 1. 從這裡開始：本POC在觀測什麼

## 1.1 研究問題

高科技廠房的數位孿生可以持續收到溫度、流量、壓差、設備狀態、能源與告警資料。然而，資料進入平台，只代表系統已經留下可見訊號。它是否已形成可理解的異常、是否取得授權、是否已派出人員或切換設備，屬於另一條作用鏈。

本POC因此將兩股流放入同一個物理時間軸：

```text
Risk Failure Flow
熱負載偏高／主冷卻能力劣化
→ 備援餘裕受壓
→ 電力／EMS約束
→ 製程熱風險
```

```text
Decision Response Flow
異常證據
→ 告警形成可理解意義
→ 授權形成
→ 實體介入
→ 備援壓力與製程熱風險耗散
```

研究焦點落在兩股流的時間競逐。感測器可以比人更早看見狀態，平台也可以快速顯示告警；真正改變物理未來的節點，仍是授權與實體介入。

## 1.2 主要發現

本POC產生四項直接觀測：

第一，兩個情境在第25分鐘以前幾乎重合，因為它們接受相同外部擾動與相同風險耦合。差異主要由第38分鐘以後的授權與介入條件逐步形成。

第二，Accelerated-response的Decision Response在第64分鐘首次超過Physical Risk；Physical Risk仍因前期累積與傳播慣性，在第72分鐘達到約 `0.0491` 的峰值，之後才持續下降。這表示響應形成與物理風險反轉之間存在時間差。

第三，Sensor-only的告警理解於第120分鐘已達 `0.3800`，授權只有 `0.0487`，實體介入則只有 `0.0040`。系統看見了風險，治理鏈仍停滯在告警與授權之間。

第四，外部熱負載在第85至105分鐘逐步回落，Sensor-only的Physical Risk依然由第85分鐘的 `0.1058` 上升至第120分鐘的 `0.2401`。原因在於主冷卻劣化仍持續、備援壓力與電力約束已累積，而實體介入不足以改寫後續狀態。

## 1.3 為什麼建立這個Repository

四篇理論文章分別處理語意量子動態、圖資演化、場域資料模型與數位拓樸。本Repository把它們壓縮為一個可執行最小入口：

- 可看到語意如何轉成可計算狀態。
- 可看到關係如何轉成會改變狀態的作用通道。
- 可看到兩股流如何在物理時間中競逐。
- 可看到介入如何透過開放系統耗散改變後續風險。
- 可由NumPy與Qiskit兩個實作交叉檢查。

---

# 2. 理論來源、順序與目前實作範圍

本Repository只採用四個理論來源，順序固定如下：

> **IQD → AGE → FFDM → Digital Topology**

| 理論來源 | 核心角色 | 本POC的可執行位置 |
|---|---|---|
| [I Ching Quantum Dynamics（IQD）](https://aj-consulting.net/iching-quantum-dynamics/) | 將語意狀態、外部張力、作用關係與動態演化轉成量子可計算結構 | 語意狀態轉成量子位元機率；作用關係轉成`Ry`、`CRY`與耗散通道 |
| [Architecture Graph Evolution（AGE）](https://aj-consulting.net/architecture-graph-evolution/) | 由不同時間、角色與來源留下的痕跡，生成多視角節點與關係 | 本POC先以人工定義的八個節點與十條作用關係，建立最小可運算圖場 |
| [Fractal Field Data Model Ontology（FFDM）](https://aj-consulting.net/fractal-field-data-model-ontology/) | 使資料痕跡、權重、版本與不確定性持續推動模型演化 | 每分鐘外部輸入、八個狀態、四個觀測量及驗證值都寫入CSV |
| [Digital Topology](https://aj-consulting.net/digital-topology/) | 讓物理、功能、資訊、權限、責任與狀態轉移關係成為可承載作用的通道 | Risk Failure Flow與Decision Response Flow在同一拓樸與同一時間軸上共同演化 |

**Digital Twin Flow Manifestation**是上述四項觀念的整體實作名稱。

## 2.1 理論到程式的最短映射

```text
IQD
語意狀態 → 量子位元機率
作用關係 → 旋轉／受控旋轉／耗散通道

AGE
場域痕跡 → 節點與候選關係

FFDM
逐分鐘輸入、狀態與結果 → 可追溯資料痕跡

Digital Topology
關係 → 真正改變目標狀態分布的作用通道

Digital Twin Flow Manifestation
雙重流向的時間演化 → 圖表、CSV與可介入狀態
```

## 2.2 目前解析度

目前模型位於八個語意節點的系統層級。它還沒有進入冷凍機、泵、閥、冷卻塔、管路與控制器的實體元件拓樸，也沒有從BIM、P&ID、BMS點位表或工單自動生成節點與關係。

本版本先回答一個更基礎的問題：語意狀態與跨系統作用鏈，能否形成可重複執行的動態模型。

---

# 3. 語意狀態、量子位元與觀測量

## 3.1 八個語意狀態

| Qubit | 程式欄位 | 中文語意 | 系統角色 |
|---|---|---|---|
| `q0` | `thermal_load_high` | 熱負載偏高 | 外部擾動 |
| `q1` | `primary_cooling_degraded` | 主冷卻能力劣化 | 外部擾動 |
| `q2` | `backup_reserve_stressed` | 備援餘裕受壓 | 風險傳播中介 |
| `q3` | `power_constraint` | 電力／EMS約束 | 跨系統限制 |
| `q4` | `process_thermal_risk` | 製程熱風險 | 主要風險目標態 |
| `q5` | `alarm_interpreted` | 告警已形成可理解意義 | 資訊進入決策鏈 |
| `q6` | `authorization_ready` | 授權已形成 | 治理與權限節點 |
| `q7` | `intervention_executed` | 實體介入已執行 | 系統改變節點 |

每一個量子位元的 `P(q_i=1)` 表示該語意狀態在目前模型中的顯化機率。這些值是模型狀態權重，並非由歷史事故頻率估計而來。

## 3.2 初始機率編碼

初始語意機率 `p` 轉成Y軸旋轉角：

```math
\theta = 2\arcsin\sqrt{p}
```

因此：

```math
P(q=1)=\sin^2\left(\frac{\theta}{2}\right)=p
```

這使語意判斷可以進入密度矩陣、量子閘與開放系統通道的共同表示。

## 3.3 四個主要觀測量

| 觀測量 | 定義 | 解讀 |
|---|---|---|
| Physical Risk | `P(q4 = 1)` | 製程熱風險本身的邊際機率 |
| Decision Response | `P(q7 = 1)` | 實體介入已形成的邊際機率 |
| Uncontained Risk | `P(q4 = 1, q7 = 0)` | 風險存在且介入尚未形成 |
| Contained / Avoided | `P(q4 = 0, q7 = 1)` | 介入已形成且製程熱風險未顯化 |

Physical Risk與Decision Response是主圖使用的兩條曲線。Uncontained Risk與Contained / Avoided保留在CSV中，用來檢查風險與介入的聯合狀態。

---

# 4. 時間動態、雙重流向與情境設定

模擬範圍為 `0–120` 分鐘，時間步長為 `1` 分鐘，共執行121次狀態更新。

## 4.1 外部事件

| 事件 | 時間 | 模型作用 |
|---|---:|---|
| Heat rise | 8 min | `q0`開始接受熱負載旋轉 |
| Cooling degradation | 15 min | `q1`開始接受冷卻劣化旋轉 |
| Detection | 25 min | `q1/q2/q3 → q5`的告警理解通道開始作用 |
| Fast authorization | 38 min | Accelerated-response的`q5 → q6`開始作用 |
| Fast intervention | 50 min | Accelerated-response的`q6 → q7`開始作用 |
| Delayed authorization | 75 min | Sensor-only的`q5 → q6`延遲啟動 |
| Delayed intervention | 95 min | Sensor-only的`q6 → q7`延遲啟動 |
| Heat-load easing | 85–105 min | 外部熱負載逐步回落 |

## 4.2 風險作用拓樸

| Control | Target | 語意 |
|---|---|---|
| `q0` | `q2` | 熱負載提高備援壓力 |
| `q1` | `q2` | 冷卻劣化提高備援壓力 |
| `q2` | `q3` | 備援壓力推動電力／EMS約束 |
| `q2` | `q4` | 備援壓力推動製程熱風險 |
| `q3` | `q4` | 電力限制進一步推動製程熱風險 |

## 4.3 響應作用拓樸

| Control | Target | 語意 |
|---|---|---|
| `q1` | `q5` | 冷卻劣化證據進入告警理解 |
| `q2` | `q5` | 備援壓力證據進入告警理解 |
| `q3` | `q5` | 電力限制證據進入告警理解 |
| `q5` | `q6` | 已理解告警推動授權形成 |
| `q6` | `q7` | 已形成授權推動實體介入 |

## 4.4 兩種響應情境

| 參數 | Sensor-only | Accelerated-response |
|---|---:|---:|
| Detection | 25 min | 25 min |
| Authorization | 75 min | 38 min |
| Intervention | 95 min | 50 min |
| Alarm gain | 0.065 | 0.065 |
| Authorization gain | 0.018 | 0.100 |
| Intervention gain | 0.022 | 0.140 |
| Mitigation gain | 0.050 | 0.280 |

`Sensor-only`在本POC中代表感測與告警已存在，但治理與行動鏈條明顯延遲的系統；它仍保留很弱的晚期授權與介入，並非絕對零響應。

---

# 5. Qiskit代表性線路的完整解讀

下圖由Qiskit單檔程式中的Matplotlib函式直接生成：

![Qiskit representative circuit](outputs/dtfm_qiskit_circuit_explainer.png)

它呈現的是**單一分鐘更新的代表性運算結構**。實際模擬會將此更新重複121次，並依目前分鐘與情境條件，決定哪些響應閘開始作用。

## 5.1 六個運算階段

| 階段 | 數值實作 | 語意解讀 | 時間條件 |
|---|---|---|---|
| 1. Initial probability encoding | 八個`RYGate(θi)` | 將八個語意狀態的初始機率放入共同狀態空間 | 模擬開始時 |
| 2. External disturbances | `q0`與`q1`的局部`RYGate` | 熱負載與冷卻劣化作為外部張力持續推動狀態 | 依擾動函數每分鐘更新 |
| 3. Risk Failure Flow | 五組`CRYGate` | 風險沿備援、電力與製程關係向下傳播 | 每分鐘作用 |
| 4. Decision Response Flow | 五組`CRYGate` | 證據經理解、授權與介入形成響應鏈 | 依Detection、Authorization與Intervention門檻啟動 |
| 5. Mitigation / Dissipation | 作用於`q2`與`q4`的Kraus振幅耗散 | 實體介入形成後，備援壓力與製程熱風險逐步耗散 | 耗散強度隨`P(q7=1)`增加 |
| 6. Measurement | `DensityMatrix`精確觀測與`sample_counts`有限shots | 形成CSV與圖表中的exact及sampled觀測量 | 每分鐘輸出 |

## 5.2 `CRYGate`在本POC中的角色

受控旋轉表示一個條件式作用：

```text
控制狀態越顯化
→ 目標狀態接受的旋轉作用越具影響
→ 兩個狀態的聯合分布被改變
```

因此，Digital Topology中的邊在程式裡並非靜態連線。每一條邊都是會改變目標狀態分布的作用通道。

受控旋轉可能在量子狀態中形成關聯，特定狀態下也可能形成糾纏；本POC對工程語意的最低主張是**條件式作用與聯合狀態改變**，沒有把每一條工程關係直接宣稱為物理量子糾纏。

## 5.3 響應鏈的真正瓶頸

`q5`代表異常已形成可理解意義，`q6`代表授權已形成，`q7`代表實體介入已執行。這三個節點刻意分開，因為：

```text
看見告警
≠ 已經理解
≠ 已取得授權
≠ 已改變物理系統
```

Sensor-only的主要失效出現在`q5 → q6 → q7`。它可以累積很高的告警理解，介入機率依然接近零。

## 5.4 介入後耗散是開放系統更新

每分鐘演化完成響應鏈後，程式讀取目前密度矩陣中的：

```math
P(q_7=1)
```

並用它調整耗散參數：

```text
γ2(t) = mitigation_gain × P(q7=1)
γ4(t) = 1.40 × mitigation_gain × P(q7=1)
```

接著對`q2`與`q4`施加Kraus振幅耗散通道。

這是一個**量子狀態演化加上經典回饋參數更新的混合機制**。耗散強度取決於當下狀態的邊際機率，因此目前實作屬於狀態相依的開放系統POC，尚未編譯為可直接部署至量子硬體的純固定電路。

## 5.5 exact觀測與sampled觀測彼此分離

Qiskit版本的後續DensityMatrix演化使用精確狀態。`sample_counts`只負責在每分鐘產生8192 shots的觀測頻率：

```text
DensityMatrix exact state
├─ 繼續進入下一分鐘演化
└─ sample_counts → sampled CSV／sampled圖線
```

因此，有限shots波動不會被送回下一時間步，也不會把取樣噪聲累積成模型動態。

---

# 6. NumPy精確時間響應的分段解讀

![NumPy time response](outputs/dtfm_numpy_time_response.png)

NumPy版本以手寫密度矩陣、局部旋轉、受控旋轉與Kraus通道，提供完全透明的精確參考實作。

## 6.1 關鍵時間點

| Minute | Sensor-only Risk | Sensor-only Response | Accelerated Risk | Accelerated Response | 主要意義 |
|---:|---:|---:|---:|---:|---|
| 25 | 0.0094 | 0.0010 | 0.0094 | 0.0010 | Detection啟動，兩情境仍重合 |
| 38 | 0.0156 | 0.0010 | 0.0155 | 0.0010 | Accelerated授權通道開始作用 |
| 50 | 0.0267 | 0.0010 | 0.0263 | 0.0012 | Accelerated介入通道開始作用 |
| 64 | 0.0496 | 0.0010 | 0.0448 | 0.0457 | Accelerated Response首次超過Risk |
| 72 | 0.0682 | 0.0010 | 0.0491 | 0.0993 | Accelerated Risk達到峰值 |
| 85 | 0.1058 | 0.0010 | 0.0410 | 0.1546 | 熱負載開始回落 |
| 95 | 0.1399 | 0.0010 | 0.0332 | 0.1685 | Sensor-only介入通道才開始作用 |
| 120 | 0.2401 | 0.0040 | 0.0134 | 0.3236 | 最終狀態形成明顯分岔 |

## 6.2 0–25分鐘：共同物理前史

兩個情境共用相同的初始狀態、熱負載、冷卻劣化與Risk Failure Flow。第25分鐘時，Physical Risk都為 `0.0094`。

這一段建立了比較基線：後續差異主要來自響應鏈的時間與強度，並非替Accelerated-response安排較輕的物理擾動。

## 6.3 25–50分鐘：看見異常仍未等於改變系統

Detection於第25分鐘啟動，告警理解開始累積。Accelerated-response於第38分鐘開啟授權通道，但第50分鐘的：

- `authorization_ready = 0.0225`
- `intervention_executed = 0.0012`
- `physical_risk = 0.0263`

授權通道剛開始形成，尚未立即造成風險下降。這段演化保留了治理動作與物理效果之間的時間差。

## 6.4 50–72分鐘：響應穿透後，風險仍有慣性

第50分鐘後，Accelerated-response的介入開始增長。第64分鐘：

```text
Decision Response = 0.0457
Physical Risk     = 0.0448
```

響應首次超過風險。Physical Risk仍在第72分鐘達到 `0.0491` 的峰值，顯示先前已形成的備援壓力與跨系統傳播不會在介入出現的同一分鐘立即消失。

Uncontained Risk更早在第 `61` 分鐘達到峰值 `0.0342`，之後隨介入形成開始下降。

## 6.5 72–120分鐘：兩種治理拓樸形成不同未來

Accelerated-response在第120分鐘形成：

| 狀態 | 機率 |
|---|---:|
| Alarm interpreted | 0.3749 |
| Authorization ready | 0.3341 |
| Intervention executed | 0.3236 |
| Physical Risk | 0.0134 |
| Contained / Avoided | 0.3174 |

Sensor-only在同一分鐘形成：

| 狀態 | 機率 |
|---|---:|
| Alarm interpreted | 0.3800 |
| Authorization ready | 0.0487 |
| Intervention executed | 0.0040 |
| Physical Risk | 0.2401 |
| Uncontained Risk | 0.2389 |

兩者都能看見異常；只有Accelerated-response形成足以推動耗散的介入強度。

## 6.6 為何熱負載下降後，Sensor-only風險仍上升

外部熱負載於第85分鐘開始回落，但主冷卻劣化保持高位。Sensor-only的備援壓力由第85分鐘的 `0.2781` 增至第120分鐘的 `0.3906`，電力／EMS約束也由 `0.0390` 增至 `0.0886`。

這代表系統狀態具有累積與路徑依賴。單一外部輸入緩解，未必足以逆轉已經進入備援、電力與製程風險鏈的狀態。

---

# 7. Qiskit有限shots結果與數值驗證

![Qiskit time response](outputs/dtfm_qiskit_time_response.png)

Qiskit版本同時輸出：

- `exact`：由`DensityMatrix`直接計算。
- `sampled`：由每個時間點8192 shots取得。

## 7.1 第120分鐘結果

| 情境 | Physical Risk sampled | Physical Risk exact | Decision Response sampled | Decision Response exact |
|---|---:|---:|---:|---:|
| Sensor-only | 0.2405 | 0.2401 | 0.0050 | 0.0040 |
| Accelerated-response | 0.0151 | 0.0134 | 0.3208 | 0.3236 |

第120分鐘的絕對差異為：

| 情境 | Physical Risk sampled − exact | Decision Response sampled − exact |
|---|---:|---:|
| Sensor-only | +0.0004 | +0.0010 |
| Accelerated-response | +0.0018 | -0.0028 |

## 7.2 全時間序列的取樣偏差

| 情境 | 觀測量 | Mean Absolute Error | Maximum Absolute Error |
|---|---|---:|---:|
| Sensor-only | Physical Risk | 0.00161 | 0.01187 |
| Sensor-only | Decision Response | 0.00030 | 0.00108 |
| Accelerated-response | Physical Risk | 0.00132 | 0.00572 |
| Accelerated-response | Decision Response | 0.00186 | 0.01171 |

這些偏差符合有限shots觀測會在exact值附近波動的預期。固定seed使本Repository在相同Python與Qiskit版本下可以重現相同取樣序列。

## 7.3 NumPy與Qiskit exact一致的意義

Pure NumPy與Qiskit共享：

- 相同初始機率
- 相同旋轉角
- 相同受控旋轉拓樸
- 相同事件時間
- 相同Kraus耗散參數
- 相同觀測量定義

兩者的exact結果一致，說明手寫密度矩陣運算與Qiskit框架實作對應成功。這是一項交叉驗證，並非兩套獨立物理模型產生巧合相同的預測。

## 7.4 shots代表什麼

8192 shots代表從目前DensityMatrix的量測分布中進行8192次有限取樣。它目前沒有包含：

- IBM Quantum硬體雜訊
- 讀出錯誤模型
- 閘誤差
- 退相干時間
- 編譯至特定硬體拓樸的限制

因此，Qiskit sampled曲線展示的是有限觀測頻率，不是量子硬體實驗結果。

---

# 8. 跨情境發現與Digital Twin Flow Manifestation

## 8.1 固定物理擾動下的響應比較

兩個情境共用相同外部擾動與Risk Failure Flow，只調整授權、介入時間與響應強度。這形成一個模型內部的反事實比較：

```text
相同風險前史
+ 不同Decision Response Flow
→ 不同後續狀態
```

在本POC設定下，響應拓樸改變後，Physical Risk降低 `94.4%`，Uncontained Risk降低 `97.0%`。

這個百分比表達的是固定模型假設下的情境差異，不能直接外推為真實工廠導入系統後的風險降低率。

## 8.2 資訊可見度與作用能力

Sensor-only最後具有很高的告警理解，實體介入仍接近零。這使下列差異可以被直接觀測：

| 層次 | 系統問題 |
|---|---|
| Data visibility | 資料是否已進入平台 |
| Alarm interpretation | 異常是否已形成可理解意義 |
| Authorization | 是否有角色能批准行動 |
| Physical intervention | 設備、人員或控制是否真的改變系統 |
| State evolution | 介入後的風險路徑是否已被改寫 |

數位孿生若只到Data visibility與Alarm interpretation，主要完成的是看見。Digital Twin Flow Manifestation要求孿生同時顯化：

- 風險正在往哪裡傳播
- 響應目前停在哪一個節點
- 哪一個權限或行動邊界正在造成延遲
- 介入是否已足以改變下一個時間步

## 8.3 Twin Information Flow的最小判準

本POC將Twin Information Flow拆成：

```text
Twin Information Flow
= Risk Failure Flow
+ Decision Response Flow
```

最小治理判準為：

> **Decision Response Flow必須在Risk Failure Flow完成關鍵傳播之前，到達能改變系統狀態的節點。**

在本案例中，這個節點是`q7 intervention_executed`。`q5 alarm_interpreted`仍位於資訊與理解層，`q6 authorization_ready`位於治理準備層；只有`q7`開始推動實體耗散。

## 8.4 本POC對數位孿生的推進

本Repository沒有以3D模型作為必要起點。八個節點同時包含：

- 物理狀態
- 功能風險
- 能源約束
- 資訊理解
- 權限形成
- 實體行動

這展示了一個更底層的數位孿生入口：先建立能承載作用的Digital Topology，再選擇圖表、BIM、GIS、3D或營運介面顯化其結果。

---

# 9. 雙實作架構與Repository結構

## 9.1 兩個實作的分工

| 實作 | 技術 | 角色 |
|---|---|---|
| Pure NumPy | 手寫Density Matrix、`Ry`、controlled-`Ry`與Kraus通道 | 透明參考引擎；可逐步檢查索引、矩陣與每分鐘更新 |
| Qiskit | `DensityMatrix`、`RYGate`、`CRYGate`、`Kraus`、`sample_counts` | 標準量子資訊框架實作；同時輸出exact與sampled觀測 |

這不是「經典模型對量子模型」的比較。NumPy版本同樣實作量子密度矩陣動態，只是未依賴Qiskit套件。

## 9.2 端到端資料流

```text
1. 初始化八個語意機率
2. 建立DensityMatrix
3. 讀取目前分鐘的熱負載與冷卻劣化
4. 套用局部Ry外部擾動
5. 套用Risk Failure Flow的CRY作用
6. 依時間門檻套用Decision Response Flow
7. 讀取P(q7=1)
8. 對q2與q4套用狀態相依Kraus耗散
9. 計算四項觀測量
10. 寫入CSV
11. 重複至第120分鐘
12. 產生時間響應圖與Qiskit線路解說圖
```

## 9.3 Repository結構

```text
Digital-Twin-Flow-Manifestation/
├─ README.md
├─ CITATION.cff
├─ CHANGELOG.md
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
   └─ MODEL_NOTES.md
```

---

# 10. 重現方式、輸出檔案與資料欄位

## 10.1 Pure NumPy

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

## 10.2 Qiskit

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

macOS或Linux使用：

```bash
source .venv/bin/activate
```

## 10.3 固定重現條件

| 項目 | 設定 |
|---|---|
| Simulation duration | 120 min |
| Time step | 1 min |
| Qubits | 8 |
| Qiskit shots | 8192 |
| Random seed | 20260806 |
| Qiskit version | 2.5.1 |
| Main outputs | CSV + PNG |

## 10.4 NumPy CSV欄位

| 欄位群組 | 內容 |
|---|---|
| Metadata | `engine`, `scenario`, `minute` |
| External inputs | `thermal_load_input`, `degradation_input` |
| Semantic states | `thermal_load_high`至`intervention_executed` |
| Main observations | `physical_risk_probability`, `decision_response_probability` |
| Joint observations | `uncontained_risk_probability`, `contained_or_avoided_probability` |
| Validation | `trace` |

## 10.5 Qiskit CSV附加欄位

| 欄位 | 說明 |
|---|---|
| `measurement_shots` | 每一時間點的取樣次數 |
| `*_exact` | 由DensityMatrix直接計算 |
| `*_sampled` | 由有限shots得到的觀測頻率 |

## 10.6 最低驗證條件

每次重跑至少應檢查：

1. 每一列`trace`接近`1.0`。
2. 所有觀測量位於`[0,1]`。
3. 每個情境都有121列資料。
4. NumPy與Qiskit的exact結果在浮點數誤差範圍內一致。
5. 固定seed時，Qiskit sampled結果可重現。
6. 三張PNG與兩份CSV都成功產生。

---

# 11. 目前證據、可檢查條件與研究邊界

## 11.1 已建立的內容

| 層次 | 本版本已建立 |
|---|---|
| IQD | 語意機率編碼、局部旋轉、受控旋轉與耗散通道 |
| AGE | 八節點、十條作用關係的最小多視角圖場 |
| FFDM | 121個時間點的輸入、狀態、觀測與驗證痕跡 |
| Digital Topology | 物理、功能、資訊、授權與行動關係共同進入動態拓樸 |
| Digital Twin Flow Manifestation | Risk Failure Flow與Decision Response Flow共同顯化 |
| 數值驗證 | NumPy與Qiskit exact交叉核對；Qiskit有限shots重現 |

## 11.2 尚未建立的內容

| 項目 | 目前狀態 |
|---|---|
| 真實BMS／EMS校準 | 尚未實作 |
| 實際冷凍機、泵、閥與管網拓樸 | 尚未實作 |
| BIM／P&ID／點位表自動生成節點 | 尚未實作 |
| 工單、角色、權限與責任資料串接 | 尚未實作 |
| 歷史事故機率估計 | 尚未實作 |
| 即時資料同化 | 尚未實作 |
| 經典ODE、動態貝氏網路或Monte Carlo基準 | 尚未實作 |
| 真實量子硬體執行 | 尚未實作 |
| 量子計算優勢 | 尚未證明 |

## 11.3 機率的正確定位

目前的機率表示模型狀態的顯化權重。它們不能直接讀成：

```text
某高科技廠房有24.01%的事故機率
```

要進入工程預測，仍需：

- 定義可觀測事件與標籤
- 對真實時間序列校準
- 建立先驗與不確定性
- 進行樣本外驗證
- 比較替代模型
- 評估決策損失與誤報成本

## 11.4 狀態相依耗散的研究邊界

目前耗散參數由`P(q7=1)`決定。這形成混合式、狀態相依的更新規則，適合表達「介入越形成，緩解越強」的概念。

後續可檢查三種替代實作：

1. 使用外部經典控制器直接設定耗散參數。
2. 將介入結果作為量測後的條件通道。
3. 建立包含環境與控制節點的更大CPTP通道，使整體演化維持線性量子操作表示。

## 11.5 可被反駁與檢查的條件

本POC不是只靠圖形敘事。下列條件可以直接檢查：

- 若NumPy與Qiskit exact無法一致，代表實作存在索引、位元順序或通道錯誤。
- 若`trace`偏離1，代表密度矩陣正規化失效。
- 若移除`q5 → q6 → q7`仍得到相同耗散，代表Decision Response Flow沒有真正進入模型。
- 若更換授權或介入時間不改變結果，代表時間拓樸沒有作用。
- 若真實資料校準後，響應參數無法解釋或改善樣本外結果，則目前語意映射需要修正。
- 若簡單經典模型在相同狀態與資料下更穩定、更可校準，量子表達的新增價值必須重新評估。

---

# 12. 研究定位、後續演化、引用與權利

## 12.1 研究定位

本Repository建立了一條可執行的方法論橋梁：

```text
IQD語意量子動態
→ AGE多視角節點與關係
→ FFDM逐時間資料痕跡
→ Digital Topology作用通道
→ Twin Information Flow雙重流向
→ Digital Twin Flow Manifestation
```

它的主要價值在於把數位孿生從物件與資料的映射，推進到跨系統作用、治理延遲與實體介入的共同演化。

本POC同時揭露一個實務上容易被平台畫面遮蔽的問題：

> **告警已經出現，不代表系統已經取得改變現實的能力。**

## 12.2 下一階段

1. 由真實BMS／EMS時間序列校準外部擾動。
2. 由P&ID、BIM、點位表與設備清冊生成AGE節點及關係。
3. 由工單、事件報告、角色與權限紀錄校準Decision Response Flow。
4. 將FFDM擴充為具有資料來源、版本、權重與不確定性的動態資料場。
5. 建立ODE、動態貝氏網路與Monte Carlo基準。
6. 比較不同介入時間、授權拓樸與備援策略。
7. 將目前八節點模型擴充至設備、子系統、廠務系統與場域多尺度拓樸。
8. 評估量子電路深度、雜訊、硬體拓樸與可能的運算優勢條件。

## 12.3 理論文章

- [I Ching Quantum Dynamics](https://aj-consulting.net/iching-quantum-dynamics/)
- [Architecture Graph Evolution](https://aj-consulting.net/architecture-graph-evolution/)
- [Fractal Field Data Model Ontology](https://aj-consulting.net/fractal-field-data-model-ontology/)
- [Digital Topology](https://aj-consulting.net/digital-topology/)

## 12.4 建議引用

```text
Kuo, Han-Jung (Alaric). (2026).
Digital Twin Flow Manifestation:
Cooling-System Risk Failure and Decision Response Time-Dynamics PoC.
A&J Management Consulting Limited Company.
https://github.com/alaric-kuo/Digital-Twin-Flow-Manifestation
```

正式機器可讀引用格式收錄於[`CITATION.cff`](CITATION.cff)。

## 12.5 權利與作者資訊

Copyright © 2026 A&J Management Consulting Limited Company. All rights reserved.

本Repository以科學檢視、引用與可重現性評估為目的公開。除非另有書面授權，公開存取不代表放棄程式、圖表、文件、理論或衍生成果的權利。

**理論提出者與通訊作者：** Dr. Han-Jung (Alaric) Kuo（郭瀚嶸 博士）  
**所屬機構：** A&J Management Consulting Limited Company（瀚菱管理顧問有限公司）  
**所在地：** 臺灣
