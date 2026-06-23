# Music Overlay

Windows에서 지금 재생 중인 음악과 영상을 작고 깔끔한 오버레이로 보여주는 앱입니다.

Spotify, Chrome, Edge처럼 Windows GSMTC(Global System Media Transport Controls)에 노출되는 미디어 세션을 읽어서, 화면 위에 "지금 무엇이 재생 중인지"만 보여줍니다. 재생/일시정지/넘기기 버튼을 넣은 미니 플레이어가 아니라, 라디오의 now playing 카드처럼 가볍게 보는 용도로 만들었습니다.

[English](README.en.md)

## 목차

- [왜 만들었나요?](#왜-만들었나요)
- [주요 기능](#주요-기능)
- [다운로드](#다운로드)
- [사용 방법](#사용-방법)
- [설정](#설정)
- [소스에서 실행](#소스에서-실행)
- [빌드](#빌드)
- [주의 사항](#주의-사항)
- [라이선스](#라이선스)

## 왜 만들었나요?

음악을 틀어두고 작업하다 보면 지금 무슨 곡이 나오는지 확인하고 싶을 때가 있습니다. 하지만 플레이어 창을 열거나 브라우저 탭을 찾는 일은 흐름을 끊습니다.

Music Overlay는 그 순간만 해결합니다.

- 화면 한쪽에 현재 재생 정보를 작게 표시
- 필요하면 곡이 바뀔 때만 잠깐 표시
- 재생 제어 버튼 없이 viewer-only로 단순하게 유지
- Spotify, YouTube Music in browser, 일반 웹 영상 등 Windows 미디어 세션을 활용

## 주요 기능

- Spotify, Chrome, Edge, 현재 Windows 미디어 세션 표시
- Auto / Spotify / Chrome / Edge / Current source 선택
- 항상 표시 또는 미디어 변경 시 일정 시간만 표시
- 썸네일만 표시하는 앨범 자켓 모드
- 제목, 상세 정보, 시간, 재생바 개별 표시/숨김
- 긴 제목은 지정한 폭에서 `...` 처리
- 배경 투명도 0%~100%
- 폰트, 폰트 크기, 색상 커스터마이징
- 한국어 / 영어 설정 UI
- 시스템 트레이 아이콘과 우클릭 메뉴
- Python 설치 없이 실행 가능한 설치 마법사/포터블 빌드

## 다운로드

가장 쉬운 방법은 설치 마법사를 사용하는 것입니다.

1. [Releases](https://github.com/jim361/Music-Overlay/releases/latest) 페이지로 이동합니다.
2. `MusicOverlaySetup-...-win-x64.exe` 파일을 다운로드합니다.
3. 설치 마법사를 실행합니다.
4. 시작 메뉴 또는 바탕화면 바로가기로 실행합니다.

포터블 방식으로 쓰고 싶다면:

1. `MusicSkinOverlay-...-win-x64.zip` 파일을 다운로드합니다.
2. 원하는 위치에 압축을 풉니다.
3. 아래 파일을 실행합니다.

```text
MusicSkinOverlay\MusicSkinOverlay.exe
```

포터블 버전에서는 `_internal` 폴더가 실행 파일 옆에 그대로 있어야 합니다. `MusicSkinOverlay.exe`만 따로 꺼내서 실행하지 마세요.

## 사용 방법

- 오버레이를 드래그해서 위치를 옮길 수 있습니다.
- 시스템 트레이 아이콘 클릭/더블클릭으로 오버레이를 숨기거나 다시 표시할 수 있습니다.
- 시스템 트레이 우클릭 메뉴에서 소스 선택, 새로고침, 설정, 종료를 할 수 있습니다.
- 오버레이 우클릭 메뉴에서도 새로고침, 소스 선택, 설정, 종료를 할 수 있습니다.
- `F5`: 즉시 새로고침
- `Esc`: 종료

## 설정

설정 창은 `Basic`과 `Advanced`로 나뉩니다.

### Basic

- `Language`: English / 한국어
- `Preferred source`: Auto, Spotify, Chrome, Edge, Current Windows session
- `Display mode`: 항상 표시 또는 미디어 변경 시 표시
- `Show duration`: 자동 숨김 모드에서 표시할 시간
- `Thumbnail`: 앨범아트/썸네일 표시
- `Title`: 제목 표시
- `Details`: 아티스트/앨범 표시
- `Time`: 시간 표시
- `Progress`: 재생바 표시

앨범 자켓만 보고 싶다면 `Thumbnail`만 켜고 `Title`, `Details`, `Time`, `Progress`를 끄면 됩니다.

### Advanced

- `Background opacity`: 오버레이 배경 투명도
- `Overlay text width`: 긴 제목이 어디부터 `...` 처리될지 결정하는 폭
- `Font`: PC에 설치된 시스템 폰트 선택
- `Title / Detail / Meta size`: 글자 크기
- `Title / Detail / Meta / Accent color`: 색상

## 소스에서 실행

필요 환경:

- Windows 10 이상
- Python 3.12

의존성 설치:

```powershell
py -3.12 -m pip install -r requirements.txt
```

실제 GSMTC provider로 실행:

```powershell
py -3.12 main.py
```

더미 데이터로 UI 확인:

```powershell
py -3.12 main.py --provider dummy
```

특정 소스를 우선 선택:

```powershell
py -3.12 main.py --provider gsmtc --source spotify
py -3.12 main.py --provider gsmtc --source chrome
```

## 빌드

Windows 실행 폴더 빌드:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

릴리스 zip 생성:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version v0.3.0
```

설치 마법사 생성:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1 -Version v0.3.0
```

설치 마법사 빌드에는 Inno Setup 6가 필요합니다.

## 주의 사항

- 재생, 일시정지, 다음 곡, 이전 곡, seek 같은 플레이어 제어 기능은 제공하지 않습니다.
- 썸네일은 일반 사용 중 파일로 저장하지 않고 메모리에서 표시합니다.
- 여러 미디어 세션이 동시에 있으면 설정에서 우선 소스를 선택하세요.
- 현재 실행 파일은 코드 서명되지 않았으므로 Windows SmartScreen 경고가 뜰 수 있습니다.
- 폰트 파일은 앱에 포함하지 않습니다. 사용자의 PC에 설치된 시스템 폰트를 선택해서 사용합니다.

## 라이선스

MIT. [LICENSE](LICENSE)를 참고하세요.
