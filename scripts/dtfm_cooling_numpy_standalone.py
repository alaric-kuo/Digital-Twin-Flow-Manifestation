"""
Digital Twin Flow Manifestation（DTFM）
高科技廠房冷卻系統時間動態 POC：純 NumPy 單檔版 V4

本程式將 Digital Twin 方法論中的兩股流向放進同一個時間軸：

1. Risk Failure Flow
   熱負載與冷卻能力劣化，經由備援壓力、電力限制，
   逐步推動製程熱風險。

2. Decision Response Flow
   異常被理解後，經由授權與實體介入形成響應，
   再透過耗散機制降低備援壓力與製程熱風險。

專案內檔案：
- scripts/dtfm_cooling_numpy_standalone.py

輸出檔案：
- dtfm_numpy_time_series.csv
- dtfm_numpy_time_response.png

執行環境：
    pip install numpy matplotlib
    python scripts/dtfm_cooling_numpy_standalone.py

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
- 本程式展示量子狀態與開放系統表達，不主張已證明量子計算優勢。
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

try:
    import numpy as np
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit(
        "缺少必要套件。請先執行：pip install numpy matplotlib"
    ) from exc


# =============================================================================
# 一、基本設定
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "dtfm_numpy_time_series.csv"
PNG_PATH = OUTPUT_DIR / "dtfm_numpy_time_response.png"

NUM_QUBITS = 8
DURATION_MIN = 120
DT_MIN = 1.0

# 狀態順序同時決定量子位元編號與 CSV 欄位順序。
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
        # 同樣於第 25 分鐘辨識異常，但授權與介入明顯延遲。
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
        # 異常辨識後，較早形成授權與實體介入。
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
    """
    建立 0～1 之間的分段線性擾動。

    start：開始上升時間
    rise ：由 0 上升至 1 所需時間
    end  ：開始下降時間；None 表示維持高位
    fall ：由 1 降回 0 所需時間
    """
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
    """
    熱負載於第 8 分鐘開始上升，第 20 分鐘達到高位；
    第 85 分鐘開始緩解，第 105 分鐘回到基準。
    """
    return ramp_profile(minute, start=8, rise=12, end=85, fall=20)


def degradation_profile(minute: float) -> float:
    """
    主冷卻能力於第 15 分鐘開始劣化，
    第 35 分鐘達到完整劣化狀態，之後維持。
    """
    return ramp_profile(minute, start=15, rise=20, end=None)


# =============================================================================
# 四、量子狀態與基本運算
# =============================================================================

def probability_to_ry_angle(probability: float) -> float:
    """
    將語意證據 p∈[0,1] 轉成 Ry 旋轉角。

    Ry(theta)|0> 的量測機率為：
        P(q=1) = sin²(theta/2)

    因此：
        theta = 2 asin(sqrt(p))
    """
    p = float(np.clip(probability, 0.0, 1.0))
    return 2.0 * math.asin(math.sqrt(p))


def ry(theta: float) -> np.ndarray:
    """回傳 Y 軸旋轉矩陣。"""
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.array(
        [[c, -s], [s, c]],
        dtype=complex,
    )


def apply_local_operator(
    density: np.ndarray,
    operator: np.ndarray,
    target: int,
) -> np.ndarray:
    """
    對密度矩陣套用單量子位元運算：

        rho' = A rho A†

    採 Qiskit 相同的小端序（little-endian）量子位元索引。
    """
    size = 1 << NUM_QUBITS
    step = 1 << target

    # 左乘 A。
    left = density.copy()
    for base in range(0, size, step * 2):
        for offset in range(step):
            i0 = base + offset
            i1 = i0 + step
            left[[i0, i1], :] = operator @ density[[i0, i1], :]

    # 右乘 A†。
    output = left.copy()
    for base in range(0, size, step * 2):
        for offset in range(step):
            i0 = base + offset
            i1 = i0 + step
            output[:, [i0, i1]] = left[:, [i0, i1]] @ operator.conj().T

    return output


def apply_controlled_operator(
    density: np.ndarray,
    operator: np.ndarray,
    control: int,
    target: int,
) -> np.ndarray:
    """
    當 control=1 時，對 target 套用單量子位元運算。

    在本 POC 中：
    - 正向 controlled-Ry 表示觸發、依賴或放大。
    - 授權與介入同樣以 controlled-Ry 表示狀態推進。
    """
    if control == target:
        raise ValueError("control 與 target 不可相同。")

    pairs = [
        (index, index | (1 << target))
        for index in range(1 << NUM_QUBITS)
        if ((index >> control) & 1) == 1
        and ((index >> target) & 1) == 0
    ]

    left = density.copy()
    for i0, i1 in pairs:
        left[[i0, i1], :] = operator @ density[[i0, i1], :]

    output = left.copy()
    for i0, i1 in pairs:
        output[:, [i0, i1]] = left[:, [i0, i1]] @ operator.conj().T

    return output


def amplitude_damping(
    density: np.ndarray,
    gamma: float,
    target: int,
) -> np.ndarray:
    """
    套用振幅耗散通道：

        E(rho) = K0 rho K0† + K1 rho K1†

    此處用來表示實體介入後，
    備援壓力或製程熱風險逐步耗散。
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

    return (
        apply_local_operator(density, k0, target)
        + apply_local_operator(density, k1, target)
    )


def initial_probabilities() -> List[float]:
    """
    模擬開始時，各語意狀態保留低但非零的背景機率。
    """
    return [
        0.020,  # 熱負載偏高
        0.015,  # 主冷卻能力劣化
        0.010,  # 備援餘裕受壓
        0.010,  # 電力限制
        0.005,  # 製程熱風險
        0.005,  # 告警已理解
        0.002,  # 授權已形成
        0.001,  # 介入已執行
    ]


def initialise_density_matrix() -> np.ndarray:
    """
    由 |00000000> 開始，依背景機率逐一編碼初始狀態，
    再轉成密度矩陣 rho = |psi><psi|。
    """
    state = np.zeros(1 << NUM_QUBITS, dtype=complex)
    state[0] = 1.0

    for qubit, probability in enumerate(initial_probabilities()):
        gate = ry(probability_to_ry_angle(probability))
        step = 1 << qubit
        updated = state.copy()

        for base in range(0, 1 << NUM_QUBITS, step * 2):
            for offset in range(step):
                i0 = base + offset
                i1 = i0 + step
                updated[[i0, i1]] = gate @ state[[i0, i1]]

        state = updated

    return np.outer(state, state.conj())


# =============================================================================
# 五、狀態觀測
# =============================================================================

def marginal_probability(density: np.ndarray, qubit: int) -> float:
    """回傳指定量子位元量測為 1 的邊際機率。"""
    diagonal = np.real(np.diag(density))
    return float(
        sum(
            diagonal[index]
            for index in range(len(diagonal))
            if ((index >> qubit) & 1) == 1
        )
    )


def joint_probability(
    density: np.ndarray,
    conditions: Mapping[int, int],
) -> float:
    """回傳多個量子位元同時符合指定條件的聯合機率。"""
    diagonal = np.real(np.diag(density))
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


def make_observation_row(
    scenario_name: str,
    minute: int,
    density: np.ndarray,
) -> Dict[str, float | int | str]:
    """
    將目前密度矩陣轉成一列 CSV 紀錄。

    Risk Failure Flow：
        製程熱風險已顯化，且實體介入尚未形成的聯合機率。

    Decision Response Flow：
        實體介入已形成的邊際機率。
    """
    row: Dict[str, float | int | str] = {
        "engine": "NumPy density matrix",
        "scenario": scenario_name,
        "minute": minute,
        "thermal_load_input": thermal_load_profile(minute),
        "degradation_input": degradation_profile(minute),
    }

    for qubit, name in enumerate(QUBIT_NAMES):
        row[name] = marginal_probability(density, qubit)

    # 主要物理風險：
    # P(q4=1)，只觀測製程熱風險本身，不把是否已介入混入定義。
    row["physical_risk_probability"] = marginal_probability(density, 4)

    # 決策響應：
    # P(q7=1)，表示實體介入已形成的機率。
    row["decision_response_probability"] = marginal_probability(density, 7)

    # 次要診斷指標：
    # P(q4=1, q7=0)，表示製程熱風險存在且介入尚未形成。
    # 此欄位會隨 q7 上升而自然下降，因此不再當作主要物理風險曲線。
    row["uncontained_risk_probability"] = joint_probability(
        density,
        {4: 1, 7: 0},
    )

    # P(q4=0, q7=1)，表示介入已形成且製程熱風險未顯化。
    row["contained_or_avoided_probability"] = joint_probability(
        density,
        {4: 0, 7: 1},
    )

    row["trace"] = float(np.real(np.trace(density)))

    return row


# =============================================================================
# 六、每分鐘的動態演化
# =============================================================================

def evolve_one_minute(
    density: np.ndarray,
    minute: int,
    scenario: Mapping[str, float | int | str],
) -> np.ndarray:
    """
    執行一分鐘的完整演化。

    執行順序：
    1. 外部熱負載與冷卻劣化進場。
    2. Risk Failure Flow 在物理／功能拓撲中傳播。
    3. Decision Response Flow 形成告警理解。
    4. 依情境時間形成授權與介入。
    5. 介入透過耗散通道降低風險。
    """
    load = thermal_load_profile(minute)
    degradation = degradation_profile(minute)

    # -----------------------------------------------------------------
    # 1. 外部擾動
    # -----------------------------------------------------------------
    density = apply_local_operator(
        density,
        ry(0.030 * load * DT_MIN),
        target=0,
    )
    density = apply_local_operator(
        density,
        ry(0.026 * degradation * DT_MIN),
        target=1,
    )

    # -----------------------------------------------------------------
    # 2. Risk Failure Flow
    # -----------------------------------------------------------------
    risk_couplings: Sequence[Tuple[int, int, float]] = [
        (0, 2, 0.025),  # 熱負載 -> 備援壓力
        (1, 2, 0.035),  # 冷卻劣化 -> 備援壓力
        (2, 3, 0.018),  # 備援壓力 -> 電力限制
        (2, 4, 0.032),  # 備援壓力 -> 製程熱風險
        (3, 4, 0.025),  # 電力限制 -> 製程熱風險
    ]

    for control, target, angle_per_min in risk_couplings:
        density = apply_controlled_operator(
            density,
            ry(angle_per_min * DT_MIN),
            control,
            target,
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
            density = apply_controlled_operator(
                density,
                ry(angle_per_min * DT_MIN),
                control,
                target,
            )

    # -----------------------------------------------------------------
    # 4. 告警理解 -> 授權 -> 實體介入
    # -----------------------------------------------------------------
    if minute >= int(scenario["authorization_min"]):
        density = apply_controlled_operator(
            density,
            ry(float(scenario["authorization_gain"]) * DT_MIN),
            control=5,
            target=6,
        )

    if minute >= int(scenario["intervention_min"]):
        density = apply_controlled_operator(
            density,
            ry(float(scenario["intervention_gain"]) * DT_MIN),
            control=6,
            target=7,
        )

    # -----------------------------------------------------------------
    # 5. 介入後的實體耗散
    # -----------------------------------------------------------------
    intervention_probability = marginal_probability(density, 7)
    mitigation_gain = float(scenario["mitigation_gain"])

    density = amplitude_damping(
        density,
        gamma=mitigation_gain * intervention_probability,
        target=2,
    )
    density = amplitude_damping(
        density,
        gamma=mitigation_gain * 1.40 * intervention_probability,
        target=4,
    )

    # 外部熱負載下降後，熱負載狀態自然緩解。
    if minute > 90:
        density = amplitude_damping(
            density,
            gamma=0.010,
            target=0,
        )

    return density


# =============================================================================
# 七、模擬、輸出 CSV 與繪圖
# =============================================================================

def simulate_scenario(
    scenario: Mapping[str, float | int | str],
) -> List[Dict[str, float | int | str]]:
    """執行單一情境的 0～120 分鐘模擬。"""
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
    產生可重複輸出的時間響應圖。

    主要曲線：
    - Physical Risk：P(q4=1)
    - Decision Response：P(q7=1)

    Legend 放在繪圖區上方，避免遮住左上角事件標線與曲線。
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
            float(row["physical_risk_probability"])
            for row in selected
        ]
        response = [
            float(row["decision_response_probability"])
            for row in selected
        ]

        axis.plot(
            minutes,
            risk,
            linewidth=2.2,
            label=f"{scenario_name}: Physical Risk",
        )
        axis.plot(
            minutes,
            response,
            linewidth=2.0,
            linestyle="--",
            label=f"{scenario_name}: Decision Response",
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
        "Digital Twin Flow Manifestation — Physical Risk and Response (NumPy V4)",
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

    # 固定留白，確保不同電腦重跑時 Legend 與標題都不會壓到繪圖區。
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
            f"PhysicalRisk={float(final_row['physical_risk_probability']):.4f} | "
            f"Response={float(final_row['decision_response_probability']):.4f} | "
            f"Uncontained={float(final_row['uncontained_risk_probability']):.4f} | "
            f"Contained={float(final_row['contained_or_avoided_probability']):.4f} | "
            f"Trace={float(final_row['trace']):.6f}"
        )


def validate_results(
    rows: Sequence[Mapping[str, float | int | str]],
) -> None:
    """執行基本數值檢查，避免輸出失真的資料。"""
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
            "physical_risk_probability",
            "decision_response_probability",
            "uncontained_risk_probability",
            "contained_or_avoided_probability",
        ):
            value = float(row[column])
            if value < -1e-10 or value > 1.0 + 1e-10:
                raise RuntimeError(
                    f"{column} 超出機率範圍：{value}"
                )


def main() -> None:
    """程式主入口。"""
    all_rows: List[Dict[str, float | int | str]] = []

    for scenario in SCENARIOS:
        print(f"正在模擬：{scenario['name']}")
        all_rows.extend(simulate_scenario(scenario))

    validate_results(all_rows)
    write_csv(all_rows, CSV_PATH)
    plot_response(all_rows, PNG_PATH)
    print_summary(all_rows)

    print("\n輸出完成：")
    print(f"- CSV：{CSV_PATH}")
    print(f"- PNG：{PNG_PATH}")


if __name__ == "__main__":
    main()
