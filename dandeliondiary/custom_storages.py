from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class StaticStorage(S3BotoStorage):
    location = settings.STATICFILES_LOCATION

    def _clean_name(self, name):
        return name

    def _normalize_name(self, name):
        if not name[0] == '/':
            name = '/' + name
        # if not name.endswith('/'):
        #    name += "/"

        # name += self.location
        name = self.location + name
        return name


class MediaStorage(S3BotoStorage):
    location = settings.MEDIAFILES_LOCATION

    def _clean_name(self, name):
        return name

    def _normalize_name(self, name):
        if not name[0] == '/':
            name = '/' + name
        # if not name.endswith('/'):
        #    name += "/"

        # name += self.location
        name = self.location + name
        return name
