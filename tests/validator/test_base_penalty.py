from llm_defender.core.validators.penalty.base import _check_prompt_response_mismatch, _check_confidence_validity,_check_response_history, check_penalty
import unittest
import pytest
import bittensor as bt


class TestBasePenaltyFunctions():

    def test_check_prompt_response_mismatch(self):
        print("\nNOW TESTING: _check_prompt_response_mismatch()\n")
        print("Testing that prompt and response match.")
        assert _check_prompt_response_mismatch(1,{'prompt': 'test'},'test') == 0.0
        print("Test successful.")

        print("Testing that prompt and response do not match.")
        assert 20.0 == _check_prompt_response_mismatch(2,{'prompt': 'test'},'different')
        print("Test successful.")

    def test_check_confidence_validity(self):
        print("\nNOW TESTING: _check_confidence_validity()\n")
        print("Testing for valid confidence score.")
        assert _check_confidence_validity(0,{'confidence': 0.5}) ==  0.0
        print("Test successful.")

        print("Testing for invalid confidence score of 1.1 raising 20.0 penalty.")
        assert _check_confidence_validity(3,{'confidence': 1.1}) == 20.0
        print("Test successful.")

        print("Testing for invalid confidence score of -0.1 raising 20.0 penalty.")
        assert _check_confidence_validity(255,{'confidence': -0.1}) == 20.0
        print("Test successful.")

    def test_check_response_history(self):
        print("\nNOW TESTING: _check_response_history()\n")
        print("Testing that 10.0 penalty outputted for avg distance between 0.0 and 0.05.")
        miner_responses = [
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.04}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.03}}}
            ] * 50
        assert _check_response_history(100, miner_responses) == 10.0
        print("Test successful.")

        print("Testing that 0.0 penalty outputted for avg distance between 0.05 and 0.35.")
        miner_responses = [
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.06}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.34}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.16}}}
            ] * 50
        assert _check_response_history(101,miner_responses) == 0.0
        print("Test successful.")

        print("Testing that 2.0 penalty outputted for avg distance between 0.35 and 0.45.")
        miner_responses = [
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.36}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.37}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.43}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.44}}}
            ] * 50
        assert _check_response_history(101, miner_responses) == 2.0
        print("Test successful.")

        print("Testing that 5.0 penalty outputted for avg distance between 0.45 and 0.55.")
        miner_responses = [
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.46}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.47}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.53}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.54}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.50}}}
            ] * 50
        assert _check_response_history(121, miner_responses) == 5.0
        print("Test successful.")

        print("Testing that 10.0 penalty outputted for avg distance between 0.55 and 1.0.")
        miner_responses = [
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.56}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.57}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.98}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.99}}}, 
            {'response':{},'scored_response': {'raw_scores': {'distance': 0.85}}}
            ] * 50
        assert _check_response_history(111, miner_responses) == 10.0
        print("Test successful.")

    def test_check_penalty(self):
        print("\nNOW TESTING: check_penalty()\n")
        faulty_uids = [
            None, 
            -1,
            256,
            0.0,
            100.0,
            'foo',
            True,
            False,
            [],
            {}
        ]
        for fuid in faulty_uids:
            print(f"Testing that 10.0 penalty outputted for invalid uid: {fuid}")
            assert check_penalty(fuid,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.56}}}] * 50,{'prompt': 'test'},'test') == 10.0
            print("Test successful.")

        print("Testing that 10.0 penalty is applied for faulty miner_responses.")
        assert check_penalty(7,None,{'prompt':'test'},'test') == 10.0 
        print("Test successful.")

        print("Testing that 10.0 penalty is applied for response not existing")
        assert check_penalty(17,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.56}}}] * 50,{},'test') == 10.0
        print("Test successful.")

        print("Testing that 5.0 penalty is applied for miner_responses not being long enough")
        assert check_penalty(10,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.04}}}] * 49,{'prompt': 'test', 'confidence': 0.5},'test') == 5.0
        print("Test successful.")

        print("Testing that no penalty applied for a perfect set of responses")
        assert check_penalty(10,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.15}}}] * 50,{'prompt': 'test', 'confidence': 0.5},'test') == 0.0
        print("Test successful.")

        print("Testing that penalty of 40.0 is applied for prompt-response mismatch and invalid confidence")
        assert check_penalty(10,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.15}}}] * 50,{'prompt': 'test', 'confidence': 1.5},'invalid prompt') == 40.0
        print("Test successful.")

        print("Testing that penalty of 50.0 is applied for prompt-response mismatch, invalid confidence and distance score avg of 0.01")
        assert check_penalty(10,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.01}}}] * 50,{'prompt': 'test', 'confidence': 1.5},'invalid prompt') == 50.0
        print("Test successful.")

        print("Testing that penalty of 50.0 is applied for prompt-response mismatch, invalid confidence and distance score avg of 0.90.")
        assert check_penalty(10,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.90}}}] * 50,{'prompt': 'test', 'confidence': 1.5},'invalid prompt') == 50.0
        print("Test successful.")

        print("Testing that penalty of 42.0 is applied for prompt-response mismatch, invalid confidence and distance score avg of 0.40")
        assert check_penalty(10,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.40}}}] * 50,{'prompt': 'test', 'confidence': 1.5},'invalid prompt') == 42.0
        print("Test successful.")

        print("Testing that penalty of 45.0 is applied for prompt-response mismatch, invalid confidence and distance score avg of 0.50.")
        assert check_penalty(10,[{'response':{},'scored_response': {'raw_scores': {'distance': 0.50}}}] * 50,{'prompt': 'test', 'confidence': 1.5},'invalid prompt') == 45.0
        print("Test successful.")


def main():
    test_base = TestBasePenaltyFunctions()
    test_base.test_check_prompt_response_mismatch()
    test_base.test_check_confidence_validity()
    test_base.test_check_response_history()
    test_base.test_check_penalty()

if __name__ == '__main__':
    main()