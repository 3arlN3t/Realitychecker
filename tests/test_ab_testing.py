
import pytest
from app.utils.ab_testing import ABTesting

@pytest.fixture
def experiments():
    return {
        'test_experiment': {
            'variants': {
                'A': 1,
                'B': 1
            }
        }
    }

def test_get_variant(experiments):
    ab_testing = ABTesting(experiments)
    user_id = 'test_user'
    variant = ab_testing.get_variant(user_id, 'test_experiment')
    assert variant in ['A', 'B']

def test_get_variant_not_in_experiment(experiments):
    ab_testing = ABTesting(experiments)
    user_id = 'test_user'
    variant = ab_testing.get_variant(user_id, 'not_an_experiment')
    assert variant is None
