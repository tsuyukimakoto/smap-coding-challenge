from decimal import Decimal

from django.test import TestCase  # noqa

from challenge.consumption.models import Consumption


class TestConsumption(TestCase):
    def test_value(self):
        obj = Consumption(original_value=Decimal('0.1'))
        self.assertEqual(1, obj.value)
        self.assertEqual(0.1, obj.value_as_base)
