from django.shortcuts import render


def summary(request):
    context = {
        'message': 'Hello!',
    }
    return render(request, 'consumption/summary.html', context)


def detail(request):
    context = {
    }
    return render(request, 'consumption/detail.html', context)
