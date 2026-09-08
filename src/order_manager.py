# src/order_manager.py
# [수정] 1번째 줄 앞에 실수로 들어가 있던 공백 4칸 제거 (기능 변화 없음, staged된 오타성 변경 정리)

# 메뉴를 구조화된 데이터(dict)로 관리 -> 항목 추가/가격 변경 시 여기만 고치면 됨
MENU_DATA = {
    "1": {"name": "햄버거", "price": 4500},
    "2": {"name": "오징어", "price": 5000},
    "3": {"name": "콜라", "price": 5500},
}


# [추가] llm.py가 반환하는 order_data는 검증 없이 그대로 넘어옴.
# llm.py 쪽 프롬프트/모델이 스키마를 어기면(메뉴에 없는 이름, 수량이 숫자가 아님 등)
# confirm_order가 그대로 신뢰하다가 죽거나 이상 동작하므로, order_manager 쪽에서
# 방어적으로 한 번 걸러준다. (llm.py/main.py는 수정하지 않음 — 담당 모듈만 손댐)
def _validate_orders(orders: list) -> list:
    valid_names = {item["name"] for item in MENU_DATA.values()}
    cleaned = []

    for item in orders:
        menu = item.get("menu")
        qty = item.get("qty")

        # 메뉴판에 없는 이름이면 항목 자체를 버림
        if menu not in valid_names:
            print(f"[시스템] '{menu}'은(는) 메뉴에 없는 항목이라 제외합니다.")
            continue

        # 수량이 없거나 잘못된 값이면 1개로 보정
        if not isinstance(qty, int) or qty <= 0:
            print(f"[시스템] '{menu}'의 수량({qty})이 올바르지 않아 1개로 처리합니다.")
            qty = 1

        requests = item.get("requests")
        cleaned.append({
            "menu": menu,
            "qty": qty,
            "requests": requests if isinstance(requests, list) else [],
        })

    return cleaned


# 메뉴판 출력 (천 단위 쉼표 등 이쁘게 포맷팅)
def display_menu():
    print("\n================ 📋 메뉴판 ================")
    for key, item in MENU_DATA.items():
        print(f"{key}. {item['name']} ({item['price']:,}원)")
    print("==========================================")


def confirm_order(order_data: dict) -> bool:
    """
    주문 내역을 보기 좋게 출력하고 확정/수정 여부를 확인하는 함수.

    - 네/맞음/응     : 주문 확정 (True)
    - 아니오/취소    : 주문 취소, 처음부터 다시 (False)
    - 수정          : 특정 항목의 수량/요청사항 수정 후 다시 확인
    - 다시          : 내용 변경 없이 주문 내역만 다시 보여줌 (다시듣기)
    """
    # [수정] 검증 안 된 orders를 바로 쓰지 않고 _validate_orders를 거치도록 변경
    orders = _validate_orders(order_data.get("orders", []))

    while True:
        print("\n[시스템] 주문하신 내역을 확인해 주세요:")

        for idx, item in enumerate(orders, start=1):
            menu = item.get("menu")
            qty = item.get("qty")
            req = ", ".join(item.get("requests", []))
            req_text = f" (요청사항: {req})" if req else ""

            print(f" {idx}. {menu} {qty}개{req_text}")

        print("\n이대로 주문 진행할까요? (네/아니오/수정/다시)")
        answer = input("👉 사용자 응답: ").strip()

        if "네" in answer or "맞" in answer or "응" in answer:
            return True

        if "취소" in answer or "아니" in answer:
            return False

        # 부분수정: 몇 번째 항목의 수량/요청사항을 바꿀지 물어보고 반영 후 다시 확인
        if "수정" in answer:
            no = input(f"👉 몇 번째 항목을 수정할까요? (1~{len(orders)}): ")
            if not (no.isdigit() and 1 <= int(no) <= len(orders)):
                print("[시스템] 올바른 항목 번호가 아닙니다.")
                continue

            target = orders[int(no) - 1]

            new_qty = input(f"👉 변경할 수량 (현재 {target.get('qty')}개, 유지하려면 그냥 엔터): ").strip()
            if new_qty:
                if new_qty.isdigit() and int(new_qty) > 0:
                    target["qty"] = int(new_qty)
                else:
                    print("[시스템] 올바른 수량이 아니라 변경하지 않았습니다.")

            new_req = input("👉 변경할 요청사항 (콤마로 구분, 유지하려면 그냥 엔터): ").strip()
            if new_req:
                target["requests"] = [r.strip() for r in new_req.split(",") if r.strip()]

            continue

        # 다시듣기: 데이터는 그대로 두고 목록만 다시 보여줌
        if "다시" in answer:
            continue

        print("[시스템] '네', '아니오', '수정', '다시' 중 하나로 답해주세요.")