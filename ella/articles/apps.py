from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EllaArticlesConfig(AppConfig):
    name = 'ella.articles'
    verbose_name = _("Articles")
