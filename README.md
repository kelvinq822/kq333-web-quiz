# Math 1.4 微分練習（v2.0 實作）

手機優先的微分選擇題練習 app：流水線出題、4 選 1（可含「以上皆非」）自動批改、全站排行榜、錯題本。後端是 Flask + 檔案式儲存，沒有資料庫、沒有 build step，可直接部署到 PythonAnywhere。

## 快速開始

```bash
cd math14
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_data.py
python app.py                                     # http://127.0.0.1:5000
```

第一次進站輸入用戶名即註冊（3–16 個中英文字、數字或底線，上限 50 人）。

## 測試

```bash
pip install pytest
python -m pytest tests -q
```

目前覆蓋：25 個模板的導數與數值微分對照、隱函數的隱微分一致性、`tidy` 冪等、MCQ 不變量（4 選項、答案唯一、NOTA 機率）、API 全流程（登入／出題／批改／重放／跨用戶／排行榜）。

## 功能

- 25 個題型模板（冪律 4、乘積 5、商 3、三角 6、隱函數 7）
- 答案**不化簡**：只套微分規則 + 五種排版整理（常數前置、消 1、單一分數線、項序固定）
- 隱函數只做到「兩邊 d/dx 展開」，不解出 dy/dx
- 4 選 1，35% 出現「以上皆非」，其中一半為正解
- 誘餌由結構變異產生：符號、指數、係數、內層係數、三角互換、根式係數、二階導數；隱函數另有乘積法則類錯誤
- 每個選項都經數值驗證（與正解在取樣點上必須不同）
- 用戶名登入（無密碼）、全站排行榜、錯題本（純記錄）
- 手機 UI：深色模式、選項 56px、答完自動接下一題（下一題已預抓）

## 專案結構

```
math14/
├─ app.py                  # create_app()
├─ config.py               # 環境變數設定
├─ exprlib/                # 運算式樹：nodes / latex / diff / tidy / mutate
├─ bank/templates.py       # 25 個題型
├─ services/
│   ├─ generator.py        # 出題與品質閘門
│   ├─ mcq.py              # 選項組裝、NOTA、驗證
│   ├─ compare.py          # 數值比較、dy/dx 代入
│   ├─ filestore.py        # 原子寫入、JSONL、鎖
│   ├─ locks.py            # O_EXCL 檔案鎖
│   ├─ users.py            # 帳號、計分、錯題本
│   ├─ pending.py          # 未批改題目（答案留在伺服器）
│   ├─ leaderboard.py      # 排行榜 + 30 秒快取
│   └─ ratelimit.py        # 記憶體限流
├─ routes/                 # pages.py / api.py / helpers.py
├─ templates/              # base / login / index / wrongbook / board / me / error
├─ static/                 # css / js / manifest / icon
├─ scripts/                # init_data / verify_data / rebuild_index / backup / prune / fetch_katex / demo_questions / stress
├─ tests/                  # pytest
├─ pythonanywhere_wsgi.py
└─ requirements.txt        # 只有 Flask
```

## 資料存放

```
data/
├─ names.json                  # 用戶名索引（可重建）
├─ users/<uid>/profile.json    # 帳號與累計
├─ users/<uid>/attempts.jsonl  # 每題一行（append-only）
├─ users/<uid>/wrongbook.json  # 錯題（上限 200）
├─ pending/<qid>.json          # 未批改題目（含正解，60 分鐘後清理）
└─ locks/                      # 短命鎖檔
```

維護指令：

```bash
python scripts/verify_data.py     # 對帳（積分 vs attempts），有問題會重建索引
python scripts/rebuild_index.py   # 重建 names.json
python scripts/backup.py          # 打包 data/ 為 tar.gz
python scripts/prune.py           # 清 pending、輪替過長的 attempts
```

## 部署到 PythonAnywhere

1. 上傳／`git clone` 專案到 `~/math14`
2. Bash：`mkvirtualenv math14 --python=python3.10` → `pip install -r requirements.txt`
3. `python scripts/init_data.py`
4. Web 分頁 → Add a new web app → **Flask** → 指向 `~/math14`
5. WSGI 設定檔貼上 `pythonanywhere_wsgi.py` 的內容，改 `USERNAME` 與 `SECRET`
6. Static files：URL `/static/` → `/home/USERNAME/math14/static/`
7. Force HTTPS，Reload

KaTeX 預設由 jsDelivr 載入（瀏覽器端）；要完全離線可執行
`python scripts/fetch_katex.py` 並設 `MATH14_LOCAL_KATEX=1`。

## 與 v2.0 規格的差異（實作紀錄）

| 項目 | v2.0 | 實作 | 原因 |
|---|---|---|---|
| 正解長度上限 | 70 字元 | **150 字元** | `((3x−1)/(3x+1))^4`、`x=√((2−y)(3+y))` 的原始形式本來就長；70 會令 3 個模板完全出不了題 |
| 誘餌選擇 | 附錄 A 逐模板指定 | **通用變異 + 數值驗證**，每題取 3 個不同家族 | 逐模板手寫 75 條易錯；通用變異配上「必須真的錯」的驗證更穩 |
| 選項長度容差 | 15% | `max(10, 15%)` | 短答案（40 字元）15% 只有 6 字元，過嚴 |
| 模板檔案 | 5 個模組 | 單一 `bank/templates.py` | 25 個模板共用大量輔助函式，拆開反而重複 |
| 誘餌代碼 | 顯式 14 + 隱函數 12 | 顯式 9 + 隱函數 8 | 部分代碼在樹上無法可靠合成（例如 `imp_product_derivs`），以可驗證者為準 |
| 隱函數測試 | 無 | 以數值解曲線驗證隱微分 | 確保規則實作正確 |

未實作但已在規格中的代碼：`imp_solved`、`imp_one_side`、`imp_product_first_missing`、`imp_product_derivs`、`imp_product_order`（需要更強的結構資訊，留待 v2.1）。

## 已知限制

- 無密碼：任何人知道用戶名即可登入（只存放分數與錯題）
- 無離線功能；斷網時無法出題
- 純選擇題，不練書寫
- 排行榜只計線上作答；少於 250ms 的作答不計分
- 指數式顯示：答案一律用 `x^{-2}`、`(x²+3)^{-3/2}` 這種寫法（依 2026-11-08 的決定）
- 相同因子不合併成冪（`csc·csc` 不會變成 `csc²`），選項因此較長
