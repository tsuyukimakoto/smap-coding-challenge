from decimal import Decimal

from django.db.models import (
  Avg,
  Sum,
  FloatField,
)
from django.db.models.functions import Cast
from django.shortcuts import render

from challenge.consumption.models import (
  Account,
  Consumption,
)


def year_month_format(year, month):
    return '{0}/{1:02}'.format(year, month)


def summary(request):
    averages = Consumption.objects.values(
      'year', 'month',
    ).annotate(
      average_value=Avg('value') / 10.0,
    ).order_by('year', 'month')

    summaries = Consumption.objects.values(
      'year', 'month',
    ).annotate(
      summary_value=Cast(Sum('value') / 10.0, FloatField()),
    ).order_by('year', 'month')

    monthly_list = [
      year_month_format(
        average['year'],
        average['month']) for average in averages
    ]
    average_list = [
      average['average_value'] for average in averages
    ]
    summary_list = [
      summary['summary_value'] for summary in summaries
    ]

    # avoid n+1
    account_list_qs = Account.objects.all().select_related('area', 'tariff')
    context = {
        'monthly_list': monthly_list,
        'average_list': average_list,
        'summary_list': summary_list,
        'account_list': account_list_qs,
        'divide_count': account_list_qs.count() // 2, # for template logic
    }
    return render(request, 'consumption/summary.html', context)


def detail(request):
    context = {
    }
    return render(request, 'consumption/detail.html', context)
