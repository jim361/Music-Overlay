# Music Skin Overlay 프로젝트 기획 정리

## 1. 프로젝트 개요

**Music Skin Overlay**는 게임 중 현재 재생 중인 음악 정보를 사용자가 직접 디자인한 오버레이 UI로 표시하는 Windows 데스크톱 앱이다.

기존 Spotify 미니플레이어나 Xbox Game Bar Spotify 위젯처럼 정해진 UI를 그대로 사용하는 것이 아니라, 사용자가 원하는 형태의 카드형 UI, 앨범아트, 곡명, 아티스트, 진행바, 재생 상태 등을 커스텀해서 게임 화면 위에 띄우는 것을 목표로 한다.

초기 목표는 **Spotify와 YouTube Music을 모두 지원하는 전체창모드 / Borderless fullscreen용 음악 오버레이**이다.

---

## 2. 프로젝트를 시작하게 된 배경

게임을 하면서 현재 어떤 노래가 재생 중인지 확인하고 싶은 경우가 있다.
특히 레이싱 게임이나 오픈월드 게임처럼 음악을 들으면서 플레이하는 상황에서는 현재 곡명, 아티스트, 진행률을 작은 PiP 형태로 확인할 수 있으면 편리하다.

기존에도 Spotify 전용 오버레이 프로그램은 존재한다. 예를 들어 GitHub에는 Python + PySide6 기반의 Spotify 오버레이 프로젝트가 있으며, 항상 위 표시, 투명 오버레이, 재생/스킵/볼륨 조절 등의 기능을 제공한다.

하지만 기존 프로젝트는 대체로 다음과 같은 한계가 있다.

* Spotify 전용인 경우가 많다.
* YouTube Music 지원이 부족하다.
* UI 커스터마이징이 제한적이다.
* OBS나 방송용 위젯에 가까운 경우가 많다.
* 사용자가 직접 디자인한 게임용 음악 카드 UI라는 방향성이 약하다.
* 전체화면 게임 위에서의 동작 방식이 명확하지 않은 경우가 있다.

이 프로젝트는 단순한 Spotify 조작 앱이 아니라, **게임 중 현재 재생 음악을 커스텀 스킨으로 보여주는 오버레이 앱**을 목표로 한다.

---

## 3. 주요 사용 시나리오

사용자는 Spotify, YouTube Music 웹, YouTube Music PWA, Spotify 데스크톱 앱 등에서 음악을 재생한다.

앱은 Windows의 미디어 세션 정보를 읽어 현재 재생 중인 곡 정보를 가져온다.

게임은 전체창모드 또는 Borderless fullscreen으로 실행한다.

앱은 투명하고 프레임이 없는 작은 오버레이 창을 게임 위에 띄운다.

사용자는 게임을 하면서 다음 정보를 확인할 수 있다.

* 곡 제목
* 아티스트
* 앨범아트 또는 썸네일
* 현재 재생 상태
* 현재 재생 위치
* 전체 곡 길이
* 진행률
* 재생 / 일시정지 상태

추가적으로 앱에서 다음 조작도 가능하게 한다.

* 재생 / 일시정지
* 이전 곡
* 다음 곡
* 진행 위치 이동
* 볼륨 확인 및 조절
* 오버레이 위치 이동
* 오버레이 잠금
* 투명도 조절
* 테마 변경

---

## 4. 지원 범위

### 4.1 1차 지원 범위

초기 MVP에서는 다음 환경을 지원한다.

* Windows 10 / Windows 11
* Spotify 데스크톱 앱
* Spotify 웹 / PWA
* YouTube Music 웹 / PWA
* Chrome / Edge 기반 미디어 세션
* 창모드 게임
* 전체창모드 게임
* Borderless fullscreen 게임

### 4.2 제한 범위

초기 버전에서는 다음은 공식 지원 범위에서 제외한다.

* DirectX 후킹 기반 독점 전체화면 오버레이
* 게임 프로세스 DLL 인젝션
* 안티치트가 적용된 게임 내부 렌더링 후킹
* Overwolf 기반 오버레이
* Xbox Game Bar 커스텀 위젯
* macOS / Linux 지원

독점 전체화면 게임에서는 일반적인 Python GUI 오버레이가 표시되지 않을 수 있다.
따라서 초기 프로젝트의 공식 목표는 **전체창모드 / Borderless fullscreen 게임 위에서 동작하는 오버레이**로 정의한다.

---

## 5. 기술 방향

### 5.1 핵심 기술 스택

* Language: Python
* GUI: PySide6
* Media Info: GlobalSystemMediaTransportControlsSessionManager, GSMTC
* Volume Control: pycaw 또는 Windows Core Audio API
* Config: JSON
* Packaging: PyInstaller

### 5.2 GUI 방식

HTML PiP나 브라우저 기반 PiP가 아니라, Python의 PySide6를 사용해 데스크톱 오버레이 창을 구현한다.

오버레이 창은 다음 속성을 가진다.

* Frameless window
* Always on top
* Transparent background
* Rounded card UI
* Draggable position
* Resizable window
* Optional click-through mode
* Lock mode
* Opacity control

---

## 6. GSMTC 사용 방향

이 프로젝트는 Spotify API를 우선 사용하기보다, Windows의 GSMTC를 통해 현재 재생 중인 미디어 세션을 읽는 방식을 기본으로 한다.

GSMTC를 사용하면 Spotify뿐만 아니라 YouTube Music 웹/PWA도 같은 방식으로 감지할 수 있다.

### 6.1 GSMTC로 가져올 정보

GSMTC를 통해 다음 정보를 가져온다.

* 곡 제목
* 아티스트
* 앨범명
* 앨범아트 또는 썸네일
* 재생 상태
* 현재 재생 위치
* 곡 전체 길이
* 재생 가능 여부
* 일시정지 가능 여부
* 이전 곡 가능 여부
* 다음 곡 가능 여부

### 6.2 GSMTC로 가능한 제어

GSMTC를 통해 다음 제어를 시도할 수 있다.

* 재생
* 일시정지
* 재생 / 일시정지 토글
* 이전 곡
* 다음 곡
* 재생 위치 이동

단, GSMTC는 명령을 강제로 실행하는 방식이 아니라 현재 미디어 세션에 요청하는 방식이다.
따라서 실제 동작 여부는 Spotify, YouTube Music, Chrome, Edge, PWA 등이 해당 명령을 지원하는지에 따라 달라진다.

구현 시에는 각 버튼을 항상 활성화하지 않고, 세션의 `Controls` 정보를 확인한 뒤 가능한 기능만 활성화한다.

예시:

* `IsPlayEnabled`
* `IsPauseEnabled`
* `IsPlayPauseToggleEnabled`
* `IsNextEnabled`
* `IsPreviousEnabled`

---

## 7. 볼륨 조절 방향

GSMTC는 곡 정보와 재생 제어에는 적합하지만, 앱별 볼륨 조절 기능은 직접 제공하지 않는다.

따라서 볼륨 기능은 별도 모듈로 분리한다.

### 7.1 볼륨 제어 방식

* 시스템 전체 볼륨 조절
* 현재 미디어 앱의 세션 볼륨 조절
* pycaw 사용 검토
* Windows Core Audio API 사용 검토

초기 MVP에서는 볼륨 조절을 필수 기능으로 두지 않고, 곡 정보 표시와 재생 제어를 먼저 구현한다.
이후 볼륨 조절을 별도 기능으로 추가한다.

---

## 8. 프로젝트 아키텍처 초안

```text
music-skin-overlay/
├─ main.py
├─ app/
│  ├─ overlay/
│  │  ├─ overlay_window.py
│  │  ├─ draggable_window.py
│  │  └─ widgets/
│  │     ├─ album_art.py
│  │     ├─ progress_bar.py
│  │     └─ track_info.py
│  │
│  ├─ media/
│  │  ├─ now_playing_provider.py
│  │  ├─ gsmtc_provider.py
│  │  ├─ playback_controller.py
│  │  └─ media_models.py
│  │
│  ├─ audio/
│  │  └─ volume_controller.py
│  │
│  ├─ config/
│  │  ├─ settings_manager.py
│  │  └─ theme_manager.py
│  │
│  └─ utils/
│     ├─ image_cache.py
│     └─ logger.py
│
├─ themes/
│  ├─ default.json
│  ├─ minimal.json
│  └─ glass.json
│
├─ assets/
│  └─ default_album.png
│
├─ docs/
│  └─ PROJECT_BRIEF.md
│
├─ requirements.txt
└─ README.md
```

---

## 9. 주요 모듈 역할

### 9.1 NowPlayingProvider

현재 재생 중인 미디어 정보를 제공하는 추상 계층이다.

초기에는 GSMTC 기반으로 구현한다.

제공 데이터:

* title
* artist
* album
* thumbnail
* duration
* position
* progress
* playback_status
* source_app
* available_controls

### 9.2 GSMTCProvider

Windows GSMTC API를 사용해 현재 미디어 세션을 읽는다.

역할:

* 현재 활성 미디어 세션 가져오기
* 미디어 속성 조회
* 타임라인 정보 조회
* 재생 상태 조회
* 컨트롤 가능 여부 조회
* 재생/일시정지/이전/다음 명령 실행

### 9.3 PlaybackController

재생 관련 명령을 처리한다.

기능:

* play()
* pause()
* toggle_play_pause()
* next_track()
* previous_track()
* seek(position)

### 9.4 VolumeController

볼륨 관련 기능을 담당한다.

초기에는 비워두거나 시스템 볼륨만 지원한다.
이후 pycaw를 사용해 앱별 볼륨 제어를 추가한다.

기능 후보:

* get_system_volume()
* set_system_volume()
* get_app_volume()
* set_app_volume()
* mute()
* unmute()

### 9.5 OverlayWindow

PySide6 기반의 실제 오버레이 창이다.

기능:

* 투명 배경
* 항상 위
* 프레임 제거
* 위치 이동
* 크기 조절
* 잠금 모드
* 클릭 통과 모드
* 음악 정보 표시
* 테마 적용

### 9.6 ThemeManager

사용자 커스텀 UI를 관리한다.

초기에는 JSON 기반 테마를 사용한다.

설정 예시:

```json
{
  "window": {
    "width": 360,
    "height": 96,
    "opacity": 0.9,
    "radius": 18
  },
  "layout": {
    "show_album_art": true,
    "show_title": true,
    "show_artist": true,
    "show_progress_bar": true,
    "show_controls": true
  },
  "style": {
    "font_family": "Pretendard",
    "title_size": 15,
    "artist_size": 12,
    "background_color": "#181818",
    "text_color": "#FFFFFF",
    "sub_text_color": "#B3B3B3",
    "progress_color": "#1DB954"
  }
}
```

---

## 10. MVP 기능 정의

### 10.1 필수 기능

MVP에서 반드시 구현할 기능은 다음과 같다.

* 현재 재생 곡 제목 표시
* 아티스트 표시
* 앨범아트 또는 썸네일 표시
* 재생 상태 표시
* 진행바 표시
* 현재 재생 시간 / 전체 시간 표시
* PySide6 오버레이 창 표시
* 항상 위 표시
* 창 위치 드래그
* 위치 저장
* 기본 테마 적용
* Spotify / YouTube Music 웹/PWA에서 GSMTC 정보 읽기

### 10.2 1차 선택 기능

시간이 남으면 추가할 기능은 다음과 같다.

* 재생 / 일시정지 버튼
* 이전 곡 버튼
* 다음 곡 버튼
* 잠금 모드
* 투명도 조절
* theme.json 커스텀
* 트레이 아이콘
* 실행 시 자동 시작 옵션

### 10.3 2차 확장 기능

추후 확장할 기능은 다음과 같다.

* 앱별 볼륨 조절
* 클릭 통과 모드
* 여러 테마 프리셋
* QML 기반 고급 스킨 시스템
* Spotify Web API 연동
* YouTube Music 브라우저 확장 연동
* Xbox Game Bar 위젯 버전 검토
* 가사 표시
* 단축키 지원

---

## 11. 기존 프로젝트와의 차별점

기존 Spotify 오버레이 프로젝트와 비교했을 때 이 프로젝트의 차별점은 다음과 같다.

### 11.1 Spotify 전용이 아님

GSMTC를 사용해 Spotify뿐만 아니라 YouTube Music 웹/PWA도 지원하는 방향으로 설계한다.

### 11.2 게임용 전체창모드 오버레이에 집중

OBS용 방송 위젯이 아니라, 실제 사용자가 게임 중에 보는 작은 음악 카드 UI를 목표로 한다.

### 11.3 커스텀 디자인 강조

사용자가 Spotify 기본 UI가 아닌 직접 디자인한 화면을 띄우는 것이 핵심이다.

단순히 정보를 표시하는 앱이 아니라, 테마와 스킨을 통해 사용자가 원하는 스타일로 바꿀 수 있는 구조를 목표로 한다.

### 11.4 안전한 구현 방식

DirectX 후킹, DLL 인젝션, 안티치트 우회 같은 위험한 방식은 사용하지 않는다.

초기 버전은 일반 Windows 오버레이 창으로 구현하고, 공식 지원 범위는 전체창모드 / Borderless fullscreen으로 제한한다.

---

## 12. 전체화면 오버레이 관련 판단

전체화면 게임 위에 오버레이를 띄우는 방식은 크게 세 가지가 있다.

### 12.1 일반 topmost 창 방식

Python + PySide6로 구현 가능하다.

장점:

* 구현이 쉽다.
* Python 프로젝트로 유지할 수 있다.
* 디자인 커스터마이징이 쉽다.
* 안티치트 리스크가 낮다.

단점:

* 독점 전체화면 게임 위에서는 표시되지 않을 수 있다.

이 프로젝트의 MVP 방식으로 채택한다.

### 12.2 Overwolf 방식

LoL 보조 프로그램처럼 게임 위에 오버레이를 띄우는 플랫폼을 사용하는 방식이다.

장점:

* 게임 오버레이에 특화되어 있다.
* HTML/CSS/JS로 UI를 만들 수 있다.
* LoL 오버레이 앱들이 많이 사용하는 방식이다.

단점:

* Python 중심 프로젝트가 아니게 된다.
* Overwolf 지원 게임과 실행 환경에 묶인다.
* Xbox 앱 / Microsoft Store / Game Pass 게임에서는 호환 문제가 있을 수 있다.

현재 프로젝트에서는 제외한다.

### 12.3 DirectX 후킹 방식

게임 렌더링 단계에 직접 UI를 그리는 방식이다.

장점:

* 독점 전체화면 위에도 표시 가능하다.

단점:

* 구현 난이도가 매우 높다.
* C++/DirectX 지식이 필요하다.
* 게임별 호환성 문제가 크다.
* 안티치트에 의해 의심받을 수 있다.
* 음악 오버레이 프로젝트에는 과하다.

현재 프로젝트에서는 제외한다.

---

## 13. 현재 결정 사항

현재까지의 결정 사항은 다음과 같다.

* 프로젝트는 Python 기반으로 진행한다.
* GUI는 PySide6를 사용한다.
* HTML PiP 방식은 사용하지 않는다.
* Overwolf는 사용하지 않는다.
* Xbox Game Bar 위젯은 추후 확장 후보로 둔다.
* 초기 목표는 전체창모드 / Borderless fullscreen 지원이다.
* Spotify와 YouTube Music을 모두 지원한다.
* Spotify API보다 GSMTC를 먼저 사용한다.
* 음량 조절은 GSMTC가 아니라 pycaw 또는 Core Audio API로 별도 구현한다.
* DirectX 후킹 방식은 사용하지 않는다.
* 핵심 차별점은 커스텀 가능한 게임용 음악 오버레이 UI이다.

---

## 14. 개발 순서 제안

### Phase 1. 기술 검증

목표: GSMTC로 현재 재생곡 정보를 읽을 수 있는지 확인한다.

작업:

* Python에서 GSMTC 접근 테스트
* 현재 활성 미디어 세션 조회
* 제목 / 아티스트 / 앨범아트 조회
* 재생 위치 / 전체 길이 조회
* 재생 상태 조회
* Spotify 앱 테스트
* Spotify 웹 테스트
* YouTube Music 웹 테스트
* YouTube Music PWA 테스트

완료 기준:

* Spotify와 YouTube Music에서 곡명과 아티스트를 읽을 수 있다.
* 진행률 계산이 가능하다.
* 재생/일시정지/다음/이전 가능 여부를 확인할 수 있다.

### Phase 2. 기본 오버레이 구현

목표: PySide6로 투명한 always-on-top 오버레이를 만든다.

작업:

* 프레임리스 창 생성
* 투명 배경 적용
* 항상 위 설정
* 기본 카드 UI 구성
* 곡명 / 아티스트 / 앨범아트 표시
* 진행바 표시
* 창 드래그 이동 구현
* 위치 저장 구현

완료 기준:

* 전체창모드 게임 위에서 오버레이가 표시된다.
* 오버레이 위치를 이동할 수 있다.
* 앱 재실행 후 위치가 유지된다.

### Phase 3. 재생 제어 추가

목표: 오버레이에서 기본 음악 제어를 할 수 있게 한다.

작업:

* 재생/일시정지 버튼
* 이전 곡 버튼
* 다음 곡 버튼
* 버튼 활성화/비활성화 처리
* GSMTC 명령 실패 처리

완료 기준:

* Spotify와 YouTube Music에서 가능한 제어만 버튼으로 표시된다.
* 지원하지 않는 기능은 비활성화된다.

### Phase 4. 커스텀 테마 추가

목표: 사용자가 UI를 커스터마이징할 수 있게 한다.

작업:

* theme.json 로드
* 창 크기 설정
* 투명도 설정
* 폰트 설정
* 색상 설정
* 표시 요소 on/off 설정
* 기본 테마 2~3개 제공

완료 기준:

* JSON 수정만으로 오버레이 스타일을 바꿀 수 있다.
* 기본 테마와 미니멀 테마를 전환할 수 있다.

### Phase 5. 볼륨 기능 추가

목표: 볼륨 표시와 조절 기능을 추가한다.

작업:

* pycaw 검토
* 시스템 볼륨 조회
* 시스템 볼륨 조절
* 앱별 볼륨 조절 가능 여부 검토
* UI에 볼륨 슬라이더 추가

완료 기준:

* 최소한 시스템 볼륨을 확인하고 조절할 수 있다.
* 가능하다면 현재 재생 앱의 볼륨을 조절할 수 있다.

---

## 15. 예상 리스크

### 15.1 앱별 GSMTC 지원 차이

Spotify, YouTube Music, Chrome, Edge, PWA가 모두 같은 수준으로 정보를 제공하지 않을 수 있다.

대응:

* 지원 가능한 정보만 표시한다.
* 누락된 값은 기본값으로 처리한다.
* 컨트롤 가능 여부를 매번 확인한다.

### 15.2 앨범아트 품질 문제

YouTube Music에서는 앨범아트가 실제 앨범 커버가 아니라 영상 썸네일처럼 들어올 수 있다.

대응:

* 우선 GSMTC 썸네일을 그대로 사용한다.
* 추후 YouTube Music 전용 보정 방식이나 브라우저 확장을 검토한다.

### 15.3 전체화면 게임 호환성

독점 전체화면에서는 오버레이가 보이지 않을 수 있다.

대응:

* 공식 지원 범위를 전체창모드 / Borderless fullscreen으로 제한한다.
* README에 제한 사항을 명확히 적는다.

### 15.4 볼륨 제어 복잡성

GSMTC만으로는 볼륨 조절이 어렵다.

대응:

* 볼륨 기능은 별도 모듈로 분리한다.
* 초기 MVP에서는 볼륨 조절을 필수에서 제외한다.
* 이후 pycaw 또는 Core Audio API로 추가한다.

---

## 16. README 소개 문구 초안

Music Skin Overlay는 Windows에서 실행되는 커스텀 음악 오버레이 앱입니다.

Spotify, YouTube Music 등 Windows 미디어 세션에 등록된 현재 재생 정보를 읽어 게임 화면 위에 작은 카드 형태로 표시합니다.

기본 음악 플레이어 UI가 아니라, 사용자가 직접 디자인한 스킨과 테마를 적용해 자신만의 음악 오버레이를 만들 수 있습니다.

이 앱은 DirectX 후킹이나 게임 프로세스 인젝션을 사용하지 않으며, 창모드 및 전체창모드 게임 환경을 대상으로 합니다.

---

## 17. 한 줄 설명

전체창모드 게임 위에 Spotify와 YouTube Music 현재 재생곡을 커스텀 스킨으로 표시하는 Python 음악 오버레이 앱.

---

## 18. 프로젝트 이름 후보

* Music Skin Overlay
* NowPlaying Skin
* Game Music Overlay
* TuneOverlay
* Skinify Overlay
* PlayCard Overlay
* TrackSkin
* OverlayBeats
* GameNowPlaying

현재 방향에는 **Music Skin Overlay** 또는 **NowPlaying Skin**이 가장 잘 어울린다.

---

## 19. Codex 작업 시작용 요청 예시

다음 요구사항을 만족하는 Windows용 Python 프로젝트의 초기 구조를 만들어줘.

프로젝트명은 Music Skin Overlay이다.

목표는 Windows의 GlobalSystemMediaTransportControlsSessionManager를 사용해 현재 재생 중인 Spotify 또는 YouTube Music의 곡명, 아티스트, 앨범아트, 재생 위치, 전체 길이, 재생 상태를 읽고, PySide6 기반의 투명한 always-on-top 오버레이 창에 표시하는 것이다.

초기 구현 범위는 다음과 같다.

1. Python 프로젝트 기본 구조 생성
2. PySide6 기반 프레임리스 투명 오버레이 창 생성
3. 항상 위 표시
4. 창 드래그 이동
5. 임시 더미 음악 데이터 표시
6. theme.json 기반 기본 스타일 로드
7. 추후 GSMTCProvider를 연결할 수 있도록 media provider 인터페이스 설계
8. README와 requirements.txt 작성

DirectX 후킹, Overwolf, Xbox Game Bar 위젯은 구현하지 않는다.
초기 공식 지원 범위는 창모드와 전체창모드 / Borderless fullscreen이다.
