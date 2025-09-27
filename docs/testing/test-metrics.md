# Métriques et Mesures de Qualité - Django GraphQL Auto

Ce guide détaille les métriques de test, les indicateurs de qualité, et les stratégies de mesure pour évaluer l'efficacité des tests dans les applications Django GraphQL.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Métriques de Couverture](#métriques-de-couverture)
- [Métriques de Performance](#métriques-de-performance)
- [Métriques de Qualité](#métriques-de-qualité)
- [Métriques GraphQL](#métriques-graphql)
- [Tableaux de Bord](#tableaux-de-bord)
- [Alertes et Seuils](#alertes-et-seuils)
- [Rapports Automatisés](#rapports-automatisés)
- [Analyse Tendancielle](#analyse-tendancielle)

## 🎯 Vue d'Ensemble

### Architecture des Métriques

```python
# tests/metrics/core.py
"""Core des métriques de test."""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import sqlite3
from contextlib import contextmanager
import logging


@dataclass
class TestMetric:
    """Métrique de test individuelle."""
    
    name: str
    value: float
    unit: str
    timestamp: datetime
    test_name: Optional[str] = None
    category: str = "general"
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'test_name': self.test_name,
            'category': self.category,
            'tags': self.tags
        }


@dataclass
class CoverageMetrics:
    """Métriques de couverture de code."""
    
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    class_coverage: float
    file_coverage: float
    total_lines: int
    covered_lines: int
    missing_lines: List[int]
    excluded_lines: List[int]
    
    @property
    def overall_score(self) -> float:
        """Score global de couverture pondéré."""
        return (
            self.line_coverage * 0.4 +
            self.branch_coverage * 0.3 +
            self.function_coverage * 0.2 +
            self.class_coverage * 0.1
        )


@dataclass
class PerformanceMetrics:
    """Métriques de performance."""
    
    execution_time: float
    memory_usage: float
    cpu_usage: float
    database_queries: int
    cache_hits: int
    cache_misses: int
    network_requests: int
    
    @property
    def efficiency_score(self) -> float:
        """Score d'efficacité basé sur les métriques."""
        # Score basé sur des seuils optimaux
        time_score = max(0, 100 - (self.execution_time * 10))
        memory_score = max(0, 100 - (self.memory_usage / 1024 / 1024))  # MB
        query_score = max(0, 100 - (self.database_queries * 5))
        
        return (time_score + memory_score + query_score) / 3


@dataclass
class QualityMetrics:
    """Métriques de qualité de code."""
    
    test_count: int
    assertion_count: int
    complexity_score: float
    maintainability_index: float
    code_duplication: float
    technical_debt_ratio: float
    
    @property
    def quality_score(self) -> float:
        """Score global de qualité."""
        return (
            min(100, self.maintainability_index) * 0.4 +
            max(0, 100 - self.complexity_score * 10) * 0.3 +
            max(0, 100 - self.code_duplication) * 0.2 +
            max(0, 100 - self.technical_debt_ratio * 100) * 0.1
        )


class MetricsCollector:
    """Collecteur de métriques de test."""
    
    def __init__(self, db_path: str = "test_metrics.db"):
        self.db_path = db_path
        self.metrics_buffer = []
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données des métriques."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    test_name TEXT,
                    category TEXT NOT NULL,
                    tags TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name 
                ON metrics(name)
            """)
    
    def record_metric(self, metric: TestMetric):
        """Enregistre une métrique."""
        
        self.metrics_buffer.append(metric)
        
        # Flush périodique
        if len(self.metrics_buffer) >= 100:
            self.flush_metrics()
    
    def flush_metrics(self):
        """Sauvegarde les métriques en attente."""
        
        if not self.metrics_buffer:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for metric in self.metrics_buffer:
                conn.execute("""
                    INSERT INTO metrics 
                    (name, value, unit, timestamp, test_name, category, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.name,
                    metric.value,
                    metric.unit,
                    metric.timestamp.isoformat(),
                    metric.test_name,
                    metric.category,
                    json.dumps(metric.tags)
                ))
        
        self.logger.info(f"Sauvegardé {len(self.metrics_buffer)} métriques")
        self.metrics_buffer.clear()
    
    def get_metrics(self, name: str = None, category: str = None,
                   start_time: datetime = None, end_time: datetime = None) -> List[TestMetric]:
        """Récupère les métriques selon les critères."""
        
        query = "SELECT * FROM metrics WHERE 1=1"
        params = []
        
        if name:
            query += " AND name = ?"
            params.append(name)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            
            metrics = []
            for row in cursor.fetchall():
                metric = TestMetric(
                    name=row[1],
                    value=row[2],
                    unit=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    test_name=row[5],
                    category=row[6],
                    tags=json.loads(row[7]) if row[7] else {}
                )
                metrics.append(metric)
            
            return metrics
    
    @contextmanager
    def measure_execution_time(self, test_name: str):
        """Context manager pour mesurer le temps d'exécution."""
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            self.record_metric(TestMetric(
                name="execution_time",
                value=execution_time,
                unit="seconds",
                timestamp=datetime.now(),
                test_name=test_name,
                category="performance"
            ))
            
            self.record_metric(TestMetric(
                name="memory_usage",
                value=memory_delta,
                unit="bytes",
                timestamp=datetime.now(),
                test_name=test_name,
                category="performance"
            ))


class CoverageAnalyzer:
    """Analyseur de couverture de code."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    def analyze_coverage(self, coverage_data: Dict[str, Any]) -> CoverageMetrics:
        """Analyse les données de couverture."""
        
        totals = coverage_data.get('totals', {})
        
        metrics = CoverageMetrics(
            line_coverage=totals.get('percent_covered', 0.0),
            branch_coverage=totals.get('percent_covered_display', 0.0),
            function_coverage=self._calculate_function_coverage(coverage_data),
            class_coverage=self._calculate_class_coverage(coverage_data),
            file_coverage=self._calculate_file_coverage(coverage_data),
            total_lines=totals.get('num_statements', 0),
            covered_lines=totals.get('covered_lines', 0),
            missing_lines=totals.get('missing_lines', []),
            excluded_lines=totals.get('excluded_lines', [])
        )
        
        # Enregistrer les métriques
        self._record_coverage_metrics(metrics)
        
        return metrics
    
    def _calculate_function_coverage(self, coverage_data: Dict[str, Any]) -> float:
        """Calcule la couverture des fonctions."""
        
        files = coverage_data.get('files', {})
        total_functions = 0
        covered_functions = 0
        
        for file_data in files.values():
            # Analyser les fonctions dans le fichier
            # (implémentation simplifiée)
            functions = file_data.get('summary', {}).get('num_statements', 0) // 10
            covered = file_data.get('summary', {}).get('covered_lines', 0) // 10
            
            total_functions += functions
            covered_functions += min(covered, functions)
        
        return (covered_functions / total_functions * 100) if total_functions > 0 else 0.0
    
    def _calculate_class_coverage(self, coverage_data: Dict[str, Any]) -> float:
        """Calcule la couverture des classes."""
        
        # Implémentation similaire pour les classes
        return 85.0  # Placeholder
    
    def _calculate_file_coverage(self, coverage_data: Dict[str, Any]) -> float:
        """Calcule la couverture des fichiers."""
        
        files = coverage_data.get('files', {})
        if not files:
            return 0.0
        
        covered_files = sum(
            1 for file_data in files.values()
            if file_data.get('summary', {}).get('percent_covered', 0) > 0
        )
        
        return (covered_files / len(files)) * 100
    
    def _record_coverage_metrics(self, metrics: CoverageMetrics):
        """Enregistre les métriques de couverture."""
        
        timestamp = datetime.now()
        
        coverage_metrics = [
            TestMetric("line_coverage", metrics.line_coverage, "percent", timestamp, category="coverage"),
            TestMetric("branch_coverage", metrics.branch_coverage, "percent", timestamp, category="coverage"),
            TestMetric("function_coverage", metrics.function_coverage, "percent", timestamp, category="coverage"),
            TestMetric("class_coverage", metrics.class_coverage, "percent", timestamp, category="coverage"),
            TestMetric("file_coverage", metrics.file_coverage, "percent", timestamp, category="coverage"),
            TestMetric("overall_coverage_score", metrics.overall_score, "score", timestamp, category="coverage")
        ]
        
        for metric in coverage_metrics:
            self.metrics_collector.record_metric(metric)


class PerformanceAnalyzer:
    """Analyseur de performance."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.query_count = 0
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    @contextmanager
    def measure_performance(self, test_name: str):
        """Context manager pour mesurer les performances."""
        
        # Réinitialiser les compteurs
        self.query_count = 0
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # Mesures initiales
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_cpu_time = process.cpu_times()
        
        try:
            yield self
        finally:
            # Mesures finales
            end_time = time.time()
            end_memory = process.memory_info().rss
            end_cpu_time = process.cpu_times()
            
            # Calculer les métriques
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = (end_cpu_time.user - start_cpu_time.user) + (end_cpu_time.system - start_cpu_time.system)
            
            metrics = PerformanceMetrics(
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                database_queries=self.query_count,
                cache_hits=self.cache_stats['hits'],
                cache_misses=self.cache_stats['misses'],
                network_requests=0  # À implémenter selon les besoins
            )
            
            self._record_performance_metrics(metrics, test_name)
    
    def record_database_query(self):
        """Enregistre une requête base de données."""
        self.query_count += 1
    
    def record_cache_hit(self):
        """Enregistre un hit de cache."""
        self.cache_stats['hits'] += 1
    
    def record_cache_miss(self):
        """Enregistre un miss de cache."""
        self.cache_stats['misses'] += 1
    
    def _record_performance_metrics(self, metrics: PerformanceMetrics, test_name: str):
        """Enregistre les métriques de performance."""
        
        timestamp = datetime.now()
        
        performance_metrics = [
            TestMetric("execution_time", metrics.execution_time, "seconds", timestamp, test_name, "performance"),
            TestMetric("memory_usage", metrics.memory_usage, "bytes", timestamp, test_name, "performance"),
            TestMetric("cpu_usage", metrics.cpu_usage, "seconds", timestamp, test_name, "performance"),
            TestMetric("database_queries", metrics.database_queries, "count", timestamp, test_name, "performance"),
            TestMetric("cache_hits", metrics.cache_hits, "count", timestamp, test_name, "performance"),
            TestMetric("cache_misses", metrics.cache_misses, "count", timestamp, test_name, "performance"),
            TestMetric("efficiency_score", metrics.efficiency_score, "score", timestamp, test_name, "performance")
        ]
        
        for metric in performance_metrics:
            self.metrics_collector.record_metric(metric)


class GraphQLMetricsAnalyzer:
    """Analyseur de métriques spécifiques à GraphQL."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    def analyze_schema_generation(self, schema_size: int, generation_time: float, 
                                 complexity_score: float):
        """Analyse la génération de schéma GraphQL."""
        
        timestamp = datetime.now()
        
        metrics = [
            TestMetric("schema_size", schema_size, "types", timestamp, category="graphql"),
            TestMetric("schema_generation_time", generation_time, "seconds", timestamp, category="graphql"),
            TestMetric("schema_complexity", complexity_score, "score", timestamp, category="graphql")
        ]
        
        for metric in metrics:
            self.metrics_collector.record_metric(metric)
    
    def analyze_query_execution(self, query: str, execution_time: float,
                               resolver_calls: int, field_count: int):
        """Analyse l'exécution de requête GraphQL."""
        
        timestamp = datetime.now()
        query_complexity = self._calculate_query_complexity(query)
        
        metrics = [
            TestMetric("query_execution_time", execution_time, "seconds", timestamp, category="graphql"),
            TestMetric("resolver_calls", resolver_calls, "count", timestamp, category="graphql"),
            TestMetric("query_field_count", field_count, "count", timestamp, category="graphql"),
            TestMetric("query_complexity", query_complexity, "score", timestamp, category="graphql")
        ]
        
        for metric in metrics:
            self.metrics_collector.record_metric(metric)
    
    def _calculate_query_complexity(self, query: str) -> float:
        """Calcule la complexité d'une requête GraphQL."""
        
        # Analyse simplifiée de la complexité
        depth = query.count('{')
        field_count = query.count('\n')
        fragments = query.count('fragment')
        
        complexity = depth * 2 + field_count * 0.5 + fragments * 3
        return min(complexity, 100.0)  # Normaliser à 100


class QualityAnalyzer:
    """Analyseur de qualité de code."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    def analyze_test_quality(self, test_files: List[Path]) -> QualityMetrics:
        """Analyse la qualité des tests."""
        
        total_tests = 0
        total_assertions = 0
        complexity_scores = []
        
        for test_file in test_files:
            if test_file.exists():
                content = test_file.read_text()
                
                # Compter les tests et assertions
                test_count = content.count('def test_')
                assertion_count = content.count('assert')
                
                total_tests += test_count
                total_assertions += assertion_count
                
                # Calculer la complexité (métrique simplifiée)
                complexity = self._calculate_file_complexity(content)
                complexity_scores.append(complexity)
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        metrics = QualityMetrics(
            test_count=total_tests,
            assertion_count=total_assertions,
            complexity_score=avg_complexity,
            maintainability_index=self._calculate_maintainability_index(test_files),
            code_duplication=self._calculate_duplication_ratio(test_files),
            technical_debt_ratio=self._calculate_technical_debt(test_files)
        )
        
        self._record_quality_metrics(metrics)
        
        return metrics
    
    def _calculate_file_complexity(self, content: str) -> float:
        """Calcule la complexité cyclomatique d'un fichier."""
        
        # Compter les structures de contrôle
        control_structures = [
            'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except:', 'with '
        ]
        
        complexity = 1  # Complexité de base
        
        for structure in control_structures:
            complexity += content.count(structure)
        
        return complexity
    
    def _calculate_maintainability_index(self, test_files: List[Path]) -> float:
        """Calcule l'index de maintenabilité."""
        
        # Métrique simplifiée basée sur la taille et la complexité
        total_lines = 0
        total_complexity = 0
        
        for test_file in test_files:
            if test_file.exists():
                content = test_file.read_text()
                lines = len(content.split('\n'))
                complexity = self._calculate_file_complexity(content)
                
                total_lines += lines
                total_complexity += complexity
        
        if total_lines == 0:
            return 100.0
        
        # Formule simplifiée d'index de maintenabilité
        maintainability = 171 - 5.2 * (total_complexity / len(test_files)) - 0.23 * (total_lines / len(test_files))
        
        return max(0, min(100, maintainability))
    
    def _calculate_duplication_ratio(self, test_files: List[Path]) -> float:
        """Calcule le ratio de duplication de code."""
        
        # Implémentation simplifiée
        # Dans un vrai projet, utiliser des outils comme jscpd ou similar
        
        all_lines = []
        
        for test_file in test_files:
            if test_file.exists():
                content = test_file.read_text()
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                all_lines.extend(lines)
        
        if not all_lines:
            return 0.0
        
        unique_lines = set(all_lines)
        duplication_ratio = (len(all_lines) - len(unique_lines)) / len(all_lines) * 100
        
        return duplication_ratio
    
    def _calculate_technical_debt(self, test_files: List[Path]) -> float:
        """Calcule le ratio de dette technique."""
        
        debt_indicators = [
            'TODO', 'FIXME', 'HACK', 'XXX', 'BUG', 'TEMP'
        ]
        
        total_lines = 0
        debt_lines = 0
        
        for test_file in test_files:
            if test_file.exists():
                content = test_file.read_text()
                lines = content.split('\n')
                total_lines += len(lines)
                
                for line in lines:
                    if any(indicator in line.upper() for indicator in debt_indicators):
                        debt_lines += 1
        
        if total_lines == 0:
            return 0.0
        
        return (debt_lines / total_lines) * 100
    
    def _record_quality_metrics(self, metrics: QualityMetrics):
        """Enregistre les métriques de qualité."""
        
        timestamp = datetime.now()
        
        quality_metrics = [
            TestMetric("test_count", metrics.test_count, "count", timestamp, category="quality"),
            TestMetric("assertion_count", metrics.assertion_count, "count", timestamp, category="quality"),
            TestMetric("complexity_score", metrics.complexity_score, "score", timestamp, category="quality"),
            TestMetric("maintainability_index", metrics.maintainability_index, "score", timestamp, category="quality"),
            TestMetric("code_duplication", metrics.code_duplication, "percent", timestamp, category="quality"),
            TestMetric("technical_debt_ratio", metrics.technical_debt_ratio, "percent", timestamp, category="quality"),
            TestMetric("overall_quality_score", metrics.quality_score, "score", timestamp, category="quality")
        ]
        
        for metric in quality_metrics:
            self.metrics_collector.record_metric(metric)


class MetricsDashboard:
    """Tableau de bord des métriques."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    def generate_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """Génère les données pour le tableau de bord."""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        metrics = self.metrics_collector.get_metrics(
            start_time=start_time,
            end_time=end_time
        )
        
        # Grouper par catégorie
        categories = {}
        for metric in metrics:
            if metric.category not in categories:
                categories[metric.category] = []
            categories[metric.category].append(metric)
        
        dashboard_data = {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days
            },
            'summary': self._generate_summary(metrics),
            'trends': self._generate_trends(categories),
            'alerts': self._generate_alerts(metrics),
            'top_metrics': self._get_top_metrics(metrics)
        }
        
        return dashboard_data
    
    def _generate_summary(self, metrics: List[TestMetric]) -> Dict[str, Any]:
        """Génère un résumé des métriques."""
        
        if not metrics:
            return {}
        
        # Dernières valeurs par métrique
        latest_metrics = {}
        for metric in sorted(metrics, key=lambda m: m.timestamp, reverse=True):
            if metric.name not in latest_metrics:
                latest_metrics[metric.name] = metric
        
        # Calculer les moyennes par catégorie
        category_averages = {}
        category_counts = {}
        
        for metric in metrics:
            if metric.category not in category_averages:
                category_averages[metric.category] = 0
                category_counts[metric.category] = 0
            
            category_averages[metric.category] += metric.value
            category_counts[metric.category] += 1
        
        for category in category_averages:
            category_averages[category] /= category_counts[category]
        
        return {
            'total_metrics': len(metrics),
            'unique_metrics': len(latest_metrics),
            'categories': list(category_averages.keys()),
            'category_averages': category_averages,
            'latest_values': {name: metric.value for name, metric in latest_metrics.items()}
        }
    
    def _generate_trends(self, categories: Dict[str, List[TestMetric]]) -> Dict[str, Any]:
        """Génère les tendances par catégorie."""
        
        trends = {}
        
        for category, metrics in categories.items():
            if not metrics:
                continue
            
            # Trier par timestamp
            sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
            
            # Calculer la tendance (régression linéaire simple)
            if len(sorted_metrics) >= 2:
                first_value = sorted_metrics[0].value
                last_value = sorted_metrics[-1].value
                
                trend_direction = "stable"
                if last_value > first_value * 1.05:
                    trend_direction = "increasing"
                elif last_value < first_value * 0.95:
                    trend_direction = "decreasing"
                
                trends[category] = {
                    'direction': trend_direction,
                    'change_percent': ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0,
                    'data_points': len(sorted_metrics)
                }
        
        return trends
    
    def _generate_alerts(self, metrics: List[TestMetric]) -> List[Dict[str, Any]]:
        """Génère les alertes basées sur les seuils."""
        
        alerts = []
        
        # Seuils d'alerte
        thresholds = {
            'line_coverage': {'min': 80.0, 'severity': 'warning'},
            'execution_time': {'max': 5.0, 'severity': 'error'},
            'memory_usage': {'max': 100 * 1024 * 1024, 'severity': 'warning'},  # 100MB
            'database_queries': {'max': 10, 'severity': 'warning'},
            'complexity_score': {'max': 10, 'severity': 'error'}
        }
        
        # Vérifier les dernières valeurs
        latest_metrics = {}
        for metric in sorted(metrics, key=lambda m: m.timestamp, reverse=True):
            if metric.name not in latest_metrics:
                latest_metrics[metric.name] = metric
        
        for metric_name, metric in latest_metrics.items():
            if metric_name in thresholds:
                threshold = thresholds[metric_name]
                
                alert = None
                
                if 'min' in threshold and metric.value < threshold['min']:
                    alert = {
                        'metric': metric_name,
                        'value': metric.value,
                        'threshold': threshold['min'],
                        'type': 'below_minimum',
                        'severity': threshold['severity'],
                        'message': f"{metric_name} est en dessous du seuil minimum"
                    }
                
                elif 'max' in threshold and metric.value > threshold['max']:
                    alert = {
                        'metric': metric_name,
                        'value': metric.value,
                        'threshold': threshold['max'],
                        'type': 'above_maximum',
                        'severity': threshold['severity'],
                        'message': f"{metric_name} dépasse le seuil maximum"
                    }
                
                if alert:
                    alerts.append(alert)
        
        return alerts
    
    def _get_top_metrics(self, metrics: List[TestMetric], limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Récupère les métriques les plus importantes."""
        
        # Grouper par nom de métrique
        metric_groups = {}
        for metric in metrics:
            if metric.name not in metric_groups:
                metric_groups[metric.name] = []
            metric_groups[metric.name].append(metric)
        
        # Calculer les statistiques pour chaque métrique
        metric_stats = []
        for name, group in metric_groups.items():
            values = [m.value for m in group]
            
            stats = {
                'name': name,
                'count': len(values),
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'latest': group[-1].value if group else 0,
                'category': group[0].category if group else 'unknown'
            }
            
            metric_stats.append(stats)
        
        # Trier par importance (nombre d'occurrences et variabilité)
        metric_stats.sort(key=lambda x: (x['count'], x['max'] - x['min']), reverse=True)
        
        return {
            'most_frequent': metric_stats[:limit],
            'most_variable': sorted(metric_stats, key=lambda x: x['max'] - x['min'], reverse=True)[:limit],
            'recent_changes': sorted(metric_stats, key=lambda x: abs(x['latest'] - x['average']), reverse=True)[:limit]
        }
    
    def export_dashboard_html(self, dashboard_data: Dict[str, Any], output_file: str):
        """Exporte le tableau de bord en HTML."""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tableau de Bord des Métriques de Test</title>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                               gap: 20px; margin-bottom: 20px; }}
                .metric-card {{ background: white; padding: 20px; border-radius: 10px; 
                              box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
                .metric-label {{ color: #666; margin-bottom: 10px; }}
                .alert {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .alert-error {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
                .alert-warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .trend-up {{ color: #28a745; }}
                .trend-down {{ color: #dc3545; }}
                .trend-stable {{ color: #6c757d; }}
                .chart-container {{ background: white; padding: 20px; border-radius: 10px; 
                                  box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Tableau de Bord des Métriques de Test</h1>
                    <p>Période: {start_date} - {end_date} ({days} jours)</p>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total des Métriques</div>
                        <div class="metric-value">{total_metrics}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Métriques Uniques</div>
                        <div class="metric-value">{unique_metrics}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Catégories</div>
                        <div class="metric-value">{categories_count}</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h2>🚨 Alertes Actives</h2>
                    {alerts_html}
                </div>
                
                <div class="chart-container">
                    <h2>📈 Tendances par Catégorie</h2>
                    {trends_html}
                </div>
                
                <div class="chart-container">
                    <h2>🏆 Métriques les Plus Importantes</h2>
                    {top_metrics_html}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Générer le contenu des alertes
        alerts_html = ""
        for alert in dashboard_data.get('alerts', []):
            alert_class = f"alert-{alert['severity']}"
            alerts_html += f"""
                <div class="alert {alert_class}">
                    <strong>{alert['metric']}</strong>: {alert['message']} 
                    (Valeur: {alert['value']}, Seuil: {alert['threshold']})
                </div>
            """
        
        if not alerts_html:
            alerts_html = "<p>✅ Aucune alerte active</p>"
        
        # Générer le contenu des tendances
        trends_html = ""
        for category, trend in dashboard_data.get('trends', {}).items():
            direction_class = f"trend-{trend['direction'].replace('ing', '')}"
            direction_icon = {
                'increasing': '📈',
                'decreasing': '📉',
                'stable': '➡️'
            }.get(trend['direction'], '➡️')
            
            trends_html += f"""
                <div style="margin: 10px 0;">
                    <strong>{category}</strong>: 
                    <span class="{direction_class}">
                        {direction_icon} {trend['direction']} 
                        ({trend['change_percent']:+.1f}%)
                    </span>
                </div>
            """
        
        # Générer le contenu des top métriques
        top_metrics_html = ""
        for metric in dashboard_data.get('top_metrics', {}).get('most_frequent', [])[:5]:
            top_metrics_html += f"""
                <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                    <strong>{metric['name']}</strong> ({metric['category']})<br>
                    Moyenne: {metric['average']:.2f}, Min: {metric['min']:.2f}, Max: {metric['max']:.2f}
                </div>
            """
        
        # Remplir le template
        summary = dashboard_data.get('summary', {})
        period = dashboard_data.get('period', {})
        
        html_content = html_template.format(
            start_date=period.get('start', ''),
            end_date=period.get('end', ''),
            days=period.get('days', 0),
            total_metrics=summary.get('total_metrics', 0),
            unique_metrics=summary.get('unique_metrics', 0),
            categories_count=len(summary.get('categories', [])),
            alerts_html=alerts_html,
            trends_html=trends_html,
            top_metrics_html=top_metrics_html
        )
        
        # Sauvegarder le fichier
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


# Exemple d'utilisation intégrée
class TestMetricsIntegration:
    """Intégration des métriques dans les tests."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.coverage_analyzer = CoverageAnalyzer(self.metrics_collector)
        self.performance_analyzer = PerformanceAnalyzer(self.metrics_collector)
        self.graphql_analyzer = GraphQLMetricsAnalyzer(self.metrics_collector)
        self.quality_analyzer = QualityAnalyzer(self.metrics_collector)
        self.dashboard = MetricsDashboard(self.metrics_collector)
    
    def setup_test_metrics(self):
        """Configure les métriques pour les tests."""
        
        # Hook pour pytest
        import pytest
        
        @pytest.fixture(autouse=True)
        def measure_test_performance(request):
            test_name = request.node.name
            
            with self.performance_analyzer.measure_performance(test_name):
                yield
        
        return self
    
    def generate_metrics_report(self, output_dir: str = "metrics_reports"):
        """Génère un rapport complet des métriques."""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Générer le tableau de bord
        dashboard_data = self.dashboard.generate_dashboard_data()
        
        # Exporter en HTML
        html_file = Path(output_dir) / "metrics_dashboard.html"
        self.dashboard.export_dashboard_html(dashboard_data, str(html_file))
        
        # Exporter en JSON
        json_file = Path(output_dir) / "metrics_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        print(f"Rapport des métriques généré dans {output_dir}")
        
        return dashboard_data


# Exemple d'utilisation
def example_usage():
    """Exemple d'utilisation des métriques de test."""
    
    # Initialiser l'intégration des métriques
    metrics_integration = TestMetricsIntegration()
    
    # Configurer pour les tests
    metrics_integration.setup_test_metrics()
    
    # Simuler quelques métriques
    collector = metrics_integration.metrics_collector
    
    # Métriques de performance
    with collector.measure_execution_time("test_example"):
        time.sleep(0.1)  # Simuler un test
    
    # Métriques GraphQL
    metrics_integration.graphql_analyzer.analyze_schema_generation(
        schema_size=50,
        generation_time=0.5,
        complexity_score=7.2
    )
    
    # Générer le rapport
    metrics_integration.generate_metrics_report()
```

Ce guide des métriques et mesures de qualité fournit une infrastructure complète pour surveiller, analyser et améliorer la qualité des tests dans le projet Django GraphQL Auto.