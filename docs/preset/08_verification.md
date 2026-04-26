# TraceWeaver — (08) Verification (`tw doctor` + 부트스트랩 + preflight)

> **위치**: `docs/preset/08_verification.md`
> **상태**: Preset Phase 6 — 모든 prep 완료 후 단일 entry point.
> **출처 plan**: `docs/plan/10_observability_diagnostics.md §10.5` (`tw doctor`), `17_risks.md §14` (preflight checklist), `16_roadmap.md §B5-7` (`scripts/demo_preflight.sh`)
> **Source of truth**: 본 파일이 부트스트랩 1-shot 스크립트 + `tw doctor` 11 체크 + 단계별 smoke + 데모 preflight의 통합.

---

## 8.1 부트스트랩 1-shot 스크립트

새 머신에서 docs/plan을 구현 시작하기 전, 본 스크립트를 한 번 실행하면 Phase 1~5가 일관 순서로 처리된다. 사용자는 sudo password만 1회 입력.

`scripts/preset_bootstrap.sh` (제안):

```bash
#!/usr/bin/env bash
# TraceWeaver preset bootstrap — 새 머신을 docs/plan 구현 가능 상태로 만듦
# Usage: bash scripts/preset_bootstrap.sh [--with-llm] [--with-extras]
#
# 단계:
#   Phase 1: apt 시스템 패키지 (sudo)
#   Phase 1b: Intel iGPU/NPU 드라이버 (sudo, --with-llm 시)
#   Phase 2: uv + Node + Python venv + pnpm install
#   Phase 3: (--with-llm) Qwen2.5-Coder-7B 변환
#   Phase 4: (옵션) systemd unit symlink
#   Phase 5: tests/fixtures/ bake (sample repos)
#   Phase 6: tw doctor 검증
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

WITH_LLM=0
WITH_EXTRAS=0
for arg in "$@"; do
  case "$arg" in
    --with-llm)    WITH_LLM=1 ;;
    --with-extras) WITH_EXTRAS=1 ;;
  esac
done

log() { printf "\033[1;34m[bootstrap]\033[0m %s\n" "$*"; }
fail() { printf "\033[1;31m[bootstrap]\033[0m %s\n" "$*" >&2; exit 1; }

# --- Phase 1: 시스템 패키지 (preset/01) ---
log "Phase 1 — apt 시스템 패키지"
sudo apt update
sudo apt install -y \
  python3.12 python3.12-dev \
  libsqlite3-0 sqlite3 libsqlite3-dev \
  netcat-openbsd jq \
  git build-essential \
  ca-certificates curl \
  systemd \
  tmux tilix python3-gi \
  gitleaks just cmake

# Node >=22 LTS (apt default 18 / stale NodeSource 20 우회)
if ! node --version 2>/dev/null | grep -qE '^v(2[2-9]|[3-9][0-9])\.'; then
  curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
  sudo apt install -y nodejs
fi

# nc OpenBSD 강제
sudo update-alternatives --set nc /bin/nc.openbsd 2>/dev/null || true

# --- Phase 1b: Intel iGPU/NPU 드라이버 (preset/02) — --with-llm 시만 ---
if [ "$WITH_LLM" -eq 1 ]; then
  log "Phase 1b — Intel iGPU/NPU 드라이버"
  sudo add-apt-repository -y universe
  sudo apt install -y libze1 libze-intel-gpu1 \
    intel-opencl-icd ocl-icd-opencl-dev intel-gpu-tools

  # NPU PPA (Lunar Lake 등 신모델은 GH release .deb 별도)
  if [ ! -f /etc/apt/sources.list.d/intel-oneapi.list ]; then
    wget -qO - https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
      | sudo gpg --dearmor -o /usr/share/keyrings/intel-sw-products.gpg
    echo "deb [signed-by=/usr/share/keyrings/intel-sw-products.gpg] https://apt.repos.intel.com/oneapi all main" \
      | sudo tee /etc/apt/sources.list.d/intel-oneapi.list >/dev/null
    sudo apt update
  fi
  sudo apt install -y intel-npu-driver intel-npu-driver-firmware || \
    log "(NPU 드라이버 미적용 — 디바이스 미장착이거나 PPA에 패키지 없음)"

  # iGPU/NPU 권한. Ubuntu 24.04/OEM kernel의 /dev/dri, /dev/accel은 render 그룹을 사용.
  sudo usermod -aG render "$USER" || true
fi

# --- Phase 2: uv + Python venv + Node deps (preset/03 + preset/04) ---
log "Phase 2 — uv + Python venv + pnpm install"

# uv
if ! command -v uv >/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# pnpm via corepack
corepack enable
corepack prepare pnpm@10.4.0 --activate

cd "$ROOT"
uv sync
[ -d ui ] && (cd ui && pnpm install) || log "(ui/ 디렉토리 미존재 — 구현 단계에서 생성)"
[ -d extensions/browser ] && (cd extensions/browser && pnpm install) || true

# pre-commit
uv run pre-commit install || log "(pre-commit hook 등록 skip — .pre-commit-config.yaml 미존재 시)"

# --- Phase 3: LLM 모델 변환 (preset/05) — --with-llm 시 ---
if [ "$WITH_LLM" -eq 1 ]; then
  log "Phase 3 — Qwen2.5-Coder-7B INT4 OpenVINO IR 변환 (~10–15 min)"
  CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4"
  if [ ! -f "$CACHE/openvino_model.xml" ]; then
    mkdir -p "$(dirname "$CACHE")"
    uv run optimum-cli export openvino \
      --model "Qwen/Qwen2.5-Coder-7B-Instruct" \
      --weight-format int4 \
      --trust-remote-code \
      --task text-generation-with-past \
      "$CACHE"
  else
    log "  ✓ 이미 변환됨 — skip"
  fi
fi

# --- Phase 4: systemd unit symlink (preset/06) ---
log "Phase 4 — systemd --user unit"
loginctl enable-linger "$USER" 2>/dev/null || true
mkdir -p ~/.config/systemd/user
if [ -f packaging/systemd/traceweaver.service ]; then
  ln -sf "$ROOT/packaging/systemd/traceweaver.service" \
         ~/.config/systemd/user/traceweaver.service
  systemctl --user daemon-reload
  log "  unit symlink 완료 — 'systemctl --user enable --now traceweaver' 로 시작 가능"
else
  log "  (packaging/systemd/traceweaver.service 미존재 — B0-6 구현 후 활성)"
fi

# --- Phase 5: 테스트 fixture (preset/07) ---
log "Phase 5 — tests/fixtures/ bake"
if [ -f scripts/bake_sample_repos.sh ]; then
  bash scripts/bake_sample_repos.sh
else
  log "  (bake script 미존재 — B5-1 구현 후 실행)"
fi

# --- Phase 6: 검증 ---
log "Phase 6 — tw doctor"
if command -v tw >/dev/null; then
  tw doctor || log "  (tw doctor 일부 항목 fail — 위 메시지 확인)"
else
  uv run python -m traceweaver.cli doctor || log "  (cli 미구현 — 구현 단계 진행)"
fi

log "✓ Bootstrap 완료. 다음:"
log "  - render 그룹 적용을 위해 재로그인 (--with-llm 시)"
log "  - 'systemctl --user start traceweaver' 로 데몬 시작"
log "  - 'tw doctor' 로 전체 상태 점검"
```

사용:
```bash
# 최소 (UI + backend만; LLM 없음)
bash scripts/preset_bootstrap.sh

# 전체 (LLM + Intel 드라이버 + 모델 변환 포함)
bash scripts/preset_bootstrap.sh --with-llm
```

---

## 8.2 `tw doctor` — 11 체크 (plan/10 §10.5)

`tw doctor`는 데몬 동작 상태 + 환경 + 의존을 11 항목으로 점검. 각 체크는 ✓/⚠/✗ + 설명.

| # | 체크 | 통과 조건 | 실패 시 가이드 |
|---|------|-----------|---------------|
| 1 | **OS** | Ubuntu 24.04 (kernel 6.8+) | "Ubuntu 24.04 only — see plan/00 §0.4" |
| 2 | **Python 인터프리터** | venv Python == 3.12.x | "uv sync로 인터프리터 동기화" |
| 3 | **데몬 프로세스** | systemd `--user` active + bind 7777 + hook.sock 0600 | "systemctl --user start traceweaver" |
| 4 | **DB 헬스** | events.db 존재 + WAL 모드 + alembic head + sqlite-vec 로드됨 | "alembic upgrade head" + "sqlite-vec 재설치" |
| 5 | **Collectors** | shell hook 설치 + git/fs/browser/tmux collector 활성 | per-collector 상세 |
| 6 | **LLM 백엔드** | 4-tier 중 1+ 활성 + 모델 IR 존재 + smoke inference OK | preset/05 단계 재확인 |
| 7 | **Intel 디바이스** | OpenVINO `available_devices` 에 NPU/GPU/CPU | preset/02 단계 재확인 |
| 8 | **Privacy** | gitleaks 가용 + 25 정규식 로드 + audit hash chain 무결성 | gitleaks 설치 (옵션) + audit_log 검증 |
| 9 | **Browser ext** | `~/.tw/extension_token` 존재 + `/ext/health` 응답 | `tw ext-token generate` |
| 10 | **Disk** | `~/.local/share/traceweaver/`, `~/.cache/traceweaver/` 쓰기 가능 + free space ≥ 2GB | 디렉토리 권한 + df -h |
| 11 | **Schedule** (★ ADR-15) | `extraction_schedule` row 존재 + APScheduler 활성 + 마지막 trigger 24h 내 | `tw extract --status` |

`tw doctor --bundle`은 위를 진단 번들 (`~/.cache/traceweaver/doctor_<ts>.tar.gz`)로 패키징.

---

## 8.3 단계별 smoke 명령

각 phase 직후 빠르게 점검할 명령:

### Phase 1 (apt)
```bash
echo "=== Phase 1 smoke ==="
for cmd in python3.12 sqlite3 nc jq git gcc node systemctl tmux; do
  command -v "$cmd" >/dev/null && printf "  ✓ %s\n" "$cmd" || printf "  ✗ %s\n" "$cmd"
done
nc -h 2>&1 | head -1 | grep -q OpenBSD && echo "  ✓ nc=OpenBSD" || echo "  ⚠ nc 변종 확인"
node --version | grep -qE '^v(2[2-9]|[3-9][0-9])\.' && echo "  ✓ Node >=22" || echo "  ✗ Node <22"
```

### Phase 1b (Intel)
```bash
echo "=== Phase 1b smoke ==="
groups "$USER" | grep -q render && echo "  ✓ render 그룹" || echo "  ✗ render 그룹 미소속 (재로그인 필요)"
[ -e /dev/dri/renderD128 ] && [ -r /dev/dri/renderD128 ] && echo "  ✓ /dev/dri/renderD128 readable"
ls /dev/accel/accel0 2>/dev/null && [ -r /dev/accel/accel0 ] && echo "  ✓ NPU device readable" || echo "  ⚠ NPU 미감지 또는 render 권한 필요"
```

### Phase 2 (Python + Node)
```bash
echo "=== Phase 2 smoke ==="
uv --version | head -1
uv run python --version
uv run python -c "
import fastapi, sqlalchemy, sqlite_vec, apscheduler, structlog, typer
print('  ✓ Python core imports OK')
"
[ -d ui/node_modules ] && echo "  ✓ ui/node_modules" || echo "  ⚠ ui/ 미구성"
```

### Phase 3 (LLM)
```bash
echo "=== Phase 3 smoke ==="
uv run python <<'PY'
import openvino as ov
core = ov.Core()
print(f"  ✓ OpenVINO devices: {core.available_devices}")
PY
MODEL_DIR="$HOME/.cache/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4"
[ -f "$MODEL_DIR/openvino_model.xml" ] \
  && echo "  ✓ Qwen2.5-Coder-7B IR present ($(du -sh $MODEL_DIR | cut -f1))" \
  || echo "  ⚠ 모델 변환 미완 — preset/05 §5.5.1 실행"
```

### Phase 4 (systemd)
```bash
echo "=== Phase 4 smoke ==="
loginctl show-user "$USER" --property=Linger | grep -q yes && echo "  ✓ Linger=yes"
systemctl --user is-active traceweaver.service 2>/dev/null && echo "  ✓ daemon active" \
  || echo "  ⚠ daemon inactive — 'systemctl --user start traceweaver'"
ss -tlnp 2>/dev/null | grep -q :7777 && echo "  ✓ port 7777 listening"
```

### Phase 5 (fixtures)
```bash
echo "=== Phase 5 smoke ==="
[ -f tests/fixtures/demo_seed.yaml ] && echo "  ✓ demo_seed.yaml" || echo "  ⚠ demo_seed.yaml 없음"
[ -f tests/fixtures/secret_corpus/manifest.yaml ] && echo "  ✓ secret_corpus manifest"
ls tests/fixtures/sample_repos/ 2>/dev/null | wc -l | awk '{print "  sample_repos: "$1" 개"}'
```

### Phase 6 (verification)
```bash
tw doctor   # 또는 uv run python -m traceweaver.cli doctor
```

---

## 8.4 데모 preflight (D-1 30분 체크리스트)

`scripts/demo_preflight.sh` — `plan/17_risks.md §14` + `plan/16_roadmap.md §9` 의 D-1 자동화. 본 preset에서 마련한 모든 사전조건을 데모 시연 직전 1회 점검.

```bash
#!/usr/bin/env bash
# 데모 시연 직전 D-1 체크리스트 (~30분 예상)
set -uo pipefail   # -e 없이 — 모든 항목 점검 후 final summary
log() { printf "[preflight] %s\n" "$*"; }

# 1. Phase 1~5 smoke (위 §8.3)
# TODO: 구현 단계에서 scripts/preset_smoke.sh를 만들면 여기서 호출한다.
# 현재 문서 버전에서는 §8.3 명령을 직접 실행한다.

# 2. tw doctor 11 항목 모두 ✓
tw doctor --json > /tmp/preflight_doctor.json
ALL_OK=$(jq '[.checks[] | select(.status != "ok")] | length' /tmp/preflight_doctor.json)
[ "$ALL_OK" = "0" ] && log "✓ tw doctor: 11/11" || log "⚠ tw doctor: $ALL_OK 항목 fail"

# 3. demo_seed 로드 + GUI Inbox 5–8 conventions
tw demo seed
sleep 2
CONV_COUNT=$(curl -s http://127.0.0.1:7777/api/v1/conventions | jq '.items | length')
[ "$CONV_COUNT" -ge 5 ] && [ "$CONV_COUNT" -le 8 ] \
  && log "✓ Conventions: $CONV_COUNT" || log "⚠ Conventions 수: $CONV_COUNT (5–8 범위 외)"

# 4. ETH Zurich 4-gate 동작 (filter ON/OFF 비교)
# (자세히는 plan/13 §S9 시나리오)

# 5. 5종 multi-agent 출력 동기화 검증
for agent in agents_md claude_md cursor_rules_mdc codex_config_toml gemini_md aider_conventions_md skill_md; do
  curl -sf "http://127.0.0.1:7777/api/v1/outputs/$agent" >/dev/null \
    && log "  ✓ $agent" || log "  ✗ $agent"
done

# 6. Hook latency p99 < 50ms (100회 호출)
log "Hook latency 100회 ..."
START=$(date +%s%N)
for i in $(seq 100); do echo "echo $i" | nc -U /run/user/$UID/traceweaver/hook.sock 2>/dev/null; done
END=$(date +%s%N)
ELAPSED_MS=$(( (END - START) / 1000000 ))
log "  100회 합산: ${ELAPSED_MS}ms (목표 <5000ms = avg <50ms)"

# 7. ★ Extraction schedule (ADR-15) — manual ↔ auto 전환 + interval 변경
curl -X PATCH http://127.0.0.1:7777/api/v1/extraction/schedule \
  -d '{"mode":"manual"}' -H "Content-Type: application/json"
sleep 1
SCHED=$(curl -s http://127.0.0.1:7777/api/v1/extraction/schedule | jq -r '.mode')
[ "$SCHED" = "manual" ] && log "✓ schedule: manual 적용 OK"
curl -X PATCH http://127.0.0.1:7777/api/v1/extraction/schedule \
  -d '{"mode":"auto","interval_seconds":1800}' -H "Content-Type: application/json"

# 8. ★ Onboarding wizard (5 step end-to-end via Playwright)
cd ui && pnpm exec playwright test --grep "@onboarding" --quiet && cd ..

# 9. 60초 dry-run
cd ui && time pnpm exec playwright test --grep "60s demo" --quiet && cd ..

log "=== Preflight 완료 — 위 ⚠ / ✗ 항목 검토 후 시연 ==="
```

---

## 8.5 데모 합격 기준 8개 (plan/16 §8 1:1)

본 preset이 만족시켜야 하는 plan의 *합격 기준*. preset 완료 시 모두 GREEN 가능해야 함.

| # | 기준 | preset 매핑 |
|---|------|------------|
| 1 | `pipx install traceweaver` 또는 `apt install ./traceweaver_amd64.deb` 한 줄 설치 동작 | `01` (apt) + `03` (uv tool/pipx) + `06` (systemd unit) |
| 2 | `tw shell init bash` → bashrc hook 설치 + 실 명령 데몬 도달 | `01` (netcat-openbsd) + `06` (hook.sock) + `03` (collector deps) |
| 3 | `tw demo seed` → GUI Evidence Inbox에 5–8 conventions + 3–5 Skill 표시 | `07` (demo_seed.yaml) + `04` (SPA) + `06` (daemon) |
| 4 | Secret regression test (10–20 fixture) 통과 | `07` (secret_corpus) + `03` (pyahocorasick) |
| 5 | ETH Zurich 4중 게이트 동작 — `is_inferable=true` / `evidence_count<3` 출력 X | `05` (LLM 백엔드 활성) — gate enforcement는 plan/07 §7.2 |
| 6 | `tw forget` 동작 (typed confirm) | `06` (data dir 쓰기 가능) + `03` (CLI deps) |
| 7 | 데몬이 시연 머신에서 동작 (체감 부담 없음) | `06` (systemd Type=notify) + `02` (Intel iGPU/NPU 가속) |
| 8 | GUI 7 화면 + 60초 demo + 5종 multi-agent 자동 갱신 | `04` (SPA + 22 shadcn) + `07` (golden snapshots) |

---

## 8.6 흔한 실패 모드 + 수정

| 증상 | 원인 | 해결 |
|------|------|------|
| `nc: invalid option -- U` | netcat-traditional 또는 ncat 사용 중 | `01_system_packages.md §1.6.1` — `update-alternatives --set nc /bin/nc.openbsd` |
| `Node version 18/20 detected` | apt nodejs 또는 stale NodeSource 사용 중 | `01_system_packages.md §1.4` — Node >=22 LTS 설치 |
| `OpenVINO devices: ['CPU']` (NPU/GPU 누락) | `02_intel_drivers.md` 단계 미완 또는 render 그룹 미소속 | `02 §2.2/§2.3` 재확인 + 재로그인 |
| `tailwind: utility @tailwindcss/vite missing` | Tailwind v3 syntax 잔재 (`tailwind.config.js` 사용) | `04 §4.6` 확인 — v4는 CSS-first only |
| `python-jose not found` | 이미 deprecate된 의존 (HMAC만 사용) | `03 §3.4` — `python-jose` 제거, `cryptography`로 통합 |
| `Type=notify timeout` 후 daemon fail | LLM 모델 컴파일이 30s 초과 | `06 §6.10` — `TimeoutStartSec=120s` 또는 `TW_LLM_DEVICE=CPU` |
| `sqlite-vec not loaded` | `sqlite_vec.load()` 호출 누락 또는 SQLite < 3.35 | `03 §3.8` — daemon lifespan 점검 |
| `gitleaks not found` | apt 미설치 (옵션) | `01 §1.2` — `sudo apt install gitleaks` 또는 GH release; 미설치 시에도 25 정규식만으로 동작 |
| `Permission denied: /run/user/$UID/...` | systemd-user 세션 X | `06 §6.10` — `loginctl enable-linger` + 재로그인 |

---

## 8.7 한 줄 요약

> 본 preset 9 파일을 모두 적용하고 `bash scripts/preset_bootstrap.sh --with-llm` + `tw doctor` 11/11 통과 시, `docs/plan` 19 파일 구현 (B0~B5 42 task) 시작 조건이 충족된다. 데모 시연 직전 `scripts/demo_preflight.sh`로 D-1 자동 검증.

---

## 8.8 Plan refs

- `docs/plan/10_observability_diagnostics.md §10.5` — `tw doctor` 11 체크 정의
- `docs/plan/16_roadmap.md §B5-7` — `scripts/demo_preflight.sh` 구현 태스크
- `docs/plan/17_risks.md §14` — D-1 preflight 체크리스트
- `docs/plan/13_user_scenarios.md §S9` — 60초 데모 시나리오 (preflight 흐름)
- `docs/plan/18_adrs.md §ADR-15` — `tw extract` + extraction_schedule (preflight §8.4 step 7)

---

이 문서로 `docs/preset/` 9 파일 세트가 완성된다. 구현 단계로 진행하기 전에 본 검증을 거치면 R2(LLM dep) / R3(GUI) / R5(dummy data) / R7(Intel driver) 위험을 사전에 감지·해결할 수 있다.
