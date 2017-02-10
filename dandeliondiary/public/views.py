from django.shortcuts import get_object_or_404, render, render_to_response


def home(request):
    return render(request, 'public/home.html')


def terms(request):
    return render(request, 'public/terms-of-use.html')


def privacy(request):
    return render(request, 'public/privacy.html')


def cookies(request):
    return render(request, 'public/cookies.html')
