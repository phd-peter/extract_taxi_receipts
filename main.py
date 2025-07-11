
import os, sys, json, base64, datetime as dt
import pandas as pd
from typing import List, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv
import openai

# 1) 환경 변수에서 API 키 읽기
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")   # 또는 openai_client = OpenAI(api_key="...")

# 2) 이미지 → Base64 인코딩
def b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 3) Vision-Chat 호출
def call_openai(front_img: str, back_img: str = None) -> Dict:
    """단일 영수증(앞·뒤)에서 정보 추출 → dict 반환"""
    
    # 이미지 payload
    vision_inputs = [
        { "type": "image_url",
          "image_url": { "url": f"data:img/jpg;base64,{b64(front_img)}" } }
    ]
    if back_img:
        vision_inputs.append(
            { "type": "image_url",
              "image_url": { "url": f"data:img/jpg;base64,{b64(back_img)}" } }
        )

    # 함수 호출용 JSON 스키마
    function_schema = {
        "name": "parse_taxi_receipt",
        "description": "Extract key fields from Korean taxi receipts",
        "parameters": {
            "type": "object",
            "properties": {
                "date":          { "type": "string", "description": "YYYY-MM-DD" },
                "applicant":     { "type": "string", "description": "Hand-written name if present" },
                "purpose":       { "type": "string", "description": "업무내용 필드, 예: '리사→집'" },
                "route":         { "type": "string", "description": "출발지 - 도착지" },
                "fare":          { "type": "integer", "description": "총 결제 금액 (원)" },
                "paid_at":       { "type": "string", "description": "YYYY-MM-DD HH:MM" }
            },
            "required": ["date", "fare", "paid_at"]
        },
    }

    messages = [
        { "role": "system",
          "content": "You are a helpful assistant that extracts structured data from Korean taxi receipts." },
        { "role": "user", "content": vision_inputs }
    ]

    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # 또는 "gpt-4o"
        temperature=0,
        messages=messages,
        tools=[{ "type": "function", **function_schema }],
        tool_choice={ "type": "function", "function": { "name": "parse_taxi_receipt" } }
    )

    # 함수 호출 결과(JSON str)가 arguments 에 담겨 있음
    tool_msg = response.choices[0].message
    data = json.loads(tool_msg.tool_calls[0].function.arguments)
    return data


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

    df = pd.DataFrame(rows, columns=["date","applicant","purpose","route","fare","paid_at"])
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