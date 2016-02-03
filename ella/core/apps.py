from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EllaCoreConfig(AppConfig):
    name = 'ella.core'
    verbose_name = _("Ella Core")

