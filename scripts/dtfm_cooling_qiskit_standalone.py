"""
Digital Twin Flow Manifestation（DTFM）
高科技廠房冷卻系統時間動態 POC：Qiskit 單檔版

本程式與純 NumPy 版本使用相同的：
- 八個語意狀態
- 外部擾動時間表
- Risk Failure Flow 耦合
- Decision Response Flow 耦合
- 介入後耗散參數
- CSV 欄位與圖表定義

差異在於本版本使用 Qiskit 的：
- DensityMatrix
- RYGate
- CRYGate
- Kraus

輸出檔案：
- dtfm_qiskit_time_series.csv
- dtfm_qiskit_time_response.png
- dtfm_qiskit_circuit_explainer.png

建議環境：
    python -m venv .venv

Windows：
    .venv\\Scripts\\activate

macOS / Linux：
    source .venv/bin/activate

安裝：
    pip install numpy matplotlib qiskit==2.5.1

執行：
    python scripts/dtfm_cooling_qiskit_standalone.py

方法論對應：
- I Ching Quantum Dynamics（IQD）：
  語意狀態轉成量子位元機率，作用關係轉成旋轉、
  受控旋轉與耗散通道。
- Architecture Graph Evolution（AGE）：
  本 POC 先以人工定義的節點與作用關係，作為多視角圖場的最小實作。
- Fractal Field Data Model Ontology（FFDM）：
  每一分鐘的外部輸入、狀態與結果都保存為可追溯的資料痕跡。
- Digital Topology：
  關係被實作為能改變狀態分布的作用通道，
  使風險失效流與決策響應流能在同一拓撲中推演。

整體 Repo：
- Digital Twin Flow Manifestation
  將上述四項觀念整合為數位孿生方法論 POC。

研究邊界：
- 這是方法論 POC，不是經 BMS／EMS 或事故資料校準的工程預測器。
- 模型參數用來呈現時間演化與雙重流向，不代表特定工廠的實際機率。
- 本程式使用 Qiskit 的本機密度矩陣演化，不會連接 IBM Quantum 硬體。
- 能以量子形式表示，不等於已證明量子硬體具有運算優勢。
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

try:
    import numpy as np
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit(
        "缺少 NumPy 或 Matplotlib。請先執行："
        "pip install numpy matplotlib qiskit==2.5.1"
    ) from exc

try:
    from qiskit.circuit.library import CRYGate, RYGate
    from qiskit.quantum_info import DensityMatrix, Kraus
    QISKIT_IMPORT_ERROR = None
except ImportError as exc:
    # 線路解說圖只依賴 Matplotlib，因此仍可先產生。
    # 真正進入密度矩陣模擬前，main() 會再檢查 Qiskit。
    QISKIT_IMPORT_ERROR = exc


# =============================================================================
# 一、基本設定
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "dtfm_qiskit_time_series.csv"
PNG_PATH = OUTPUT_DIR / "dtfm_qiskit_time_response.png"
CIRCUIT_PNG_PATH = OUTPUT_DIR / "dtfm_qiskit_circuit_explainer.png"

NUM_QUBITS = 8
DURATION_MIN = 120
DT_MIN = 1.0

# 每個時間點進行有限次量測取樣。
# 這會產生可重現的 shot noise，但不是 IBM Quantum 硬體雜訊。
MEASUREMENT_SHOTS = 8192
BASE_RANDOM_SEED = 20260806

QUBIT_NAMES: List[str] = [
    "thermal_load_high",          # q0：熱負載偏高
    "primary_cooling_degraded",   # q1：主冷卻能力劣化
    "backup_reserve_stressed",    # q2：備援餘裕受壓
    "power_constraint",           # q3：電力／EMS 約束
    "process_thermal_risk",       # q4：製程熱風險
    "alarm_interpreted",          # q5：告警已形成可理解意義
    "authorization_ready",        # q6：授權已形成
    "intervention_executed",      # q7：實體介入已執行
]


# =============================================================================
# 二、兩種響應情境
# =============================================================================

SCENARIOS: List[Dict[str, float | int | str]] = [
    {
        "name": "Sensor-only",
        "detection_min": 25,
        "authorization_min": 75,
        "intervention_min": 95,
        "alarm_gain": 0.065,
        "authorization_gain": 0.018,
        "intervention_gain": 0.022,
        "mitigation_gain": 0.050,
    },
    {
        "name": "Accelerated-response",
        "detection_min": 25,
        "authorization_min": 38,
        "intervention_min": 50,
        "alarm_gain": 0.065,
        "authorization_gain": 0.100,
        "intervention_gain": 0.140,
        "mitigation_gain": 0.280,
    },
]


# =============================================================================
# 三、外部擾動的時間函數
# =============================================================================

def ramp_profile(
    minute: float,
    start: float,
    rise: float,
    end: float | None = None,
    fall: float = 20.0,
) -> float:
    """建立 0～1 之間的分段線性擾動。"""
    if minute < start:
        return 0.0

    if minute < start + rise:
        return (minute - start) / rise

    if end is None or minute < end:
        return 1.0

    if minute < end + fall:
        return max(0.0, 1.0 - (minute - end) / fall)

    return 0.0


def thermal_load_profile(minute: float) -> float:
    """第 8 分鐘開始升高，第 85 分鐘開始緩解。"""
    return ramp_profile(minute, start=8, rise=12, end=85, fall=20)


def degradation_profile(minute: float) -> float:
    """第 15 分鐘開始劣化，第 35 分鐘達到完整劣化。"""
    return ramp_profile(minute, start=15, rise=20, end=None)


# =============================================================================
# 四、Qiskit 狀態編碼與量子通道
# =============================================================================

def probability_to_ry_angle(probability: float) -> float:
    """
    將語意證據 p∈[0,1] 轉成 Ry 旋轉角：

        theta = 2 asin(sqrt(p))
    """
    p = float(np.clip(probability, 0.0, 1.0))
    return 2.0 * math.asin(math.sqrt(p))


def initial_probabilities() -> List[float]:
    """模擬開始時，各語意狀態的背景機率。"""
    return [
        0.020,
        0.015,
        0.010,
        0.010,
        0.005,
        0.005,
        0.002,
        0.001,
    ]


def initialise_density_matrix() -> DensityMatrix:
    """
    由 |00000000> 開始，
    以 RYGate 將背景機率編碼至八個量子位元。
    """
    density = DensityMatrix.from_label("0" * NUM_QUBITS)

    for qubit, probability in enumerate(initial_probabilities()):
        density = density.evolve(
            RYGate(probability_to_ry_angle(probability)),
            qargs=[qubit],
        )

    return density


def amplitude_damping_channel(gamma: float) -> Kraus:
    """
    建立振幅耗散 Kraus 通道：

        E(rho) = K0 rho K0† + K1 rho K1†
    """
    gamma = float(np.clip(gamma, 0.0, 1.0))

    k0 = np.array(
        [[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]],
        dtype=complex,
    )
    k1 = np.array(
        [[0.0, math.sqrt(gamma)], [0.0, 0.0]],
        dtype=complex,
    )

    return Kraus([k0, k1])


# =============================================================================
# 五、狀態觀測
# =============================================================================

def marginal_probability(
    density: DensityMatrix,
    qubit: int,
) -> float:
    """回傳指定量子位元量測為 1 的邊際機率。"""
    diagonal = np.real(np.diag(density.data))

    return float(
        sum(
            diagonal[index]
            for index in range(len(diagonal))
            if ((index >> qubit) & 1) == 1
        )
    )


def joint_probability(
    density: DensityMatrix,
    conditions: Mapping[int, int],
) -> float:
    """回傳多個量子位元同時符合指定條件的聯合機率。"""
    diagonal = np.real(np.diag(density.data))

    return float(
        sum(
            diagonal[index]
            for index in range(len(diagonal))
            if all(
                ((index >> qubit) & 1) == value
                for qubit, value in conditions.items()
            )
        )
    )


def sampled_marginal_probability(
    counts: Mapping[str, int],
    qubit: int,
    shots: int,
) -> float:
    """
    由 Qiskit sample_counts 的 bitstring 計算 P(q=1)。

    Qiskit 顯示 bitstring 時，最右側是 q0，
    因此 q_k 對應 bits[-1-k]。
    """
    hits = 0

    for bits, count in counts.items():
        if bits[-1 - qubit] == "1":
            hits += int(count)

    return hits / shots


def sampled_joint_probability(
    counts: Mapping[str, int],
    conditions: Mapping[int, int],
    shots: int,
) -> float:
    """由有限 shots 計算聯合事件的觀測頻率。"""
    hits = 0

    for bits, count in counts.items():
        matched = all(
            int(bits[-1 - qubit]) == value
            for qubit, value in conditions.items()
        )
        if matched:
            hits += int(count)

    return hits / shots


def make_observation_row(
    scenario_name: str,
    scenario_index: int,
    minute: int,
    density: DensityMatrix,
) -> Dict[str, float | int | str]:
    """將目前 Qiskit DensityMatrix 轉成一列 CSV 紀錄。"""
    row: Dict[str, float | int | str] = {
        "engine": "Qiskit DensityMatrix",
        "scenario": scenario_name,
        "minute": minute,
        "thermal_load_input": thermal_load_profile(minute),
        "degradation_input": degradation_profile(minute),
    }

    for qubit, name in enumerate(QUBIT_NAMES):
        row[name] = marginal_probability(density, qubit)

    # -------------------------------------------------------------
    # 精確值：由 DensityMatrix 直接計算。
    # 這一組數值理論上應與純 NumPy 參考實作一致。
    # -------------------------------------------------------------
    row["physical_risk_probability_exact"] = marginal_probability(
        density,
        4,
    )
    row["decision_response_probability_exact"] = marginal_probability(
        density,
        7,
    )
    row["uncontained_risk_probability_exact"] = joint_probability(
        density,
        {4: 1, 7: 0},
    )
    row["contained_or_avoided_probability_exact"] = joint_probability(
        density,
        {4: 0, 7: 1},
    )

    # -------------------------------------------------------------
    # 有限 shots 觀測值：
    # sample_counts 不改變 DensityMatrix，只從目前機率分布取樣。
    # 固定 seed 讓本機重跑時可以重現。
    # -------------------------------------------------------------
    density.seed(
        BASE_RANDOM_SEED
        + scenario_index * 10000
        + minute
    )
    counts = density.sample_counts(
        shots=MEASUREMENT_SHOTS
    )

    row["measurement_shots"] = MEASUREMENT_SHOTS
    row["physical_risk_probability_sampled"] = sampled_marginal_probability(
        counts,
        qubit=4,
        shots=MEASUREMENT_SHOTS,
    )
    row["decision_response_probability_sampled"] = sampled_marginal_probability(
        counts,
        qubit=7,
        shots=MEASUREMENT_SHOTS,
    )
    row["uncontained_risk_probability_sampled"] = sampled_joint_probability(
        counts,
        conditions={4: 1, 7: 0},
        shots=MEASUREMENT_SHOTS,
    )
    row["contained_or_avoided_probability_sampled"] = sampled_joint_probability(
        counts,
        conditions={4: 0, 7: 1},
        shots=MEASUREMENT_SHOTS,
    )

    row["trace"] = float(np.real(np.trace(density.data)))

    return row


# =============================================================================
# 六、每分鐘的 Qiskit 動態演化
# =============================================================================

def evolve_one_minute(
    density: DensityMatrix,
    minute: int,
    scenario: Mapping[str, float | int | str],
) -> DensityMatrix:
    """
    執行一分鐘的完整演化。

    RYGate：
        外部熱負載與冷卻劣化。

    CRYGate：
        風險傳播、告警理解、授權與介入。

    Kraus：
        介入後的備援壓力與製程熱風險耗散。
    """
    load = thermal_load_profile(minute)
    degradation = degradation_profile(minute)

    # -----------------------------------------------------------------
    # 1. 外部擾動
    # -----------------------------------------------------------------
    density = density.evolve(
        RYGate(0.030 * load * DT_MIN),
        qargs=[0],
    )
    density = density.evolve(
        RYGate(0.026 * degradation * DT_MIN),
        qargs=[1],
    )

    # -----------------------------------------------------------------
    # 2. Risk Failure Flow
    # -----------------------------------------------------------------
    risk_couplings: Sequence[Tuple[int, int, float]] = [
        (0, 2, 0.025),
        (1, 2, 0.035),
        (2, 3, 0.018),
        (2, 4, 0.032),
        (3, 4, 0.025),
    ]

    for control, target, angle_per_min in risk_couplings:
        density = density.evolve(
            CRYGate(angle_per_min * DT_MIN),
            qargs=[control, target],
        )

    # -----------------------------------------------------------------
    # 3. 異常資料形成可理解的告警
    # -----------------------------------------------------------------
    if minute >= int(scenario["detection_min"]):
        alarm_gain = float(scenario["alarm_gain"])
        response_couplings: Sequence[Tuple[int, int, float]] = [
            (1, 5, alarm_gain),
            (2, 5, alarm_gain * 0.85),
            (3, 5, alarm_gain * 0.65),
        ]

        for control, target, angle_per_min in response_couplings:
            density = density.evolve(
                CRYGate(angle_per_min * DT_MIN),
                qargs=[control, target],
            )

    # -----------------------------------------------------------------
    # 4. 告警理解 -> 授權 -> 實體介入
    # -----------------------------------------------------------------
    if minute >= int(scenario["authorization_min"]):
        density = density.evolve(
            CRYGate(
                float(scenario["authorization_gain"]) * DT_MIN
            ),
            qargs=[5, 6],
        )

    if minute >= int(scenario["intervention_min"]):
        density = density.evolve(
            CRYGate(
                float(scenario["intervention_gain"]) * DT_MIN
            ),
            qargs=[6, 7],
        )

    # -----------------------------------------------------------------
    # 5. 介入後的實體耗散
    # -----------------------------------------------------------------
    intervention_probability = marginal_probability(
        density,
        7,
    )
    mitigation_gain = float(scenario["mitigation_gain"])

    density = density.evolve(
        amplitude_damping_channel(
            mitigation_gain * intervention_probability
        ),
        qargs=[2],
    )
    density = density.evolve(
        amplitude_damping_channel(
            mitigation_gain * 1.40 * intervention_probability
        ),
        qargs=[4],
    )

    if minute > 90:
        density = density.evolve(
            amplitude_damping_channel(0.010),
            qargs=[0],
        )

    return density


# =============================================================================
# 七、模擬、輸出 CSV 與繪圖
# =============================================================================

def simulate_scenario(
    scenario: Mapping[str, float | int | str],
    scenario_index: int,
) -> List[Dict[str, float | int | str]]:
    """執行單一情境的 0～120 分鐘 Qiskit 模擬。"""
    density = initialise_density_matrix()
    rows: List[Dict[str, float | int | str]] = []

    for minute in range(DURATION_MIN + 1):
        density = evolve_one_minute(
            density,
            minute,
            scenario,
        )
        rows.append(
            make_observation_row(
                str(scenario["name"]),
                scenario_index,
                minute,
                density,
            )
        )

    return rows


def write_csv(
    rows: Sequence[Mapping[str, float | int | str]],
    path: Path,
) -> None:
    """將完整逐分鐘原始資料寫入 CSV。"""
    if not rows:
        raise ValueError("沒有可輸出的模擬資料。")

    fieldnames = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def configure_plot_fonts() -> None:
    """
    設定跨平台字型候選。
    找不到前面的中文字型時，Matplotlib 會依序改用後面的字型。
    """
    plt.rcParams["font.sans-serif"] = [
        "Microsoft JhengHei",
        "Noto Sans CJK TC",
        "PingFang TC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def plot_response(
    rows: Sequence[Mapping[str, float | int | str]],
    path: Path,
) -> None:
    """
    產生可重複輸出的 Qiskit 有限 shots 時間響應圖。

    圖中使用 sampled 欄位；exact 欄位仍保存在 CSV，
    用來與純 NumPy 密度矩陣結果進行數值核對。
    """
    configure_plot_fonts()

    figure, axis = plt.subplots(figsize=(14, 8))

    for scenario in SCENARIOS:
        scenario_name = str(scenario["name"])
        selected = [
            row for row in rows
            if row["scenario"] == scenario_name
        ]

        minutes = [int(row["minute"]) for row in selected]
        risk = [
            float(row["physical_risk_probability_sampled"])
            for row in selected
        ]
        response = [
            float(row["decision_response_probability_sampled"])
            for row in selected
        ]

        axis.plot(
            minutes,
            risk,
            linewidth=1.8,
            marker="o",
            markersize=2.2,
            markevery=4,
            label=f"{scenario_name}: Physical Risk (sampled)",
        )
        axis.plot(
            minutes,
            response,
            linewidth=1.8,
            linestyle="--",
            marker="s",
            markersize=2.2,
            markevery=4,
            label=f"{scenario_name}: Decision Response (sampled)",
        )

    event_minutes = [8, 15, 25, 38, 50, 75, 95]
    event_labels = [
        "Heat rise",
        "Cooling degradation",
        "Detection",
        "Fast authorization",
        "Fast intervention",
        "Delayed authorization",
        "Delayed intervention",
    ]

    for minute, label in zip(event_minutes, event_labels):
        axis.axvline(
            minute,
            linewidth=0.9,
            linestyle=":",
            alpha=0.45,
        )
        axis.text(
            minute + 0.8,
            0.975,
            label,
            transform=axis.get_xaxis_transform(),
            rotation=90,
            va="top",
            ha="left",
            fontsize=8,
        )

    axis.set_title(
        "Digital Twin Flow Manifestation — Qiskit Measurement Response "
        f"({MEASUREMENT_SHOTS} shots)",
        fontsize=16,
        pad=82,
    )
    axis.set_xlabel("Physical time (minutes)", fontsize=11)
    axis.set_ylabel("Manifestation probability", fontsize=11)
    axis.set_xlim(0, DURATION_MIN)
    axis.set_ylim(0, 0.42)
    axis.grid(True, alpha=0.25)

    axis.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.025),
        ncol=2,
        fontsize=9,
        frameon=True,
        columnspacing=1.8,
        handlelength=3.2,
        borderpad=0.8,
    )

    figure.subplots_adjust(
        left=0.08,
        right=0.98,
        bottom=0.12,
        top=0.76,
    )
    figure.savefig(
        path,
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)


def plot_qiskit_circuit_explainer(path: Path) -> None:
    """
    以 Matplotlib 產生可重複輸出的 Qiskit 線路解說圖。
    此版本額外調整 gate / wire 的 zorder，避免符號被量子線遮住。

    圖中整理的是「單一分鐘更新」的代表性運算結構。
    實際模擬會依 minute 與 scenario 決定哪些響應閘啟動。

    字型處理：
    - 找得到繁中文字型時，輸出中英雙語。
    - 找不到繁中文字型時，自動改用英文，避免產生方框缺字。
    """
    configure_plot_fonts()

    from matplotlib import font_manager
    from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

    available_fonts = {
        font.name
        for font in font_manager.fontManager.ttflist
    }
    cjk_candidates = [
        "Microsoft JhengHei",
        "Noto Sans CJK TC",
        "Noto Sans CJK JP",
        "PingFang TC",
        "Arial Unicode MS",
    ]
    cjk_font = next(
        (
            candidate
            for candidate in cjk_candidates
            if candidate in available_fonts
        ),
        None,
    )
    bilingual = cjk_font is not None

    if cjk_font is not None:
        plt.rcParams["font.sans-serif"] = [
            cjk_font,
            "DejaVu Sans",
        ]

    def bi(english: str, chinese: str) -> str:
        """依本機字型能力輸出雙語或英文。"""
        if bilingual:
            return f"{english}\n{chinese}"
        return english

    figure, axis = plt.subplots(figsize=(20, 10.5))
    axis.set_xlim(-2.0, 22.3)
    axis.set_ylim(-1.0, 10.7)
    axis.axis("off")

    wire_y = {
        0: 7.55,
        1: 6.72,
        2: 5.89,
        3: 5.06,
        4: 4.23,
        5: 3.40,
        6: 2.57,
        7: 1.74,
    }

    semantic_labels = [
        ("q0", "thermal_load_high", "熱負載偏高"),
        ("q1", "primary_cooling_degraded", "主冷卻能力劣化"),
        ("q2", "backup_reserve_stressed", "備援餘裕受壓"),
        ("q3", "power_constraint", "電力／EMS 約束"),
        ("q4", "process_thermal_risk", "製程熱風險"),
        ("q5", "alarm_interpreted", "告警已形成可理解意義"),
        ("q6", "authorization_ready", "授權已形成"),
        ("q7", "intervention_executed", "實體介入已執行"),
    ]

    stage_specs = [
        (
            0.3,
            2.7,
            bi("1  Initial probability encoding", "初始機率編碼"),
            "#eaf2ff",
            "#2f67b2",
        ),
        (
            2.7,
            4.8,
            bi("2  External disturbances", "外部擾動"),
            "#e9f8fb",
            "#16879a",
        ),
        (
            4.8,
            9.5,
            bi("3  Risk Failure Flow", "風險失效流"),
            "#eef8e8",
            "#4b8f29",
        ),
        (
            9.5,
            14.4,
            bi("4  Decision Response Flow", "決策響應流"),
            "#fff1e8",
            "#e56a00",
        ),
        (
            14.4,
            16.4,
            bi("5  Mitigation / Dissipation", "緩解／耗散"),
            "#f2edff",
            "#6f54b5",
        ),
        (
            16.4,
            18.4,
            bi("6  Measurement", "量測觀測"),
            "#f1f1f1",
            "#555555",
        ),
    ]

    # 圖名置於階段標題上方，避免彼此重疊。
    axis.text(
        10.15,
        10.38,
        "Digital Twin Flow Manifestation — Representative Qiskit Update Circuit",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
    )
    axis.text(
        10.15,
        10.02,
        "One-minute update: encoding → disturbance → risk → response "
        "→ dissipation → observation",
        ha="center",
        va="center",
        fontsize=10.5,
    )

    # 階段底色與標題。
    for x0, x1, title, fill, edge in stage_specs:
        axis.add_patch(
            Rectangle(
                (x0, 8.55),
                x1 - x0,
                0.95,
                facecolor=fill,
                edgecolor=edge,
                linewidth=1.2,
                zorder=0.2,
            )
        )
        axis.text(
            (x0 + x1) / 2,
            9.03,
            title,
            ha="center",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=edge,
            zorder=1.0,
        )
        axis.axvline(
            x1,
            ymin=0.15,
            ymax=0.84,
            linestyle="--",
            linewidth=0.8,
            color="#9a9a9a",
            alpha=0.8,
            zorder=0.1,
        )

    # 左側狀態標籤與量子線。
    axis.text(
        -1.75,
        8.98,
        bi(
            "Qubit / Semantic state",
            "量子位元／語意狀態",
        ),
        ha="left",
        va="center",
        fontsize=10.5,
        fontweight="bold",
    )

    for index, (q_label, english, chinese) in enumerate(semantic_labels):
        y = wire_y[index]
        axis.plot(
            [0.2, 18.1],
            [y, y],
            color="#202020",
            linewidth=1.15,
            zorder=1.0,
        )
        axis.text(
            -1.65,
            y,
            rf"${q_label}$",
            ha="left",
            va="center",
            fontsize=12,
            fontweight="bold",
            zorder=4.0,
        )
        axis.text(
            -1.10,
            y + (0.13 if bilingual else 0.0),
            english,
            ha="left",
            va="center",
            fontsize=9.0,
            zorder=4.0,
        )
        if bilingual:
            axis.text(
                -1.10,
                y - 0.16,
                chinese,
                ha="left",
                va="center",
                fontsize=9.0,
                zorder=4.0,
            )

    def gate_box(
        x: float,
        y: float,
        label: str,
        face: str,
        edge: str,
        width: float = 0.72,
        height: float = 0.42,
        fontsize: float = 9.0,
    ) -> None:
        axis.add_patch(
            FancyBboxPatch(
                (x - width / 2, y - height / 2),
                width,
                height,
                boxstyle="round,pad=0.03,rounding_size=0.04",
                facecolor=face,
                edgecolor=edge,
                linewidth=1.25,
                zorder=5.0,
            )
        )
        axis.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            color=edge,
            fontweight="bold",
            zorder=6.0,
        )

    def controlled_ry(
        x: float,
        control: int,
        target: int,
        label: str,
        color: str,
    ) -> None:
        yc = wire_y[control]
        yt = wire_y[target]

        axis.plot(
            [x, x],
            [yc, yt],
            color=color,
            linewidth=1.5,
            zorder=3.0,
        )
        axis.add_patch(
            Circle(
                (x, yc),
                0.075,
                facecolor=color,
                edgecolor=color,
                zorder=4.0,
            )
        )
        gate_box(
            x,
            yt,
            "Ry",
            face="#ffffff",
            edge=color,
            width=0.50,
            height=0.38,
            fontsize=8.4,
        )
        axis.text(
            x + 0.10,
            (yc + yt) / 2,
            label,
            ha="left",
            va="center",
            fontsize=8.1,
            color=color,
            zorder=4.5,
        )

    def measurement_box(
        x: float,
        y: float,
        classical_label: str,
    ) -> None:
        gate_box(
            x,
            y,
            "M",
            face="#efefef",
            edge="#555555",
            width=0.45,
            height=0.38,
            fontsize=9.0,
        )
        axis.annotate(
            "",
            xy=(18.05, y),
            xytext=(x + 0.26, y),
            arrowprops={
                "arrowstyle": "->",
                "linestyle": "--",
                "linewidth": 0.9,
                "color": "#666666",
                "zorder": 3.0,
            },
        )
        axis.text(
            18.10,
            y,
            classical_label,
            ha="left",
            va="center",
            fontsize=8.5,
            zorder=4.0,
        )

    # 1. 初始機率編碼。
    for index in range(NUM_QUBITS):
        gate_box(
            1.50,
            wire_y[index],
            rf"Ry($\theta_{index}$)",
            face="#eef4ff",
            edge="#2f67b2",
            width=0.78,
        )

    # 2. 外部擾動。
    gate_box(
        3.65,
        wire_y[0],
        r"Ry($\phi_L(t)$)",
        face="#e8f8fb",
        edge="#16879a",
        width=0.95,
    )
    gate_box(
        3.65,
        wire_y[1],
        r"Ry($\phi_D(t)$)",
        face="#e8f8fb",
        edge="#16879a",
        width=0.95,
    )

    # 3. Risk Failure Flow。
    controlled_ry(5.35, 0, 2, r"$\alpha_{02}$", "#4b8f29")
    controlled_ry(6.15, 1, 2, r"$\alpha_{12}$", "#4b8f29")
    controlled_ry(6.95, 2, 3, r"$\alpha_{23}$", "#4b8f29")
    controlled_ry(7.80, 2, 4, r"$\alpha_{24}$", "#4b8f29")
    controlled_ry(8.70, 3, 4, r"$\alpha_{34}$", "#4b8f29")

    # 4. Decision Response Flow。
    controlled_ry(10.05, 1, 5, r"$\beta_{15}$", "#e56a00")
    controlled_ry(10.90, 2, 5, r"$\beta_{25}$", "#e56a00")
    controlled_ry(11.75, 3, 5, r"$\beta_{35}$", "#e56a00")
    controlled_ry(12.75, 5, 6, r"$\gamma_{56}$", "#e56a00")
    controlled_ry(13.60, 6, 7, r"$\gamma_{67}$", "#e56a00")

    # 5. 介入後耗散。
    gate_box(
        15.35,
        wire_y[2],
        r"AD $\Gamma_2(t)$",
        face="#f2edff",
        edge="#6f54b5",
        width=1.15,
    )
    gate_box(
        15.35,
        wire_y[4],
        r"AD $\Gamma_4(t)$",
        face="#f2edff",
        edge="#6f54b5",
        width=1.15,
    )

    # 6. Z 基底量測與 classical bits。
    for index in range(NUM_QUBITS):
        measurement_box(
            17.15,
            wire_y[index],
            rf"$c_{index}$",
        )

    # 右側觀測量。
    observed_box = FancyBboxPatch(
        (18.65, 1.40),
        3.15,
        6.45,
        boxstyle="round,pad=0.12,rounding_size=0.08",
        facecolor="#f7faff",
        edgecolor="#2f67b2",
        linewidth=1.3,
        zorder=2.0,
    )
    axis.add_patch(observed_box)
    axis.text(
        20.22,
        7.55,
        bi("Observed quantities", "觀測量"),
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="#2f67b2",
        zorder=3.0,
    )

    observed_lines = [
        (
            bi("Physical Risk", "物理風險"),
            r"$P(q_4=1)$",
        ),
        (
            bi("Decision Response", "決策響應"),
            r"$P(q_7=1)$",
        ),
        (
            bi("Uncontained Risk", "未控風險"),
            r"$P(q_4=1,\ q_7=0)$",
        ),
        (
            bi("Contained / Avoided", "已控／避免"),
            r"$P(q_4=0,\ q_7=1)$",
        ),
    ]

    y_text = 6.85
    for label, formula in observed_lines:
        axis.text(
            18.90,
            y_text,
            "• " + label,
            ha="left",
            va="center",
            fontsize=9.0,
            color="#1f4f9a",
            fontweight="bold",
        )
        axis.text(
            19.10,
            y_text - (0.45 if bilingual else 0.34),
            formula,
            ha="left",
            va="center",
            fontsize=10.0,
        )
        y_text -= 1.35

    # 底部圖例與時間啟動條件。
    if bilingual:
        legend_line = (
            r"$Ry(\theta_i)$：初始語意機率編碼   "
            r"$CRY$：作用關係／條件傳播   "
            r"$AD$：Kraus 振幅耗散   "
            r"$M$：Z 基底量測"
        )
        schedule_line = (
            "時間條件：外部擾動與風險耦合每分鐘更新；"
            "告警、授權與介入閘依情境門檻啟動；"
            "sample_counts 僅取樣觀測，不改寫後續 DensityMatrix。"
        )
        boundary_line = (
            "此圖呈現程式中的運算結構，"
            "並未宣稱參數已由真實 BMS／EMS 資料完成校準。"
        )
    else:
        legend_line = (
            r"$Ry(\theta_i)$: initial probability encoding   "
            r"$CRY$: relational propagation   "
            r"$AD$: Kraus amplitude damping   "
            r"$M$: Z-basis measurement"
        )
        schedule_line = (
            "Timing: disturbances and risk couplings update every minute; "
            "response gates activate at scenario thresholds; "
            "sample_counts observes without replacing the DensityMatrix."
        )
        boundary_line = (
            "The diagram represents the implemented structure; "
            "its parameters have not been calibrated from real BMS/EMS data."
        )

    axis.text(
        0.30,
        0.78,
        legend_line,
        ha="left",
        va="center",
        fontsize=9.2,
    )
    axis.text(
        0.30,
        0.35,
        schedule_line,
        ha="left",
        va="center",
        fontsize=8.8,
    )
    axis.text(
        0.30,
        -0.05,
        boundary_line,
        ha="left",
        va="center",
        fontsize=8.8,
        color="#555555",
    )

    figure.subplots_adjust(
        left=0.02,
        right=0.99,
        bottom=0.05,
        top=0.98,
    )
    figure.savefig(
        path,
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)


def print_summary(
    rows: Sequence[Mapping[str, float | int | str]],
) -> None:
    """在終端機顯示兩個情境的第 120 分鐘結果。"""
    print("\n第 120 分鐘結果")
    print("-" * 78)

    for scenario in SCENARIOS:
        scenario_name = str(scenario["name"])
        final_row = next(
            row for row in reversed(rows)
            if row["scenario"] == scenario_name
        )

        print(
            f"{scenario_name:22s} | "
            f"PhysicalRisk(sampled)="
            f"{float(final_row['physical_risk_probability_sampled']):.4f} | "
            f"Response(sampled)="
            f"{float(final_row['decision_response_probability_sampled']):.4f} | "
            f"PhysicalRisk(exact)="
            f"{float(final_row['physical_risk_probability_exact']):.4f} | "
            f"Response(exact)="
            f"{float(final_row['decision_response_probability_exact']):.4f} | "
            f"Trace={float(final_row['trace']):.6f}"
        )


def validate_results(
    rows: Sequence[Mapping[str, float | int | str]],
) -> None:
    """執行基本數值檢查。"""
    expected_rows = len(SCENARIOS) * (DURATION_MIN + 1)

    if len(rows) != expected_rows:
        raise RuntimeError(
            f"資料列數不符：預期 {expected_rows}，實際 {len(rows)}。"
        )

    for row in rows:
        trace = float(row["trace"])

        if not math.isclose(trace, 1.0, abs_tol=1e-8):
            raise RuntimeError(
                f"密度矩陣 trace 偏離 1："
                f"scenario={row['scenario']}, minute={row['minute']}, trace={trace}"
            )

        for column in (
            "physical_risk_probability_exact",
            "decision_response_probability_exact",
            "uncontained_risk_probability_exact",
            "contained_or_avoided_probability_exact",
            "physical_risk_probability_sampled",
            "decision_response_probability_sampled",
            "uncontained_risk_probability_sampled",
            "contained_or_avoided_probability_sampled",
        ):
            value = float(row[column])

            if value < -1e-10 or value > 1.0 + 1e-10:
                raise RuntimeError(
                    f"{column} 超出機率範圍：{value}"
                )


def main() -> None:
    """程式主入口。"""
    # 線路圖由 Matplotlib 直接生成，每次執行可得到相同版面。
    plot_qiskit_circuit_explainer(CIRCUIT_PNG_PATH)

    if QISKIT_IMPORT_ERROR is not None:
        raise SystemExit(
            "已產生 Qiskit 線路解說圖，但缺少 Qiskit 模擬套件。\n"
            "請先執行：pip install qiskit==2.5.1"
        ) from QISKIT_IMPORT_ERROR

    all_rows: List[Dict[str, float | int | str]] = []

    for scenario_index, scenario in enumerate(SCENARIOS):
        print(f"正在模擬：{scenario['name']}")
        all_rows.extend(
            simulate_scenario(
                scenario,
                scenario_index,
            )
        )

    validate_results(all_rows)
    write_csv(all_rows, CSV_PATH)
    plot_response(all_rows, PNG_PATH)
    print_summary(all_rows)

    print("\n輸出完成：")
    print(f"- CSV：{CSV_PATH}")
    print(f"- 時間響應圖：{PNG_PATH}")
    print(f"- Qiskit 線路解說圖：{CIRCUIT_PNG_PATH}")


if __name__ == "__main__":
    main()
