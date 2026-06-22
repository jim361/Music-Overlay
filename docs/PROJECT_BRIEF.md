# Music Skin Overlay Project Brief

## 목적

Music Skin Overlay는 Windows에서 현재 재생 중인 음악 정보를 작은 커스텀 오버레이 카드로 보여주는 데스크톱 앱이다.

초기 목표는 Spotify 데스크톱 앱과 Chrome/Edge 기반 미디어 세션을 대상으로, 게임을 전체창모드 또는 Borderless fullscreen으로 실행할 때 현재 곡 정보를 화면 위에 표시하는 것이다.

제품 방향은 음악 플레이어 조작 앱이 아니라 라디오의 now playing 패널처럼 현재 재생 정보를 가볍게 확인하는 viewer-only 오버레이이다.

## 핵심 가치

- Spotify 전용 미니플레이어가 아니라 Windows 미디어 세션 기반 오버레이로 시작한다.
- 사용자가 원하는 카드형 UI, 색상, 투명도, 표시 요소를 테마로 조정할 수 있게 한다.
- DirectX 후킹, DLL 인젝션, 안티치트 우회 같은 위험한 방식은 사용하지 않는다.
- 독점 전체화면보다 창모드, 전체창모드, Borderless fullscreen 환경을 공식 지원한다.
- 재생/일시정지/다음/이전 곡 조작은 제공하지 않는다.

## 1차 사용자 시나리오

1. 사용자가 Spotify 데스크톱 앱에서 음악을 재생한다.
2. Music Skin Overlay가 GSMTC를 통해 현재 미디어 세션을 읽는다.
3. 앱이 곡명, 아티스트, 앨범명, 앨범아트, 재생 상태, 진행률을 작은 오버레이 카드에 표시한다.
4. 사용자는 게임 중 오버레이 위치를 드래그해 원하는 위치에 둔다.
5. 앱 재실행 후에도 마지막 위치와 테마가 유지된다.

## 2차 사용자 시나리오

1. 사용자가 Spotify 웹, YouTube, YouTube Music, PWA 등 브라우저 기반 미디어를 재생한다.
2. 앱이 Chrome/Edge GSMTC 세션을 읽어 현재 재생 정보를 표시한다.
3. Spotify와 브라우저 미디어가 동시에 존재할 경우 사용자는 preferred source를 선택한다.

## 현재 검증 상태

2026-06-22 기준으로 GSMTC probe를 통해 다음을 확인했다.

- Chrome 미디어 세션에서 제목, 아티스트, 재생 상태, 진행 위치, 전체 길이, seek 가능 여부, 썸네일 존재 여부를 읽을 수 있었다.
- Spotify 데스크톱 세션에서 제목, 아티스트, 앨범명, 재생 상태, 진행 위치, 전체 길이, 이전/다음/토글/seek 가능 여부, 앨범아트를 읽을 수 있었다.
- Spotify 앨범아트는 PNG 바이트로 추출 가능했다.
- 콘솔 출력 인코딩 문제는 스크립트에서 UTF-8/replace 출력으로 보완했다.

## 현재 결정

- 기본 Provider는 GSMTC로 진행한다.
- Spotify API는 MVP 범위에서 제외하고, 추후 fallback 후보로 둔다.
- YouTube Music은 사용자가 현재 검증할 수 없으므로 공식 지원 확정이 아니라 "GSMTC 호환 가능성 있음"으로 둔다.
- 동시에 여러 미디어 세션이 있을 수 있으므로 Auto mode와 Fixed source mode를 설계에 포함한다.
- 앨범아트는 실사용 시 매번 파일로 저장하지 않고 메모리 캐시로 표시한다.
