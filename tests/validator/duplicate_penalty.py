from llm_defender.core.validators.penalty.duplicate import _calculate_duplicate_percentage, _find_identical_reply, check_penalty
import unittest
import pytest

class TestPenaltyCheckFunctions(unittest.TestCase):

    def test_calculate_duplicate_percentage(self):
        # Test cases for _calculate_duplicate_percentage
        miner_responses = [{'engine_data': [{'name': 'engine:text_classification'}] * 10}]
        self.assertAlmostEqual(_calculate_duplicate_percentage('uid1', 
                                                               miner_responses, 'engine:text_classification'), 
                               0.15, 
                               places=2)
        # Add more test cases with different 'miner_responses' and 'engine' values

    def test_find_identical_reply(self):
        # Test cases for _find_identical_reply
        miner_responses = [{'engine_data': [{'name': 'engine:text_classification', 
        'reply': 'test'}]}]
        response = {'engines': [{'name': 'engine:text_classification', 'reply': 'test'}]}
        self.assertEqual(_find_identical_reply('uid1', miner_responses, response, 'engine:text_classification'), 0.25)
        # Add more test cases with different 'miner_responses', 'response', and 'engine' values

    def test_check_penalty(self):
        # Test cases for check_penalty
        miner_responses = [{'engine_data': [{'name': 'engine:text_classification', 'reply': 'test'}]}]
        response = {'engines': [{'name': 'engine:text_classification', 'reply': 'test'}]}
        self.assertEqual(check_penalty('invalid_uid', miner_responses, response), 20.0)
        self.assertGreaterEqual(check_penalty('valid_uid', miner_responses, response), 0.0)
        # Add more test cases with different 'uid', 'miner_responses', and 'response' values

if __name__ == '__main__':
    unittest.main()