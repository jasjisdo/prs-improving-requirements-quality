import os
import sys
import unittest
import warnings
import json
import random

from starter import amb_api
import tests.lib as lib

class TestCheckNominalizations(unittest.TestCase):

    def setUp(self):
        # Ignore third-party warnings from setup phase..
        warnings.simplefilter('ignore')
        # Initialize Flask server hosting api
        self.amb_api = amb_api.test_client()

    # Routes to the APIs that are being tested

    def _call_check_quality(self, req):
        # Load the JSON payload from the config file
        json_payload = json.loads(lib.API_INPUT_FORMAT)
        # Add the configuration to only run the algorithm we want to check in this test file
        json_payload['config'] = { 'algorithms': ['Nominalization'] }
        return self.amb_api.post(
            '/check-quality',
            data=json.dumps(json_payload).replace('{{requirement}}', req),
            follow_redirects=True)

    def _get_single_item_from_response(self, response, title):
        # Get JSON from response
        resp_json = json.loads(response.get_data())['1']
        item_l = [item for item in resp_json if item['title'] == title]
        if item_l:
            return random.choice(item_l)
        else:
            return None

    # Unit Tests

    def test_algorithm_reached_and_found(self):
        response = self._call_check_quality('The system will begin the activation process.')
        item = self._get_single_item_from_response(response, 'Ambiguous Nominalization')
        self.assertEqual(item['title'], 'Ambiguous Nominalization')


if __name__ == '__main__':
    unittest.main(verbosity=2)
