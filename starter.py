"""Учебный фрагмент для тестового задания ТОЛЬКООПТ.

Python 3.10+, только стандартная библиотека. Запуск примера: python starter.py
"""

import asyncio
from decimal import Decimal, ROUND_DOWN
from typing import Any, Awaitable, Callable

OWN_SELLER = "MYSHOP"
MAX_DELIVERY_DAYS = 6
DISCOUNT_MULTIPLIER = Decimal("0.985")
MAX_DEVIATION_RATIO = Decimal("0.30")
PENNY = Decimal("0.01")


def _make_result(price: Decimal, decision: str, reason: str) -> dict[str, Any]:
    return {
        "price": price,
        "decision": decision,
        "reason": reason,
    }


def _is_valid_competitor_offer(offer: dict[str, Any]) -> bool:
    seller = offer.get("seller", "")
    if seller.strip().upper() == OWN_SELLER:
        return False

    delivery_days = offer.get("delivery_days")
    return delivery_days is not None and delivery_days <= MAX_DELIVERY_DAYS


async def recommend_price(
    fetch_offers: Callable[[], Awaitable[dict[str, Any]]],
    current_price: Decimal,
    min_price: Decimal,
    timeout_s: float = 2.0,
) -> dict[str, Any]:
    # 1. Ограничение ожидания и обработка сбоев / некорректного статуса источника
    try:
        result = await asyncio.wait_for(fetch_offers(), timeout=timeout_s)
    except asyncio.TimeoutError:
        return _make_result(current_price, "HOLD", "Превышено время ожидания источника")
    except Exception as exc:
        return _make_result(current_price, "HOLD", f"Ошибка источника данных: {exc}")

    if not isinstance(result, dict) or result.get("status") != "success":
        status = result.get("status") if isinstance(result, dict) else "unknown"
        return _make_result(current_price, "HOLD", f"Неуспешный статус источника: {status}")

    # 2. Фильтрация предложений конкурентов
    offers = result.get("offers", [])
    valid_prices = [
        offer["price"]
        for offer in offers
        if _is_valid_competitor_offer(offer)
    ]

    # 3. Если подходящих предложений нет — оставляем текущую цену (даже если она < min_price)
    if not valid_prices:
        return _make_result(current_price, "HOLD", "Нет подходящих предложений конкурентов")

    # 4. Снижение минимальной цены на 1,5%, округление вниз до копейки и ограничение min_price
    min_competitor_price = min(valid_prices)
    discounted_price = (min_competitor_price * DISCOUNT_MULTIPLIER).quantize(
        PENNY, rounding=ROUND_DOWN
    )
    recommended_price = max(discounted_price, min_price)

    # 5. Проверка отклонения более чем на 30% в любую сторону (ровно 30% допускается)
    max_allowed_diff = current_price * MAX_DEVIATION_RATIO
    if abs(recommended_price - current_price) > max_allowed_diff:
        return _make_result(
            recommended_price,
            "REVIEW",
            "Отклонение новой цены от текущей превышает 30%",
        )

    return _make_result(
        recommended_price,
        "APPLY",
        "Рассчитана конкурентная цена в допустимых пределах",
    )


async def sample_fetch_offers() -> dict[str, Any]:
    return {
        "status": "success",
        "offers": [
            {"seller": "myshop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ],
    }


if __name__ == "__main__":
    print(
        asyncio.run(
            recommend_price(
                sample_fetch_offers,
                current_price=Decimal("4900.00"),
                min_price=Decimal("4500.00"),
            )
        )
    )
