from llm_defender.core.validators.penalty.similarity import _check_response_history, check_penalty 
import unittest
import pytest 

class TestPenaltyCheckFunctions(unittest.TestCase):

    def test_check_response_history(self):
        # Test cases for _check_response_history
        miner_responses = [{
            'engine_data': [{'name': 'engine:text_classification', 'data': 'test data'}] * 5 +
                           [{'name': 'engine:text_classification', 'data': 'different data'}] * 5
        }]
        self.assertGreater(_check_response_history('uid1', miner_responses, 'engine:text_classification'), 0.0)
        # Add more test cases with different 'miner_responses' and 'engine' values

    def test_check_penalty(self):
        # Test cases for check_penalty
        miner_responses_valid = [{
            'engine_data': [{'name': 'engine:text_classification', 'data': 'test data'}] * 5 +
                           [{'name': 'engine:text_classification', 'data': 'different data'}] * 5
        }]
        miner_responses_invalid = []
        self.assertGreater(check_penalty('valid_uid', miner_responses_valid), 0.0)
        self.assertEqual(check_penalty('invalid_uid', miner_responses_invalid), 20.0)
        # Add more test cases with different 'uid' and 'miner_responses' values

if __name__ == '__main__':
    unittest.main()