# GSMTC Decision Record

## 결론

GSMTC는 Music Skin Overlay의 MVP Provider로 사용할 수 있다.

검증 결과 Spotify 데스크톱 앱과 Chrome 미디어 세션에서 오버레이 MVP에 필요한 핵심 정보가 조회됐다. 따라서 초기 구현은 GSMTC를 중심으로 진행하고, Spotify API나 브라우저 확장 방식은 보조 후보로 남긴다.

## 검증 결과

### Chrome 세션

실행 명령:

```powershell
py -3.12 scripts\gsmtc_probe.py --current-only
```

확인된 출력:

```text
source:   Chrome
title:    AI가 정상화된 이번 업데이트를 살펴보자
artist:   푸쿠푸쿠푸
status:   playing
time:     3:26 / 10:27
controls: play=False, pause=True, toggle=True, prev=False, next=False, seek=True
artwork:  yes
```

판단:

- 브라우저 기반 미디어도 GSMTC로 감지 가능하다.
- 일반 YouTube와 YouTube Music이 모두 Chrome source로 표시될 수 있으므로, GSMTC만으로 서비스 종류를 완벽히 구분하기는 어렵다.

### Spotify Desktop 세션

실행 명령:

```powershell
py -3.12 scripts\gsmtc_probe.py --current-only --save-thumbnail
```

확인된 출력:

```text
source:   SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify
title:    CARNIVAL
album:    VULTURES 1
status:   playing
controls: play=False, pause=True, toggle=True, prev=True, next=True, seek=True
artwork:  yes
thumbnail: probe-output\session_0_thumbnail.png
```

판단:

- Spotify 데스크톱 앱은 MVP 대상 Provider로 충분히 안정적이다.
- source app id에 Spotify가 포함되어 있어 fixed source 선택이 가능하다.
- 앨범아트 추출이 가능하므로 UI에 커버 이미지를 표시할 수 있다.

## 실사용 캐싱 정책

검증 스크립트의 `--save-thumbnail`은 디버깅용이다. 실제 앱에서는 다음 정책을 사용한다.

1. GSMTC에서 현재 snapshot을 읽는다.
2. `source_app + title + artist + album + duration`을 track identity로 사용한다.
3. track identity가 바뀌면 앨범아트를 새로 읽는다.
4. 앨범아트 바이트는 우선 메모리에 보관해 `QPixmap`으로 표시한다.
5. 디스크 캐시는 선택 기능으로 두고, 사용하더라도 최근 N개 또는 일정 기간만 유지한다.

## 다중 세션 선택 정책

Spotify로 음악을 재생하면서 YouTube 영상을 보는 경우, Windows의 current session이 사용자가 원하는 음악 세션과 다를 수 있다. 이를 해결하기 위해 MVP부터 source selection 정책을 둔다.

### Auto

기본값이다.

우선순위:

1. 사용자가 preferred source를 설정했고 해당 source가 playing이면 그 세션
2. playing 상태인 Spotify 세션
3. playing 상태인 세션
4. Windows current session
5. 마지막으로 정상 표시했던 세션

### Fixed Source

사용자가 표시할 플랫폼을 고른다.

초기 후보:

- Spotify
- Chrome
- Edge
- Current Session

### Manual Session

현재 감지된 세션 목록에서 직접 선택하는 방식이다. MVP 직후 확장 기능으로 둔다.

## 남은 리스크

- YouTube Music Premium 환경을 아직 직접 검증하지 못했다.
- Chrome source만으로는 일반 YouTube와 YouTube Music 구분이 어렵다.
- GSMTC 제어 명령은 앱에 요청하는 방식이므로, 앱별로 play/pause/next/previous 지원이 다를 수 있다.
- 독점 전체화면 게임 위에서는 일반 topmost 창이 보이지 않을 수 있다.
