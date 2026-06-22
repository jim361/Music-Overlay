# Roadmap

## Phase 0. GSMTC 검증

상태: 완료

- Python 3.12 설치
- `winsdk` 설치
- GSMTC probe 작성
- Chrome 세션 검증
- Spotify 데스크톱 세션 검증
- Spotify 앨범아트 추출 검증

## Phase 1. MVP 오버레이

상태: 진행 중

목표:

- 더미 데이터 기반 오버레이 실행
- GSMTC 기반 Spotify 표시
- 기본 테마와 위치 저장

작업:

- 프로젝트 구조 생성
- PySide6 오버레이 창 구현
- Provider 인터페이스 구현
- DummyProvider 구현
- GSMTCProvider 구현
- SessionSelector 구현
- SettingsManager 구현
- ThemeManager 구현
- 백그라운드 Provider polling 구현

검증 완료:

- `py -3.12 main.py --provider dummy --exit-after 2`
- `py -3.12 main.py --provider gsmtc --exit-after 2`
- 우클릭 source 메뉴 추가
- `Esc` 종료, `F5` refresh 추가
- PyInstaller onedir 빌드 설정 추가
- packaged exe smoke test 통과

## Phase 2. MVP 안정화

상태: 예정

목표:

- Spotify 데스크톱 사용 경험을 안정화한다.

작업:

- watch 모드에서 곡 변경 갱신 확인
- 일시정지/재생 상태 갱신 확인
- 앨범아트 누락 fallback 확인
- source fixed mode 확인
- packaged exe 실행 확인
- README 실행 가이드 정리
- PyInstaller 패키징 세부 개선

## Phase 3. 표시 안정화

상태: 예정

목표:

- 라디오형 now playing 오버레이로서 표시 품질을 높인다.

작업:

- 긴 곡명/아티스트 말줄임 개선
- 앨범아트 fallback 개선
- 진행률 갱신 안정화
- 소스 선택 상태 표시 개선
- packaged exe 배포 폴더 정리

## Phase 4. 커스터마이징

상태: 예정

목표:

- 사용자가 스킨처럼 조정할 수 있는 구조를 만든다.

작업:

- 테마 프리셋 추가
- UI 요소 on/off
- 투명도 조절
- 폰트/색상/간격 확장
- 설정 UI 또는 설정 파일 가이드

## Phase 5. 확장 검토

상태: 예정

후보:

- YouTube Music PWA 검증
- Chrome 내 YouTube/YouTube Music 구분 보조 방식
- 표시용 단축키
- 트레이 아이콘
- 클릭 통과 모드
- Xbox Game Bar 위젯 검토
