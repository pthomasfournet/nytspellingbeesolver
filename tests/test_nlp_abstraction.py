"""
Tests for NLP Abstraction Layer - Dependency Inversion Principle

This test suite verifies that the NLP provider abstraction:
1. Decouples from spaCy (can use different backends)
2. Supports mock providers for testing
3. Maintains backward compatibility
4. Allows backend swapping without code changes
"""

import pytest

from src.spelling_bee_solver.intelligent_word_filter import (
    IntelligentWordFilter,
    create_word_filter,
)
from src.spelling_bee_solver.nlp import (
    MockNLPProvider,
    SpacyNLPProvider,
    create_mock_provider,
    create_spacy_provider,
)


def test_mock_provider_basic():
    """Test that MockNLPProvider works correctly"""
    provider = MockNLPProvider()
    provider.add_proper_noun("NASA")
    provider.add_entity("Apple Inc.", "ORG")

    # Process text
    doc = provider.process_text("NASA and Apple Inc. are here")

    # Check tokens
    tokens = doc.get_tokens()
    assert len(tokens) > 0
    assert any(t.text == "NASA" and t.is_proper_noun for t in tokens)

    # Check entities
    entities = doc.get_entities()
    assert any(e.text == "Apple Inc." and e.label == "ORG" for e in entities)

    # Check proper noun detection
    assert doc.has_proper_noun("NASA")
    assert not doc.has_proper_noun("and")

    # Check entity type detection
    assert doc.has_entity_type("Apple", ["ORG"])
    assert not doc.has_entity_type("NASA", ["ORG"])  # NASA is not configured as ORG


def test_mock_provider_tracking():
    """Test that MockNLPProvider tracks processed texts"""
    provider = MockNLPProvider()

    assert len(provider.processed_texts) == 0

    provider.process_text("First text")
    provider.process_text("Second text")

    assert len(provider.processed_texts) == 2
    assert "First text" in provider.processed_texts
    assert "Second text" in provider.processed_texts


def test_mock_provider_reset():
    """Test that MockNLPProvider can be reset"""
    provider = MockNLPProvider()
    provider.add_proper_noun("NASA")
    provider.process_text("test")

    assert len(provider.proper_nouns) > 0
    assert len(provider.processed_texts) > 0

    provider.reset()

    assert len(provider.proper_nouns) == 0
    assert len(provider.processed_texts) == 0
    assert provider.is_available()


def test_spacy_provider_basic():
    """Test that SpacyNLPProvider works correctly"""
    provider = SpacyNLPProvider(use_gpu=False)

    # Check availability
    assert provider.is_available()
    assert "spaCy" in provider.get_name()

    # Process text
    doc = provider.process_text("Apple Inc. is in California.")

    # Check tokens
    tokens = doc.get_tokens()
    assert len(tokens) > 0
    assert all(hasattr(t, 'text') and hasattr(t, 'pos') for t in tokens)

    # Check entities (spaCy should detect these)
    entities = doc.get_entities()
    assert len(entities) > 0
    # Apple Inc. should be ORG, California should be GPE
    assert any(e.label in ["ORG", "GPE"] for e in entities)


def test_spacy_provider_proper_noun_detection():
    """Test spaCy proper noun detection"""
    provider = SpacyNLPProvider(use_gpu=False)
    doc = provider.process_text("The NASA is here.")

    # NASA should be detected as proper noun
    token = doc.find_token("NASA")
    assert token is not None
    assert token.is_proper_noun or doc.has_entity_type("NASA", ["ORG"])


def test_word_filter_with_mock_provider():
    """Test IntelligentWordFilter with MockNLPProvider"""
    # Create mock provider with custom proper nouns
    mock = MockNLPProvider()
    mock.add_proper_noun("NASA")
    mock.add_proper_noun("London")
    mock.add_entity("Microsoft", "ORG")

    # Create filter with mock provider
    filter_instance = create_word_filter(nlp_provider=mock, use_gpu=False)

    # Test proper noun detection
    assert filter_instance.is_proper_noun_intelligent("NASA")
    assert filter_instance.is_proper_noun_intelligent("London")
    assert not filter_instance.is_proper_noun_intelligent("hello")

    # Verify mock was actually used
    assert len(mock.processed_texts) > 0


def test_word_filter_with_spacy_provider():
    """Test IntelligentWordFilter with SpacyNLPProvider"""
    # Create explicit spaCy provider
    spacy_provider = create_spacy_provider(use_gpu=False)

    # Create filter with spaCy provider
    filter_instance = create_word_filter(nlp_provider=spacy_provider, use_gpu=False)

    # Test proper noun detection (spaCy should recognize these)
    assert filter_instance.is_proper_noun_intelligent("NASA")
    assert filter_instance.is_proper_noun_intelligent("Microsoft")
    assert not filter_instance.is_proper_noun_intelligent("hello")


def test_word_filter_default_provider():
    """Test that IntelligentWordFilter uses spaCy by default"""
    filter_instance = create_word_filter(use_gpu=False)

    # Should use spaCy by default
    assert filter_instance.nlp_provider is not None
    assert filter_instance.spacy_available

    # Should still work for proper noun detection
    assert filter_instance.is_proper_noun_intelligent("NASA")


def test_provider_swapping():
    """Test that we can easily swap providers"""
    # Create two filters with different providers
    mock = MockNLPProvider()
    mock.add_proper_noun("TestWord")

    filter_mock = create_word_filter(nlp_provider=mock, use_gpu=False)
    filter_spacy = create_word_filter(use_gpu=False)  # Default spaCy

    # Both should be valid but independent
    assert filter_mock.nlp_provider is mock
    assert filter_spacy.nlp_provider is not mock
    assert isinstance(filter_spacy.nlp_provider, SpacyNLPProvider)


def test_mock_provider_word_filtering():
    """Test full word filtering pipeline with mock provider"""
    # Create mock with specific proper nouns
    mock = MockNLPProvider()
    mock.add_proper_noun("NASA")
    mock.add_proper_noun("FBI")

    # Create filter
    filter_instance = create_word_filter(nlp_provider=mock, use_gpu=False)

    # Filter words
    test_words = ["hello", "world", "NASA", "test", "FBI", "apple"]
    filtered = filter_instance.filter_words_intelligent(test_words)

    # NASA and FBI should be filtered out (proper nouns)
    assert "NASA" not in filtered
    assert "FBI" not in filtered

    # Regular words should pass
    assert "hello" in filtered or "world" in filtered or "test" in filtered or "apple" in filtered


def test_backward_compatibility_no_provider():
    """Test that code without explicit provider still works"""
    # Old way (no provider argument)
    filter_instance = IntelligentWordFilter(use_gpu=False)

    # Should still work with default spaCy provider
    assert filter_instance.spacy_available
    result = filter_instance.is_proper_noun_intelligent("NASA")
    assert isinstance(result, bool)


def test_factory_functions():
    """Test the factory functions"""
    spacy_prov = create_spacy_provider(use_gpu=False)
    mock_prov = create_mock_provider()

    assert isinstance(spacy_prov, SpacyNLPProvider)
    assert isinstance(mock_prov, MockNLPProvider)

    assert spacy_prov.is_available()
    assert mock_prov.is_available()


def test_provider_abstraction_benefits():
    """
    Test that demonstrates the benefits of provider abstraction:
    1. Easy to test with mock
    2. Can swap backends
    3. No coupling to spaCy
    """
    # Benefit 1: Easy testing with mock (no spaCy model loading)
    mock = MockNLPProvider()
    mock.add_proper_noun("TestWord")
    filter_fast = create_word_filter(nlp_provider=mock, use_gpu=False)
    assert filter_fast.is_proper_noun_intelligent("TestWord")

    # Benefit 2: Can swap backends easily
    spacy = SpacyNLPProvider(use_gpu=False)
    filter_accurate = create_word_filter(nlp_provider=spacy, use_gpu=False)
    assert filter_accurate.nlp_provider is spacy

    # Benefit 3: No direct spaCy coupling in filter class
    # The filter doesn't know or care about spaCy specifics
    assert hasattr(filter_fast.nlp_provider, 'process_text')
    assert hasattr(filter_accurate.nlp_provider, 'process_text')


if __name__ == "__main__":
    print("Running NLP abstraction tests...")
    pytest.main([__file__, "-v"])
