# Technical Design

## 아키텍처

```text
main.py
app/
  media/
    media_models.py
    now_playing_provider.py
    dummy_provider.py
    gsmtc_provider.py
    session_selector.py
  overlay/
    overlay_window.py
  config/
    settings_manager.py
    theme_manager.py
themes/
  default.json
```

## 데이터 흐름

```text
GSMTCProvider
  -> list sessions
  -> read properties/timeline/playback info/artwork
  -> SessionSelector
  -> MediaSnapshot
  -> background polling worker
  -> OverlayWindow.update_snapshot()
```

## Provider 인터페이스

`NowPlayingProvider`는 UI가 의존하는 추상 계층이다.

필수 메서드:

- `get_snapshot() -> MediaSnapshot`

초기 구현:

- `DummyProvider`: UI 개발과 테스트용
- `GSMTCProvider`: Windows GSMTC 기반 실제 Provider

Provider가 GSMTC controls 정보를 읽을 수는 있지만, MVP UI는 playback command를 실행하지 않는다. controls 정보는 향후 진단/호환성 확인용 metadata로만 취급한다.

## MediaSnapshot

UI는 다음 데이터만 사용한다.

- `source_app`
- `title`
- `artist`
- `album`
- `playback_status`
- `position_seconds`
- `duration_seconds`
- `progress_percent`
- `thumbnail_bytes`
- `controls`

## 앨범아트 처리

실사용 앱은 검증 스크립트처럼 매번 파일을 저장하지 않는다.

- Provider가 GSMTC thumbnail stream을 bytes로 읽는다.
- OverlayWindow는 bytes를 `QPixmap.loadFromData()`로 표시한다.
- 이전 track identity와 같으면 기존 pixmap을 재사용한다.
- track identity가 바뀌면 pixmap을 갱신한다.

선택적 디스크 캐시는 추후 기능이다.

## UI Thread 정책

Qt 메인 스레드에서 GSMTC WinRT async 호출을 직접 실행하면 앱이 멈출 수 있다. 실제 스모크 테스트에서 `QApplication` 컨텍스트의 메인 스레드 호출이 timeout으로 이어졌다.

따라서 오버레이는 다음 정책을 사용한다.

- UI thread는 창 표시와 렌더링만 담당한다.
- Provider polling은 `ThreadPoolExecutor(max_workers=1)`에서 수행한다.
- poll 결과는 Qt Signal로 UI thread에 전달한다.
- 이전 polling이 끝나지 않았으면 새 polling을 건너뛴다.
- Provider 오류는 error snapshot으로 변환해 UI에 표시한다.

## 다중 세션 처리

GSMTC는 여러 미디어 세션을 반환할 수 있다. UI가 임의로 current session만 믿으면 Spotify 음악과 YouTube 영상이 동시에 있을 때 원하지 않는 세션이 표시될 수 있다.

초기 정책:

```text
selection_mode = auto | fixed
preferred_source = spotify | chrome | edge | current
```

Auto 우선순위:

1. preferred source가 있고 playing이면 preferred source
2. playing Spotify
3. any playing session
4. current session
5. last good snapshot
6. empty snapshot

Fixed 우선순위:

1. preferred source와 source app id가 매칭되는 세션
2. last good snapshot
3. empty snapshot

## 설정 저장

사용자 설정은 다음 위치에 저장한다.

```text
%LOCALAPPDATA%\Music Skin Overlay\settings.json
```

저장 대상:

- window position
- overlay display options
- media selection mode
- preferred source

## 오버레이 조작

초기 MVP는 별도 설정 창이나 트레이 아이콘을 만들지 않는다. 대신 frameless window의 최소 조작성을 위해 다음을 제공한다.

- 좌클릭 드래그로 위치 이동
- 우클릭 메뉴로 source 선택
- 우클릭 메뉴로 즉시 refresh
- 우클릭 메뉴 또는 `Esc`로 종료
- `F5`로 즉시 refresh

재생/일시정지/다음/이전 곡 같은 플레이어 조작은 제공하지 않는다.

## 시스템 트레이

Windows notification area에 `QSystemTrayIcon`을 표시한다.

트레이 메뉴:

- 현재 곡 제목 표시
- 오버레이 숨김/표시
- 우선 source 선택: Auto, Spotify, Chrome, Edge, Current
- 즉시 refresh
- 설정 창 열기
- 종료

트레이 아이콘:

- 기본 아이콘은 코드에서 그린다.
- 앨범아트 대신 RunCat처럼 앱 상태 심볼을 유지한다.
- tooltip에는 현재 곡명과 아티스트를 표시한다.

## 설정 창

트레이 메뉴와 오버레이 우클릭 메뉴에서 `Settings...`를 열 수 있다.

초기 설정 항목:

- preferred source
- thumbnail visibility
- background opacity
- time/progress visibility
- title/detail/meta font sizes
- title/detail/meta/accent colors
- reset overlay position

설정은 즉시 적용하고 `SettingsManager`를 통해 저장한다. 창을 닫아도 앱은 트레이에 남아 계속 동작한다.

## 테마

테마는 JSON으로 관리한다.

초기 지원:

- window width/height/opacity/radius
- background color
- text color
- sub text color
- accent/progress color
- font family
- font sizes
- album art layout
- progress bar layout

## 패키징

PyInstaller onedir 빌드를 우선 사용한다.

```text
scripts/build_exe.ps1
packaging/music_skin_overlay.spec
dist/MusicSkinOverlay/MusicSkinOverlay.exe
```

테마 파일은 PyInstaller data file로 포함한다. 앱 내부에서는 `resource_path()`를 통해 개발 환경과 PyInstaller 환경 모두에서 같은 방식으로 테마를 찾는다.

초기에는 one-file exe를 사용하지 않는다. PySide6와 WinRT 의존성이 있어 onedir 배포가 디버깅과 안정성 면에서 유리하다.

## 오류 처리

- `winsdk` 미설치: Provider가 명확한 에러 snapshot을 반환한다.
- 활성 세션 없음: empty snapshot을 표시한다.
- artwork 읽기 실패: 기본 placeholder를 표시한다.
- timeline 누락: 진행바를 0으로 표시하고 시간은 `--:--`로 표시한다.
