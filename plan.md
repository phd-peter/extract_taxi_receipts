# 📑 Implementation Plan

## 1️⃣ 공용 코어 레이어 구축

### 목표
`main.py` 의 추출 로직을 재사용 가능한 모듈로 분리하여 CLI·GUI·Lambda 등 다양한 실행 환경에서 동일하게 호출할 수 있도록 한다.

### 산출물
- `extract_taxi_receipts/core.py` (신규)
  - `extract_from_images(front_path: str, back_path: str | None) -> dict`
  - 내부적으로 `call_openai`(vision-chat), `parse_front_taxi_receipt`, `parse_back_taxi_receipt` 포함
- `extract_taxi_receipts/__init__.py` → 핵심 함수 re-export
- 리팩터링된 `main.py` → 입·출력(디렉터리 스캔 & CSV 저장) 전담
- 단위 테스트(`tests/test_core.py`)

### 작업 순서
1. **모듈 생성**: `core.py` 파일 신설, 기존 `call_openai`, `pair_images_from_dir` 함수 이동·정리
2. **API 설계**: `extract_from_images()` 를 public 함수로 노출, type-hint 추가
3. **예외 처리 공통화**: OpenAI 오류·네트워크 실패 시 `CoreError` 커스텀 예외 정의
4. **main.py 리팩터**: `from extract_taxi_receipts.core import extract_from_images, pair_images_from_dir`
5. **테스트 작성**: 샘플 이미지를 사용한 happy-path / failure-path 테스트 구현(PyTest)
6. **패키징**: `setup.cfg`(또는 `pyproject.toml`) 생성 → pip install 가능하게

---

## 2️⃣ 사내 배포(데스크톱) 준비

### 목표
사내 사용자가 인터넷 연결이 제한된 환경에서도 손쉽게 영수증을 드래그-앤-드롭하여 CSV를 생성하도록 “원 파일 실행 프로그램” 제공.

### 기술 스택
- **PySide6**: 네이티브 Windows GUI (설치 용량 <30 MB)
- **PyInstaller**: `--onefile --noconsole` 모드 빌드
- **dotenv / keyring**: OpenAI API 키 보관

### 아키텍처 구성
```
[사용자]
   │ Drag-&-Drop
[PySide6 GUI]  ──▶  [core.extract_from_images]
                           │
                           └─▶ 결과 CSV 저장(local)
```

### 주요 기능 목록
1. **메인 윈도우**
   - Drag-&-Drop 영역 (여러 이미지 선택 가능)
   - ‘추출 시작’ 버튼, 진행률 ProgressBar
   - 완료 후 CSV 파일 자동 열기(Excel 연결)
2. **설정 다이얼로그**
   - 출력 디렉터리 지정
   - .env 편집 창 / API 키 입력 & 저장(keyring)
3. **로그 뷰어** (오류 발생 시 상세 로그 팝업)

### 빌드 & 배포 절차
1. `pyinstaller gui_app.spec` (spec 파일에 hidden-import, 데이터 파일 포함)
2. 출력된 `dist/gui_app.exe` 를 ZIP 압축 → 사내 공유 폴더 / 배포 페이지 업로드
3. **버전 관리**: `dist/v{major}.{minor}.{patch}/` 구조, CHANGELOG.md 작성

### 운영/보안 가이드
- API 키 저장 위치
  - 1차: `%APPDATA%\.env` (간편), 2차: Windows 자격 증명 관리자(keyring)
- 로그 파일: `%LOCALAPPDATA%/TaxiExtractor/logs/` 7일 보관 후 자동 삭제
- 개인정보 보호: 이미지·CSV 자동 삭제 옵션(30일)

---

## 3️⃣ 일정 제안
| 단계 | 작업 | 담당 | 기간 |
|------|------|------|------|
| 1 | Core 모듈화 & 테스트 | Dev | W1 | 
| 2 | main.py 리팩터 & CLI 검증 | Dev | W1 | 
| 3 | GUI 프로토타입(PySide6) | Dev | W2 | 
| 4 | PyInstaller 빌드 파이프라인 | DevOps | W2 | 
| 5 | 내부 시범배포 & 피드백 | QA | W3 | 
| 6 | 버그 수정 & 문서화 | Dev | W4 | 

---

## 4️⃣ 후속 과제(선택)
- 대용량 처리용 멀티프로세싱 / GPU OCR 백엔드 연동
- SaaS 전환 시 FastAPI 래퍼 추가, Stripe 결제 모듈
- 프롬프트 튜닝 자동화 파이프라인(A/B 테스트)

> 위 일정은 1명 기준 4주 예상. 팀·우선순위에 따라 조정 가능합니다. 