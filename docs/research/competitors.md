# T21 — 影片物理合理性審核：競品與差異

**更新日期：2026 年 10 月 27 日**  
**研究問題：** 使用者上傳一段影片後，工具能否檢查物體運動是否符合一個明確假設的物理模型？這與研究基準、一般影片分析軟體和教學模擬的重疊在哪裡？

## 目前的任務範圍

最新版 `docs/STATUS.md` 已將 T21 改為研究影片物理合理性工具，點名 VideoPhy、Physics-IQ、Tracker、PhET，並要求確認產品差異。[1] 專案現在驗證的是一個很窄的主張：檢查影片中的物體運動是否符合指定的拋體／自由落體假設。結果只可說「與此假設一致」、「不一致」或「目前無法判斷」，不可說影片是真實或 AI 生成，也不可說能檢查任何影片。[1] [2]

關卡使用固定規則評估追蹤與軌跡，包括自行拍攝的影片是否能量到可信的 g，以及另一段影片是否呈現足以支持「與自由飛行模型不一致」的異常。影片來源只作紀錄，不作答案標籤；規則不應因看到單支影片而逐片調整。[1] 這些是待執行的可行性門檻，不是已證明的產品效果。

## VideoPhy 與 VideoPhy-2：最接近「影片的物理一致性」研究方向

VideoPhy 是 ICLR 2025 的影片生成物理常識 benchmark，測試文字轉影片模型產生的影片是否同時符合提示內容與基本物理常識。論文研究的是生成模型能否產生符合物理的畫面，不是替一般人核驗自己拍攝的影片是否符合指定自由落體方程。[3]

但不能只把它說成「純資料集、沒有工具」。VideoPhy 專案也公開 VideoCon-Physics 自動評估器。研究者可提供自訂 caption 和影片，依其流程在本機執行語意符合度及物理常識評分；官方範例使用已下載的模型檢查點和 CUDA 推論命令。這代表「用模型替影片打物理一致性分數」已有研究實作。它與此產品的差異在可用性及問題定義，而不是從未有人用模型檢查影片物理。[4]

VideoPhy-2 是 ICLR 2026 的後續 benchmark，以約 4,000 個動作導向提示評估生成影片的語意、物理常識和物理規則落地程度，也訓練自動評估器。它進一步證明「評估生成影片中的物理常識」是活躍研究主題，不是本專案可以宣稱首創的能力。[5]

## Physics-IQ：用真實實驗測影片模型的物理理解

Physics-IQ 是 WACV 2026 的研究基準，使用 396 段真實錄製影片、66 種物理情境，涵蓋固體力學、流體、光學、熱力學和磁學。模型從影片開頭預測後續發展，研究者再比較預測和實驗影片；它測的是影片生成模型是否掌握物理，不是一般消費者上傳任意片段後得到「這段影片符合自由落體嗎」的即時判讀。[6]

官方程式庫公開了資料集和評測流程，但使用者要下載特定 benchmark 資料、安裝環境、準備對應生成影片並依 benchmark 格式評分。這是可取得的研究程式，不等於已經有一個免設定、面向一般人的通用影片物理稽核網站。[7]

## MotionPhys：必須避開的「AI 影片真偽」主張

MotionPhys 是 2026 年 8 月上傳到 arXiv 的研究，提出以光流軌跡的跨時間物理一致性偵測 AI 生成影片。它雖然是預印本研究，不代表已成為一般使用者產品，但足以說明「用物理運動痕跡識別 AI 影片」已有直接先例。[8]

因此，本專案必須遵守 STATUS 的限制：**不做 AI 影片偵測，不宣稱影片來源真偽，不把物理模型不合直接等同合成影片。**真實影片也可能因鏡頭角度、遮擋、動態模糊、物體尺寸輸入錯誤或追蹤失準而偏離模型；生成影片也可能在這項特定測試裡看似符合。這個工具的輸出只能是相對於明確假設與可見證據的運動檢查。[1] [2] [8]

## 一般人已可使用的工具

### Tracker Video Analysis

Tracker 是免費、開源並面向物理教學的影片分析與建模工具。官方列有手動及自動追蹤、位置／速度／加速度、座標校準、曲線擬合、資料匯出，以及把數學模型直接同步疊到影片軌跡上等功能。[9] 使用者已可用它分析自己的影片、調整模型，再由圖表和疊加自行判斷模型是否合理。它因此是實際而重要的替代方案，不應只拿 VideoPhy 和 Physics-IQ 兩個研究 benchmark 當競品。

Tracker 的差異是一般工作流程需要使用者設定追蹤、校準與模型參數，再檢視擬合或疊加；官方文件所描述的核心是影片分析和建模工具。這次檢視到的官方功能頁沒有展示本專案那種固定假設、預先凍結的品質閘門、統一通過條件和「無法判斷」處理流程。不過，這只是對已檢視文件的描述，不能據此斷言 Tracker 在所有情境都不能做到類似檢查。[9] [10]

### FizziQ：最貼近一般使用者的直接替代

FizziQ 官方將產品描述為免費、免帳號的手機和網頁影片物理分析工具。使用者逐格標記移動點、校準尺度後，可以得到位置、速度、加速度、角運動、能量，擬合模型、量測 g 並檢查守恆定律。其官方頁面明確說逐格手動標記是刻意的教學設計。[11]

這是本研究找到最值得正面比較的日常可用工具之一。它已涵蓋「一般影片轉成運動數據」、「測 g」與「檢查物理定律」等大塊價值，因此本專案不能籠統主張自己是第一個用手機影片做物理檢查的產品。[11] 目前可主張的窄差異，是把**指定的單一物理假設**做成固定而可重算的稽核流程：先要求確認模型和影片條件，再檢查追蹤與關鍵觀測是否可信，最後只在門檻通過時輸出模型相符或不相符，否則拒判。FizziQ 是否有其他未在頁面列出的自動判定流程，仍未知；結論只限已查閱的公開說明。[11]

### PhET Projectile Motion

PhET 的 Projectile Motion 是互動式拋體模擬。學習者可改變初始高度、角度、速度、質量、直徑和空氣阻力，預測軌跡與落點。[12] 它是有用的物理教學參照，但它改變的是模擬條件，不是量測使用者上傳的真實影片，因此不是同類影片稽核器。

## 可主張的差異與不可主張的差異

目前找到的工具分成兩群。VideoPhy、VideoPhy-2、Physics-IQ 和 MotionPhys 代表研究端的影片物理評估或物理一致性分析；它們不是同一種產品，也不能被一概稱為消費級應用。[3] [4] [5] [6] [7] [8] Tracker 和 FizziQ 則是一般人可使用的真實影片量測／教學工具，已能追蹤物件、算運動量，讓人擬合或檢查物理模型。[9] [10] [11]

所以，最站得住腳的差異不是「我們第一個檢查影片物理」或「AI 一眼看出影片真偽」，而是更窄的一句話：**對使用者指定的自由落體／拋體假設，利用追蹤與影格品質門檻，提供可追溯的數值檢查，並在關鍵證據不足時拒絕下結論。**這種差異目前是由 STATUS 所列的產品設計和凍結門檻支持的定位，還不是已驗證的競品優勢。[1] [2]

目前的技術實作也有重要邊界。STATUS 說明關卡追蹤採畫面差異法，不用模型；時間窗由人標註，尚待 Muse Spark 提供候選區段並由使用者確認。鏡頭固定、正側視、已知物體尺寸是條件；透視、物體朝鏡頭移動和動態模糊會影響結果。[1] 因此，此階段不能說已經做成自動化、通用或由 Muse 完整驅動的物理審核器。

**研究限制：**這份比較是來源檢視，沒有在本輪重新安裝 Tracker、操作 FizziQ 或 PhET，也沒有在本機部署 VideoCon-Physics 或 Physics-IQ pipeline。各產品能力以其官方頁、官方程式庫和論文為據；未公開記載的功能標為未知，不推論為不存在。

## References

[1]: https://raw.githubusercontent.com/johncat88425-del/slope-coach/main/docs/STATUS.md "Slope Coach current status and T21 task definition"
[2]: https://raw.githubusercontent.com/johncat88425-del/slope-coach/main/AGENTS.md "Slope Coach agent rules and claims boundary"
[3]: https://proceedings.iclr.cc/paper_files/paper/2025/hash/fce2d8a485746f76aac7b5650db2679d-Abstract-Conference.html "VideoPhy: Evaluating Physical Commonsense for Video Generation"
[4]: https://github.com/Hritikbansal/videophy "VideoPhy official code and VideoCon-Physics evaluator"
[5]: https://proceedings.iclr.cc/paper_files/paper/2026/hash/c02f6a1d5c55e16db50d339dad905b4d-Abstract-Conference.html "VideoPhy-2: Action-Centric Physical Commonsense Evaluation"
[6]: https://openaccess.thecvf.com/content/WACV2026/papers/Motamed_Do_Generative_Video_Models_Understand_Physical_Principles_WACV_2026_paper.pdf "Do Generative Video Models Understand Physical Principles? Physics-IQ"
[7]: https://github.com/google-deepmind/physics-IQ-benchmark "Physics-IQ benchmark official code and evaluation workflow"
[8]: https://arxiv.org/abs/2608.20770 "MotionPhys: Detecting AI-Generated Videos via Physical Consistency of Optical-Flow Trajectories"
[9]: https://opensourcephysics.github.io/tracker-website/ "Tracker Video Analysis and Modeling Tool"
[10]: https://opensourcephysics.github.io/tracker-website/help/particles.html "Tracker Particle Models and Model Overlays"
[11]: https://www.fizziq.org/en/video-analysis/ "FizziQ Video Analysis for Physics"
[12]: https://phet.colorado.edu/en/simulations/projectile-motion "PhET Projectile Motion"
