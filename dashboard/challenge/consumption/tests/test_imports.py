from datetime import timedelta
import importlib
import os

from django.db.models import (
    Avg,
    Sum,
    FloatField,
)
from django.db.models.functions import Cast
from django.test import TestCase

from challenge.consumption.models import (
    Account,
    Consumption,
    Area,
    Tariff,
)

import_command = importlib.import_module('challenge.consumption.management.commands.import')


class TestImport(TestCase):
    fixtures = (
        'area.yaml',
        'tariff.yaml',
        'test_accounts.yaml',
    )

    def setUp(self):
        self.account = Account.objects.get(pk=1)

    def _generate_consumption(self):
        return import_command.generage_consumption_from_row(
            self.account,
            ['2019-08-31 00:00:00', '0.1'],
        )

    def test_extract_user_id(self):
        self.assertEqual(
            '0123',
            import_command.extract_user_id(
                '/spam/egg/ham/0123.csv',
            )
        )

    def test_generage_consumption_from_row(self):
        consumption = self._generate_consumption()
        self.assertTrue(consumption.id is None)
        self.assertEqual(2019, consumption.year)
        self.assertEqual(8, consumption.month)
        self.assertEqual(31, consumption.day)
        self.assertEqual(1, consumption.value)
        self.assertEqual(0.1, consumption.float_value)

    def test_is_duplicate(self):
        consumption = self._generate_consumption()
        dlt = timedelta(seconds=1)
        self.assertTrue(import_command.is_duplicate(consumption.measured_datetime, consumption))
        self.assertFalse(import_command.is_duplicate(consumption.measured_datetime + dlt, consumption))

    def test_glob_consumption_files(self):
        filepaths = import_command.glob_consumption_files(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal', 'consumption',
            ),
        )
        data_ids = [import_command.extract_user_id(filepath) for filepath in filepaths]
        self.assertEqual(2, len(data_ids))
        self.assertTrue('3011' in data_ids)
        self.assertTrue('3029' in data_ids)

    def test_import_user_data(self):
        read_count, create_count = import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )
        self.assertEqual(2, create_count)
        self.assertEqual(2, read_count)

        Account.objects.get(data_id='3011').delete()

        read_count, create_count = import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )
        self.assertEqual(1, create_count)
        self.assertEqual(2, read_count)

    def test_import_user_data__dont_touch_exist_user(self):
        before_account = Account.objects.get(data_id='9999')

        read_count, create_count = import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'duplicate_user',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )

        after_account = Account.objects.get(data_id='9999')

        self.assertEqual(1, create_count)
        self.assertEqual(2, read_count)
        self.assertEqual(before_account.area_id, after_account.area_id)
        self.assertEqual(before_account.tariff_id, after_account.tariff_id)

    def test_import_consumption_data(self):
        import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )
        import_command.import_consumption_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal', 'consumption',
            )
        )
        average_list = Consumption.objects.filter(
          year=2016,
          month=7,
        ).values(
          'year', 'month',
        ).annotate(
          average_value=Avg('value') / 10.0,
        ).order_by('year', 'month')

        self.assertEqual(1, len(average_list))
        self.assertEqual(0.1, average_list.first()['average_value'])

        summary_list = Consumption.objects.filter(
          year=2016,
          month=7,
        ).values(
          'year', 'month',
        ).annotate(
          summary_value=Cast(Sum('value') / 10.0, FloatField()),
        ).order_by('year', 'month')

        self.assertEqual(1, len(summary_list))
        self.assertEqual(0.3, summary_list.first()['summary_value'])

    def test_import_consumption_data__duplicate_measured_datetime__first_win(self):
        # 3011's `2016-07-15 00:30:00,0.3` is ignored
        import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )
        with self.assertLogs(
            'challenge.consumption.management.commands.import',
            level='WARNING',
        ) as log_context:
            import_command.import_consumption_data(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'data', 'duplicate_measured_datetime', 'consumption',
                )
            )
            self.assertEqual(1, len(log_context.output))
            self.assertTrue(
                'measured_datetime duplicate' in log_context.output[0]
            )

        summary_list = Consumption.objects.filter(
          year=2016,
          month=7,
        ).values(
          'year', 'month',
        ).annotate(
          summary_value=Cast(Sum('value') / 10.0, FloatField()),
        ).order_by('year', 'month')

        self.assertEqual(1, len(summary_list))
        self.assertEqual(0.3, summary_list.first()['summary_value'])

    def test_import_consumption_data__account_doesnot_exists(self):
        import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )
        with self.assertLogs(
            'challenge.consumption.management.commands.import',
            level='ERROR',
        ) as log_context:
            import_command.import_consumption_data(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'data', 'account_doesnot_exists', 'consumption',
                )
            )
            self.assertEqual(1, len(log_context.output))
            self.assertTrue(
                'User(9998) does not exist' in log_context.output[0]
            )

        summary_list = Consumption.objects.filter(
          year=2016,
          month=7,
        ).values(
          'year', 'month',
        ).annotate(
          summary_value=Cast(Sum('value') / 10.0, FloatField()),
        ).order_by('year', 'month')

        self.assertEqual(1, len(summary_list))
        self.assertEqual(0.3, summary_list.first()['summary_value'])

    def test_import_consumption_data__invalid_datetime_format_ignore_the_file(self):
        import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )
        with self.assertLogs(
            'challenge.consumption.management.commands.import',
            level='ERROR',
        ) as log_context:
            import_command.import_consumption_data(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'data', 'measured_datetime_invalid_format', 'consumption',
                )
            )
            self.assertEqual(1, len(log_context.output))
            self.assertTrue(
                "User(3011)'s consumption data has errors, maybe datetime" in log_context.output[0]
            )

        summary_list = Consumption.objects.filter(
          year=2016,
          month=7,
        ).values(
          'year', 'month',
        ).annotate(
          summary_value=Cast(Sum('value') / 10.0, FloatField()),
        ).order_by('year', 'month')

        self.assertEqual(0, len(summary_list))

    def test_import_consumption_data__duplicate_measured_datetime_and_mixed_order_ignore_the_file(self):
        import_command.import_user_data(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'normal',
                'user_data.csv',
            ),
            Area.objects.master_data(),
            Tariff.objects.master_data(),
        )
        with self.assertLogs(
            'challenge.consumption.management.commands.import',
            level='ERROR',
        ) as log_context:
            import_command.import_consumption_data(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'data', 'duplicate_measured_datetime_and_mixed_order', 'consumption',
                )
            )
            self.assertEqual(1, len(log_context.output))
            self.assertTrue(
                "User(3011)'s consumption data has errors, caused db error" in log_context.output[0]
            )

        summary_list = Consumption.objects.filter(
          year=2016,
          month=7,
        ).values(
          'year', 'month',
        ).annotate(
          summary_value=Cast(Sum('value') / 10.0, FloatField()),
        ).order_by('year', 'month')

        self.assertEqual(0, len(summary_list))
