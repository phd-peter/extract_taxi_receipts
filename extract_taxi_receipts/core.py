"""extract_taxi_receipts.core

공용 추출 로직 모듈. CLI, GUI, Lambda 등 모든 환경에서
`extract_from_images()` 하나로 영수증 정보를 추출할 수 있도록 한다.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

__all__ = [
    "extract_from_images",
    "pair_images_from_dir",
    "CoreError",
]


class CoreError(Exception):
    """Core 레이어에서 발생하는 예외의 베이스 클래스."""


# ---- 환경 설정 -----------------------------------------------------------

load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# ---- 내부 유틸 -----------------------------------------------------------


def _b64(path: str | Path) -> str:
    """이미지 파일을 base64 문자열로 인코딩."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ---- OpenAI Vision 호출 --------------------------------------------------


def _call_openai(front_img: str | Path, back_img: str | Path | None = None) -> Dict:
    """단일 영수증(앞·뒤)에서 정보 추출.

    Parameters
    ----------
    front_img : str | Path
        앞면 이미지 경로.
    back_img : str | Path | None, optional
        뒷면 이미지 경로. 제공되지 않으면 이름·경로는 빈 문자열로 채움.

    Returns
    -------
    dict
        {paid_at, fare, name, route}
    """

    # --- Tool Schemas -----------------------------------------------------
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

    tools_back = [{
        "type": "function",
        "name": "parse_back_taxi_receipt",
        "description": "Extract key fields from Korean taxi receipts",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "팀원 이름을 확인해서 이 중에 1명이름을 가져오도록 함. 유사한 이름이 있으면 팀원 이름으로 대체해.  최홍영, 박다혜, 박상현, 김민주, 최윤선, 김익현, 장수현, 이한울, 김호연, 박성진 중 1명임"
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

    # --- 프롬프트 구성 ----------------------------------------------------
    sys_msg = {
        "role": "system",
        "content": "You are a helpful assistant that extracts structured data from Korean taxi receipts.",
    }

    # 앞면 요청
    input_front = [
        sys_msg,
        {
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{_b64(front_img)}",
                }
            ],
        },
    ]

    # 뒷면 요청 (optional)
    input_back = None
    if back_img is not None:
        input_back = [
            sys_msg,
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{_b64(back_img)}",
                    }
                ],
            },
        ]

    try:
        res_front = _client.responses.create(
            model="gpt-4o",
            input=input_front,
            tools=tools_front,
        )
    except Exception as e:
        raise CoreError(f"OpenAI front-page vision call failed: {e}") from e

    data_front = json.loads(res_front.output[0].arguments)

    # back page is optional
    data_back: Dict = {"name": "", "route": ""}
    if input_back is not None:
        try:
            res_back = _client.responses.create(
                model="gpt-4o",
                input=input_back,
                tools=tools_back,
            )
            data_back = json.loads(res_back.output[0].arguments)
        except Exception as e:
            raise CoreError(f"OpenAI back-page vision call failed: {e}") from e

    return {**data_front, **data_back}


# ---- Public API ----------------------------------------------------------


def extract_from_images(front_path: str | Path, back_path: str | Path | None = None) -> Dict:
    """공용 API 함수.

    다른 계층(CLI, GUI 등)에서 이 함수를 불러 영수증 정보를 추출한다.
    예외 발생 시 `CoreError` 를 던진다.
    """

    return _call_openai(front_path, back_path)


def pair_images_from_dir(image_dir: str | Path) -> List[Tuple[str, str]]:
    """디렉터리 안의 이미지 파일을 이름순으로 정렬한 뒤 (앞, 뒤) 쌍으로 묶는다.

    홀수 개의 파일이 있을 경우 마지막 이미지는 무시한다.
    지원 확장자: .jpg, .jpeg, .png
    """

    p = Path(image_dir)
    imgs = sorted([str(f) for f in p.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")])
    n = len(imgs) // 2 * 2  # 짝수 개수 유지
    return [(imgs[i], imgs[i + 1]) for i in range(0, n, 2)] 