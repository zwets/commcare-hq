from __future__ import absolute_import
from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.conf import settings

from celery.task import task
from celery.utils.log import get_task_logger

from corehq.apps.app_manager.dbaccessors import get_app, get_latest_build_id, get_auto_generated_built_apps
from corehq.apps.app_manager.exceptions import SavedAppBuildException
from corehq.apps.users.models import CommCareUser
from corehq.util.decorators import serial_task


logger = get_task_logger(__name__)


@task(serializer='pickle', queue='background_queue', ignore_result=True)
def create_user_cases(domain_name):
    from corehq.apps.callcenter.sync_user_case import sync_usercase
    for user in CommCareUser.by_domain(domain_name):
        sync_usercase(user)


@serial_task('{app_id}-{version}', max_retries=0, timeout=60 * 60)
def make_async_build_v2(app_id, domain, version, username, allow_prune=True, comment=None):
    app = get_app(domain, app_id)
    errors = app.validate_app()
    if not errors:
        if allow_prune and comment is None:
            comment = _('Auto-generated by a phone update. Will expire after next build if not marked released.')
        if username:
            comment = (comment + ' ') or ''
            comment += _('Generated by user {}.').format(username)
        copy = app.make_build(comment=comment)
        copy.is_auto_generated = allow_prune
        copy.save(increment_version=False)
        return copy


def make_build(app, username, allow_prune=True, comment=None, perform_async=True):
    latest_build = app.get_latest_build()
    if latest_build and latest_build.version == app.version:
        return
    if perform_async:
        make_async_build_v2.delay(app.get_id, app.domain, app.version, username,
                                  allow_prune=allow_prune, comment=comment)
    else:
        make_async_build_v2(app.get_id, app.domain, app.version, username,
                            allow_prune=allow_prune, comment=comment)


@task(serializer='pickle', queue='background_queue', ignore_result=True)
def create_build_files_for_all_app_profiles(domain, build_id):
    app = get_app(domain, build_id)
    build_profiles = app.build_profiles
    save_app = False
    for profile in build_profiles:
        if not app.has_attachment('files/{id}/profile.xml'.format(id=profile)):
            app.create_build_files(build_profile_id=profile)
            save_app = True
    if save_app:
        app.save()


@task(serializer='pickle', queue='background_queue')
def prune_auto_generated_builds(domain, app_id):
    last_build_id = get_latest_build_id(domain, app_id)
    saved_builds = get_auto_generated_built_apps(domain, app_id)

    for doc in saved_builds:
        app = get_app(domain, doc['_id'])
        if app.id == last_build_id or app.is_released:
            continue
        if not app.is_auto_generated or app.copy_of != app_id or app.id == last_build_id:
            raise SavedAppBuildException("Attempted to delete build that should not be deleted")
        app.delete_app()
        logger.info("Pruned build {} from domain {}".format(app.id, domain))
        app.save(increment_version=False)


@task(serializer='pickle', queue='background_queue', ignore_result=True)
def update_linked_app_and_notify_task(domain, app_id, user_id, email):
    from corehq.apps.app_manager.views.utils import update_linked_app_and_notify
    update_linked_app_and_notify(domain, app_id, user_id, email)


@task
def load_appcues_template_app(domain, username, app_slug):
    from corehq.apps.app_manager.views.apps import load_app_from_slug
    load_app_from_slug(domain, username, app_slug)
