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
    def create_consumption(self, account, timestamp, value):
        return self.model(
            account=account,
            timestamp=timestamp,
            original_value=Decimal(value),
            value = int(Decimal(value) * 10),
            float_value=value,
            year = timestamp.year,
            month = timestamp.month,
            day = timestamp.day,
            year_month=int(timestamp.strftime('%Y%m')),
        )

class Consumption(models.Model):
    account = models.ForeignKey(Account)
    timestamp = models.DateTimeField()
    year_month = models.IntegerField()
    year = models.IntegerField()
    month = models.IntegerField()
    day = models.IntegerField()
    # 10 times the original value
    value = models.IntegerField()
    float_value = models.FloatField()
    original_value = models.DecimalField(
        _("Consumption"),
        max_digits=6,
        decimal_places=1,
    )

    objects = ConsumptionManager()

    @property
    def value_as_base(self):
        return self.value / 10

    class Meta:
        get_latest_by = 'timestamp'
        indexes = [
            models.Index(fields=['timestamp'], name='idx_consumption__timestamp'),
            models.Index(fields=['year_month'], name='idx_consumption__year_month'),
            models.Index(fields=['year', 'month', 'day'], name='idx_consumption__ymd'),
        ]
        unique_together = (("account", "timestamp"),)
