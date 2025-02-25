from django.utils.translation import gettext as _

from corehq.apps.celery import task
from celery.utils.log import get_task_logger

from corehq.apps.app_manager.dbaccessors import (
    get_app,
    get_auto_generated_built_apps,
    get_latest_build_id,
    get_build_ids,
)
from corehq.apps.app_manager.exceptions import (
    AppValidationError,
    SavedAppBuildException,
)
from corehq.apps.users.models import CommCareUser, CouchUser
from corehq.toggles import USH_USERCASES_FOR_WEB_USERS
from corehq.util.decorators import serial_task
from corehq.util.metrics import metrics_counter

logger = get_task_logger(__name__)


@task(queue='background_queue', ignore_result=True)
def create_usercases(domain_name):
    from corehq.apps.callcenter.sync_usercase import sync_usercases
    if USH_USERCASES_FOR_WEB_USERS.enabled(domain_name):
        users = CouchUser.by_domain(domain_name)
    else:
        users = CommCareUser.by_domain(domain_name)
    for user in users:
        sync_usercases(user, domain_name, sync_call_center=False)


def autogenerate_build(app, username):
    comment = _('Auto-generated by a phone update. Will expire after next build if not marked released. '
                'Generated by user {}.').format(username)
    latest_build = app.get_latest_build()
    if not latest_build or latest_build.version != app.version:
        autogenerate_build_task.delay(app.get_id, app.domain, app.version, comment)


@serial_task('{app_id}-{version}', max_retries=0, timeout=60 * 60)
def autogenerate_build_task(app_id, domain, version, comment):
    app = get_app(domain, app_id)
    try:
        copy = app.make_build(comment=comment)
    except AppValidationError:
        return
    copy.is_auto_generated = True
    copy.save(increment_version=False)
    return copy


@task(queue='background_queue', ignore_result=True)
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


@task(queue='background_queue')
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


@task(queue='background_queue', ignore_result=True)
def update_linked_app_and_notify_task(domain, app_id, master_app_id, user_id, email):
    from corehq.apps.app_manager.views.utils import (
        update_linked_app_and_notify,
    )
    update_linked_app_and_notify(domain, app_id, master_app_id, user_id, email)


@task(queue='background_queue', ignore_result=True)
def analyse_new_app_build(domain, new_build_id):
    new_build = get_app(domain, new_build_id)

    check_for_custom_callouts(new_build)
    check_build_dependencies(new_build)


def check_for_custom_callouts(new_build):
    from corehq.apps.app_manager.util import app_callout_templates_ids
    template_ids = app_callout_templates_ids()

    def app_has_custom_intents():
        return any(
            any(set(form.wrapped_xform().odk_intents) - template_ids)
            for form in new_build.get_forms()
        )

    if app_has_custom_intents():
        metrics_counter(
            'commcare.app_build.custom_app_callout',
            tags={'domain': new_build.domain, 'app_id': new_build.copy_of},
        )


def check_build_dependencies(new_build):
    """
    Reports whether the app dependencies have been added or removed.
    """

    def has_dependencies(build):
        return bool(
            build.profile.get('features', {}).get('dependencies')
        )

    new_build_has_dependencies = has_dependencies(new_build)
    app_build_ids = get_build_ids(new_build.domain, new_build.copy_of)

    last_build_has_dependencies = False

    if len(app_build_ids) > 1:
        previous_build_id = app_build_ids[app_build_ids.index(new_build.id) + 1]
        previous_build = get_app(new_build.domain, previous_build_id)
        last_build_has_dependencies = has_dependencies(previous_build) if previous_build else False

    if not last_build_has_dependencies and new_build_has_dependencies:
        metrics_counter('commcare.app_build.dependencies_added')
    elif last_build_has_dependencies and not new_build_has_dependencies:
        metrics_counter('commcare.app_build.dependencies_removed')
