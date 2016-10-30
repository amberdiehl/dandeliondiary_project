from .models import BudgetCategory, GooglePlaceType, CategorytoGoogleTypes


def helpers_get_current_location_categories(google_types):

    # google_types is an array of arrays that need to be unpacked into a unique list of types
    unpacked_types = []
    for types in google_types:
        for type in types:
            if not type in unpacked_types:
                unpacked_types.append(type)

    items = CategorytoGoogleTypes.objects.filter(google_type__type__in=unpacked_types)

    perma_keys = []
    for item in items:
        perma_keys.append(item.category.category_perma_key)

    return perma_keys
