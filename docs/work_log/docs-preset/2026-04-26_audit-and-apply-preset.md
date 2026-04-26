# 2026-04-26 — preset 문서 감사 및 적용 가능한 로컬 설정 반영

## Context

사용자가 `docs/preset/` 문서들이 구현 전 준비 절차를 담고 있으므로, 실제 PC에 이미 설치/설정된 항목은 제외하고, 잘못된 문서는 수정하며, Codex가 직접 할 수 있는 설정은 적용하고, 사용자/sudo가 필요한 항목은 별도 md로 정리해 달라고 요청했다.

작업 대상 PC는 Ubuntu 24.04.4 LTS, kernel `6.17.0-20-generic`, 사용자 `bh-mark-samsung`이다. 저장소는 아직 구현 파일(`pyproject.toml`, `ui/package.json`, systemd unit, fixtures)이 없는 문서 중심 상태라, `uv sync`, `pnpm install`, Playwright, systemd activation, 모델 변환은 구현 후 단계로 분리했다.

## Files changed

- `docs/preset/00_overview.md` (13-230) — canonical 9파일과 machine-specific `99_user_required_actions.md`의 경계를 명시하고 Node/APScheduler/dependency count를 실제 검증 결과에 맞게 보정.
- `docs/preset/01_system_packages.md` (16-210) — `sqlite3` CLI 누락, NodeSource 설치 순서/버전, GCC alternatives 이슈, verification script의 `nc`/`tmux` version 처리 수정.
- `docs/preset/02_intel_drivers.md` (16-281) — Ubuntu 24.04에서 후보가 없는 legacy Level Zero 패키지명을 제거하고, NPU 권한을 이 PC의 실제 `root:render` 모델에 맞게 수정.
- `docs/preset/03_python_environment.md` (6-388) — APScheduler stable pin을 `>=3.11,<4`로 보정하고, LLM 의존을 별도 optional group으로 분리.
- `docs/preset/04_node_frontend.md` (4-465) — Node 요구조건을 `>=22 LTS`로 조정하고, Playwright browser-only install과 `--with-deps` sudo 경계를 분리.
- `docs/preset/05_llm_models.md` (29-467) — LLM dependency group 설명, Llama 3.3 8B/Apache-2.0 오기, Ollama system service 설명, llama.cpp Vulkan prerequisites 수정.
- `docs/preset/06_systemd_runtime.md` (168-172) — TraceWeaver XDG 디렉토리 `chmod 700` 사전 생성 절차 추가.
- `docs/preset/07_test_fixtures.md` (97-358) — demo seed surface count 4→5 수정, sample repo bake script의 literal `\n` 버그를 `printf`로 수정, Node matrix를 `>=22 LTS`로 보정.
- `docs/preset/08_verification.md` (49-353) — bootstrap/smoke/preflight에서 `sqlite3`, Node >=22, current Intel package names, render group, nonexistent `--check-only` 호출을 수정.
- `docs/preset/99_user_required_actions.md` (신규, 1-149) — 이 PC에서 사용자/sudo가 해야 하는 apt source 정리, missing apt packages, GCC alternatives, render group, lingering, 구현 후 실행 항목 정리.
- `docs/work_log/docs-preset/2026-04-26_audit-and-apply-preset.md` (신규) — 본 세션 로그.

## Why

문서 오류 중 실제 구현을 막을 가능성이 큰 항목을 우선했다. `sqlite3`는 검증 명령에는 있었지만 apt 설치 목록에 없었고, Node는 이 PC에 nvm Node 24가 이미 있어 요구사항을 충족하지만 문서는 Node 22 only처럼 적혀 있었다. 2026-04-26 기준 Node 24는 Active LTS이고 Node 22는 Maintenance LTS라, preset은 Node `>=22 LTS`로 보정하는 편이 현재 PC 상태와 계획의 최소 요구를 모두 만족한다.

APScheduler는 PyPI stable 최신이 3.11.2이고 4.x stable이 없어 `>=4.0,<5`가 그대로는 설치 불가능했다. alpha 의존을 preset에 강제하면 첫 `uv sync`에서 실패할 수 있으므로, 구현 ADR은 scheduler-backed extraction으로 유지하되 preset pin은 stable `>=3.11,<4`로 낮췄다.

Intel 드라이버 문서는 실제 Ubuntu 24.04 apt 후보와 맞지 않았다. 이 PC에는 Meteor Lake iGPU/NPU가 있고 `/dev/accel/accel0`가 존재하지만 group은 `accel`이 아니라 `render`다. 따라서 권한 안내를 render 중심으로 바꿨고, apt 후보가 없는 `level-zero` / `intel-level-zero-gpu` 대신 현재 설치/후보가 있는 `libze1`, `libze-intel-gpu1`, `intel-opencl-icd` 중심으로 수정했다.

직접 적용한 설정은 사용자 권한으로 안전하게 가능한 것만 했다. sudo가 필요한 apt source 수정, apt install, group membership, `loginctl enable-linger`, GCC alternatives는 실행하지 않고 `99_user_required_actions.md`로 분리했다.

## Verification

- 실제 PC 상태 확인:
  ```bash
  lsb_release -ds
  uname -r
  python3.12 --version
  uv --version
  node --version
  dpkg-query -W ...
  ```
  확인 결과: Ubuntu 24.04.4, kernel 6.17, Python 3.12.3, uv 0.11.7, Node v24.15.0, Ollama 0.18.2 active.
- 적용 설정 검증:
  ```bash
  pnpm --version
  command -v pnpm
  find ~/.config/traceweaver ~/.local/share/traceweaver ~/.cache/traceweaver -maxdepth 3 -type d -printf '%m %p\n' | sort
  ```
  결과: pnpm `10.4.0`, 경로 `~/.nvm/versions/node/v24.15.0/bin/pnpm`, TraceWeaver XDG 디렉토리 모두 `700`.
- PyPI stable 확인:
  ```bash
  python3 -m pip index versions apscheduler | head -2
  ```
  결과: latest stable `apscheduler (3.11.2)`, 4.x stable 없음.
- stale 문구 검색:
  ```bash
  rg -n "setup_22|>=4\\.0,<5|Llama 3\\.3|render/accel|brower|4 surface|echo 'def test_smoke|--check-only|Node ≠ 22|intel-level-zero-gpu 미설치|sudo apt install intel-level-zero-gpu" docs/preset
  ```
  결과: 의도한 `pre-commit>=4.0,<5`와 legacy 패키지 설명 문맥 외 stale 항목 없음.
- `git status --short` 확인: `docs/preset/` 전체는 아직 untracked 상태라 기존 사용자 변경을 되돌리지 않았다.

## Follow-ups

- 사용자가 `docs/preset/99_user_required_actions.md`의 sudo 항목을 처리한 뒤, 재로그인 후 `render` 그룹/NPU 접근/GCC/apt source 상태를 다시 검증해야 한다.
- B0 구현으로 `pyproject.toml`, `uv.lock`, `ui/package.json`, `packaging/systemd/traceweaver.service`가 생긴 뒤 `uv sync`, `pnpm install`, Playwright 설치, systemd unit activation을 이어서 실행한다.
- `docs/plan/` 쪽에는 아직 APScheduler 4.x/Node 22 only 같은 표현이 남아 있을 수 있다. 이번 요청 범위는 `docs/preset/`였으므로 plan 문서 동기화는 별도 세션에서 처리한다.
