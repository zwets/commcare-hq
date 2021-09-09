from django.http.response import Http404, HttpResponse
from django.test import SimpleTestCase, override_settings
from unittest.mock import Mock, patch

from django.test.client import RequestFactory

from .. import views
from ..views import (
    EnableMobilePrivilegesView,
    TwoFactorProfileView,
    TwoFactorSetupView,
    TwoFactorPhoneSetupView,
)

from two_factor.views import ProfileView, SetupView, PhoneSetupView


class EnableMobilePrivilegesViewTests(SimpleTestCase):

    def test_qr_code(self):
        """
        Check that the qr code in the context is a string, as opposed to a byte object
        """
        view = EnableMobilePrivilegesView()
        view.get_context_data = Mock(return_value={})
        view.render_to_response = lambda x: x
        mock_request = Mock()
        mock_request.user.username = "test"

        with patch('corehq.apps.settings.views.sign', lambda x: b'foo'):
            context = view.get(mock_request)

        self.assertTrue(isinstance(context['qrcode_64'], str))


@override_settings(ALLOW_PHONE_AS_DEFAULT_TWO_FACTOR_DEVICE=True)
class TwoFactorProfileView_Context_Tests(SimpleTestCase):
    @override_settings(ALLOW_PHONE_AS_DEFAULT_TWO_FACTOR_DEVICE=False)
    def test_phone_methods_do_not_display_when_settings_are_disabled(self):
        user = self._create_user(two_factor_enabled=True, belongs_to_messaging_domain=True)
        view = self._create_view_for_user(user)
        context = view.get_context_data()
        self.assertFalse(context.get('allow_phone'))

    def test_phone_methods_display_when_user_belongs_to_messaging_domain(self):
        user = self._create_user(two_factor_enabled=True, belongs_to_messaging_domain=True)
        view = self._create_view_for_user(user)
        context = view.get_context_data()
        self.assertTrue(context.get('allow_phone'))

    def test_phone_methods_do_not_display_when_user_does_not_belong_to_messaging_domain(self):
        user = self._create_user(two_factor_enabled=True, belongs_to_messaging_domain=False)
        view = self._create_view_for_user(user)
        context = view.get_context_data()
        self.assertFalse(context.get('allow_phone'))

    def test_phone_methods_display_when_user_has_previous_backup_phones(self):
        user = self._create_user(
            two_factor_enabled=True,
            belongs_to_messaging_domain=False,
            has_backup_phones=True)
        view = self._create_view_for_user(user)
        context = view.get_context_data()
        self.assertTrue(context.get('allow_phone'))

    def setUp(self):
        self.factory = RequestFactory()
        self.two_factor_enabled = False
        self.backup_phones = []
        mock_2fa_context_patcher = patch.object(ProfileView, 'get_context_data')
        mock_2fa_context = mock_2fa_context_patcher.start()
        mock_2fa_context.side_effect = lambda: ({
            'default_device': self.two_factor_enabled,
            'backup_phones': self.backup_phones
        })

        self.addCleanup(mock_2fa_context_patcher.stop)

    def _create_user(self, two_factor_enabled=True, belongs_to_messaging_domain=True, has_backup_phones=False):
        user = Mock(is_authenticated=True, is_active=True)
        user.belongs_to_messaging_domain.return_value = belongs_to_messaging_domain
        self.two_factor_enabled = two_factor_enabled
        if has_backup_phones:
            self.backup_phones = ['phone1', 'phone2']
        return user

    def _create_view_for_user(self, user):
        request = self.factory.get('/some_url')
        request.user = request.couch_user = user
        view = TwoFactorProfileView()
        view.setup(request)
        return view


@override_settings(ALLOW_PHONE_AS_DEFAULT_TWO_FACTOR_DEVICE=True)
class TwoFactorSetupView_FormKwargs_Tests(SimpleTestCase):
    @override_settings(ALLOW_PHONE_AS_DEFAULT_TWO_FACTOR_DEVICE=False)
    def test_phone_methods_are_prohibited_when_settings_are_disabled(self):
        user = self._create_user(belongs_to_messaging_domain=True)
        view = self._create_view_for_user(user)
        self.assertFalse(view.get_form_kwargs(step='method').get('allow_phone'))

    def test_phone_methods_are_allowed_when_user_belongs_to_messaging_domain(self):
        user = self._create_user(belongs_to_messaging_domain=True)
        view = self._create_view_for_user(user)
        self.assertTrue(view.get_form_kwargs(step='method').get('allow_phone'))

    def test_phone_methods_are_prohibited_when_user_does_not_belongs_to_messaging_domain(self):
        user = self._create_user(belongs_to_messaging_domain=False)
        view = self._create_view_for_user(user)
        self.assertFalse(view.get_form_kwargs(step='method').get('allow_phone'))

    def setUp(self):
        self.factory = RequestFactory()
        mock_2fa_form_kwargs_patcher = patch.object(SetupView, 'get_form_kwargs', return_value={})
        mock_2fa_form_kwargs_patcher.start()

        self.addCleanup(mock_2fa_form_kwargs_patcher.stop)

    def _create_user(self, belongs_to_messaging_domain=True):
        user = Mock(is_authenticated=True, is_active=True)
        user.belongs_to_messaging_domain.return_value = belongs_to_messaging_domain
        return user

    def _create_view_for_user(self, user):
        request = self.factory.post('/some_url')
        request.user = request.couch_user = user
        view = TwoFactorSetupView()
        view.setup(request)

        return view


@override_settings(ALLOW_PHONE_AS_DEFAULT_TWO_FACTOR_DEVICE=True)
class TwoFactorPhoneSetupViewTests(SimpleTestCase):
    @override_settings(ALLOW_PHONE_AS_DEFAULT_TWO_FACTOR_DEVICE=False)
    def test_when_settings_are_disabled_view_returns_404(self):
        user = self._create_user(belongs_to_messaging_domain=True)
        with self.assertRaises(Http404):
            self._call_view(user)

    def test_when_user_belongs_to_messaging_domain_returns_200(self):
        user = self._create_user(belongs_to_messaging_domain=True)
        response = self._call_view(user)
        self.assertEqual(response.status_code, 200)

    def test_when_user_does_not_belong_to_messaging_domain_returns_404(self):
        user = self._create_user(belongs_to_messaging_domain=False)
        with self.assertRaises(Http404):
            self._call_view(user)

    def test_when_user_has_grandfathered_phones_returns_200(self):
        # Even if domain access has been shut off, we still want to show the user his phones
        user = self._create_user(belongs_to_messaging_domain=False, has_backup_phones=True)
        response = self._call_view(user)

        self.assertEqual(response.status_code, 200)

    def setUp(self):
        self.factory = RequestFactory()
        mock_parent_dispatch = patch.object(PhoneSetupView, 'dispatch', return_value=HttpResponse(status=200))
        mock_parent_dispatch.start()

        self.addCleanup(mock_parent_dispatch.stop)

    def _create_user(self, belongs_to_messaging_domain=True, has_backup_phones=False):
        user = Mock(is_authenticated=True, is_active=True)
        user.belongs_to_messaging_domain.return_value = belongs_to_messaging_domain

        if has_backup_phones:
            # NOTE: This is not intended to be used multiple times in the same test
            backup_phone_patcher = patch.object(views, 'backup_phones',
                return_value=['phone1', 'phone2'])  # Only matters that it isn't empty
            backup_phone_patcher.start()
            self.addCleanup(backup_phone_patcher.stop)
        return user

    def _call_view(self, user):
        request = self.factory.post('/some_url')
        request.user = request.couch_user = user
        view = TwoFactorPhoneSetupView.as_view()
        return view(request)
