"""
If celery is installed, register our maintenance commands as periodic tasks to
avoid the requirement for external crond.
"""

try:
    from datetime import timedelta

    from celery.task import periodic_task

    from ella.core.management import generate_publish_signals, regenerate_listing_handlers
    from ella.core.management import unpublish_publish_to_expirations

    periodic_task(run_every=timedelta(minutes=5))(generate_publish_signals)
    periodic_task(run_every=timedelta(hours=3))(regenerate_listing_handlers)
    periodic_task(run_every=timedelta(hours=1))(unpublish_publish_to_expirations)
except ImportError:
    # celery not installed
    pass

