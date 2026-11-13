# only-wholesale

Исправленные ошибки в starter.py:
1. Тайм-аут и обработка ошибок источника (Правило 1): Вызов fetch_offers() не был обёрнут в asyncio.wait_for(..., timeout=timeout_s) и try...except Exception, а также не проверялся result.get("status") != "success".

2. Фильтрация предложений (Правила 2 и 3):
  - Не исключался собственный магазин MYSHOP (offer["seller"].strip().upper() == "MYSHOP").
  - Если delivery_days is None, сравнение offer["delivery_days"] <= 6 вызывало TypeError.
  - При пустом списке подходящих цен min(prices) вызывал ValueError вместо возврата current_price со статусом HOLD.

3. Точность расчётов и округление (Правило 4):
  - Использовался float и банковское округление round(..., 2) вместо точной арифметики Decimal и округления вниз ROUND_DOWN до Decimal("0.01").
  - Не применялся нижний порог max(discounted_price, min_price).

4. Проверка отклонения от текущей цены (Правило 5): Отсутствовала проверка отклонения более чем на 30% (abs(recommended - current_price) > current_price * Decimal("0.30")) с возвратом решения REVIEW.
