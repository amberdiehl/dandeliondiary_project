import datetime
from django.shortcuts import HttpResponse
from .models import CategorytoGoogleTypes, GooglePlaceDetail


def helpers_get_current_location_categories(google_types):

    # google_types is an array of arrays that need to be unpacked into a unique list of types
    unpacked_types = []
    for types in google_types:
        for tp in types:
            if tp not in unpacked_types:
                unpacked_types.append(tp)

    items = CategorytoGoogleTypes.objects.filter(google_type__type__in=unpacked_types)\

    perma_keys = []
    for item in items:
        perma_keys.append(item.category.category_perma_key)

    return perma_keys


def helpers_add_google_place(pid, name, lat, lng):

    obj, created = GooglePlaceDetail.objects.get_or_create(
        place_id=pid,
        defaults={'place_name': name, 'place_lat': lat, 'place_lng': lng, 'place_count': 1},
    )

    if not created:
        obj.place_count += 1
        obj.place_last_count = datetime.datetime.now()
        obj.save()

    return obj


def login_required_ajax(function=None,redirect_field_name=None):
    """
    Make sure the user is authenticated to access a certain ajax view

    Otherwise return a HttpResponse 401 - authentication required
    instead of the 302 redirect of the original Django decorator
    """
    def _decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(status=401)
        return _wrapped_view

    if function is None:
        return _decorator
    else:
        return _decorator(function)