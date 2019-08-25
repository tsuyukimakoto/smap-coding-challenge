import csv
from datetime import datetime
from decimal import Decimal
from glob import glob
import logging
import os


from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import (
    transaction,
    IntegrityError,
)
from django.utils.timezone import make_aware

from challenge.consumption.models import (
    Account,
    Area,
    Consumption,
    Tariff,
)
USER_CSV_USER_ID = 0
USER_CSV_AREA = 1
USER_CSV_TARIFF = 2

CONSUMPTION_CSV_TIMESTAMP = 0
CONSUMPTION_CSV_CONSUMPTION = 1


logger = logging.getLogger(__name__)


def import_user_data(filepath, areas, tariffs):
    logger.info('Start importing user data')

    with open(filepath, 'r', newline='') as f:
        create_count = 0
        read_count = 0
        reader = csv.reader(f)
        # skip 1st line
        next(reader)

        for row in reader:
            read_count += 1
            area = areas.get(row[USER_CSV_AREA], None)
            tariff = tariffs.get(row[USER_CSV_TARIFF], None)
            if area and tariff:
                obj, created = Account.objects.get_or_create(
                    data_id=row[USER_CSV_USER_ID],
                    defaults={
                        'area': area,
                        'tariff': tariff,
                    }
                )
                if created:
                    create_count += 1
                logger.debug("user(%s) created: %s", row[USER_CSV_USER_ID], created)
            else:
                logger.error(
                    "user(%s)'s area(%s) or tariff(%s) are illegal.",
                    row[USER_CSV_USER_ID],
                    row[USER_CSV_AREA],
                    row[USER_CSV_TARIFF],
                )
    logger.info(
        'END importing user data: created(%d)/read(%d)',
        create_count,
        read_count,
    )


def _extract_user_id(filepath):
    _, filename = os.path.split(filepath)
    return os.path.splitext(filename)[0]


def insert_consumption(filepath):
    logger.info('Start importing consumption data: %s', filepath)

    data_list = []
    data_id = _extract_user_id(filepath)
    try:
        account = Account.objects.get(data_id=data_id)
    except Account.DoesNotExist:
        logger.error('User(%s) does not exist.', data_id)

    with open(filepath, 'r', newline='') as f:
        reader = csv.reader(f)

        next(reader)  # skip 1st line

        _before = None  # check for duplicate timestamp
        for row in reader:
            timestamp = make_aware(
                datetime.strptime(row[CONSUMPTION_CSV_TIMESTAMP], "%Y-%m-%d %H:%M:%S"),
            )
            if _before and _before.timestamp() == timestamp.timestamp():
                logger.warning(
                    "User(%s)'s consumption data timestamp duplicate: %s.",
                    data_id,
                    row[CONSUMPTION_CSV_TIMESTAMP],
                )
                continue
            _before = timestamp

            data_list.append(
                Consumption(
                    account=account,
                    timestamp=timestamp,
                    original_value=Decimal(row[CONSUMPTION_CSV_CONSUMPTION]),
                ),
            )
    with transaction.atomic():
        try:
            # 999 for SQLite
            Consumption.objects.bulk_create(data_list)
        except IntegrityError as e:  # rollbacked
            logger.exception(
                """User(%s)'s consumption data has errors: %s.""",
                data_id,
                e,
            )
        else:
            logger.info('END importing consumption data: %s', data_id)


class Command(BaseCommand):
    help = 'import data'

    def handle(self, *args, **options):
        areas = Area.objects.master_data()
        tariffs = Tariff.objects.master_data()
        import_user_data(
            settings.USER_DATA_FILE,
            areas,
            tariffs,
        )
        file_list = glob(
            os.path.join(
                settings.CONSUMPTION_DATA_DIR,
                '*.csv',
            )
        )

        # sqlite should not use multiprocessing
        # from multiprocessing import Pool
        # with Pool(processes=4) as pool:
        #     result = pool.map(insert_consumption, file_list)

        for filepath in file_list:
            insert_consumption(filepath)
