from django.shortcuts import render


def home(request):
    return render(request, 'public/home.html')


def terms(request):
    return render(request, 'public/terms-of-use.html')


def privacy(request):
    return render(request, 'public/privacy.html')


def cookies(request):
    return render(request, 'public/cookies.html')


def capture(request):
    return render(request, 'public/capture.html')


def compare(request):
    return render(request, 'public/compare.html')


def contribute(request):
    return render(request, 'public/contribute.html')


def about_us(request):
    return render(request, 'public/about-us.html')


def faq(request):
    return render(request, 'public/frequently-asked-questions.html')


def contact(request):
    return render(request, 'public/contact.html')


def code_of_conduct(request):
    return render(request, 'public/community_code_of_conduct.html')
