from django.test import TestCase

from casexml.apps.case.mock import CaseFactory
from corehq.apps.data_cleaning.models import (
    BulkEditChange,
    EditActionType,
)
from corehq.form_processor.tests.utils import FormProcessorTestUtils


class BulkEditChangeTest(TestCase):
    domain = 'planet'
    case_type = 'island'

    def setUp(self):
        factory = CaseFactory(domain=self.domain)
        self.case = factory.create_case(
            case_type=self.case_type,
            owner_id='q123',
            case_name='Vieques',
            update={
                'nearest_ocean': 'atlantic',
                'town': 'Isabel Segunda',
                'favorite_beach': 'Playa Bastimento',
                'art': '\n  :)   \n  \t',
                'second_favorite_beach': 'no idea',
                'friend': 'Brittney \t\nClaasen',
            },
        )

        super().setUp()

    def tearDown(self):
        FormProcessorTestUtils.delete_all_cases()
        super().tearDown()

    def test_replace(self):
        change = BulkEditChange(
            prop_id='town',
            action_type=EditActionType.REPLACE,
            replace_string='Esperanza',
        )
        self.assertEqual(change.edited_value(self.case), 'Esperanza')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'town': 'Segunda',
            }), 'Esperanza'
        )

    def test_replace_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.REPLACE,
            replace_string='Esperanza',
        )
        self.assertEqual(change.edited_value(self.case), 'Esperanza')

    def test_find_replace(self):
        change = BulkEditChange(
            prop_id='favorite_beach',
            action_type=EditActionType.FIND_REPLACE,
            find_string='Playa',
            replace_string='Punta',
        )
        self.assertEqual(change.edited_value(self.case), 'Punta Bastimento')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'favorite_beach': 'Bastimento Playa',
            }), 'Bastimento Punta'
        )

    def test_find_replace_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.FIND_REPLACE,
            find_string='Playa',
            replace_string='Punta',
        )
        self.assertEqual(change.edited_value(self.case), None)

    def test_find_replace_regex(self):
        change = BulkEditChange(
            prop_id='friend',
            action_type=EditActionType.FIND_REPLACE,
            use_regex=True,
            find_string='(\\s)+',
            replace_string=' ',
        )
        self.assertEqual(change.edited_value(self.case), 'Brittney Claasen')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'friend': 'brittney \t\nclaasen',
            }), 'brittney claasen'
        )

    def test_find_replace_regex_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.FIND_REPLACE,
            use_regex=True,
            find_string='(\\s)+',
            replace_string=' ',
        )
        self.assertEqual(change.edited_value(self.case), None)

    def test_strip(self):
        change = BulkEditChange(
            prop_id='art',
            action_type=EditActionType.STRIP,
        )
        self.assertEqual(change.edited_value(self.case), ':)')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'art': '    :-)\t\n  ',
            }), ':-)'
        )

    def test_strip_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.STRIP,
        )
        self.assertEqual(change.edited_value(self.case), None)

    def test_copy_replace(self):
        change = BulkEditChange(
            prop_id='nearest_ocean',
            action_type=EditActionType.COPY_REPLACE,
            copy_from_prop_id='favorite_beach',
        )
        self.assertEqual(change.edited_value(self.case), 'Playa Bastimento')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'favorite_beach': 'playa bastimento',
                'nearest_ocean': 'Atlantic',
            }), 'playa bastimento'
        )

    def test_copy_replace_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.COPY_REPLACE,
            copy_from_prop_id='favorite_beach',
        )
        self.assertEqual(change.edited_value(self.case), 'Playa Bastimento')

    def test_title_case(self):
        change = BulkEditChange(
            prop_id='nearest_ocean',
            action_type=EditActionType.TITLE_CASE,
        )
        self.assertEqual(change.edited_value(self.case), 'Atlantic')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'nearest_ocean': 'atlantic  ',
            }), 'Atlantic  '
        )

    def test_title_case_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.TITLE_CASE,
        )
        self.assertEqual(change.edited_value(self.case), None)

    def test_upper_case(self):
        change = BulkEditChange(
            prop_id='town',
            action_type=EditActionType.UPPER_CASE,
        )
        self.assertEqual(change.edited_value(self.case), 'ISABEL SEGUNDA')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'town': 'isbel',
            }), 'ISBEL'
        )

    def test_upper_case_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.UPPER_CASE,
        )
        self.assertEqual(change.edited_value(self.case), None)

    def test_lower_case(self):
        change = BulkEditChange(
            prop_id='town',
            action_type=EditActionType.LOWER_CASE,
        )
        self.assertEqual(change.edited_value(self.case), 'isabel segunda')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'town': 'SEGUNDA',
            }), 'segunda'
        )

    def test_lower_case_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.LOWER_CASE,
        )
        self.assertEqual(change.edited_value(self.case), None)

    def test_make_empty(self):
        change = BulkEditChange(
            prop_id='nearest_ocean',
            action_type=EditActionType.MAKE_EMPTY,
        )
        self.assertEqual(change.edited_value(self.case), '')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'nearest_ocean': 'pacific',
            }), ''
        )

    def test_empty_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.MAKE_EMPTY,
        )
        self.assertEqual(change.edited_value(self.case), '')

    def test_make_null(self):
        change = BulkEditChange(
            prop_id='nearest_ocean',
            action_type=EditActionType.MAKE_NULL,
        )
        self.assertEqual(change.edited_value(self.case), None)
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'nearest_ocean': 'pacific',
            }), None
        )

    def test_make_null_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.MAKE_NULL,
        )
        self.assertEqual(change.edited_value(self.case), None)

    def test_reset(self):
        change = BulkEditChange(
            prop_id='nearest_ocean',
            action_type=EditActionType.RESET,
        )
        self.assertEqual(change.edited_value(self.case), 'atlantic')
        self.assertEqual(change.edited_value(
            self.case, edited_properties={
                'nearest_ocean': 'pacific',
            }), 'atlantic'
        )

    def test_reset_none(self):
        change = BulkEditChange(
            prop_id='unset',
            action_type=EditActionType.RESET,
        )
        self.assertIsNone(change.edited_value(self.case))
