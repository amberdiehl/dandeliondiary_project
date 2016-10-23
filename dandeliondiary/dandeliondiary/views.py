from django.shortcuts import redirect


def launch_homepage(request):
    return redirect('public:home')
