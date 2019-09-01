from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
import json

from django.db.models import Avg, Sum, FloatField
from django.db.models.functions import Cast, TruncMonth
from django.shortcuts import render

from challenge.consumption.models import Account, Consumption


PLACES = Decimal('0.1')


def year_month_format(year, month):
    return '{0}/{1:02}'.format(year, month)


def summary(request):
    # averages = Consumption.objects.annotate(
    #   used_year_month=TruncMonth('timestamp'),
    # ).values(
    #   'used_year_month',
    # ).annotate(
    #   average_value=Avg('original_value'),
    # ).order_by('used_year_month')


    # summaries = Consumption.objects.annotate(
    #   used_year_month=TruncMonth('timestamp'),
    # ).values(
    #   'used_year_month',
    # ).annotate(
    #   summary_value=Sum('original_value'),
    # ).order_by('used_year_month')

    # averages = Consumption.objects.values(
    #   'year_month',
    # ).annotate(
    #   average_value=Avg('float_value'),
    # ).order_by('year_month')


    # summaries = Consumption.objects.values(
    #   'year_month',
    # ).annotate(
    #   summary_value=Sum('float_value'),
    # ).order_by('year_month')

    averages = Consumption.objects.values(
      'year', 'month',
    ).annotate(
      average_value=Avg('value') / 10.0,
      # average_value=Avg('float_value'),
    ).order_by('year', 'month')

    summaries = Consumption.objects.values(
      'year', 'month',
    ).annotate(
      summary_value=Cast(Sum('value') / 10.0, FloatField()),
      # summary_value=Sum('float_value'),
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


    account_list_qs = Account.objects.all().select_related('area', 'tariff')
    context = {
        'monthly_list': monthly_list,
        'average_list': average_list,
        'summary_list': summary_list,
        'account_list': account_list_qs,
        'divide_count': account_list_qs.count() // 2,
    }
    return render(request, 'consumption/summary.html', context)



def detail(request):
    context = {
    }
    return render(request, 'consumption/detail.html', context)


"""
from django.db.models import Avg, Sum
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth


from challenge.consumption.models import Consumption

Consumption.objects.annotate(
  used_month=ExtractMonth('timestamp'),
).values(
  'used_month',
).annotate(
  average_value=Avg('original_value'),
).order_by('used_month')



from django.db.models import Avg, Sum
from django.db.models.functions import TruncMonth

from challenge.consumption.models import Consumption


Consumption.objects.annotate(
  used_year_month=TruncMonth('timestamp'),
).values(
  'used_year_month',
).annotate(
  average_value=Avg('original_value'),
).order_by('used_year_month')



OrderItem.objects.all().annotate(order_month=ExtractMonth('order__payment_date'))



from datetime import datetime

from django.db.models import Avg, Sum
from django.utils.timezone import make_aware

from challenge.consumption.models import Consumption


Consumption.objects.values(
  'timestamp',
).annotate(
  average_value=Avg('original_value'),
).order_by(
  'timestamp',
).filter(
  timestamp__range=(
    make_aware(datetime(2016, 10, 1)),
    make_aware(datetime(2016, 10, 2)),
  )
)


Consumption.objects.values(
  'timestamp',
).annotate(
  average_value=Sum('original_value'),
).order_by(
  'timestamp',
).filter(
  timestamp__range=(
    make_aware(datetime(2016, 10, 1)),
    make_aware(datetime(2016, 10, 2)),
  )
)
"""
