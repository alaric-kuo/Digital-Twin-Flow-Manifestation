# Changelog

## README V4 — 2026-08-06

- 全面移除GitHub表格中的inline LaTeX，避免科學符號以原始字串顯示。
- 統一數學符號、Qiskit類別與Python識別字的表示規則。
- 修正第三章的qᵢ、pᵢ與θᵢ符號系統。
- 將線路圖圖例中的下標改為Unicode顯示，避免底線裸露。
- 重寫六階段表格，將複雜公式移至GitHub可穩定渲染的math區塊。
- 統一Pure NumPy與Qiskit實作表格的欄位語法與資訊粒度。

## README V3 — 2026-08-06

- 統一第三章的$p_i$、$q_i$與$\theta_i$符號。
- 重寫Qiskit線路圖圖例，逐項說明水平線、旋轉閘、受控閘、Kraus耗散、量測與觀測框。
- 將六個運算階段展開為輸入、Qiskit運算、數學改變、語意輸出與啟動條件。
- 逐線解讀五條Risk Failure Flow與五條Decision Response Flow。
- 新增完整風險—響應—耗散閉環與exact／sampled計算說明。
- 統一Pure NumPy與Qiskit技術表格的欄位、語法及資訊層級。

## README V2 — 2026-08-06

- 收斂為十二章。
- 新增最小入口、研究問題、主要發現與閱讀指南。
- 完整解讀Qiskit六階段線路與狀態相依耗散。
- 補強NumPy精確時間響應的分段解讀。
- 新增Qiskit sampled／exact誤差分析。
- 補充跨情境比較、可檢查條件與研究邊界。
- 新增CITATION.cff與作者／權利資訊。

## Initial release — 2026-08-06

- Pure NumPy密度矩陣實作。
- Qiskit DensityMatrix與8192 shots實作。
- 三張可重複生成圖表。
- 兩份逐分鐘CSV輸出。
