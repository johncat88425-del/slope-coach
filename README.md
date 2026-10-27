# Slope Coach：實物模擬實驗教練

Meta Global AI Developer Hackathon（Indie 賽道）參賽作品。拍下斜坡與滑塊，先鎖定預測，再實測、比較差異，並建議下一次驗證。

- AI 工具共用規則：`AGENTS.md`
- 目前進度與缺口：`docs/STATUS.md`
- 完整計畫：`docs/PLAN.md`
- 各 AI 的開工 prompt：`docs/PROMPTS.md`

產品內所有模型呼叫皆為 Meta 模型（Muse Spark、SAM 3.1，視測試結果加入 Muse Wonder）。開發過程使用 AI 程式助手（Muse Code、Claude Code、Codex、Antigravity）。

## 安裝

需要：git、Python 3.11、Node 20、ffmpeg、Muse Code。

```
# Muse Code（macOS / Linux）
curl -fsSL https://dev.meta.ai/install.sh | sh
# Muse Code（Windows PowerShell）
irm https://dev.meta.ai/install.ps1 | iex

cp .env.example .env   # 填入 MODEL_API_KEY
```
