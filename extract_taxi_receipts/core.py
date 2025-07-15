"""extract_taxi_receipts.core

공용 추출 로직 모듈. CLI, GUI, Lambda 등 모든 환경에서
`extract_from_images()` 하나로 영수증 정보를 추출할 수 있도록 한다.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime
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

# ---- 로깅 설정 -----------------------------------------------------------

logger = logging.getLogger("extract_taxi_receipts")
logger.setLevel(logging.INFO)

# 콘솔 핸들러 설정
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)



# ---- 상수 정의 -----------------------------------------------------------

TEAM_MEMBERS = [
    "최홍영", "박다혜", "박상현", "김민주", "최윤선", 
    "김익현", "장수현", "이한울", "김호연", "박성진"
]


# ---- 내부 유틸 -----------------------------------------------------------


def _b64(path: str | Path) -> str:
    """이미지 파일을 base64 문자열로 인코딩."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ---- 검증 함수 -----------------------------------------------------------


def _validate_team_member(name: str) -> str:
    """팀원 이름을 검증하고 정정된 이름을 반환.
    
    Parameters
    ----------
    name : str
        추출된 이름
        
    Returns
    -------
    str
        정정된 이름 (매칭되는 팀원이 있으면 정확한 이름, 없으면 원본 이름)
    """
    if not name or not isinstance(name, str):
        return name
    
    # 정확히 일치하는 팀원이 있는지 확인
    if name in TEAM_MEMBERS:
        return name
    
    # 부분 일치 또는 유사한 이름 검색
    name_stripped = name.strip()
    for team_member in TEAM_MEMBERS:
        # 공백 제거 후 비교
        if name_stripped == team_member.strip():
            return team_member
        # 포함 관계 확인 (추출된 이름이 팀원 이름에 포함되거나 그 반대)
        if name_stripped in team_member or team_member in name_stripped:
            return team_member
    
    # 매칭되는 팀원이 없으면 원본 이름 반환
    return name


def _validate_date(paid_at: str) -> None:
    """날짜를 검증하고 2025년 이전인 경우 경고 로그를 출력.
    
    Parameters
    ----------
    paid_at : str
        추출된 날짜 문자열 (예: "2025-07-07 23:43")
    """
    if not paid_at or not isinstance(paid_at, str):
        return
    
    try:
        # 날짜 문자열을 파싱 (YYYY-MM-DD HH:MM 형식 예상)
        date_obj = datetime.strptime(paid_at.strip(), "%Y-%m-%d %H:%M")
        
        # 2025년 이전인지 확인
        if date_obj.year < 2025:
            logger.warning(f"Date is before 2025: {paid_at}")
            
    except ValueError:
        # 날짜 형식이 잘못된 경우 gracefully 처리
        logger.warning(f"Invalid date format: {paid_at}")
    except Exception:
        # 기타 예외 상황도 gracefully 처리
        logger.warning(f"Error validating date: {paid_at}")


def _validate_fare(fare) -> None:
    """요금을 검증하고 100,000원을 초과하는 경우 경고 로그를 출력.
    
    Parameters
    ----------
    fare : int or str or any
        추출된 요금 (정수, 문자열, 또는 기타 타입)
    """
    if fare is None:
        return
    
    try:
        # 다양한 타입을 정수로 변환 시도
        if isinstance(fare, str):
            # 문자열에서 숫자가 아닌 문자 제거 (쉼표, 원화 기호 등)
            fare_cleaned = ''.join(filter(str.isdigit, fare))
            if not fare_cleaned:
                logger.warning(f"Non-numeric fare value: {fare}")
                return
            fare_int = int(fare_cleaned)
        elif isinstance(fare, (int, float)):
            fare_int = int(fare)
        else:
            logger.warning(f"Non-numeric fare value: {fare}")
            return
        
        # 100,000원 초과 여부 확인
        if fare_int > 100000:
            logger.warning(f"High fare amount detected: {fare_int:,} KRW")
            
    except (ValueError, TypeError):
        # 숫자로 변환할 수 없는 경우 gracefully 처리
        logger.warning(f"Non-numeric fare value: {fare}")
    except Exception:
        # 기타 예외 상황도 gracefully 처리
        logger.warning(f"Error validating fare: {fare}")


def _validate_extracted_data(data: Dict) -> Dict:
    """추출된 데이터에 모든 검증을 적용하는 메인 검증 함수.
    
    Parameters
    ----------
    data : Dict
        추출된 데이터 딕셔너리 (paid_at, fare, name, route 포함)
        
    Returns
    -------
    Dict
        검증된 데이터 딕셔너리
    """
    if not data or not isinstance(data, dict):
        logger.warning("Invalid or empty data provided for validation")
        return data or {}
    
    # 데이터 복사본 생성 (원본 수정 방지)
    validated_data = data.copy()
    
    # 1. 팀원 이름 검증 및 정정
    if 'name' in validated_data:
        validated_data['name'] = _validate_team_member(validated_data.get('name'))
    
    # 2. 날짜 검증 (경고 로그만 출력, 데이터는 수정하지 않음)
    if 'paid_at' in validated_data:
        _validate_date(validated_data.get('paid_at'))
    
    # 3. 요금 검증 (경고 로그만 출력, 데이터는 수정하지 않음)
    if 'fare' in validated_data:
        _validate_fare(validated_data.get('fare'))
    
    return validated_data


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

    # Combine front and back data
    combined_data = {**data_front, **data_back}
    
    # Apply validation to the combined data
    validated_data = _validate_extracted_data(combined_data)
    
    return validated_data


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