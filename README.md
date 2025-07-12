# 🚕 택시 영수증 자동 추출 시스템

OpenAI GPT-4 Vision을 활용한 한국 택시 영수증 자동 데이터 추출 도구입니다.

## 🎯 주요 기능

- **자동 데이터 추출**: 택시 영수증 이미지에서 핵심 정보 자동 추출
- **앞뒤면 처리**: 영수증 앞면(거래정보)과 뒤면(승객정보)을 동시에 처리
- **CSV 출력**: 추출된 데이터를 CSV 파일로 자동 저장
- **배치 처리**: 여러 영수증을 한 번에 처리

## 📋 추출 가능한 정보

- **거래 일시** (paid_at): 2025-07-07 23:43 형태
- **승객 이름** (name): 팀원 이름 자동 인식
- **이동 경로** (route): 출발지-도착지 또는 용도 (회사-집, 야근택시비 등)
- **요금** (fare): 총 결제 금액 (원)

## 🛠️ 설치 방법

### 1. 저장소 복제
```bash
git clone https://github.com/your-username/extract_taxi_receipts.git
cd extract_taxi_receipts
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 OpenAI API 키를 추가하세요:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## 📂 프로젝트 구조

```
extract_taxi_receipts/
├── main.py              # 메인 실행 파일
├── img/                 # 영수증 이미지 폴더
│   ├── receipt_01.jpg   # 앞면
│   ├── receipt_02.jpg   # 뒤면
│   └── ...
├── requirements.txt     # 필요한 패키지 목록
├── README.md           # 프로젝트 설명서
└── .env                # 환경 변수 (직접 생성)
```

## 🚀 사용 방법

### 1. 이미지 준비
- 택시 영수증 이미지를 `img/` 폴더에 넣어주세요
- 파일명은 알파벳 순서로 정렬되어야 합니다 (앞면, 뒤면 순서)
- 지원 형식: `.jpg`, `.jpeg`, `.png`

### 2. 실행
```bash
python main.py
```

또는 다른 이미지 폴더를 지정:
```bash
python main.py /path/to/your/image/folder
```

### 3. 결과 확인
실행 후 `receipts_YYYYMMDD_HHMM.csv` 파일이 생성됩니다.

## 📊 출력 예시

```csv
paid_at,name,route,fare
2025-07-07 23:43,홍길동,회사 - 집,27700
2025-07-07 23:44,원빈,야근택시비,27100
2025-07-07 23:45,유재석,회사 - 집,11700
```

## ⚙️ 설정 사항

### 인식 가능한 팀원 이름
현재 다음 이름들을 인식합니다:
- 최홍영, 박다혜, 박상현, 김민주, 최윤선
- 김익현, 장수현, 이한울, 김호연, 박성진

### 경로 예시
- `회사 - 집`
- `집 - 회사`
- `야근택시비`
- `회식 - 집`
- `기타`

## 🔧 주요 함수

### `call_openai(front_img, back_img)`
- 영수증 앞면과 뒤면 이미지를 분석하여 정보 추출
- OpenAI GPT-4 Vision API 사용
- 구조화된 JSON 데이터 반환

### `pair_images_from_dir(image_dir)`
- 지정된 폴더의 이미지들을 앞뒤면 쌍으로 그룹화
- 알파벳 순서로 정렬하여 순서대로 페어링

## 🚨 주의사항

- OpenAI API 키가 필요합니다
- 인터넷 연결이 필요합니다
- 이미지 품질이 좋을수록 정확도가 높아집니다
- 한국어 택시 영수증에 최적화되어 있습니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

버그 리포트, 기능 제안, 풀 리퀘스트를 환영합니다!

## 📞 지원

문의사항이 있으시면 이슈를 등록해주세요. 