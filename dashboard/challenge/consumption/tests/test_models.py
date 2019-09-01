from datetime import datetime
from decimal import Decimal

from django.test import TestCase  # noqa
from django.utils.timezone import make_aware

from challenge.consumption.models import (
    Account,
    Consumption,
)


class TestConsumption(TestCase):
    fixtures = (
        'area.yaml',
        'tariff.yaml',
        'test_accounts.yaml',
    )

    def test_create_consumption(self):
        measured_datetime = make_aware(
            datetime(2019, 8, 31, 0, 0, 0),
        )
        consumption = Consumption.objects.create_consumption(
            Account.objects.get(pk=1),
            measured_datetime,
            '0.1',
        )
        self.assertTrue(consumption.id is None)
        self.assertEqual(2019, consumption.year)
        self.assertEqual(8, consumption.month)
        self.assertEqual(31, consumption.day)
        self.assertEqual(1, consumption.value)
        self.assertEqual(0.1, consumption.float_value)
