# 1. 설치

## 설치 파일 받기

GitHub 저장소의 **Releases** 페이지에서 운영체제에 맞는 파일을 받습니다.

| 운영체제 | 파일 |
|---|---|
| Windows 10/11 64비트 (일반 PC) | `QualityValidator-<버전>-win-x64.exe` |
| Windows 11 ARM (Snapdragon 등 ARM 노트북) | `QualityValidator-<버전>-win-arm64.exe` |
| macOS (Apple Silicon) | `QualityValidator-<버전>-mac-arm64.dmg` |

어느 것을 받을지 모르면 Windows 는 x64, Mac 은 arm64 를 받습니다. 32비트 Windows 와 Intel Mac 용은 제공하지 않습니다.

설치 파일은 모두 코드 서명이 되어 있습니다. Windows 는 GlobalSign EV 인증서(게시자 Nanum Space Co,. Ltd), macOS 는 Apple Developer ID 서명과 공증입니다. 파일의 SHA-256 은 Release 페이지의 `SHA256SUMS.txt` 와 대조할 수 있습니다.

## Windows

1. 받은 `.exe` 파일을 실행합니다. 파일 속성의 "디지털 서명" 탭에서 서명자 **Nanum Space Co,. Ltd** 를 확인할 수 있습니다.
2. 설치 위치를 확인하고 설치합니다. 관리자 권한 없이 사용자 폴더에 설치됩니다.
3. 설치가 끝나면 시작 메뉴의 **Quality Validator**로 엽니다.

"Windows의 PC 보호" 경고가 뜨면 파일이 손상되었거나 다른 곳에서 받은 것입니다. Release 페이지에서 다시 받습니다.

## macOS

1. 받은 `.dmg`를 열고 **Quality Validator**를 **Applications** 폴더로 끌어다 놓습니다.
2. Applications 폴더에서 앱을 엽니다. 공증된 앱이므로 경고 없이 열립니다.

"확인되지 않은 개발자" 경고가 뜨면 파일이 손상되었거나 다른 곳에서 받은 것입니다. Release 페이지에서 다시 받습니다.

## 설치 후 확인

- 프로그램은 인터넷 연결 없이 동작합니다. 방화벽이나 망 분리 환경에서도 그대로 쓸 수 있습니다.
- 명세와 검증 규칙은 프로그램 안에 들어 있습니다. 따로 받을 파일이 없습니다.
- 실행 결과와 이력은 사용자 컴퓨터의 앱 데이터 폴더에 저장됩니다. 위치는 **설정** 화면에서 볼 수 있습니다.

| 운영체제 | 저장 위치 |
|---|---|
| Windows | `%APPDATA%\kai-quality-validator` |
| macOS | `~/Library/Application Support/kai-quality-validator` |

## 삭제

Windows는 **설정 → 앱**에서, macOS는 Applications 폴더에서 앱을 지웁니다. 실행 이력까지 지우려면 위 저장 위치 폴더를 함께 지웁니다.
