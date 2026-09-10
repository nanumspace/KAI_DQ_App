#!/usr/bin/env bash
# Quality Validator 릴리스: 빌드 → 코드 서명 → 공증 → 검증 → GitHub Release
#
# 사용법
#   ./release.sh                 package.json 의 버전으로 릴리스
#   ./release.sh 0.2.0           버전을 0.2.0 으로 올리고(커밋) 릴리스
#   옵션  --skip-mac  --skip-win  macOS / Windows 빌드 생략
#         --no-publish            빌드·서명·공증·검증까지만 (태그·Release 안 만듦)
#         --publish-only          release/ 에 이미 있는 산출물로 태그·Release 만
#         --unsigned              서명·공증 없이 빌드 (시험용, 배포 금지)
#         --replace               같은 버전의 기존 태그와 GitHub Release 를 지우고 다시 게시
#
# 준비물 (한 번만)
#   brew install osslsigncode opensc gh
#   토큰 PIN     : security add-generic-password -a "$USER" -s kai-safenet-pin -w
#   Apple 공증   : xcrun notarytool store-credentials kai-notary --apple-id <Apple ID> --team-id <Team ID>
#   GitHub 로그인: gh auth login
#   SafeNet USB 토큰을 꽂아 둔다. 키체인에 "Developer ID Application" 인증서가 있어야 한다.
#   앱 아이콘은 app/build/icon.svg → icon.png (1024×1024). SVG 를 고치면 아래로 다시 만든다:
#     qlmanage -t -s 1024 -o app/build app/build/icon.svg && mv app/build/icon.svg.png app/build/icon.png
#
# 산출물 (app/release/)
#   QualityValidator-<버전>-mac-arm64.dmg     Developer ID 서명 + 공증 + staple
#   QualityValidator-<버전>-win-x64.exe       GlobalSign EV 서명 (SafeNet 토큰)
#   QualityValidator-<버전>-win-arm64.exe
#   SampleData-<버전>-<COHORT>-<clean|dirty>.zip ×12, SampleData-<버전>-all.zip   견본 데이터 (가상데이터, app/build/pack-samples.cjs)
#   SHA256SUMS.txt

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$ROOT/app"
NOTARY_PROFILE="${KAI_NOTARY_PROFILE:-kai-notary}"
PIN_SERVICE="${KAI_PIN_SERVICE:-kai-safenet-pin}"
PKCS11_MODULE="${KAI_PKCS11_MODULE:-/opt/homebrew/lib/opensc-pkcs11.so}"
CACHE="$HOME/Library/Caches/kai-release"
WIN_ARCHS=(x64 arm64)

SKIP_MAC=0; SKIP_WIN=0; PUBLISH=1; PUBLISH_ONLY=0; UNSIGNED=0; REPLACE=0; NEW_VERSION=""
for a in "$@"; do
  case "$a" in
    --skip-mac) SKIP_MAC=1 ;;
    --skip-win) SKIP_WIN=1 ;;
    --no-publish) PUBLISH=0 ;;
    --publish-only) PUBLISH_ONLY=1 ;;
    --unsigned) UNSIGNED=1 ;;
    --replace) REPLACE=1 ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    [0-9]*) NEW_VERSION="$a" ;;
    *) echo "알 수 없는 옵션: $a" >&2; exit 2 ;;
  esac
done

log()  { printf '\n\033[1;36m▶ %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
fail() { printf '  \033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "$1 이(가) 없습니다. $2"; }

# ---------------------------------------------------------------- 1. 사전 점검
log "사전 점검"
[ "$(uname)" = "Darwin" ] || fail "이 스크립트는 macOS 에서 실행합니다 (Windows 서명은 토큰, macOS 서명은 키체인)."
need node "https://nodejs.org"; need npm ""; need git ""; need gh "brew install gh"
[ "$UNSIGNED" = 1 ] && ok "서명 없는 시험 빌드 (--unsigned). 배포하지 마세요." || true
if [ "$UNSIGNED" = 0 ]; then
  if [ "$SKIP_WIN" = 0 ]; then
    need osslsigncode "brew install osslsigncode"; need pkcs11-tool "brew install opensc"
    [ -f "$PKCS11_MODULE" ] || fail "PKCS#11 모듈이 없습니다: $PKCS11_MODULE (brew install opensc)"
    pkcs11-tool --module "$PKCS11_MODULE" -L 2>/dev/null | grep -q "token label" || fail "USB 토큰이 인식되지 않습니다. 꽂혀 있는지 확인하세요."
    security find-generic-password -s "$PIN_SERVICE" >/dev/null 2>&1 || fail "토큰 PIN 이 키체인에 없습니다: security add-generic-password -a \"\$USER\" -s $PIN_SERVICE -w"
    pkcs11-tool --module "$PKCS11_MODULE" --login --pin "$(security find-generic-password -s "$PIN_SERVICE" -w)" -O 2>/dev/null | grep -q "Private Key" \
      || fail "토큰 로그인에 실패했습니다 (PIN 이 틀렸거나 개인키가 없음)."
    [ -f "$APP/build/globalsign-ev-codesigning-ca-2020.pem" ] || fail "중간 인증서가 없습니다: app/build/globalsign-ev-codesigning-ca-2020.pem"
    ok "SafeNet 토큰, PIN, 중간 인증서"
  fi
  if [ "$SKIP_MAC" = 0 ]; then
    security find-identity -v -p codesigning | grep -q "Developer ID Application" || fail "키체인에 Developer ID Application 인증서가 없습니다."
    xcrun notarytool history --keychain-profile "$NOTARY_PROFILE" >/dev/null 2>&1 \
      || fail "공증 프로필이 없습니다: xcrun notarytool store-credentials $NOTARY_PROFILE --apple-id <Apple ID> --team-id <Team ID>"
    ok "Developer ID 인증서, 공증 프로필 $NOTARY_PROFILE"
  fi
fi
if [ "$PUBLISH" = 1 ] || [ "$PUBLISH_ONLY" = 1 ]; then
  gh auth status >/dev/null 2>&1 || fail "GitHub 에 로그인되어 있지 않습니다: gh auth login"
  [ "$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)" = "main" ] || fail "main 브랜치에서 실행하세요."
  ok "GitHub 로그인, main 브랜치"
fi

# ---------------------------------------------------------------- 2. 버전
cd "$APP"
if [ -n "$NEW_VERSION" ]; then
  log "버전 올리기: $NEW_VERSION"
  npm version "$NEW_VERSION" --no-git-tag-version >/dev/null
  (cd "$ROOT/dq-ts" && npm version "$NEW_VERSION" --no-git-tag-version >/dev/null) || true
  git -C "$ROOT" add app/package.json app/package-lock.json dq-ts/package.json dq-ts/package-lock.json 2>/dev/null || true
  git -C "$ROOT" commit -q -m "버전 $NEW_VERSION" && ok "커밋: 버전 $NEW_VERSION"
fi
VERSION="$(node -p "require('./package.json').version")"
TAG="v$VERSION"
OUT="$APP/release"
log "릴리스 버전 $TAG"
if [ "$PUBLISH" = 1 ] || [ "$PUBLISH_ONLY" = 1 ]; then
  [ -z "$(git -C "$ROOT" status --porcelain)" ] || fail "커밋되지 않은 변경이 있습니다. 먼저 커밋하세요 (git status)."
  if [ "$REPLACE" = 1 ]; then
    gh release view "$TAG" >/dev/null 2>&1 && gh release delete "$TAG" --yes --cleanup-tag >/dev/null && ok "기존 Release $TAG 삭제"
    git -C "$ROOT" tag -d "$TAG" >/dev/null 2>&1 || true
    git -C "$ROOT" push -q --delete origin "$TAG" >/dev/null 2>&1 || true
  else
    git -C "$ROOT" rev-parse "$TAG" >/dev/null 2>&1 && fail "태그 $TAG 가 이미 있습니다. 새 버전을 지정하거나 --replace 를 쓰세요."
    gh release view "$TAG" >/dev/null 2>&1 && fail "Release $TAG 가 이미 GitHub 에 있습니다. 다시 게시하려면 --replace 를 쓰세요."
  fi
fi

# ---------------------------------------------------------------- 3. 빌드 준비
BINDINGS="$APP/node_modules/@duckdb"
STASH="$APP/node_modules/.kai-bindings-stash"
restore_bindings() {
  if [ -d "$STASH" ]; then
    for d in "$STASH"/node-bindings-*; do [ -d "$d" ] && rm -rf "$BINDINGS/$(basename "$d")" && mv "$d" "$BINDINGS/"; done
    rmdir "$STASH" 2>/dev/null || true
  fi
}
trap restore_bindings EXIT
# 빌드 대상 플랫폼의 DuckDB 바이너리만 node_modules 에 남긴다 (설치본 크기를 줄이기 위해)
select_binding() {
  local keep="$1"
  mkdir -p "$STASH"
  for d in "$BINDINGS"/node-bindings-*; do
    [ -d "$d" ] || continue
    local n; n="$(basename "$d")"
    if [ "$n" != "$keep" ]; then rm -rf "$STASH/$n"; mv "$d" "$STASH/"; fi
  done
  if [ ! -d "$BINDINGS/$keep" ]; then
    if [ -d "$STASH/$keep" ]; then mv "$STASH/$keep" "$BINDINGS/"; else fail "DuckDB 바이너리가 없습니다: $keep"; fi
  fi
}
ensure_win_binding() {
  local arch="$1" ver tgz
  ver="$(node -p "require('$BINDINGS/node-bindings/package.json').version")"
  [ -d "$BINDINGS/node-bindings-win32-$arch" ] || [ -d "$STASH/node-bindings-win32-$arch" ] && return 0
  mkdir -p "$CACHE"; tgz="$CACHE/node-bindings-win32-$arch-$ver.tgz"
  [ -f "$tgz" ] || curl -fsSL "https://registry.npmjs.org/@duckdb/node-bindings-win32-$arch/-/node-bindings-win32-$arch-$ver.tgz" -o "$tgz"
  mkdir -p "$BINDINGS/node-bindings-win32-$arch"
  tar -xzf "$tgz" -C "$BINDINGS/node-bindings-win32-$arch" --strip-components=1
  ok "DuckDB win32-$arch $ver 준비"
}

if [ "$PUBLISH_ONLY" = 0 ]; then
  log "의존성과 렌더러 빌드"
  [ -d node_modules ] || npm ci
  npm run typecheck >/dev/null && ok "타입 검사"
  npx electron-vite build >/dev/null && ok "electron-vite build"
  mkdir -p "$OUT"
  [ "$SKIP_MAC" = 0 ] && rm -rf "$OUT"/*.dmg "$OUT"/*.dmg.blockmap "$OUT"/mac-* 2>/dev/null || true
  [ "$SKIP_WIN" = 0 ] && rm -rf "$OUT"/*.exe "$OUT"/*.exe.blockmap "$OUT"/win-* 2>/dev/null || true
  rm -f "$OUT"/SHA256SUMS.txt "$OUT"/SampleData-*.zip

  # -------------------------------------------------------------- 4. macOS
  if [ "$SKIP_MAC" = 0 ]; then
    log "macOS arm64 빌드·서명·공증"
    select_binding node-bindings-darwin-arm64
    if [ "$UNSIGNED" = 1 ]; then
      CSC_IDENTITY_AUTO_DISCOVERY=false npx electron-builder --mac --arm64 --publish never -c.mac.notarize=false
    else
      APPLE_KEYCHAIN_PROFILE="$NOTARY_PROFILE" npx electron-builder --mac --arm64 --publish never
      DMG="$(ls "$OUT"/*.dmg)"
      log "DMG 공증과 staple: $(basename "$DMG")"
      xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait | tail -3
      xcrun stapler staple "$DMG" >/dev/null && ok "staple"
    fi
  fi

  # -------------------------------------------------------------- 5. Windows
  if [ "$SKIP_WIN" = 0 ]; then
    for arch in "${WIN_ARCHS[@]}"; do
      log "Windows $arch 빌드·서명"
      ensure_win_binding "$arch"
      select_binding "node-bindings-win32-$arch"
      if [ "$UNSIGNED" = 1 ]; then
        KAI_SKIP_WIN_SIGN=1 npx electron-builder --win "--$arch" --publish never
      else
        npx electron-builder --win "--$arch" --publish never
      fi
      # 설치본에 든 DuckDB 바이너리가 이 아키텍처 것인지 확인
      unpacked="$OUT/win-unpacked"; [ "$arch" = "arm64" ] && unpacked="$OUT/win-arm64-unpacked"
      [ -d "$unpacked/resources/app.asar.unpacked/node_modules/@duckdb/node-bindings-win32-$arch" ] || fail "win32-$arch 설치본에 DuckDB win32-$arch 바이너리가 없습니다."
      [ "$(ls -d "$unpacked"/resources/app.asar.unpacked/node_modules/@duckdb/node-bindings-*/ | wc -l | tr -d " ")" = 1 ] || fail "win32-$arch 설치본에 다른 플랫폼의 DuckDB 바이너리가 섞였습니다."
      ok "Windows $arch: $(ls "$OUT"/*-win-$arch.exe | xargs -n1 basename)"
    done
  fi
  restore_bindings

fi

# ---------------------------------------------------------------- 6. 견본 데이터와 검증
{
  log "견본 데이터 묶음 (가상데이터)"
  rm -f "$OUT"/SampleData-*.zip
  node "$APP/build/pack-samples.cjs" "$OUT" "$VERSION"
  log "산출물 검증"
  rm -rf "$OUT"/*.blockmap "$OUT"/builder-*.yml "$OUT"/latest*.yml "$OUT"/*-unpacked "$OUT"/mac-* "$OUT"/.icon-* 2>/dev/null || true
  if [ "$UNSIGNED" = 0 ]; then
    for f in "$OUT"/*.exe; do
      [ -f "$f" ] || continue
      osslsigncode verify -CAfile "$APP/build/globalsign-codesigning-root-r45.pem" -in "$f" 2>/dev/null | grep -q "Signature verification: ok" && ok "서명 확인: $(basename "$f")" || fail "서명 검증 실패: $(basename "$f")"
    done
    for f in "$OUT"/*.dmg; do
      [ -f "$f" ] || continue
      spctl -a -t open --context context:primary-signature -v "$f" 2>&1 | grep -q "accepted" && ok "Gatekeeper 확인: $(basename "$f")" || fail "Gatekeeper 검증 실패: $(basename "$f")"
      xcrun stapler validate "$f" >/dev/null 2>&1 && ok "staple 확인" || fail "staple 검증 실패"
    done
  fi
  (cd "$OUT" && shasum -a 256 *.dmg *.exe *.zip 2>/dev/null > SHA256SUMS.txt) && ok "SHA256SUMS.txt"
  ls -lh "$OUT" | awk 'NR>1 {printf "  %8s  %s\n", $5, $9}'
}

# ---------------------------------------------------------------- 7. 게시
if [ "$PUBLISH" = 0 ] && [ "$PUBLISH_ONLY" = 0 ]; then
  log "--no-publish: 태그와 Release 는 만들지 않았습니다. 게시하려면: ./release.sh --publish-only"
  exit 0
fi
log "GitHub Release $TAG"
ASSETS=("$OUT"/*.dmg "$OUT"/*.exe "$OUT"/SampleData-*.zip "$OUT"/SHA256SUMS.txt)
NOTES="$(mktemp)"
{
  echo "## Quality Validator $TAG"
  echo
  echo "| 파일 | 대상 | 서명 |"
  echo "|---|---|---|"
  for f in "$OUT"/*.dmg; do [ -f "$f" ] && echo "| \`$(basename "$f")\` | macOS (Apple Silicon) | Developer ID 서명, Apple 공증 |"; done
  for f in "$OUT"/*-win-x64.exe; do [ -f "$f" ] && echo "| \`$(basename "$f")\` | Windows 10/11 64비트 (x64) | GlobalSign EV 코드 서명 |"; done
  for f in "$OUT"/*-win-arm64.exe; do [ -f "$f" ] && echo "| \`$(basename "$f")\` | Windows 11 ARM (arm64) | GlobalSign EV 코드 서명 |"; done
  echo
  echo "### 견본 데이터 (가상데이터)"
  echo
  echo "앱 동작을 확인할 때 쓰는 가상데이터입니다. 실제 환자와 무관합니다. \`SampleData-$VERSION-all.zip\` 은 6개 코호트 × clean(오류 없음) / dirty(오류 주입 + 정답표) 12개 폴더 전체이고, 코호트별 zip 은 그중 하나입니다. 각 zip 의 README.txt 에 기대 결과(규칙 수, 위반 건수)가 있습니다. 폴더째 앱의 검증 실행 화면에 끌어다 놓으면 됩니다."
  echo
  echo "설치와 사용 방법은 [사용자 설명서](https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/blob/main/manual/README.md)를 보세요."
  echo
  echo "### SHA-256"
  echo '```'
  cat "$OUT/SHA256SUMS.txt"
  echo '```'
} > "$NOTES"
if ! git -C "$ROOT" rev-parse "$TAG" >/dev/null 2>&1; then
  git -C "$ROOT" tag -a "$TAG" -m "Quality Validator $TAG"
fi
git -C "$ROOT" push -q origin main "$TAG" && ok "push: main, $TAG"
gh release create "$TAG" "${ASSETS[@]}" --title "Quality Validator $TAG" --notes-file "$NOTES" --latest
rm -f "$NOTES"
ok "Release: $(gh release view "$TAG" --json url -q .url)"
