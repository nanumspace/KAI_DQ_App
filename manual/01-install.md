# 1. 설치

## 설치 파일 받기

GitHub 저장소의 **Releases** 페이지에서 운영체제에 맞는 파일을 받습니다.

| 운영체제 | 파일 |
|---|---|
| Windows 11 (64비트) | `Quality Validator Setup <버전>.exe` |
| macOS (Apple Silicon 또는 Intel) | `Quality Validator-<버전>.dmg` |

## Windows

1. 받은 `.exe` 파일을 실행합니다.
2. "Windows의 PC 보호" 경고가 뜨면 **추가 정보**를 누른 뒤 **실행**을 누릅니다. 설치 파일에 코드 서명이 아직 없어서 나오는 경고입니다.
3. 설치가 끝나면 시작 메뉴의 **Quality Validator**로 엽니다.

## macOS

1. 받은 `.dmg`를 열고 **Quality Validator**를 **Applications** 폴더로 끌어다 놓습니다.
2. 처음 열 때 "확인되지 않은 개발자" 경고가 뜨면, Finder에서 앱을 **control 키를 누른 채 클릭**하고 **열기**를 선택합니다. 한 번 허용하면 다음부터는 바로 열립니다.
3. 그래도 열리지 않으면 **시스템 설정 → 개인정보 보호 및 보안**에서 **그래도 열기**를 누릅니다.

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
