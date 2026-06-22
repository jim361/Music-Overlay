# MVP Spec

## MVP 목표

Spotify 데스크톱 앱에서 재생 중인 음악을 GSMTC로 읽고, PySide6 투명 오버레이에 카드 형태로 표시한다.

MVP는 viewer-only 앱이다. 현재 곡 표시, 앨범아트, 진행률, 소스 선택, 위치 저장에 집중하고 플레이어 조작 기능은 넣지 않는다.

## 필수 기능

- PySide6 기반 frameless overlay window
- always-on-top 표시
- 투명 배경과 rounded card UI
- 더미 Provider로 UI 단독 실행 가능
- GSMTC Provider로 실제 Spotify 세션 조회 가능
- 곡 제목 표시
- 아티스트 표시
- 앨범명 표시
- 앨범아트 표시
- 재생 상태 표시
- 현재 시간 / 전체 시간 표시
- 진행바 표시
- 창 드래그 이동
- 창 위치 저장
- JSON 기반 기본 테마 로드
- source selection 기본 구조
- 우클릭 메뉴에서 source 전환
- 시스템 트레이 아이콘
- 시스템 트레이 메뉴에서 source 전환
- 시스템 트레이에서 오버레이 숨김/표시
- 별도 설정 창
- 우클릭 메뉴 또는 `Esc` 종료

## MVP에서 제외

- 앱별 볼륨 조절
- 재생/일시정지/이전/다음 버튼
- GSMTC playback command 실행
- 클릭 통과 모드
- 트레이 아이콘
- 실행 시 자동 시작
- Spotify Web API
- YouTube Music 전용 보정
- DirectX 후킹
- Overwolf
- Xbox Game Bar 위젯

## 완료 기준

### UI

- `py -3.12 main.py --provider dummy`로 오버레이가 실행된다.
- 오버레이를 드래그할 수 있다.
- 앱 종료 후 다음 실행에서 위치가 복원된다.
- `themes/default.json` 수정으로 색상, 크기, 투명도 일부가 바뀐다.

### GSMTC

- `py -3.12 main.py --provider gsmtc` 실행 시 Spotify 재생곡이 표시된다.
- 곡 변경 시 title, artist, album, artwork, progress가 갱신된다.
- 일시정지 상태가 표시된다.
- GSMTC 세션이 없으면 "No media playing" 상태를 표시한다.
- 우클릭 메뉴에서 Spotify/Chrome/Edge/current source를 선택할 수 있다.
- 시스템 트레이 메뉴에서 source를 선택하고 설정 창을 열 수 있다.
- 설정 창에서 source, thumbnail visibility, background opacity, time/progress visibility, font sizes, colors, reset position을 설정할 수 있다.
- 트레이 툴팁에서 현재 곡과 아티스트를 확인할 수 있다.

### 설계

- UI는 Provider 구현체에 직접 의존하지 않는다.
- `NowPlayingProvider` 인터페이스 뒤에 `DummyProvider`와 `GSMTCProvider`가 있다.
- source selection 정책은 Provider 또는 selector 계층에 분리되어 있다.

### Packaging

- `scripts/build_exe.ps1`로 PyInstaller onedir 빌드를 만들 수 있다.
- 결과물은 `dist\MusicSkinOverlay\MusicSkinOverlay.exe`이다.
- one-file exe는 초기 MVP 안정화 후 검토한다.
