from django.conf import settings

def setting_tags( request ):
    return {'STATIC_URL': settings.STATIC_URL,}
