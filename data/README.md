# data

影片與標註不進 git（太大，也可能拍到私人畫面）。只把標註 CSV 和這份說明放進 git。

- `raw/`：原始影片，檔名 `YYYYMMDD_<組別>_<編號>.mp4`，組別為 dev / calib / holdout。
- `labels/`：人工標註 CSV（起滑時刻、終點時刻、選定影格的位置），只能由 john 人工標，不可用 AI。
- 保留測試（holdout）在 11/01 功能凍結前不得用來調參。
