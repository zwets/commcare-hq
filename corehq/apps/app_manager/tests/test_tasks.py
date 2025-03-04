from unittest.mock import patch

from corehq.apps.app_manager.dbaccessors import get_app, get_build_ids
from corehq.apps.app_manager.models import import_app
from corehq.apps.app_manager.tasks import (
    autogenerate_build,
    prune_auto_generated_builds,
)
from corehq.apps.app_manager.tests.app_factory import AppFactory
from corehq.apps.app_manager.tests.test_apps import AppManagerTest
from corehq.apps.app_manager.tests.util import get_simple_form, patch_validate_xform
from corehq.apps.app_manager.views.releases import make_app_build


@patch_validate_xform()
class AppManagerTasksTest(AppManagerTest):
    def test_prune_auto_generated_builds(self):
        # Build #1, manually generated
        app = import_app(self._yesno_source, self.domain)
        for module in app.modules:
            module.get_or_create_unique_id()
        app.save()
        build1 = app.make_build()
        build1.save()
        self.assertFalse(build1.is_auto_generated)

        # Build #2, auto-generated
        app.save()
        autogenerate_build(app, "username")
        build_ids = get_build_ids(app.domain, app.id)
        self.assertEqual(len(build_ids), 2)
        self.assertEqual(build_ids[1], build1.id)
        build2 = get_app(app.domain, build_ids[0])
        self.assertTrue(build2.is_auto_generated)

        # First prune: delete nothing because the auto build is the most recent
        prune_auto_generated_builds(self.domain, app.id)
        self.assertEqual(len(get_build_ids(app.domain, app.id)), 2)

        # Build #3, manually generated
        app.save()
        build3 = app.make_build()
        build3.save()

        # Release the auto-generated build and prune again, should still delete nothing
        build2.is_released = True
        build2.save()
        prune_auto_generated_builds(self.domain, app.id)
        self.assertEqual(len(get_build_ids(app.domain, app.id)), 3)

        # Un-release the auto-generated build and prune again, which should delete it
        build2.is_released = False
        build2.save()
        prune_auto_generated_builds(self.domain, app.id)
        build_ids = get_build_ids(app.domain, app.id)
        self.assertEqual(len(build_ids), 2)
        self.assertNotIn(build2.id, build_ids)

    def test_dependencies_feature_removed(self):
        factory = AppFactory(build_version='2.40.0')
        m0, f0 = factory.new_basic_module('register', 'case')
        f0.source = get_simple_form(xmlns=f0.unique_id)
        factory.app.profile = {'features': {'dependencies': ['coffee']}}
        factory.app.save()
        self.addCleanup(factory.app.delete)
        build1 = factory.app.make_build()
        build1.save()

        factory.app.profile = {'features': {'dependencies': []}}
        factory.app.save()

        with patch("corehq.apps.app_manager.tasks.metrics_counter") as metric_counter_mock:
            make_app_build(factory.app, "comment", user_id="user_id")
            metric_counter_mock.assert_called_with('commcare.app_build.dependencies_removed')

    def test_dependencies_feature_metrics_not_triggerd(self):
        factory = AppFactory(build_version='2.40.0')
        m0, f0 = factory.new_basic_module('register', 'case')
        f0.source = get_simple_form(xmlns=f0.unique_id)
        factory.app.profile = {'features': {'dependencies': []}}
        factory.app.save()
        self.addCleanup(factory.app.delete)
        build1 = factory.app.make_build()
        build1.save()

        factory.app.save()

        with patch("corehq.apps.app_manager.tasks.metrics_counter") as metric_counter_mock:
            make_app_build(factory.app, "comment", user_id="user_id")
            metric_counter_mock.assert_not_called()
