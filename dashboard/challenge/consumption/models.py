from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _


class MasterManager(models.Manager):
    def master_data(self):
        result = {}
        for data in self.get_queryset().all():
            result[data.label] = data
        return result


class MasterDataModel(models.Model):
    objects = MasterManager()

    def __str__(self):
        return self.label

    class Meta:
        abstract = True


class Area(MasterDataModel):
    label = models.CharField(_("Area name"), max_length=10)


class Tariff(MasterDataModel):
    label = models.CharField(_("Tariff type"), max_length=10)


class Account(models.Model):
    data_id = models.IntegerField(_("User ID"), unique=True)
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ['data_id']
        indexes = [
            models.Index(fields=['data_id'], name='idx_account__data_id'),
        ]


class ConsumptionManager(models.Manager):
    def create_consumption(self, account, measured_datetime, value):
        return self.model(
            account=account,
            measured_datetime=measured_datetime,
            value = int(Decimal(value) * 10),
            float_value=float(value),
            year = measured_datetime.year,
            month = measured_datetime.month,
            day = measured_datetime.day,
        )


class Consumption(models.Model):
    account = models.ForeignKey(Account)
    measured_datetime = models.DateTimeField()
    year = models.IntegerField()
    month = models.IntegerField()
    day = models.IntegerField()
    # 10 times the original value
    value = models.IntegerField()
    float_value = models.FloatField()

    objects = ConsumptionManager()

    @property
    def value_as_base(self):
        return self.value / 10

    class Meta:
        get_latest_by = 'measured_datetime'
        indexes = [
            models.Index(fields=['measured_datetime'], name='idx_consumption__measured_dt'),
            models.Index(fields=['year', 'month', 'day'], name='idx_consumption__ymd'),
        ]
        unique_together = (("account", "measured_datetime"),)
