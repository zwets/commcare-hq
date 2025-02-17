import doctest

from django.test import TestCase

import jsonschema
import pytest

from corehq.apps.app_manager.const import USERCASE_TYPE
from corehq.apps.domain.shortcuts import create_domain
from corehq.apps.integration.kyc.models import KycConfig, UserDataStore
from corehq.apps.integration.kyc.services import (
    UserCaseNotFound,
    _get_source_data,
    _validate_schema,
    get_user_data_for_api,
)
from corehq.apps.users.models import CommCareUser
from corehq.form_processor.tests.utils import create_case
from corehq.motech.models import ConnectionSettings

DOMAIN = 'test-domain'


def test_doctests():
    import corehq.apps.integration.kyc.services as module
    results = doctest.testmod(module)
    assert results.failed == 0


class TestSaveResult(TestCase):
    # TODO: ...
    pass


class TestGetSourceData(TestCase):

    def setUp(self):
        self.commcare_user = CommCareUser.create(
            DOMAIN, f'test.user@{DOMAIN}.commcarehq.org', 'Passw0rd!',
            None, None,
            user_data={'custom_field': 'custom_value'},
        )
        self.addCleanup(self.commcare_user.delete, DOMAIN, deleted_by=None)
        self.user_case = create_case(
            DOMAIN,
            case_type=USERCASE_TYPE,
            user_id=self.commcare_user._id,
            name='test.user',
            external_id=self.commcare_user._id,
            save=True,
            case_json={'user_case_property': 'user_case_value'},
        )
        self.other_case = create_case(
            DOMAIN,
            case_type='other_case_type',
            save=True,
            case_json={'other_case_property': 'other_case_value'},
        )

    def test_custom_user_data(self):
        config = KycConfig(
            domain=DOMAIN,
            user_data_store=UserDataStore.CUSTOM_USER_DATA,
        )
        source_data = _get_source_data(self.commcare_user, config)
        assert source_data == {
            'custom_field': 'custom_value',
            'commcare_profile': '',
        }

    def test_user_case(self):
        config = KycConfig(
            domain=DOMAIN,
            user_data_store=UserDataStore.USER_CASE,
        )
        source_data = _get_source_data(self.commcare_user, config)
        assert source_data == {'user_case_property': 'user_case_value'}

    def test_other_case_type(self):
        config = KycConfig(
            domain=DOMAIN,
            user_data_store=UserDataStore.OTHER_CASE_TYPE,
            other_case_type='other_case_type',
        )
        source_data = _get_source_data(self.other_case, config)
        assert source_data == {'other_case_property': 'other_case_value'}


class TestValidateSchema(TestCase):

    def test_valid_schema(self):
        endpoint = 'kycVerify/v1'
        data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'phoneNumber': '27650600900',
            'emailAddress': 'john.doe@email.com',
            'nationalIdNumber': '123456789',
            'streetAddress': '1st Park Avenue, Mzansi, Johannesburg',
            'city': 'Johannesburg',
            'postCode': '20200',
            'country': 'South Africa',
        }
        _validate_schema(endpoint, data)  # Should not raise an exception

    def test_invalid_schema(self):
        endpoint = 'kycVerify/v1'
        data = {
            'firstName': 'John',
            'lastName': 'Doe',
            # Missing required fields
        }
        with pytest.raises(jsonschema.ValidationError):
            _validate_schema(endpoint, data)


class TestGetUserDataForAPI(TestCase):
    domain = 'test-kyc-integration'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.domain_obj = create_domain(cls.domain)
        cls.connection_settings = ConnectionSettings.objects.create(
            domain=cls.domain,
            name='test',
            url='https://example.com'
        )

    @classmethod
    def tearDownClass(cls):
        cls.connection_settings.delete()
        cls.domain_obj.delete()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = CommCareUser.create(self.domain, 'test-kyc', '123', None, None, first_name='abc')
        self.config = KycConfig.objects.create(
            domain=self.domain,
            user_data_store=UserDataStore.CUSTOM_USER_DATA,
            api_field_to_user_data_map=self._sample_api_field_to_user_data_map(),
            connection_settings=self.connection_settings
        )

    def tearDown(self):
        self.user.delete(self.domain, None)
        self.config.delete()
        super().tearDown()

    def _sample_api_field_to_user_data_map(self):
        return [
            {
                "fieldName": "first_name",
                "mapsTo": "first_name",
                "source": "standard"
            },
            {
                "fieldName": "nationality",
                "mapsTo": "nationality",
                "source": "custom"
            }
        ]

    def test_custom_user_data_store(self):
        self.user.get_user_data(self.domain).update({'nationality': 'Indian'})
        result = get_user_data_for_api(self.user, self.config)
        self.assertEqual(result, {'first_name': 'abc', 'nationality': 'Indian'})

    def test_custom_user_data_store_with_no_data(self):
        result = get_user_data_for_api(self.user, self.config)
        self.assertEqual(result, {'first_name': 'abc'})

    def test_user_case_data_store(self):
        self.config.user_data_store = UserDataStore.USER_CASE
        self.config.save()
        case = create_case(
            self.domain,
            case_type=USERCASE_TYPE,
            external_id=self.user.user_id,
            save=True,
            case_json={'nationality': 'German'}
        )
        self.addCleanup(case.delete)

        result = get_user_data_for_api(self.user, self.config)
        self.assertEqual(result, {'first_name': 'abc', 'nationality': 'German'})

    def test_user_case_data_store_with_no_case(self):
        self.config.user_data_store = UserDataStore.USER_CASE
        self.config.save()

        with self.assertRaises(UserCaseNotFound):
            get_user_data_for_api(self.user, self.config)

    def test_custom_case_data_store(self):
        self.config.user_data_store = UserDataStore.OTHER_CASE_TYPE
        self.config.other_case_type = 'other-case'
        self.config.api_field_to_user_data_map[0]['source'] = 'custom'
        self.config.save()
        case = create_case(
            self.domain,
            case_type='other-case',
            save=True,
            case_json={'first_name': 'abc', 'nationality': 'Dutch'}
        )
        self.addCleanup(case.delete)

        result = get_user_data_for_api(case, self.config)
        self.assertEqual(result, {'first_name': 'abc', 'nationality': 'Dutch'})

    def test_custom_case_data_store_with_no_data(self):
        self.config.user_data_store = UserDataStore.OTHER_CASE_TYPE
        self.config.other_case_type = 'other-case'
        self.config.save()
        case = create_case(self.domain, case_type='other-case', save=True)
        self.addCleanup(case.delete)

        result = get_user_data_for_api(case, self.config)
        self.assertEqual(result, {})

    def test_incorrect_mapping_standard_field(self):
        api_field_to_user_data_map = self._sample_api_field_to_user_data_map()
        api_field_to_user_data_map[0]['mapsTo'] = 'wrong-standard_field'
        self.config.api_field_to_user_data_map = api_field_to_user_data_map
        self.config.save()

        result = get_user_data_for_api(self.user, self.config)

        self.assertEqual(result, {})
