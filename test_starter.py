import asyncio
import unittest
from decimal import Decimal

from starter import recommend_price, sample_fetch_offers


class TestRecommendPrice(unittest.IsolatedAsyncioTestCase):
    async def test_standard_calculation_apply(self):
        """Обычный расчёт: исключается MYSHOP и доставка > 6 дней, скидка 1.5% вниз."""
        res = await recommend_price(
            sample_fetch_offers,
            current_price=Decimal("4900.00"),
            min_price=Decimal("4500.00"),
        )
        self.assertEqual(res["price"], Decimal("4728.00"))
        self.assertEqual(res["decision"], "APPLY")
        self.assertIsInstance(res["reason"], str)

    async def test_source_timeout_returns_hold(self):
        """Сбой: превышение timeout_s возвращает текущую цену и HOLD."""
        async def slow_fetch():
            await asyncio.sleep(0.2)
            return {"status": "success", "offers": []}

        res = await recommend_price(
            slow_fetch,
            current_price=Decimal("4900.00"),
            min_price=Decimal("4500.00"),
            timeout_s=0.05,
        )
        self.assertEqual(res["price"], Decimal("4900.00"))
        self.assertEqual(res["decision"], "HOLD")

    async def test_deviation_boundary_30_percent_and_above(self):
        """Граничный случай: ровно 30% -> APPLY, более 30% -> REVIEW."""
        async def fetch_for_30_percent():
            # COMP_A отсекается (delivery_days=None), для COMP_B: 1000.00 * 0.985 = 985.00
            return {
                "status": "success",
                "offers": [
                    {"seller": "COMP_A", "price": Decimal("500.00"), "delivery_days": None},
                    {"seller": "COMP_B", "price": Decimal("1000.00"), "delivery_days": 6},
                ],
            }

        # max(985.00, 1300.00) = 1300.00 -> отклонение от 1000.00 ровно +30% -> APPLY
        res_exact = await recommend_price(
            fetch_for_30_percent,
            current_price=Decimal("1000.00"),
            min_price=Decimal("1300.00"),
        )
        self.assertEqual(res_exact["price"], Decimal("1300.00"))
        self.assertEqual(res_exact["decision"], "APPLY")

        # max(985.00, 1300.01) = 1300.01 -> отклонение от 1000.00 более +30% -> REVIEW
        res_over = await recommend_price(
            fetch_for_30_percent,
            current_price=Decimal("1000.00"),
            min_price=Decimal("1300.01"),
        )
        self.assertEqual(res_over["price"], Decimal("1300.01"))
        self.assertEqual(res_over["decision"], "REVIEW")

    async def test_no_valid_offers_keeps_current_even_below_min_price(self):
        """Правило 3: если подходящих офферов нет, возвращается current_price и HOLD даже если < min_price."""
        async def only_myshop_and_unknown_delivery():
            return {
                "status": "success",
                "offers": [
                    {"seller": "MyShop", "price": Decimal("3000.00"), "delivery_days": 1},
                    {"seller": "OTHER", "price": Decimal("3500.00"), "delivery_days": None},
                ],
            }

        res = await recommend_price(
            only_myshop_and_unknown_delivery,
            current_price=Decimal("4000.00"),
            min_price=Decimal("4500.00"),
        )
        self.assertEqual(res["price"], Decimal("4000.00"))
        self.assertEqual(res["decision"], "HOLD")


if __name__ == "__main__":
    unittest.main()