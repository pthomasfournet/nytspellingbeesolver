"""Tests for ResultFormatter component.

This test suite verifies the result formatting logic for Spelling Bee puzzles,
including:
- Factory function creation
- Console output formatting
- JSON output formatting
- Compact output formatting
- Statistics calculation
- Pangram highlighting
- Word grouping by length
- Input validation and error handling
"""

import pytest
import json
from spelling_bee_solver.core import (
    ResultFormatter, 
    create_result_formatter,
    OutputFormat
)


class TestResultFormatter:
    """Test suite for ResultFormatter class."""

    # ==================== Factory Function Tests ====================

    def test_create_result_formatter_default(self):
        """Test creating ResultFormatter with default configuration."""
        formatter = create_result_formatter()
        
        assert isinstance(formatter, ResultFormatter)
        assert formatter.output_format == OutputFormat.CONSOLE
        assert formatter.show_confidence is True
        assert formatter.group_by_length is True
        assert formatter.highlight_pangrams is True

    def test_create_result_formatter_json(self):
        """Test creating ResultFormatter with JSON format."""
        formatter = create_result_formatter(output_format=OutputFormat.JSON)
        
        assert formatter.output_format == OutputFormat.JSON

    def test_create_result_formatter_compact(self):
        """Test creating ResultFormatter with compact format."""
        formatter = create_result_formatter(output_format=OutputFormat.COMPACT)
        
        assert formatter.output_format == OutputFormat.COMPACT

    def test_create_result_formatter_custom_options(self):
        """Test creating ResultFormatter with custom options."""
        formatter = create_result_formatter(
            output_format=OutputFormat.JSON,
            show_confidence=False,
            group_by_length=False,
            highlight_pangrams=False
        )
        
        assert formatter.output_format == OutputFormat.JSON
        assert formatter.show_confidence is False
        assert formatter.group_by_length is False
        assert formatter.highlight_pangrams is False

    # ==================== Initialization Tests ====================

    def test_init_default(self):
        """Test ResultFormatter initialization with defaults."""
        formatter = ResultFormatter()
        
        assert formatter.output_format == OutputFormat.CONSOLE
        assert formatter.show_confidence is True
        assert formatter.group_by_length is True
        assert formatter.highlight_pangrams is True

    def test_init_custom(self):
        """Test ResultFormatter initialization with custom values."""
        formatter = ResultFormatter(
            output_format=OutputFormat.COMPACT,
            show_confidence=False,
            group_by_length=False,
            highlight_pangrams=False
        )
        
        assert formatter.output_format == OutputFormat.COMPACT
        assert formatter.show_confidence is False
        assert formatter.group_by_length is False
        assert formatter.highlight_pangrams is False

    def test_init_invalid_output_format_type(self):
        """Test ResultFormatter initialization with invalid output format type."""
        with pytest.raises(TypeError, match="output_format must be OutputFormat"):
            ResultFormatter(output_format="console")

    def test_init_invalid_show_confidence_type(self):
        """Test ResultFormatter initialization with invalid show_confidence type."""
        with pytest.raises(TypeError, match="show_confidence must be bool"):
            ResultFormatter(show_confidence="true")

    def test_init_invalid_group_by_length_type(self):
        """Test ResultFormatter initialization with invalid group_by_length type."""
        with pytest.raises(TypeError, match="group_by_length must be bool"):
            ResultFormatter(group_by_length=1)

    def test_init_invalid_highlight_pangrams_type(self):
        """Test ResultFormatter initialization with invalid highlight_pangrams type."""
        with pytest.raises(TypeError, match="highlight_pangrams must be bool"):
            ResultFormatter(highlight_pangrams="yes")

    # ==================== Console Formatting Tests ====================

    def test_format_console_basic(self):
        """Test basic console formatting."""
        formatter = ResultFormatter()
        results = [('count', 90.0), ('upon', 85.0)]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        
        assert 'SPELLING BEE SOLVER RESULTS' in output
        assert 'Letters: NACUOTP' in output
        assert 'Required: N' in output
        assert 'Total words found: 2' in output
        assert 'count' in output
        assert 'upon' in output

    def test_format_console_with_solve_time(self):
        """Test console formatting with solve time."""
        formatter = ResultFormatter()
        results = [('count', 90.0)]
        
        output = formatter.format_results(
            results, 'nacuotp', 'n', solve_time=2.5
        )
        
        assert 'Solve time: 2.500s' in output

    def test_format_console_with_mode(self):
        """Test console formatting with mode."""
        formatter = ResultFormatter()
        results = [('count', 90.0)]
        
        output = formatter.format_results(
            results, 'nacuotp', 'n', mode='production'
        )
        
        assert 'Mode: PRODUCTION' in output

    def test_format_console_empty_results(self):
        """Test console formatting with empty results."""
        formatter = ResultFormatter()
        
        output = formatter.format_results([], 'nacuotp', 'n')
        
        assert 'No words found' in output

    def test_format_console_with_pangram(self):
        """Test console formatting with pangram."""
        formatter = ResultFormatter()
        results = [('caption', 95.0), ('count', 90.0)]
        
        output = formatter.format_results(results, 'captoin', 'c')
        
        assert '🌟 PANGRAMS (1):' in output
        assert 'CAPTION' in output

    def test_format_console_without_confidence(self):
        """Test console formatting without confidence scores."""
        formatter = ResultFormatter(show_confidence=False)
        results = [('count', 90.0), ('upon', 85.0)]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        
        assert 'count' in output
        assert '90%' not in output

    def test_format_console_without_grouping(self):
        """Test console formatting without grouping by length."""
        formatter = ResultFormatter(group_by_length=False)
        results = [('count', 90.0), ('upon', 85.0), ('noun', 80.0)]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        
        assert 'Words:' in output
        assert '4-letter words' not in output

    def test_format_console_without_pangram_highlighting(self):
        """Test console formatting without pangram highlighting."""
        formatter = ResultFormatter(highlight_pangrams=False)
        results = [('caption', 95.0), ('count', 90.0)]
        
        output = formatter.format_results(results, 'captoin', 'c')
        
        assert '🌟 PANGRAMS' not in output

    def test_format_console_grouped_by_length(self):
        """Test console formatting groups words by length correctly."""
        formatter = ResultFormatter()
        results = [
            ('count', 90.0),  # 5 letters
            ('upon', 85.0),   # 4 letters
            ('unto', 80.0),   # 4 letters
            ('canton', 75.0)  # 6 letters
        ]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        
        assert '6-letter words (1):' in output
        assert '5-letter words (1):' in output
        assert '4-letter words (2):' in output

    # ==================== JSON Formatting Tests ====================

    def test_format_json_basic(self):
        """Test basic JSON formatting."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        results = [('count', 90.0), ('upon', 85.0)]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        data = json.loads(output)
        
        assert data['puzzle']['letters'] == 'NACUOTP'
        assert data['puzzle']['required_letter'] == 'N'
        assert data['summary']['total_words'] == 2
        assert len(data['words']) == 2
        assert data['words'][0]['word'] == 'count'
        assert data['words'][0]['confidence'] == 90.0

    def test_format_json_with_solve_time(self):
        """Test JSON formatting with solve time."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        results = [('count', 90.0)]
        
        output = formatter.format_results(
            results, 'nacuotp', 'n', solve_time=2.567
        )
        data = json.loads(output)
        
        assert 'solve_time' in data['summary']
        assert data['summary']['solve_time'] == 2.567

    def test_format_json_with_mode(self):
        """Test JSON formatting with mode."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        results = [('count', 90.0)]
        
        output = formatter.format_results(
            results, 'nacuotp', 'n', mode='production'
        )
        data = json.loads(output)
        
        assert data['puzzle']['mode'] == 'production'

    def test_format_json_with_pangrams(self):
        """Test JSON formatting includes pangrams."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        results = [('caption', 95.0), ('count', 90.0)]
        
        output = formatter.format_results(results, 'captoin', 'c')
        data = json.loads(output)
        
        assert 'pangrams' in data
        assert len(data['pangrams']) == 1
        assert data['pangrams'][0]['word'] == 'caption'
        assert data['summary']['pangram_count'] == 1

    def test_format_json_with_by_length(self):
        """Test JSON formatting includes by_length grouping."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        results = [('count', 90.0), ('upon', 85.0), ('canton', 80.0)]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        data = json.loads(output)
        
        assert 'by_length' in data
        assert '6' in data['by_length']
        assert '5' in data['by_length']
        assert '4' in data['by_length']
        assert len(data['by_length']['6']) == 1
        assert len(data['by_length']['4']) == 1

    def test_format_json_empty_results(self):
        """Test JSON formatting with empty results."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        
        output = formatter.format_results([], 'nacuotp', 'n')
        data = json.loads(output)
        
        assert data['summary']['total_words'] == 0
        assert len(data['words']) == 0

    # ==================== Compact Formatting Tests ====================

    def test_format_compact_basic(self):
        """Test basic compact formatting."""
        formatter = ResultFormatter(output_format=OutputFormat.COMPACT)
        results = [('count', 90.0), ('upon', 85.0)]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        
        assert 'Puzzle: NACUOTP (required: N) - 2 words' in output
        assert 'count (90%)' in output
        assert 'upon (85%)' in output

    def test_format_compact_without_confidence(self):
        """Test compact formatting without confidence scores."""
        formatter = ResultFormatter(
            output_format=OutputFormat.COMPACT,
            show_confidence=False
        )
        results = [('count', 90.0), ('upon', 85.0)]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        
        assert 'count' in output
        assert '90%' not in output

    def test_format_compact_empty_results(self):
        """Test compact formatting with empty results."""
        formatter = ResultFormatter(output_format=OutputFormat.COMPACT)
        
        output = formatter.format_results([], 'nacuotp', 'n')
        
        assert 'Puzzle: NACUOTP (required: N) - 0 words' in output
        assert output.count('\n') == 0  # Single line only

    # ==================== Format Override Tests ====================

    def test_format_override_console_to_json(self):
        """Test overriding console format to JSON."""
        formatter = ResultFormatter(output_format=OutputFormat.CONSOLE)
        results = [('count', 90.0)]
        
        output = formatter.format_results(
            results, 'nacuotp', 'n', output_format=OutputFormat.JSON
        )
        
        data = json.loads(output)
        assert 'words' in data

    def test_format_override_json_to_compact(self):
        """Test overriding JSON format to compact."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        results = [('count', 90.0)]
        
        output = formatter.format_results(
            results, 'nacuotp', 'n', output_format=OutputFormat.COMPACT
        )
        
        assert 'Puzzle:' in output
        # Should not be valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(output)

    # ==================== Input Validation Tests ====================

    def test_format_invalid_results_type(self):
        """Test format_results with invalid results type."""
        formatter = ResultFormatter()
        
        with pytest.raises(TypeError, match="Results must be a list"):
            formatter.format_results({'count': 90.0}, 'nacuotp', 'n')

    def test_format_invalid_letters_type(self):
        """Test format_results with invalid letters type."""
        formatter = ResultFormatter()
        
        with pytest.raises(TypeError, match="Letters must be a string"):
            formatter.format_results([], 1234567, 'n')

    def test_format_invalid_required_letter_type(self):
        """Test format_results with invalid required_letter type."""
        formatter = ResultFormatter()
        
        with pytest.raises(TypeError, match="Required letter must be a string"):
            formatter.format_results([], 'nacuotp', 1)

    def test_format_invalid_solve_time_type(self):
        """Test format_results with invalid solve_time type."""
        formatter = ResultFormatter()
        
        with pytest.raises(TypeError, match="Solve time must be a number"):
            formatter.format_results([], 'nacuotp', 'n', solve_time="2.5")

    def test_format_invalid_mode_type(self):
        """Test format_results with invalid mode type."""
        formatter = ResultFormatter()
        
        with pytest.raises(TypeError, match="Mode must be a string"):
            formatter.format_results([], 'nacuotp', 'n', mode=123)

    def test_format_invalid_letters_length(self):
        """Test format_results with invalid letters length."""
        formatter = ResultFormatter()
        
        with pytest.raises(ValueError, match="Letters must be exactly 7 characters"):
            formatter.format_results([], 'abc', 'n')

    def test_format_invalid_required_letter_length(self):
        """Test format_results with invalid required_letter length."""
        formatter = ResultFormatter()
        
        with pytest.raises(ValueError, match="Required letter must be exactly 1 character"):
            formatter.format_results([], 'nacuotp', 'nn')

    # ==================== print_results Tests ====================

    def test_print_results_basic(self, capsys):
        """Test print_results prints to stdout."""
        formatter = ResultFormatter()
        results = [('count', 90.0)]
        
        formatter.print_results(results, 'nacuotp', 'n')
        captured = capsys.readouterr()
        
        assert 'count' in captured.out
        assert 'SPELLING BEE SOLVER RESULTS' in captured.out

    def test_print_results_json(self, capsys):
        """Test print_results with JSON format."""
        formatter = ResultFormatter(output_format=OutputFormat.JSON)
        results = [('count', 90.0)]
        
        formatter.print_results(results, 'nacuotp', 'n')
        captured = capsys.readouterr()
        
        data = json.loads(captured.out)
        assert data['summary']['total_words'] == 1

    # ==================== Statistics Tests ====================

    def test_get_statistics_basic(self):
        """Test get_statistics with basic results."""
        formatter = ResultFormatter()
        results = [('count', 90.0), ('upon', 85.0), ('noun', 80.0)]
        
        stats = formatter.get_statistics(results)
        
        assert stats['total_words'] == 3
        assert stats['pangram_count'] == 0
        assert stats['avg_confidence'] == 85.0
        assert stats['min_confidence'] == 80.0
        assert stats['max_confidence'] == 90.0

    def test_get_statistics_with_pangram(self):
        """Test get_statistics with pangram."""
        formatter = ResultFormatter()
        results = [('caption', 95.0), ('count', 90.0)]
        
        stats = formatter.get_statistics(results)
        
        assert stats['total_words'] == 2
        assert stats['pangram_count'] == 1

    def test_get_statistics_by_length(self):
        """Test get_statistics includes by_length grouping."""
        formatter = ResultFormatter()
        results = [
            ('count', 90.0),   # 5 letters
            ('upon', 85.0),    # 4 letters
            ('noun', 80.0),    # 4 letters
            ('canton', 75.0)   # 6 letters
        ]
        
        stats = formatter.get_statistics(results)
        
        assert stats['by_length'][6] == 1
        assert stats['by_length'][5] == 1
        assert stats['by_length'][4] == 2

    def test_get_statistics_avg_word_length(self):
        """Test get_statistics calculates average word length."""
        formatter = ResultFormatter()
        results = [('count', 90.0), ('upon', 85.0)]  # 5 and 4 letters
        
        stats = formatter.get_statistics(results)
        
        assert stats['avg_word_length'] == 4.5

    def test_get_statistics_empty_results(self):
        """Test get_statistics with empty results."""
        formatter = ResultFormatter()
        
        stats = formatter.get_statistics([])
        
        assert stats['total_words'] == 0
        assert stats['pangram_count'] == 0
        assert stats['avg_confidence'] == 0.0
        assert stats['min_confidence'] == 0.0
        assert stats['max_confidence'] == 0.0
        assert stats['avg_word_length'] == 0.0

    def test_get_statistics_invalid_type(self):
        """Test get_statistics with invalid type."""
        formatter = ResultFormatter()
        
        with pytest.raises(TypeError, match="Results must be a list"):
            formatter.get_statistics({'count': 90.0})

    # ==================== Integration Tests ====================

    def test_real_world_scenario(self):
        """Test with realistic Spelling Bee scenario."""
        formatter = ResultFormatter()
        
        # Real puzzle results
        results = [
            ('account', 95.0),
            ('canton', 90.0),
            ('count', 90.0),
            ('upon', 85.0),
            ('noun', 80.0),
            ('onto', 75.0)
        ]
        
        output = formatter.format_results(results, 'nacuotp', 'n', solve_time=2.5)
        
        assert 'SPELLING BEE SOLVER RESULTS' in output
        assert 'Total words found: 6' in output
        assert 'Solve time: 2.500s' in output
        assert '7-letter words (1):' in output
        assert '6-letter words (1):' in output
        assert '5-letter words (1):' in output
        assert '4-letter words (3):' in output

    def test_multiple_output_formats(self):
        """Test formatting same results in multiple formats."""
        results = [('count', 90.0), ('upon', 85.0)]
        
        # Console format
        console_formatter = ResultFormatter(output_format=OutputFormat.CONSOLE)
        console_output = console_formatter.format_results(results, 'nacuotp', 'n')
        assert 'SPELLING BEE SOLVER RESULTS' in console_output
        
        # JSON format
        json_formatter = ResultFormatter(output_format=OutputFormat.JSON)
        json_output = json_formatter.format_results(results, 'nacuotp', 'n')
        json_data = json.loads(json_output)
        assert json_data['summary']['total_words'] == 2
        
        # Compact format
        compact_formatter = ResultFormatter(output_format=OutputFormat.COMPACT)
        compact_output = compact_formatter.format_results(results, 'nacuotp', 'n')
        assert 'Puzzle:' in compact_output

    def test_pangram_detection_accuracy(self):
        """Test accurate pangram detection."""
        formatter = ResultFormatter()
        
        # 'caption' uses all 7 unique letters (c-a-p-t-i-o-n)
        results = [
            ('caption', 95.0),  # Pangram
            ('paint', 90.0),    # Not pangram (5 unique letters: p-a-i-n-t)
            ('action', 85.0)    # Not pangram (6 unique letters: a-c-t-i-o-n)
        ]
        
        output = formatter.format_results(results, 'captoin', 'c')
        stats = formatter.get_statistics(results)
        
        assert '🌟 PANGRAMS (1):' in output
        assert 'CAPTION' in output
        assert stats['pangram_count'] == 1

    def test_statistics_consistency_with_formatting(self):
        """Test that statistics match formatting output."""
        formatter = ResultFormatter()
        results = [
            ('count', 90.0),
            ('upon', 85.0),
            ('noun', 80.0),
            ('canton', 75.0)
        ]
        
        output = formatter.format_results(results, 'nacuotp', 'n')
        stats = formatter.get_statistics(results)
        
        # Check that word counts match
        assert f'Total words found: {stats["total_words"]}' in output
        assert '6-letter words (1):' in output
        assert stats['by_length'][6] == 1
        assert '5-letter words (1):' in output
        assert stats['by_length'][5] == 1
        assert '4-letter words (2):' in output
        assert stats['by_length'][4] == 2
