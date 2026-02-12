"""
Statistics analysis and reporting for automation results.
"""

import json
from typing import Dict, List
from datetime import datetime
from collections import Counter
from pathlib import Path

from loguru import logger


class StatisticsAnalyzer:
    """Analyzes automation results and generates statistics."""
    
    def __init__(self, results: List[Dict]):
        self.results = results
        self.total_runs = len(results)
    
    def calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        if not self.results:
            return 0.0
        successful = sum(1 for r in self.results if r.get("success"))
        return (successful / self.total_runs) * 100
    
    def calculate_average_solve_time(self) -> float:
        """Calculate average solve time for successful runs."""
        solve_times = [r["solve_time"] for r in self.results if r.get("solve_time")]
        if not solve_times:
            return 0.0
        return sum(solve_times) / len(solve_times)
    
    def get_error_distribution(self) -> Dict[str, int]:
        """Get distribution of error types."""
        errors = [r.get("error", "Unknown") for r in self.results if not r.get("success")]
        return dict(Counter(errors))
    
    def get_proxy_performance(self) -> Dict[str, Dict]:
        """Analyze performance by proxy type."""
        proxy_stats = {}
        
        for proxy_type in ["ipv4", "ipv6", None]:
            proxy_results = [r for r in self.results if r.get("proxy_type") == proxy_type]
            if not proxy_results:
                continue
            
            successful = sum(1 for r in proxy_results if r.get("success"))
            total = len(proxy_results)
            solve_times = [r["solve_time"] for r in proxy_results if r.get("solve_time")]
            
            proxy_label = proxy_type or "no_proxy"
            proxy_stats[proxy_label] = {
                "total_runs": total,
                "successful": successful,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "average_solve_time": sum(solve_times) / len(solve_times) if solve_times else 0,
                "min_solve_time": min(solve_times) if solve_times else 0,
                "max_solve_time": max(solve_times) if solve_times else 0
            }
        
        return proxy_stats
    
    def get_time_distribution(self) -> Dict[str, int]:
        """Get distribution of solve times in buckets."""
        solve_times = [r["solve_time"] for r in self.results if r.get("solve_time")]
        
        buckets = {
            "0-5s": 0,
            "5-10s": 0,
            "10-15s": 0,
            "15-20s": 0,
            "20-30s": 0,
            "30s+": 0
        }
        
        for time in solve_times:
            if time < 5:
                buckets["0-5s"] += 1
            elif time < 10:
                buckets["5-10s"] += 1
            elif time < 15:
                buckets["10-15s"] += 1
            elif time < 20:
                buckets["15-20s"] += 1
            elif time < 30:
                buckets["20-30s"] += 1
            else:
                buckets["30s+"] += 1
        
        return buckets
    
    def get_token_statistics(self) -> Dict:
        """Analyze extracted tokens."""
        tokens = [r.get("token") for r in self.results if r.get("token")]
        
        return {
            "total_tokens_extracted": len(tokens),
            "unique_tokens": len(set(tokens)),
            "average_token_length": sum(len(t) for t in tokens) / len(tokens) if tokens else 0,
            "sample_token": tokens[0] if tokens else None
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive statistics report."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_runs": self.total_runs
            },
            "overall_statistics": {
                "success_rate": round(self.calculate_success_rate(), 2),
                "successful_runs": sum(1 for r in self.results if r.get("success")),
                "failed_runs": sum(1 for r in self.results if not r.get("success")),
                "average_solve_time": round(self.calculate_average_solve_time(), 2)
            },
            "proxy_performance": self.get_proxy_performance(),
            "time_distribution": self.get_time_distribution(),
            "error_distribution": self.get_error_distribution(),
            "token_statistics": self.get_token_statistics()
        }
        
        return report
    
    def print_summary(self):
        """Print a formatted summary to console."""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("AUTOMATION STATISTICS SUMMARY")
        print("="*60)
        
        print(f"\nTotal Runs: {report['metadata']['total_runs']}")
        print(f"Generated: {report['metadata']['generated_at']}")
        
        print("\n--- Overall Statistics ---")
        overall = report['overall_statistics']
        print(f"Success Rate: {overall['success_rate']}%")
        print(f"Successful: {overall['successful_runs']}")
        print(f"Failed: {overall['failed_runs']}")
        print(f"Average Solve Time: {overall['average_solve_time']}s")
        
        print("\n--- Proxy Performance ---")
        for proxy_type, stats in report['proxy_performance'].items():
            print(f"\n{proxy_type.upper()}:")
            print(f"  Total Runs: {stats['total_runs']}")
            print(f"  Success Rate: {stats['success_rate']:.2f}%")
            print(f"  Avg Solve Time: {stats['average_solve_time']:.2f}s")
            print(f"  Min/Max Time: {stats['min_solve_time']:.2f}s / {stats['max_solve_time']:.2f}s")
        
        print("\n--- Time Distribution ---")
        for bucket, count in report['time_distribution'].items():
            print(f"{bucket}: {count} runs")
        
        print("\n--- Token Statistics ---")
        token_stats = report['token_statistics']
        print(f"Tokens Extracted: {token_stats['total_tokens_extracted']}")
        print(f"Unique Tokens: {token_stats['unique_tokens']}")
        print(f"Average Token Length: {token_stats['average_token_length']:.0f} chars")
        
        if report['error_distribution']:
            print("\n--- Error Distribution ---")
            for error, count in report['error_distribution'].items():
                print(f"{error}: {count}")
        
        print("\n" + "="*60 + "\n")
    
    def export_to_json(self, output_path: Path):
        """Export report to JSON file."""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Statistics exported to {output_path}")
    
    def export_to_csv(self, output_path: Path):
        """Export results to CSV file."""
        import csv
        
        if not self.results:
            return
        
        fieldnames = ["run", "timestamp", "success", "token", "solve_time", "error", "proxy_type"]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                row = {k: result.get(k, "") for k in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Results exported to CSV: {output_path}")
