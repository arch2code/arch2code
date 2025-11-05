#!/usr/bin/env python3
"""
Quick test script for truncation functionality.

Tests edge cases and specific scenarios for the new truncation modes.

This test script demonstrates proper testing practices:
- Captures output for verification instead of just visual inspection
- Uses assertions to validate expected behavior
- Provides clear pass/fail indicators
- Returns appropriate exit codes for CI/CD integration
- Tracks and reports detailed failure information

Usage:
    python3 test_table_format.py

Exit codes:
    0: All tests passed
    1: One or more tests failed
"""

import sys
import os

# Add parent directory to path to find table_format package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from table_format import TableFormatter


class TestResults:
    """Helper class to track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []

    def assert_equal(self, actual, expected, description):
        """Assert that actual equals expected."""
        if actual == expected:
            self.passed += 1
            print(f"✓ PASS: {description}")
        else:
            self.failed += 1
            self.failures.append(f"FAIL: {description} - Expected: {expected}, Got: {actual}")
            print(f"✗ FAIL: {description} - Expected: {expected}, Got: {actual}")

    def assert_contains(self, text, substring, description):
        """Assert that text contains substring."""
        if substring in text:
            self.passed += 1
            print(f"✓ PASS: {description}")
        else:
            self.failed += 1
            self.failures.append(f"FAIL: {description} - Expected '{substring}' in output")
            print(f"✗ FAIL: {description} - Expected '{substring}' in output")

    def assert_not_contains(self, text, substring, description):
        """Assert that text does not contain substring."""
        if substring not in text:
            self.passed += 1
            print(f"✓ PASS: {description}")
        else:
            self.failed += 1
            self.failures.append(f"FAIL: {description} - Should not contain '{substring}'")
            print(f"✗ FAIL: {description} - Should not contain '{substring}'")

    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.failed > 0:
            print(f"FAILURES ({self.failed}):")
            for failure in self.failures:
                print(f"  - {failure}")
        print(f"{'='*60}")
        return self.failed == 0


def capture_table_output(table_func, *args, **kwargs):
    """Capture the output from a table display function."""
    # With the new API, table functions return strings directly
    return table_func(*args, **kwargs)

def test_truncation_edge_cases():
    """Test edge cases for truncation functionality."""
    results = TestResults()
    print("=" * 60)
    print("TRUNCATION EDGE CASE TESTS")
    print("=" * 60)

    # Test data with various text lengths
    test_data = {
        'exact_fit': '12345',  # Exactly fits width 5
        'one_over': '123456',  # One character over width 5
        'way_over': 'this_is_a_very_long_string_that_exceeds_width',
        'empty': '',
        'short': 'hi'
    }

    # Very narrow columns to test truncation
    narrow_columns = [('Key', 10), ('Value', 5)]

    print("\nTesting with very narrow columns (width=5):")
    print("Text lengths: exact(5), over(6), way_over(44), empty(0), short(2)")

    # Right truncation test
    print("\n1. RIGHT TRUNCATION (ellipsis at beginning):")
    table_right = TableFormatter('ascii', 'right')
    right_output = capture_table_output(table_right.format_dict_table, test_data, narrow_columns)

    # Verify right truncation behavior
    results.assert_contains(right_output, "...56", "Right truncation: one_over shows '...56'")
    results.assert_contains(right_output, "...th", "Right truncation: way_over shows '...th'")
    results.assert_contains(right_output, "12345", "No truncation: exact_fit shows '12345'")
    results.assert_contains(right_output, "hi   ", "No truncation: short shows 'hi'")

    # Left truncation test
    print("\n2. LEFT TRUNCATION (ellipsis at end):")
    table_left = TableFormatter('ascii', 'left')
    left_output = capture_table_output(table_left.format_dict_table, test_data, narrow_columns)

    # Verify left truncation behavior
    results.assert_contains(left_output, "12...", "Left truncation: one_over shows '12...'")
    results.assert_contains(left_output, "th...", "Left truncation: way_over shows 'th...'")
    results.assert_contains(left_output, "12345", "No truncation: exact_fit shows '12345'")
    results.assert_contains(left_output, "hi   ", "No truncation: short shows 'hi'")

    print("\n" + "=" * 60)
    print("EDGE CASE VERIFICATION:")
    return results

def test_minimal_width():
    """Test with very small column widths and header width enforcement."""
    results = TestResults()
    print("\n" + "=" * 60)
    print("MINIMAL WIDTH AND HEADER WIDTH TESTS")
    print("=" * 60)

    data = {'test': 'abcdefghijklmnop'}

    # Test header width enforcement
    table = TableFormatter('ascii', 'right')

    print("\nTesting header width enforcement...")

    # Test 1: Column width smaller than header "Value" (5 chars)
    output1 = capture_table_output(table.format_dict_table, data, [('Key', 8), ('Value', 4)])
    results.assert_contains(output1, "| Value |", "Header 'Value' fits properly despite width=4")
    results.assert_contains(output1, "...op", "Data truncated with right alignment")

    # Test 2: Very small width vs header
    output2 = capture_table_output(table.format_dict_table, data, [('Key', 8), ('Value', 2)])
    results.assert_contains(output2, "| Value |", "Header 'Value' fits properly despite width=2")

    # Test 3: Very long header enforcement
    output3 = capture_table_output(table.format_dict_table, data, [('Key', 8), ('VeryLongHeaderName', 3)])
    results.assert_contains(output3, "| VeryLongHeaderName |", "Long header fits properly despite width=3")

    # Test the _adjust_column_widths method directly
    adjusted = table._adjust_column_widths([('Value', 4), ('VeryLong', 2)])
    results.assert_equal(adjusted[0][1], 5, "Width adjusted for 'Value' header (5 chars)")
    results.assert_equal(adjusted[1][1], 8, "Width adjusted for 'VeryLong' header (8 chars)")

    # Test no adjustment needed
    adjusted2 = table._adjust_column_widths([('Key', 10), ('Value', 10)])
    results.assert_equal(adjusted2[0][1], 10, "Width unchanged when sufficient (Key)")
    results.assert_equal(adjusted2[1][1], 10, "Width unchanged when sufficient (Value)")

    print("\n" + "=" * 60)
    print("HEADER WIDTH ENFORCEMENT VERIFICATION:")
    return results


def test_truncation_modes():
    """Test that truncation modes work correctly."""
    results = TestResults()
    print("\n" + "=" * 60)
    print("TRUNCATION MODE VERIFICATION TESTS")
    print("=" * 60)

    # Use list data for clearer testing
    data = [{'Item': 'short', 'Data': 'verylongtext'}]
    columns = [('Item', 5), ('Data', 6)]

    # Test right truncation
    table_right = TableFormatter('ascii', 'right')
    right_output = capture_table_output(table_right.format_list_table, data, columns)
    print("Right truncation output (first few lines):")
    print('\n'.join(right_output.split('\n')[:10]))
    results.assert_contains(right_output, "...ext", "Right truncation shows end of text")
    results.assert_not_contains(right_output, "very...", "Right truncation does not show start")

    # Test left truncation
    table_left = TableFormatter('ascii', 'left')
    left_output = capture_table_output(table_left.format_list_table, data, columns)
    print("\nLeft truncation output (first few lines):")
    print('\n'.join(left_output.split('\n')[:10]))
    results.assert_contains(left_output, "ver...", "Left truncation shows start of text")
    results.assert_not_contains(left_output, "...ext", "Left truncation does not show end")

    return results

def test_autosize_functionality():
    """Test autosize feature with width=0"""
    results = TestResults()
    print("============================================================")
    print("AUTOSIZE FUNCTIONALITY TESTS")
    print("============================================================")

    # Test data with varying content lengths
    data = {
        'short_key': 'short',
        'very_long_key_name_here': 'this is a very long value that should determine column width'
    }

    # Use larger max_autosize_width for test to allow full content
    formatter = TableFormatter(max_autosize_width=100)

    # Test autosize with dictionary data
    result = formatter.format_dict_table(
        data,
        [('Key', 0), ('Value', 0)],  # Both columns autosize
        title="Autosize Test"
    )

    # Verify long content fits without truncation
    long_key = 'very_long_key_name_here'
    long_value = 'this is a very long value that should determine column width'

    results.assert_contains(result, long_key, "Long key fits without truncation")
    results.assert_contains(result, long_value, "Long value fits without truncation")
    results.assert_not_contains(result, "...", "No truncation should occur with autosize")

    # Test mixed sizing - one fixed, one autosize
    result2 = formatter.format_dict_table(
        data,
        [('Key', 10), ('Value', 0)],  # Fixed width for Key, autosize for Value
        title="Mixed Sizing Test"
    )

    # Key should be truncated due to fixed width
    results.assert_contains(result2, "...", "Fixed width column truncates long keys")
    results.assert_not_contains(result2, 'very_long_key_name_here', "Fixed width column should truncate long keys")

    # Value should fit fully with autosize
    results.assert_contains(result2, long_value, "Autosize value column fits full content")

    return results

def test_autosize_with_lists():
    """Test autosize functionality with list data."""
    results = TestResults()
    print("\n" + "=" * 60)
    print("AUTOSIZE WITH LIST DATA TESTS")
    print("=" * 60)

    # Test data - list of dictionaries with varying content lengths
    list_data = [
        {'name': 'A', 'description': 'Short desc', 'category': 'cat1'},
        {'name': 'Very Long Component Name', 'description': 'This is a much longer description that spans multiple words', 'category': 'category_name'},
        {'name': 'Medium', 'description': 'Medium length description', 'category': 'cat2'}
    ]

    # All columns autosize
    autosize_columns = [('Name', 0), ('Description', 0), ('Category', 0)]
    table = TableFormatter('ascii', max_autosize_width=100)  # Use larger limit for test
    output = table.format_list_table(list_data, autosize_columns, title="List Autosize Test")

    # Verify no truncation occurs
    results.assert_contains(output, "Very Long Component Name", "Long name fits without truncation")
    results.assert_contains(output, "This is a much longer description that spans multiple words",
                          "Long description fits without truncation")
    results.assert_contains(output, "category_name", "Long category fits without truncation")
    results.assert_not_contains(output, "...", "No truncation with autosize")

    return results

def test_autosize_edge_cases():
    """Test autosize edge cases and limits."""
    results = TestResults()
    print("\n" + "=" * 60)
    print("AUTOSIZE EDGE CASE TESTS")
    print("=" * 60)

    # Test with empty data
    empty_data = {}
    autosize_columns = [('Key', 0), ('Value', 0)]
    table = TableFormatter('ascii')
    empty_output = table.format_dict_table(empty_data, autosize_columns)
    results.assert_contains(empty_output, "No data to format", "Empty data handled correctly")

    # Test minimum width enforcement (should be at least header width)
    minimal_data = {'k': 'v'}
    minimal_output = table.format_dict_table(minimal_data, autosize_columns)
    # Should at least fit the headers "Key" and "Value"
    results.assert_contains(minimal_output, "| Key", "Header width enforced for autosize")
    results.assert_contains(minimal_output, "| Value", "Header width enforced for autosize")

    # Test very long content (should be limited to reasonable max)
    very_long_content = 'x' * 100  # 100 character string
    long_data = {'test': very_long_content}
    long_output = table.format_dict_table(long_data, [('Key', 0), ('Value', 0)])

    # Should be limited to max width (80 characters) and truncated
    lines = long_output.split('\n')
    # Find the data row (should contain the long content)
    data_row = None
    for line in lines:
        if 'test' in line and 'xxx' in line:
            data_row = line
            break

    if data_row:
        # The line should not be extremely long due to the 80 char limit
        results.assert_equal(len(data_row) <= 100, True, "Very long content limited to reasonable width")
    else:
        results.assert_equal(True, False, "Could not find data row in output")

    return results

def test_autosize_with_custom_extractor():
    """Test autosize with custom data extractors."""
    results = TestResults()
    print("\n" + "=" * 60)
    print("AUTOSIZE WITH CUSTOM EXTRACTOR TESTS")
    print("=" * 60)

    # Test data with nested structure
    complex_data = {
        'item1': {'info': {'name': 'Short Name', 'desc': 'Short'}, 'count': 10},
        'item2': {'info': {'name': 'Very Long Descriptive Name Here', 'desc': 'This is a much longer description'}, 'count': 250}
    }

    def custom_extractor(key, value, columns):
        return [
            key,
            value['info']['name'],
            value['info']['desc'],
            str(value['count'])
        ]

    autosize_columns = [('Item', 0), ('Name', 0), ('Description', 0), ('Count', 0)]
    table = TableFormatter('ascii')
    output = table.format_dict_table(complex_data, autosize_columns, custom_extractor, "Custom Extractor Test")

    # Verify proper autosize with custom extraction
    results.assert_contains(output, "Very Long Descriptive Name Here", "Custom extractor with autosize works")
    results.assert_contains(output, "This is a much longer description", "Long extracted content fits")
    results.assert_not_contains(output, "...", "No truncation with autosize and custom extractor")

    return results

def test_configurable_max_autosize_width():
    """Test configurable maximum autosize width functionality."""
    results = TestResults()
    print("\n" + "=" * 60)
    print("CONFIGURABLE MAX AUTOSIZE WIDTH TESTS")
    print("=" * 60)

    # Test data with very long content
    long_content_data = {
        'short_key': 'short value',
        'long_key': 'This is an extremely long value that would normally make the column very wide but should be truncated when max_autosize_width is set to a smaller value than the content length'
    }

    # Test 1: Default max_autosize_width (50)
    default_table = TableFormatter('ascii')  # default max_autosize_width=50
    default_output = default_table.format_dict_table(long_content_data, [('Key', 0), ('Value', 0)], title="Default Max Width (50)")

    # Should truncate the long content
    results.assert_contains(default_output, "...", "Long content truncated with default max width")

    # Test 2: Custom smaller max_autosize_width (20)
    small_table = TableFormatter('ascii', 'right', max_autosize_width=20)
    small_output = small_table.format_dict_table(long_content_data, [('Key', 0), ('Value', 0)], title="Small Max Width (20)")

    # Should truncate even more aggressively
    results.assert_contains(small_output, "...", "Long content truncated with small max width")

    # Test 3: Large max_autosize_width (200)
    large_table = TableFormatter('ascii', 'right', max_autosize_width=200)
    large_output = large_table.format_dict_table(long_content_data, [('Key', 0), ('Value', 0)], title="Large Max Width (200)")

    # Should fit more content without truncation
    results.assert_contains(large_output, "This is an extremely long value that would normally make the column very wide", "More content fits with larger max width")

    # Test 4: Test with left truncation mode
    left_table = TableFormatter('ascii', 'left', max_autosize_width=25)
    left_output = left_table.format_dict_table(long_content_data, [('Key', 0), ('Value', 0)], title="Left Truncation Max Width (25)")

    # Should show start of content with ellipsis at end - adjust expected text to match actual truncation
    results.assert_contains(left_output, "This is an extremely l...", "Left truncation works with max autosize width")

    # Test 5: Test with convenience function
    from table_format import format_dict_table
    convenience_output = format_dict_table(
        long_content_data,
        [('Key', 0), ('Value', 0)],
        title="Convenience Function Test",
        max_autosize_width=30,
        print_output=False
    )
    results.assert_contains(convenience_output, "...", "Convenience function supports max_autosize_width parameter")

    return results

if __name__ == "__main__":
    all_passed = True

    # Run all test functions
    results1 = test_truncation_edge_cases()
    results2 = test_minimal_width()
    results3 = test_truncation_modes()
    results4 = test_autosize_functionality()
    results5 = test_autosize_with_lists()
    results6 = test_autosize_edge_cases()
    results7 = test_autosize_with_custom_extractor()
    results8 = test_configurable_max_autosize_width()

    # Combine results
    all_results = [results1, results2, results3, results4, results5, results6, results7, results8]
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    all_failures = []
    for r in all_results:
        all_failures.extend(r.failures)

    # Print overall summary
    print(f"\n{'='*70}")
    print(f"OVERALL TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")

    if total_failed > 0:
        print(f"\nFAILURES:")
        for failure in all_failures:
            print(f"  - {failure}")
        print(f"\n❌ TESTS FAILED: {total_failed} test(s) did not pass")
        exit(1)
    else:
        print(f"\n✅ ALL TESTS PASSED: {total_passed} test(s) completed successfully!")
        exit(0)