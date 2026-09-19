#!/usr/bin/env bash
# Agent Desk 一鍵安裝（macOS / Linux）
#
# 用法（在終端機貼上其中一行）：
#   curl -fsSL https://raw.githubusercontent.com/qunatedge-del/qunatedge-del.github.io/main/install.sh | bash
#   已經 clone 下來的話：bash install.sh
#
# 選項（放在指令後面）：
#   --branch NAME   要用的分支（預設：main；PR 合併前用 claude/feasibility-assessment-mj4j2c）
#   --dir PATH      安裝到哪個資料夾（預設：~/agent-desk）
#   --offline       第一輪用合成資料，不連網（測試用）
#   --no-run        只安裝，不跑第一輪、不開監控頁
set -euo pipefail

REPO="https://github.com/qunatedge-del/qunatedge-del.github.io.git"
BRANCH="main"
DIR="$HOME/agent-desk"
OFFLINE=""
RUN=1
while [ $# -gt 0 ]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    --dir) DIR="$2"; shift 2 ;;
    --offline) OFFLINE="--offline --demo-news"; shift ;;
    --no-run) RUN=0; shift ;;
    *) echo "不認識的參數：$1"; exit 1 ;;
  esac
done

say() { printf '\n\033[1;36m▶ %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31m✖ %s\033[0m\n' "$*"; exit 1; }

# ---- 0. 如果是在 repo 裡執行，就直接用這個資料夾 --------------------------
if [ -f "agent_desk/__init__.py" ] && [ -f "requirements.txt" ]; then
  DIR="$(pwd)"
  say "偵測到已在 repo 內，安裝到目前資料夾：${DIR}"
fi

# ---- 1. 工具檢查 -----------------------------------------------------------
say "檢查 git 與 Python"
if ! command -v git >/dev/null 2>&1; then
  if [ "$(uname)" = "Darwin" ]; then
    echo "沒有 git。macOS 會跳出安裝 Command Line Tools 的視窗，按「安裝」，裝完後重新執行這個腳本。"
    xcode-select --install 2>/dev/null || true
    exit 1
  fi
  die "沒有 git，請先安裝。"
fi

PY=""
for c in python3.13 python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    if "$c" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then PY="$c"; break; fi
  fi
done
if [ -z "${PY}" ]; then
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    say "沒有 Python 3.11 以上，用 Homebrew 安裝 python@3.12"
    brew install python@3.12
    PY="$(brew --prefix python@3.12)/bin/python3.12"
  else
    die "需要 Python 3.11 以上。macOS 請先裝 Homebrew（https://brew.sh）再執行 brew install python@3.12"
  fi
fi
echo "使用 ${PY}（$("${PY}" --version)）"

# ---- 2. 取得程式碼 ---------------------------------------------------------
if [ ! -f "${DIR}/agent_desk/__init__.py" ]; then
  say "下載程式碼到 ${DIR}"
  git clone --branch "${BRANCH}" "${REPO}" "${DIR}" || {
    echo "分支 ${BRANCH} 不存在，改抓預設分支"
    git clone "${REPO}" "${DIR}"
  }
else
  say "更新程式碼（${DIR}）"
  git -C "${DIR}" pull --ff-only || echo "pull 失敗（可能有本機修改），繼續用現有版本"
fi
cd "${DIR}"

# ---- 3. 虛擬環境與套件 ----------------------------------------------------
say "建立虛擬環境並安裝套件"
[ -d .venv ] || "${PY}" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# ---- 4. 方便以後使用的捷徑 ------------------------------------------------
cat > desk <<'SH'
#!/usr/bin/env bash
# 捷徑：./desk run | pending | approve ORD-xxxxx | reject ORD-xxxxx | status | report | killswitch on|off | web
cd "$(dirname "$0")"
source .venv/bin/activate
if [ "${1:-}" = "web" ]; then
  echo "監控頁：http://localhost:8000/agent_desk.html（按 Ctrl+C 停止）"
  (sleep 1; command -v open >/dev/null && open "http://localhost:8000/agent_desk.html") &
  exec python3 -m http.server 8000
fi
exec python -m agent_desk "$@"
SH
chmod +x desk

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo
  echo "提示：沒有設定 ANTHROPIC_API_KEY，新聞情緒會是中性、日報用模板。"
  echo "      要啟用的話：export ANTHROPIC_API_KEY=sk-ant-...（可加進 ~/.zshrc）"
fi

# ---- 5. 跑第一輪並開監控頁 --------------------------------------------------
if [ "${RUN}" = "1" ]; then
  say "跑第一輪（抓資料 → 情緒 → 訊號 → 風控 → 紙上執行 → 日報）"
  # shellcheck disable=SC2086
  python -m agent_desk ${OFFLINE} run || echo "第一輪失敗，通常是行情抓取問題；稍後用 ./desk run 再試一次"
  say "安裝完成。以後在 ${DIR} 裡用："
  echo "   ./desk run                  收盤後跑一輪"
  echo "   ./desk pending              看待審核單"
  echo "   ./desk approve ORD-00012    核准    ./desk reject ORD-00013 駁回"
  echo "   ./desk web                  開監控頁"
  echo
  ./desk web
else
  say "安裝完成（未執行）。到 ${DIR} 用 ./desk run 跑第一輪，./desk web 開監控頁。"
fi
