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


class Consumption(models.Model):
    account = models.ForeignKey(Account)
    timestamp = models.DateTimeField()
    # 10 times the original value
    value = models.IntegerField()
    original_value = models.DecimalField(
        _("Consumption"),
        max_digits=6,
        decimal_places=1,
    )

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if 'original_value' == name:
            self.value = int(value * 10)

    @property
    def value_as_base(self):
        return self.value / 10

    class Meta:
        get_latest_by = 'timestamp'
        indexes = [
            models.Index(fields=['timestamp'], name='idx_consumption__timestamp'),
        ]
        unique_together = (("account", "timestamp"),)
