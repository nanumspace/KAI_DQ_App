// electron-builder 의 Windows 사용자 정의 서명 훅.
// macOS 에서 SafeNet USB 토큰(GlobalSign EV Code Signing)으로 osslsigncode + OpenSC PKCS#11 을 써서 서명한다.
// electron-builder 가 만드는 exe(앱 본체, 언인스톨러, NSIS 설치 파일)마다 한 번씩 호출된다.
//
// 필요한 것
//   - brew: osslsigncode, opensc (PKCS#11 모듈 /opt/homebrew/lib/opensc-pkcs11.so)
//   - 토큰 PIN: macOS 키체인 항목 kai-safenet-pin  (security add-generic-password -a "$USER" -s kai-safenet-pin -w)
//   - 중간 인증서: build/globalsign-ev-codesigning-ca-2020.pem
// 환경 변수로 바꿀 수 있는 것
//   KAI_PKCS11_MODULE  PKCS#11 모듈 경로
//   KAI_PKCS11_TOKEN   토큰 이름 (URL 인코딩). 인증서를 다른 토큰으로 바꾸면 수정
//   KAI_PKCS11_ID      토큰 안 인증서·개인키 객체 id (기본 %00%01)
//   KAI_PIN_SERVICE    키체인 서비스 이름 (기본 kai-safenet-pin)
//   KAI_TSA_URL        RFC 3161 타임스탬프 서버 (기본 http://timestamp.digicert.com)
//   KAI_SKIP_WIN_SIGN  1 이면 서명하지 않음 (서명 없는 시험 빌드)

const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const MODULE = process.env.KAI_PKCS11_MODULE || "/opt/homebrew/lib/opensc-pkcs11.so";
const PIN_SERVICE = process.env.KAI_PIN_SERVICE || "kai-safenet-pin";
const TSA = process.env.KAI_TSA_URL || "http://timestamp.digicert.com";
const CHAIN = path.join(__dirname, "globalsign-ev-codesigning-ca-2020.pem");
// 토큰에 슬롯이 둘(일반 PIN, Digital Signature PIN)이라 토큰 이름으로 슬롯을 고정한다 (pkcs11-tool -L 의 token label, URL 인코딩)
const TOKEN = process.env.KAI_PKCS11_TOKEN || "Nanum%20Space%20Co%2c.Ltd";
// 토큰 안의 인증서와 개인키 (pkcs11-tool -O 로 확인한 id=00 01)
const OBJECT_ID = process.env.KAI_PKCS11_ID || "%00%01";
const CERT_URI = `pkcs11:token=${TOKEN};id=${OBJECT_ID};type=cert`;
const KEY_URI = `pkcs11:token=${TOKEN};id=${OBJECT_ID};type=private`;
// Homebrew OpenSSL 은 자기 Cellar 안에서만 provider 를 찾으므로 libp11 이 설치한 위치를 알려 준다
const OPENSSL_ENV = {
  ...process.env,
  OPENSSL_MODULES: process.env.OPENSSL_MODULES || "/opt/homebrew/lib/ossl-modules",
  OPENSSL_ENGINES: process.env.OPENSSL_ENGINES || "/opt/homebrew/lib/engines-3",
};

function readPin() {
  if (process.env.KAI_TOKEN_PIN) return process.env.KAI_TOKEN_PIN;
  try {
    return execFileSync("security", ["find-generic-password", "-s", PIN_SERVICE, "-w"], { stdio: ["ignore", "pipe", "ignore"] })
      .toString()
      .trim();
  } catch {
    throw new Error(`토큰 PIN 을 키체인에서 읽지 못했습니다. 저장: security add-generic-password -a "$USER" -s ${PIN_SERVICE} -w`);
  }
}

module.exports = async function signWindows(configuration) {
  const file = configuration.path;
  if (process.env.KAI_SKIP_WIN_SIGN === "1") {
    console.log(`  [sign-win] 건너뜀 (KAI_SKIP_WIN_SIGN=1): ${path.basename(file)}`);
    return;
  }
  if (!fs.existsSync(MODULE)) throw new Error(`PKCS#11 모듈이 없습니다: ${MODULE} (brew install opensc)`);
  if (!fs.existsSync(CHAIN)) throw new Error(`중간 인증서가 없습니다: ${CHAIN}`);

  const hash = configuration.hash === "sha2" ? "sha256" : configuration.hash || "sha256";
  const pin = readPin();
  // PIN 은 명령줄 인자 대신 0600 임시 파일로 전달한다 (프로세스 목록에 노출되지 않도록)
  const passDir = fs.mkdtempSync(path.join(os.tmpdir(), "kai-sign-"));
  const passFile = path.join(passDir, "pass");
  fs.writeFileSync(passFile, pin, { mode: 0o600 });
  const out = `${file}.signed`;
  const args = [
    "sign",
    "-pkcs11module", MODULE,
    "-pkcs11cert", CERT_URI,
    "-key", KEY_URI,
    "-provider", "pkcs11prov",
    "-readpass", passFile,
    "-ac", CHAIN,
    "-h", hash,
    "-n", "Quality Validator",
    "-i", "https://github.com/nanumspace/KAI_DQ_App",
    "-ts", TSA,
    "-in", file,
    "-out", out,
  ];
  try {
    execFileSync("osslsigncode", args, { stdio: ["ignore", "pipe", "pipe"], env: OPENSSL_ENV });
    fs.renameSync(out, file);
    console.log(`  [sign-win] 서명 완료 (${hash}, ${TSA}): ${path.basename(file)}`);
  } catch (e) {
    const msg = (e.stderr && e.stderr.toString()) || (e.stdout && e.stdout.toString()) || e.message;
    throw new Error(`osslsigncode 서명 실패: ${path.basename(file)}\n${msg}`);
  } finally {
    fs.rmSync(passDir, { recursive: true, force: true });
    if (fs.existsSync(out)) fs.rmSync(out, { force: true });
  }
};
