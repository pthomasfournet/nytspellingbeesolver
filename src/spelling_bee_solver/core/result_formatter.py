"""Result formatting for Spelling Bee puzzle solutions.

This module provides the ResultFormatter class, which is responsible for
formatting and displaying puzzle results in various formats:
- Console output with formatted text and grouping
- JSON output for programmatic access
- Statistics and summary information
- Pangram highlighting

The ResultFormatter follows the Single Responsibility Principle by focusing
solely on result presentation, delegating puzzle solving and scoring to
specialized components.

Example:
    Basic console formatting::

        from spelling_bee_solver.core import create_result_formatter

        formatter = create_result_formatter()
        results = [('count', 90.0), ('upon', 85.0), ('noun', 80.0)]

        formatter.print_results(
            results=results,
            letters='nacuotp',
            required_letter='n',
            solve_time=2.5
        )

    JSON output::

        formatter = create_result_formatter(output_format='json')
        json_output = formatter.format_results(
            results=results,
            letters='nacuotp',
            required_letter='n'
        )
        print(json_output)

Classes:
    ResultFormatter: Formats puzzle results for display

Functions:
    create_result_formatter: Factory function for creating ResultFormatter instances
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class OutputFormat(Enum):
    """Output format options for result formatting."""
    CONSOLE = "console"
    JSON = "json"
    COMPACT = "compact"


class ResultFormatter:
    """Formats Spelling Bee puzzle results for display.

    This class is responsible for formatting puzzle results in various output
    formats, including:
    - Console output with formatted text, grouping by length, and pangram highlighting
    - JSON output for programmatic access
    - Compact console output for minimal display
    - Summary statistics

    Attributes:
        output_format (OutputFormat): Default output format for results
        show_confidence (bool): Whether to display confidence scores
        group_by_length (bool): Whether to group results by word length
        highlight_pangrams (bool): Whether to highlight pangrams specially

    Thread Safety:
        ResultFormatter instances are thread-safe for read operations.
    """

    def __init__(
        self,
        output_format: OutputFormat = OutputFormat.CONSOLE,
        show_confidence: bool = True,
        group_by_length: bool = True,
        highlight_pangrams: bool = True
    ):
        """Initialize a ResultFormatter.

        Args:
            output_format (OutputFormat, optional): Default output format.
                Defaults to OutputFormat.CONSOLE.
            show_confidence (bool, optional): Whether to display confidence scores.
                Defaults to True.
            group_by_length (bool, optional): Whether to group results by word length.
                Defaults to True.
            highlight_pangrams (bool, optional): Whether to highlight pangrams.
                Defaults to True.

        Example:
            >>> formatter = ResultFormatter(
            ...     output_format=OutputFormat.JSON,
            ...     show_confidence=True
            ... )
            >>> formatter.output_format
            <OutputFormat.JSON: 'json'>
        """
        if not isinstance(output_format, OutputFormat):
            raise TypeError(
                f"output_format must be OutputFormat, got {type(output_format).__name__}"
            )
        if not isinstance(show_confidence, bool):
            raise TypeError(
                f"show_confidence must be bool, got {type(show_confidence).__name__}"
            )
        if not isinstance(group_by_length, bool):
            raise TypeError(
                f"group_by_length must be bool, got {type(group_by_length).__name__}"
            )
        if not isinstance(highlight_pangrams, bool):
            raise TypeError(
                f"highlight_pangrams must be bool, got {type(highlight_pangrams).__name__}"
            )

        self.output_format = output_format
        self.show_confidence = show_confidence
        self.group_by_length = group_by_length
        self.highlight_pangrams = highlight_pangrams

    def format_results(
        self,
        results: List[Tuple[str, float]],
        letters: str,
        required_letter: str,
        solve_time: Optional[float] = None,
        mode: Optional[str] = None,
        output_format: Optional[OutputFormat] = None
    ) -> str:
        """Format puzzle results as a string.

        Args:
            results (List[Tuple[str, float]]): List of (word, confidence_score) tuples
            letters (str): The 7 puzzle letters
            required_letter (str): The required letter
            solve_time (float, optional): Time taken to solve (seconds). Defaults to None.
            mode (str, optional): Solver mode name. Defaults to None.
            output_format (OutputFormat, optional): Output format override.
                If None, uses self.output_format. Defaults to None.

        Returns:
            str: Formatted results string

        Raises:
            TypeError: If parameters have incorrect types
            ValueError: If parameters have invalid values

        Example:
            >>> formatter = ResultFormatter()
            >>> results = [('count', 90.0), ('upon', 85.0)]
            >>> output = formatter.format_results(
            ...     results, 'nacuotp', 'n', solve_time=2.5
            ... )
            >>> 'count' in output
            True
        """
        # Input validation
        if not isinstance(results, list):
            raise TypeError(
                f"Results must be a list, got {type(results).__name__}"
            )
        if not isinstance(letters, str):
            raise TypeError(
                f"Letters must be a string, got {type(letters).__name__}"
            )
        if not isinstance(required_letter, str):
            raise TypeError(
                f"Required letter must be a string, got {type(required_letter).__name__}"
            )
        if solve_time is not None and not isinstance(solve_time, (int, float)):
            raise TypeError(
                f"Solve time must be a number, got {type(solve_time).__name__}"
            )
        if mode is not None and not isinstance(mode, str):
            raise TypeError(
                f"Mode must be a string, got {type(mode).__name__}"
            )

        if len(letters) != 7:
            raise ValueError(
                f"Letters must be exactly 7 characters, got {len(letters)}"
            )
        if len(required_letter) != 1:
            raise ValueError(
                f"Required letter must be exactly 1 character, got {len(required_letter)}"
            )

        # Use override or default format
        fmt = output_format if output_format is not None else self.output_format

        if fmt == OutputFormat.JSON:
            return self._format_json(results, letters, required_letter, solve_time, mode)
        if fmt == OutputFormat.COMPACT:
            return self._format_compact(results, letters, required_letter)
        # CONSOLE
        return self._format_console(results, letters, required_letter, solve_time, mode)

    def print_results(
        self,
        results: List[Tuple[str, float]],
        letters: str,
        required_letter: str,
        solve_time: Optional[float] = None,
        mode: Optional[str] = None,
        output_format: Optional[OutputFormat] = None
    ) -> None:
        """Print formatted puzzle results to stdout.

        Convenience method that formats and prints results in one call.

        Args:
            results (List[Tuple[str, float]]): List of (word, confidence_score) tuples
            letters (str): The 7 puzzle letters
            required_letter (str): The required letter
            solve_time (float, optional): Time taken to solve (seconds). Defaults to None.
            mode (str, optional): Solver mode name. Defaults to None.
            output_format (OutputFormat, optional): Output format override. Defaults to None.

        Example:
            >>> formatter = ResultFormatter()
            >>> results = [('count', 90.0), ('upon', 85.0)]
            >>> formatter.print_results(results, 'nacuotp', 'n')
            ============================================================
            SPELLING BEE SOLVER RESULTS
            ...
        """
        output = self.format_results(
            results, letters, required_letter, solve_time, mode, output_format
        )
        print(output)

    def _format_console(
        self,
        results: List[Tuple[str, float]],
        letters: str,
        required_letter: str,
        solve_time: Optional[float],
        mode: Optional[str]
    ) -> str:
        """Format results for console display with grouping and highlighting."""
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("SPELLING BEE SOLVER RESULTS")
        lines.append("=" * 60)
        lines.append(f"Letters: {letters.upper()}")
        lines.append(f"Required: {required_letter.upper()}")

        if mode:
            lines.append(f"Mode: {mode.upper()}")

        lines.append(f"Total words found: {len(results)}")

        if solve_time is not None:
            lines.append(f"Solve time: {solve_time:.3f}s")

        lines.append("=" * 60)

        if not results:
            lines.append("\nNo words found.")
            lines.append("=" * 60)
            return "\n".join(lines)

        # Group by length and identify pangrams
        by_length: Dict[int, List[Tuple[str, float]]] = {}
        pangrams = []

        for word, confidence in results:
            if len(set(word.lower())) == 7:  # Pangram
                pangrams.append((word, confidence))

            length = len(word)
            if length not in by_length:
                by_length[length] = []
            by_length[length].append((word, confidence))

        # Show pangrams first if enabled
        if self.highlight_pangrams and pangrams:
            lines.append(f"\n🌟 PANGRAMS ({len(pangrams)}):")
            for word, confidence in pangrams:
                if self.show_confidence:
                    lines.append(f"  {word.upper():<20} ({confidence:.0f}% confidence)")
                else:
                    lines.append(f"  {word.upper()}")

        # Print by length groups if enabled
        if self.group_by_length:
            for length in sorted(by_length.keys(), reverse=True):
                words_of_length = by_length[length]
                lines.append(f"\n{length}-letter words ({len(words_of_length)}):")

                # Print in columns with confidence
                for i in range(0, len(words_of_length), 3):
                    row = words_of_length[i : i + 3]
                    line_parts = []
                    for word, confidence in row:
                        if self.show_confidence:
                            line_parts.append(f"{word:<15} ({confidence:.0f}%)")
                        else:
                            line_parts.append(f"{word:<15}")
                    lines.append(f"  {'  '.join(line_parts)}")
        else:
            # Simple list without grouping
            lines.append("\nWords:")
            for word, confidence in results:
                if self.show_confidence:
                    lines.append(f"  {word:<20} ({confidence:.0f}%)")
                else:
                    lines.append(f"  {word}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def _format_compact(
        self,
        results: List[Tuple[str, float]],
        letters: str,
        required_letter: str
    ) -> str:
        """Format results in compact format (single line per word)."""
        lines = []
        lines.append(f"Puzzle: {letters.upper()} (required: {required_letter.upper()}) - {len(results)} words")

        if not results:
            return lines[0]

        for word, confidence in results:
            if self.show_confidence:
                lines.append(f"{word} ({confidence:.0f}%)")
            else:
                lines.append(word)

        return "\n".join(lines)

    def _format_json(
        self,
        results: List[Tuple[str, float]],
        letters: str,
        required_letter: str,
        solve_time: Optional[float],
        mode: Optional[str]
    ) -> str:
        """Format results as JSON."""
        # Group by length and identify pangrams
        by_length: Dict[int, List[Dict[str, Any]]] = {}
        pangrams = []

        for word, confidence in results:
            word_dict = {"word": word, "confidence": confidence}

            if len(set(word.lower())) == 7:
                pangrams.append(word_dict)

            length = len(word)
            if length not in by_length:
                by_length[length] = []
            by_length[length].append(word_dict)

        output = {
            "puzzle": {
                "letters": letters.upper(),
                "required_letter": required_letter.upper()
            },
            "summary": {
                "total_words": len(results),
                "pangram_count": len(pangrams)
            },
            "words": [{"word": w, "confidence": c} for w, c in results]
        }

        if mode:
            output["puzzle"]["mode"] = mode

        if solve_time is not None:
            output["summary"]["solve_time"] = round(solve_time, 3)

        if self.highlight_pangrams and pangrams:
            output["pangrams"] = pangrams

        if self.group_by_length:
            output["by_length"] = {
                str(length): words
                for length, words in sorted(by_length.items(), reverse=True)
            }

        return json.dumps(output, indent=2)

    def get_statistics(
        self,
        results: List[Tuple[str, float]]
    ) -> Dict[str, Any]:
        """Calculate statistics from puzzle results.

        Args:
            results (List[Tuple[str, float]]): List of (word, confidence_score) tuples

        Returns:
            Dict[str, Any]: Dictionary containing statistics:
                - total_words: Total number of words found
                - pangram_count: Number of pangrams
                - by_length: Word count grouped by length
                - avg_confidence: Average confidence score
                - min_confidence: Minimum confidence score
                - max_confidence: Maximum confidence score
                - avg_word_length: Average word length

        Raises:
            TypeError: If results is not a list

        Example:
            >>> formatter = ResultFormatter()
            >>> results = [('count', 90.0), ('upon', 85.0), ('unto', 80.0)]
            >>> stats = formatter.get_statistics(results)
            >>> stats['total_words']
            3
            >>> stats['avg_word_length']
            4.33...
        """
        if not isinstance(results, list):
            raise TypeError(
                f"Results must be a list, got {type(results).__name__}"
            )

        if not results:
            return {
                "total_words": 0,
                "pangram_count": 0,
                "by_length": {},
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "avg_word_length": 0.0
            }

        # Count pangrams and words by length
        pangram_count = 0
        by_length: Dict[int, int] = {}
        confidences = []

        for word, confidence in results:
            if len(set(word.lower())) == 7:
                pangram_count += 1

            length = len(word)
            by_length[length] = by_length.get(length, 0) + 1
            confidences.append(confidence)

        return {
            "total_words": len(results),
            "pangram_count": pangram_count,
            "by_length": dict(sorted(by_length.items(), reverse=True)),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "avg_word_length": sum(len(w) for w, _ in results) / len(results)
        }


def create_result_formatter(
    output_format: OutputFormat = OutputFormat.CONSOLE,
    show_confidence: bool = True,
    group_by_length: bool = True,
    highlight_pangrams: bool = True
) -> ResultFormatter:
    """Create a ResultFormatter instance with specified configuration.

    Factory function that creates and configures a ResultFormatter. This is
    the recommended way to create ResultFormatter instances, as it provides
    a stable API and allows for future initialization logic without breaking
    existing code.

    Args:
        output_format (OutputFormat, optional): Default output format.
            Defaults to OutputFormat.CONSOLE.
        show_confidence (bool, optional): Whether to display confidence scores.
            Defaults to True.
        group_by_length (bool, optional): Whether to group results by word length.
            Defaults to True.
        highlight_pangrams (bool, optional): Whether to highlight pangrams.
            Defaults to True.

    Returns:
        ResultFormatter: Configured ResultFormatter instance

    Raises:
        TypeError: If parameters have incorrect types

    Example:
        >>> formatter = create_result_formatter(
        ...     output_format=OutputFormat.JSON,
        ...     show_confidence=False
        ... )
        >>> formatter.output_format
        <OutputFormat.JSON: 'json'>
    """
    return ResultFormatter(
        output_format=output_format,
        show_confidence=show_confidence,
        group_by_length=group_by_length,
        highlight_pangrams=highlight_pangrams
    )
