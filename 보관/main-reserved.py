
import os, sys, json, base64, datetime as dt
import pandas as pd
from typing import List, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 1) 환경 변수에서 API 키 읽기
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2) 이미지 → Base64 인코딩
def b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 3) Vision-Chat 호출
def call_openai(front_img: str, back_img: str = None) -> Dict:
    """단일 영수증(앞·뒤)에서 정보 추출 → dict 반환"""
    
    print(front_img)
    # front_img="./img/KakaoTalk_20250711_132102437.jpg"


    """앞면 Tool calling = 거래일시와 전체금액""" 
    tools_front = [{
        "type": "function",
        "name": "parse_front_taxi_receipt",
        "description": "Extract key fields from Korean taxi receipts",
        "parameters": {
            "type": "object",
            "properties": {
                "paid_at": {
                    "type": "string",
                    "description": "거래 일시로 적혀있음. 결과는 2025년 이후임. 출력예시: 2025-07-07 23:43"
                },
                "fare": {
                    "type": "integer",
                    "description": "총 결제 금액 (원)"
                },
            },
            "required": ["paid_at", "fare"],
            "additionalProperties": False
        }
    }]
    """뒷면 Tool calling = 출발지와 도착지"""
    tools_back = [{
        "type": "function",
        "name": "parse_back_taxi_receipt",
        "description": "Extract key fields from Korean taxi receipts",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "팀원 이름임. 최홍영, 박다혜, 박상현, 김민주, 최윤선, 김익현, 장수현, 이한울, 김호연, 박성진 중 1명임"
                },
                "route": {
                    "type": "string",
                    "description": "출발지 - 도착지. example: 회사 - 집 / 집 - 회사 / 야근택시비 / 야근 / 회식 - 집 등등"
                },
            },
            "required": ["name", "route"],
            "additionalProperties": False
        }
    }]

    # 앞장 이미지 인풋
    input_front=[
            {
                "role": "system",
                "content": "You are a helpful assistant that extracts structured data from Korean taxi receipts."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{b64(front_img)}"
                    }
                ]
            },
        ]      
    
    # 뒷장 이미지 인풋
    input_back=[
        {
            "role": "system",
            "content": "You are a helpful assistant that extracts structured data from Korean taxi receipts."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{b64(back_img)}"
                }
            ]
        },
    ]

    response_front = client.responses.create(
        model="gpt-4o",
        input=input_front,
        tools=tools_front
    )
    response_back = client.responses.create(
        model="gpt-4o",
        input=input_back,
        tools=tools_back
    )

    print(response_front)
    print(response_back)

    # 함수 호출 결과(JSON str)가 arguments 에 담겨 있음
    # 새로운 API 응답 구조에 맞게 수정
    data_front = json.loads(response_front.output[0].arguments)
    data_back = json.loads(response_back.output[0].arguments)
    
    # front와 back 결과를 하나의 딕셔너리로 합치기
    combined_data = {**data_front, **data_back}
    return combined_data


# 4) 메인
def pair_images_from_dir(image_dir: str) -> List[Tuple[str, str]]:
    """
    • `image_dir` 안의 모든 .jpg/.jpeg/.png 파일을 이름순으로 정렬한 뒤,
      순서대로 2개씩 (앞면, 뒷면) 튜플 리스트로 반환한다.
    • 파일 개수가 홀수라면 마지막 하나는 무시한다.
    """
    p = Path(image_dir)
    imgs = sorted([str(f) for f in p.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")])
    # 짝수 개수만 유지
    n = len(imgs) // 2 * 2
    return [(imgs[i], imgs[i + 1]) for i in range(0, n, 2)]


def main(image_dir: str = "./img"):
    rows = []
    for front, back in pair_images_from_dir(image_dir):
        try:
            info = call_openai(front, back)
            rows.append(info)
            print(f"✓ Parsed {os.path.basename(front)} → {info}")
        except Exception as e:
            print(f"✗ Failed on {front}: {e}")

    # 원하는 컬럼 순서로 DataFrame 생성
    df = pd.DataFrame(rows)
    if len(df) > 0:
        # 컬럼 순서 지정: 일자, name, route, fare
        column_order = ['paid_at', 'name', 'route', 'fare']
        df = df[column_order]
    
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out_file = f"receipts_{ts}.csv"
    df.to_csv(out_file, index=False, encoding="utf-8-sig")
    # 또는 Excel 저장: df.to_excel(out_file.replace(".csv",".xlsx"), index=False)
    print(f"\nSaved {len(df)} rows → {out_file}")


if __name__ == "__main__":
    # 이미지 디렉터리 경로를 인자로 받을 수 있으며, 생략하면 기본으로 ./img 사용
    dir_path = sys.argv[1] if len(sys.argv) >= 2 else "./img"
    if not Path(dir_path).exists():
        print(f"Directory not found: {dir_path}")
        sys.exit(1)
    main(dir_path)