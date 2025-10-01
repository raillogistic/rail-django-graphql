#!/usr/bin/env python
"""
Comprehensive Test Runner for Django GraphQL Multi-Schema System.

This script provides a unified interface for running all test suites including
unit tests, integration tests, performance tests, load tests, and benchmarks.
It supports various configuration options and generates detailed reports.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --performance      # Run only performance tests
    python run_tests.py --load             # Run only load tests
    python run_tests.py --benchmarks       # Run only benchmarks
    python run_tests.py --coverage         # Run with coverage reporting
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --fast             # Skip slow tests
    python run_tests.py --report           # Generate detailed reports
"""

import os
import sys
import argparse
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rail_django_graphql.settings')

try:
    import django
    django.setup()
except ImportError:
    print("Error: Django not found. Please install Django and ensure settings are configured.")
    sys.exit(1)


class TestRunner:
    """Comprehensive test runner for the Django GraphQL Multi-Schema System."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.project_root = project_root
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
        # Test suite configurations
        self.test_suites = {
            'unit': {
                'path': 'tests/unit',
                'description': 'Unit tests for individual components',
                'command': ['python', '-m', 'pytest', 'tests/unit/', '-v'],
                'timeout': 300,  # 5 minutes
            },
            'integration': {
                'path': 'tests/integration',
                'description': 'Integration tests for component interactions',
                'command': ['python', '-m', 'pytest', 'tests/integration/', '-v'],
                'timeout': 600,  # 10 minutes
            },
            'performance': {
                'path': 'tests/performance/test_schema_registry_performance.py',
                'description': 'Performance tests for schema registry operations',
                'command': ['python', 'tests/performance/test_schema_registry_performance.py'],
                'timeout': 900,  # 15 minutes
            },
            'load': {
                'path': 'tests/performance/test_load_testing.py',
                'description': 'Load tests for stress testing under high traffic',
                'command': ['python', 'tests/performance/test_load_testing.py'],
                'timeout': 1800,  # 30 minutes
            },
            'benchmarks': {
                'path': 'tests/performance/test_benchmarks.py',
                'description': 'Benchmark tests for performance measurement',
                'command': ['python', 'tests/performance/test_benchmarks.py'],
                'timeout': 1200,  # 20 minutes
            }
        }
    
    def parse_arguments(self):
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description='Comprehensive test runner for Django GraphQL Multi-Schema System',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit --coverage  # Run unit tests with coverage
  python run_tests.py --performance --verbose  # Run performance tests with verbose output
  python run_tests.py --fast --report    # Run fast tests and generate report
            """
        )
        
        # Test suite selection
        parser.add_argument('--unit', action='store_true',
                          help='Run unit tests only')
        parser.add_argument('--integration', action='store_true',
                          help='Run integration tests only')
        parser.add_argument('--performance', action='store_true',
                          help='Run performance tests only')
        parser.add_argument('--load', action='store_true',
                          help='Run load tests only')
        parser.add_argument('--benchmarks', action='store_true',
                          help='Run benchmark tests only')
        
        # Test execution options
        parser.add_argument('--coverage', action='store_true',
                          help='Run tests with coverage reporting')
        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output')
        parser.add_argument('--fast', action='store_true',
                          help='Skip slow tests (performance, load, benchmarks)')
        parser.add_argument('--parallel', type=int, metavar='N',
                          help='Run tests in parallel with N processes')
        
        # Reporting options
        parser.add_argument('--report', action='store_true',
                          help='Generate detailed test reports')
        parser.add_argument('--output-dir', default='test_results',
                          help='Directory for test reports and artifacts')
        parser.add_argument('--junit-xml', metavar='FILE',
                          help='Generate JUnit XML report')
        
        # Filtering options
        parser.add_argument('--pattern', '-k', metavar='PATTERN',
                          help='Run tests matching pattern')
        parser.add_argument('--marker', '-m', metavar='MARKER',
                          help='Run tests with specific marker')
        parser.add_argument('--failed-first', action='store_true',
                          help='Run failed tests first')
        
        # Environment options
        parser.add_argument('--settings', metavar='MODULE',
                          help='Django settings module to use')
        parser.add_argument('--database', metavar='ENGINE',
                          help='Database engine to use for tests')
        
        return parser.parse_args()
    
    def setup_environment(self, args):
        """Set up the test environment based on arguments."""
        # Set Django settings
        if args.settings:
            os.environ['DJANGO_SETTINGS_MODULE'] = args.settings
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Set up coverage if requested
        if args.coverage:
            try:
                import coverage
                self.coverage = coverage.Coverage(
                    source=['rail_django_graphql'],
                    omit=[
                        '*/tests/*',
                        '*/migrations/*',
                        '*/venv/*',
                        '*/env/*',
                        'manage.py',
                        'setup.py',
                    ]
                )
                self.coverage.start()
            except ImportError:
                print("Warning: coverage package not found. Install with: pip install coverage")
                args.coverage = False
    
    def determine_test_suites(self, args):
        """Determine which test suites to run based on arguments."""
        if args.fast:
            # Skip slow tests in fast mode
            return ['unit', 'integration']
        
        # If specific suites are requested, run only those
        requested_suites = []
        if args.unit:
            requested_suites.append('unit')
        if args.integration:
            requested_suites.append('integration')
        if args.performance:
            requested_suites.append('performance')
        if args.load:
            requested_suites.append('load')
        if args.benchmarks:
            requested_suites.append('benchmarks')
        
        # If no specific suites requested, run all
        if not requested_suites:
            return list(self.test_suites.keys())
        
        return requested_suites
    
    def build_test_command(self, suite_name, args):
        """Build the command to run a specific test suite."""
        suite_config = self.test_suites[suite_name]
        command = suite_config['command'].copy()
        
        # Add pytest-specific options for pytest-based tests
        if 'pytest' in command:
            if args.verbose:
                if '-v' not in command:
                    command.append('-v')
            
            if args.parallel and args.parallel > 1:
                command.extend(['-n', str(args.parallel)])
            
            if args.pattern:
                command.extend(['-k', args.pattern])
            
            if args.marker:
                command.extend(['-m', args.marker])
            
            if args.failed_first:
                command.append('--lf')
            
            if args.junit_xml:
                junit_file = os.path.join(args.output_dir, f'{suite_name}_junit.xml')
                command.extend(['--junit-xml', junit_file])
            
            if args.coverage and suite_name in ['unit', 'integration']:
                command.extend(['--cov=rail_django_graphql', '--cov-report=term-missing'])
        
        return command
    
    def run_test_suite(self, suite_name, args):
        """Run a specific test suite."""
        suite_config = self.test_suites[suite_name]
        
        print(f"\n{'='*60}")
        print(f"Running {suite_name.upper()} TESTS")
        print(f"Description: {suite_config['description']}")
        print(f"{'='*60}")
        
        # Check if test path exists
        test_path = os.path.join(self.project_root, suite_config['path'])
        if not os.path.exists(test_path):
            print(f"Warning: Test path {test_path} does not exist. Skipping {suite_name} tests.")
            return {
                'suite': suite_name,
                'status': 'skipped',
                'reason': 'Test path not found',
                'duration': 0,
            }
        
        # Build and run command
        command = self.build_test_command(suite_name, args)
        
        print(f"Command: {' '.join(command)}")
        print(f"Working directory: {self.project_root}")
        print(f"Timeout: {suite_config['timeout']} seconds")
        print()
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                timeout=suite_config['timeout'],
                capture_output=not args.verbose,
                text=True
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Determine status
            if result.returncode == 0:
                status = 'passed'
                print(f"✅ {suite_name.upper()} tests PASSED ({duration:.2f}s)")
            else:
                status = 'failed'
                print(f"❌ {suite_name.upper()} tests FAILED ({duration:.2f}s)")
                if not args.verbose and result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if not args.verbose and result.stderr:
                    print("STDERR:")
                    print(result.stderr)
            
            return {
                'suite': suite_name,
                'status': status,
                'return_code': result.returncode,
                'duration': duration,
                'stdout': result.stdout if result.stdout else '',
                'stderr': result.stderr if result.stderr else '',
            }
        
        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ {suite_name.upper()} tests TIMED OUT after {duration:.2f}s")
            
            return {
                'suite': suite_name,
                'status': 'timeout',
                'duration': duration,
                'timeout': suite_config['timeout'],
            }
        
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"💥 {suite_name.upper()} tests ERROR: {e}")
            
            return {
                'suite': suite_name,
                'status': 'error',
                'error': str(e),
                'duration': duration,
            }
    
    def run_all_tests(self, args):
        """Run all selected test suites."""
        self.start_time = time.time()
        
        print("🚀 Starting Django GraphQL Multi-Schema System Test Suite")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Python: {sys.version}")
        print(f"Working directory: {self.project_root}")
        
        # Determine which test suites to run
        suites_to_run = self.determine_test_suites(args)
        
        print(f"Test suites to run: {', '.join(suites_to_run)}")
        
        # Run each test suite
        for suite_name in suites_to_run:
            result = self.run_test_suite(suite_name, args)
            self.test_results[suite_name] = result
        
        self.end_time = time.time()
        
        # Generate summary
        self.print_summary()
        
        # Generate reports if requested
        if args.report:
            self.generate_reports(args)
        
        # Handle coverage reporting
        if args.coverage and hasattr(self, 'coverage'):
            self.generate_coverage_report(args)
        
        # Return overall success status
        return self.get_overall_status()
    
    def print_summary(self):
        """Print a summary of all test results."""
        total_duration = self.end_time - self.start_time
        
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for r in self.test_results.values() if r['status'] == 'passed')
        failed = sum(1 for r in self.test_results.values() if r['status'] == 'failed')
        skipped = sum(1 for r in self.test_results.values() if r['status'] == 'skipped')
        timeout = sum(1 for r in self.test_results.values() if r['status'] == 'timeout')
        error = sum(1 for r in self.test_results.values() if r['status'] == 'error')
        
        print(f"Total test suites: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Timeout: {timeout}")
        print(f"Error: {error}")
        print(f"Total duration: {total_duration:.2f}s")
        
        print(f"\nDetailed Results:")
        for suite_name, result in self.test_results.items():
            status_icon = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'timeout': '⏰',
                'error': '💥'
            }.get(result['status'], '❓')
            
            print(f"  {status_icon} {suite_name:12} {result['status']:10} ({result['duration']:.2f}s)")
        
        # Overall status
        if failed > 0 or timeout > 0 or error > 0:
            print(f"\n❌ OVERALL: FAILED")
        else:
            print(f"\n✅ OVERALL: PASSED")
    
    def generate_reports(self, args):
        """Generate detailed test reports."""
        print(f"\n📊 Generating test reports in {args.output_dir}/")
        
        # Generate JSON report
        json_report = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': self.end_time - self.start_time,
            'python_version': sys.version,
            'working_directory': str(self.project_root),
            'test_results': self.test_results,
            'summary': {
                'total_suites': len(self.test_results),
                'passed': sum(1 for r in self.test_results.values() if r['status'] == 'passed'),
                'failed': sum(1 for r in self.test_results.values() if r['status'] == 'failed'),
                'skipped': sum(1 for r in self.test_results.values() if r['status'] == 'skipped'),
                'timeout': sum(1 for r in self.test_results.values() if r['status'] == 'timeout'),
                'error': sum(1 for r in self.test_results.values() if r['status'] == 'error'),
            }
        }
        
        json_file = os.path.join(args.output_dir, 'test_report.json')
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        print(f"  📄 JSON report: {json_file}")
        
        # Generate HTML report
        html_file = os.path.join(args.output_dir, 'test_report.html')
        self.generate_html_report(html_file, json_report)
        print(f"  🌐 HTML report: {html_file}")
        
        # Generate markdown report
        md_file = os.path.join(args.output_dir, 'test_report.md')
        self.generate_markdown_report(md_file, json_report)
        print(f"  📝 Markdown report: {md_file}")
    
    def generate_html_report(self, filename, report_data):
        """Generate an HTML test report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Django GraphQL Multi-Schema System - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-suite {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        .skipped {{ background-color: #fff3cd; }}
        .timeout {{ background-color: #ffeaa7; }}
        .error {{ background-color: #fdcae1; }}
        .duration {{ float: right; font-weight: bold; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Django GraphQL Multi-Schema System - Test Report</h1>
        <p><strong>Timestamp:</strong> {report_data['timestamp']}</p>
        <p><strong>Duration:</strong> {report_data['total_duration']:.2f} seconds</p>
        <p><strong>Python Version:</strong> {report_data['python_version']}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li>Total Suites: {report_data['summary']['total_suites']}</li>
            <li>Passed: {report_data['summary']['passed']}</li>
            <li>Failed: {report_data['summary']['failed']}</li>
            <li>Skipped: {report_data['summary']['skipped']}</li>
            <li>Timeout: {report_data['summary']['timeout']}</li>
            <li>Error: {report_data['summary']['error']}</li>
        </ul>
    </div>
    
    <div class="results">
        <h2>Test Suite Results</h2>
"""
        
        for suite_name, result in report_data['test_results'].items():
            status_class = result['status']
            html_content += f"""
        <div class="test-suite {status_class}">
            <h3>{suite_name.upper()} <span class="duration">{result['duration']:.2f}s</span></h3>
            <p><strong>Status:</strong> {result['status']}</p>
"""
            
            if result.get('stdout'):
                html_content += f"""
            <h4>Output:</h4>
            <pre>{result['stdout']}</pre>
"""
            
            if result.get('stderr'):
                html_content += f"""
            <h4>Errors:</h4>
            <pre>{result['stderr']}</pre>
"""
            
            html_content += "        </div>\n"
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html_content)
    
    def generate_markdown_report(self, filename, report_data):
        """Generate a Markdown test report."""
        md_content = f"""# Django GraphQL Multi-Schema System - Test Report

**Timestamp:** {report_data['timestamp']}  
**Duration:** {report_data['total_duration']:.2f} seconds  
**Python Version:** {report_data['python_version']}  

## Summary

- **Total Suites:** {report_data['summary']['total_suites']}
- **Passed:** {report_data['summary']['passed']}
- **Failed:** {report_data['summary']['failed']}
- **Skipped:** {report_data['summary']['skipped']}
- **Timeout:** {report_data['summary']['timeout']}
- **Error:** {report_data['summary']['error']}

## Test Suite Results

"""
        
        for suite_name, result in report_data['test_results'].items():
            status_emoji = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'timeout': '⏰',
                'error': '💥'
            }.get(result['status'], '❓')
            
            md_content += f"""### {status_emoji} {suite_name.upper()}

**Status:** {result['status']}  
**Duration:** {result['duration']:.2f} seconds  

"""
            
            if result.get('stdout'):
                md_content += f"""**Output:**
```
{result['stdout']}
```

"""
            
            if result.get('stderr'):
                md_content += f"""**Errors:**
```
{result['stderr']}
```

"""
        
        with open(filename, 'w') as f:
            f.write(md_content)
    
    def generate_coverage_report(self, args):
        """Generate coverage report if coverage was enabled."""
        if not hasattr(self, 'coverage'):
            return
        
        print(f"\n📈 Generating coverage report...")
        
        self.coverage.stop()
        self.coverage.save()
        
        # Generate console report
        print("Coverage Summary:")
        self.coverage.report()
        
        # Generate HTML coverage report
        html_dir = os.path.join(args.output_dir, 'coverage_html')
        self.coverage.html_report(directory=html_dir)
        print(f"  🌐 HTML coverage report: {html_dir}/index.html")
        
        # Generate XML coverage report
        xml_file = os.path.join(args.output_dir, 'coverage.xml')
        self.coverage.xml_report(outfile=xml_file)
        print(f"  📄 XML coverage report: {xml_file}")
    
    def get_overall_status(self):
        """Get the overall test status."""
        for result in self.test_results.values():
            if result['status'] in ['failed', 'timeout', 'error']:
                return False
        return True


def main():
    """Main entry point for the test runner."""
    runner = TestRunner()
    args = runner.parse_arguments()
    
    # Setup environment
    runner.setup_environment(args)
    
    # Run tests
    success = runner.run_all_tests(args)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()