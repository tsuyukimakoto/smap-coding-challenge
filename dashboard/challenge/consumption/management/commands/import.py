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
        # skip 1st line (header)
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
    return (read_count, create_count, )


def extract_user_id(filepath):
    _, filename = os.path.split(filepath)
    return os.path.splitext(filename)[0]


def generage_consumption_from_row(account, row):
    _s = row[CONSUMPTION_CSV_TIMESTAMP]
    timestamp = make_aware(
        # strptime costs 1.5 times
        datetime(
            year=int(_s[0:4]),
            month=int(_s[5:7]),
            day=int(_s[8:10]),
            hour=int(_s[11:13]),
            minute=int(_s[14:16]),
            second=int(_s[17:19]),
        )
    )
    return Consumption.objects.create_consumption(
        account,
        timestamp,
        row[CONSUMPTION_CSV_CONSUMPTION],
    )

def is_duplicate(prev_measured_datetime, consumption):
    if prev_measured_datetime and \
       prev_measured_datetime.timestamp() == consumption.measured_datetime.timestamp():
        logger.warning(
            "User(%s)'s consumption data measured_datetime duplicate: %s.",
            consumption.account_id,
            prev_measured_datetime,
        )
        return True
    return False


def bulk_insert(data_list):
    if len(data_list) == 0:
        return

    with transaction.atomic():
        # 999 for SQLite
        Consumption.objects.bulk_create(data_list)
        # for c in data_list:
        #     c.save()
        logger.info('END importing consumption data: %s', data_list[0].account_id)


def insert_consumption(filepath):
    logger.info('Start importing consumption data: %s', filepath)

    data_list = []
    data_id = extract_user_id(filepath)
    account = Account.objects.get(data_id=data_id)

    with open(filepath, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # skip 1st line (header)

        _before = None  # check for duplicate measured_datetime
        for row in reader:
            consumption = generage_consumption_from_row(account, row)
            if is_duplicate(_before, consumption):  # depends on specification
                continue
            _before = consumption.measured_datetime
            data_list.append(
                consumption,
            )

    bulk_insert(data_list)


def glob_consumption_files():
    return glob(
        os.path.join(
            settings.CONSUMPTION_DATA_DIR,
            '*.csv',
        )
    )


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
        file_list = glob_consumption_files()

        # bulk_insert_start = datetime.now()
        # # sqlite should not use multiprocessing
        # from multiprocessing import Pool
        # with Pool(processes=4) as pool:
        #     result = pool.map(insert_consumption, file_list)
        # bulk_insert_end = datetime.now()
        # logger.error('bulk insert %s', bulk_insert_end - bulk_insert_start)

        bulk_insert_start = datetime.now()
        for filepath in file_list:
            try:
                insert_consumption(filepath)
            except Account.DoesNotExist:
                logger.error(
                    'User(%s) does not exist. %s skiped.',
                    extract_user_id(filepath),
                    filepath,
                )
            except IntegrityError as e:  # rollbacked
                logger.exception(
                    """User(%s)'s consumption data has errors: %s.""",
                    extract_user_id(filepath),
                    e,
                )
            except ValueError as e:
                logger.exception(
                    """User(%s)'s consumption data has errors: %s.""",
                    extract_user_id(filepath),
                    e,
                )
        bulk_insert_end = datetime.now()
        logger.error('bulk insert %s', bulk_insert_end - bulk_insert_start)
