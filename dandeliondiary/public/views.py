from django.shortcuts import get_object_or_404, render, render_to_response

# Home page
def home(request):
    return render(request, 'public/home.html')