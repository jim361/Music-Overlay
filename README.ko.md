# Music Overlay

[English](README.en.md)

Music Overlay는 Windows의 GSMTC(Global System Media Transport Controls) 정보를 읽어서 현재 재생 중인 곡을 작은 오버레이로 보여주는 앱입니다.

플레이어 조작 앱이 아니라 라디오의 now playing 카드처럼 "지금 무슨 노래가 재생 중인지"를 확인하는 viewer-only 앱입니다.

## 주요 기능

- Spotify, Chrome, Edge 등 Windows 미디어 세션 표시
- 자동 소스 선택 또는 Spotify/Chrome/Edge/current source 우선 선택
- 항상 위에 표시되는 compact overlay
- 시스템 트레이 메뉴
- 별도 설정 창
- 썸네일 표시 켜기/끄기
- 배경 투명도 0%~100%
- 시간/재생바 표시 켜기/끄기
- 제목/상세/메타 폰트 크기 조절
- 제목/상세/메타/accent 색상 조절
- GSMTC 위치 갱신이 느릴 때도 시간/재생바를 부드럽게 보간

## 다운로드 및 실행

1. [Releases](https://github.com/jim361/Music-Overlay/releases/latest) 페이지로 이동합니다.
2. `MusicSkinOverlay-...-win-x64.zip` 파일을 다운로드합니다.
3. 원하는 위치에 압축을 풉니다.
4. 아래 파일을 실행합니다.

```text
MusicSkinOverlay\MusicSkinOverlay.exe
```

주의:

- `MusicSkinOverlay.exe`만 따로 꺼내서 실행하지 마세요.
- `_internal` 폴더가 exe 옆에 그대로 있어야 합니다.
- 아직 코드 서명이 없어서 Windows SmartScreen 경고가 뜰 수 있습니다.

## 사용 방법

- 오버레이를 드래그해서 위치를 옮길 수 있습니다.
- 시스템 트레이 아이콘 클릭/더블클릭으로 오버레이를 숨기거나 다시 표시할 수 있습니다.
- 시스템 트레이 우클릭 메뉴에서 소스를 선택하거나 설정 창을 열 수 있습니다.
- 오버레이 우클릭 메뉴에서도 새로고침, 소스 선택, 설정, 종료가 가능합니다.
- `F5`: 즉시 새로고침
- `Esc`: 종료

## 설정

설정 창에서 다음 항목을 조절할 수 있습니다.

- Preferred source
- Show thumbnail
- Background opacity
- Show time
- Show progress bar
- Title size
- Detail size
- Meta size
- Title color
- Detail color
- Meta color
- Accent color
- Reset Position

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

Windows 실행 폴더를 빌드합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

빌드 결과:

```text
dist\MusicSkinOverlay\MusicSkinOverlay.exe
```

릴리즈 zip 생성:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version v0.1.0
```

결과:

```text
artifacts\MusicSkinOverlay-v0.1.0-win-x64.zip
```

## 참고

- 재생, 일시정지, 다음 곡, 이전 곡, seek 같은 플레이어 제어 기능은 제공하지 않습니다.
- 썸네일은 일반 사용 중 파일로 저장하지 않고 메모리에서 표시합니다.
- 여러 미디어 세션이 동시에 있으면 설정에서 우선 소스를 선택하세요.
- 현재 실행 파일은 unsigned 상태입니다.

## 라이선스

MIT. [LICENSE](LICENSE)를 참고하세요.
