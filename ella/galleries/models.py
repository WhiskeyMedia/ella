from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.utils.datastructures import SortedDict

from ella.core.box import Box
from ella.db.models import Publishable
from ella.core.models import Category, Author
from ella.core.cache.utils import get_cached_object, cache_this
from ella.core.cache.invalidate import CACHE_DELETER
from ella.photos.models import Photo


def gallery_cache_invalidator(key, gallery, *args, **kwargs):
    """Registers gallery cache invalidator test in the cache system."""
    CACHE_DELETER.register_pk(gallery, key)
    CACHE_DELETER.register_test(GalleryItem, 'gallery_id:%s' % gallery.pk, key)

def get_gallery_key(func, gallery):
    return 'ella.galleries.models.Gallery.items:%d' % gallery.id

class Gallery(Publishable, models.Model):
    """
    Definition of objects gallery
    """
    # Gallery heading
    title = models.CharField(_('Title'), max_length=255)
    slug = models.CharField(_('Slug'), max_length=255)
    # Gallery metadata
    description = models.CharField(_('Description'), max_length=3000, blank=True)
    content = models.TextField(_('Content'), blank=True)
    owner = models.ForeignKey(Author, verbose_name=_('Gallery owner'), blank=True, null=True)
    category = models.ForeignKey(Category, verbose_name=_('Category'), blank=True, null=True)
    created = models.DateTimeField(_('Created'), default=datetime.now, editable=False)

    @property
    @cache_this(get_gallery_key, gallery_cache_invalidator)
    def items(self):
        """
        Returns sorted dict of gallery items. Unique items slugs are used as keys. Values are tuples of items and its targets.
        """
        slugs_count = {}
        itms = [ (item, item.target) for item in self.galleryitem_set.all() ]
        slugs_unique = set((i[1].slug for i in itms))
        res = SortedDict()

        for item, target in itms:
            slug = target.slug
            if slug not in slugs_count:
                slugs_count[slug] = 1
                res[slug] = (item, target)
            else:
                while "%s%s" % (slug, slugs_count[slug]) in slugs_unique:
                    slugs_count[slug] += 1
                new_slug = "%s%s" % (slug, slugs_count[slug])
                slugs_unique.add(new_slug)
                res[new_slug] = (item, target)
        return res

    def get_photo(self):
        """
        Returns first Photo item in the gallery.

        Overrides Publishable.get_photo.
        """
        for item in self.items.itervalues():
            if isinstance(item[1], Photo):
                return item[1]

    class Meta:
        verbose_name = _('Gallery')
        verbose_name_plural = _('Galleries')

    def __unicode__(self):
        return u'%s gallery' % self.title


class GalleryItem(models.Model):
    """
    Specific object in gallery
    """
    gallery = models.ForeignKey(Gallery, verbose_name=_("Parent gallery"))
    target_ct = models.ForeignKey(ContentType, verbose_name=_('Target content type'))
    target_id = models.IntegerField(_('Target ID'), db_index=True)
    order = models.IntegerField(_('Object order')) # TODO: order with respect to

    @property
    def target(self):
        """Returns item's target object."""
        ct = get_cached_object(ContentType, pk=self.target_ct_id)
        return get_cached_object(ct, pk=self.target_id)

    def _get_slug(self):
        if not hasattr(self, '_item_list'):
            self._item_list = self.gallery.items

        for slug, item in self._item_list.items():
            if item[0] == self:
                return slug
        else:
            raise Http404

    def Box(self, box_type, nodelist):
        return Box(self.target, box_type, nodelist)

    def get_slug(self):
        """
        Return a unique slug for given gallery, even if there are more objects with the same slug.
        """
        if not hasattr(self, '_slug'):
            self._slug = self._get_slug()
        return self._slug

    def get_absolute_url(self):
        return '%s%s/%s/' % (self.gallery.get_absolute_url(), slugify(_('items')), self.get_slug())

    class Meta:
        ordering = ('order',)
        verbose_name = _('Gallery item')
        verbose_name_plural = _('Gallery items')
        unique_together = (('gallery', 'order',),)

# initialization
from ella.galleries import register
del register

