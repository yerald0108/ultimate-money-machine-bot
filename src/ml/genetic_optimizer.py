"""
Optimizador Genético para Estrategias de Trading
Evoluciona parámetros de estrategias automáticamente
"""

import logging
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import copy

logger = logging.getLogger(__name__)

class GeneticOptimizer:
    def __init__(self):
        # Configuración del algoritmo genético
        self.population_size = 20
        self.mutation_rate = 0.15
        self.crossover_rate = 0.8
        self.elite_size = 4  # Mejores individuos que pasan directamente
        self.max_generations = 50
        
        # Población actual
        self.population = []
        self.fitness_scores = []
        self.generation = 0
        self.best_individual = None
        self.best_fitness = -float('inf')
        
        # Historial de evolución
        self.evolution_history = []
        
        # Parámetros a optimizar (genes)
        self.gene_definitions = {
            'rsi_oversold': {'min': 20, 'max': 35, 'type': 'int'},
            'rsi_overbought': {'min': 65, 'max': 80, 'type': 'int'},
            'macd_threshold': {'min': 0.00005, 'max': 0.0005, 'type': 'float'},
            'bb_squeeze_threshold': {'min': 0.01, 'max': 0.05, 'type': 'float'},
            'atr_multiplier': {'min': 1.0, 'max': 3.0, 'type': 'float'},
            'ema_fast': {'min': 8, 'max': 21, 'type': 'int'},
            'ema_slow': {'min': 21, 'max': 55, 'type': 'int'},
            'adx_threshold': {'min': 20, 'max': 35, 'type': 'int'},
            'volume_threshold': {'min': 1.2, 'max': 2.5, 'type': 'float'},
            'min_confidence': {'min': 65, 'max': 85, 'type': 'int'},
            'risk_reward_ratio': {'min': 1.5, 'max': 3.0, 'type': 'float'},
            'stop_loss_atr': {'min': 1.0, 'max': 2.5, 'type': 'float'},
            'take_profit_atr': {'min': 2.0, 'max': 4.0, 'type': 'float'}
        }
        
    def initialize_population(self):
        """Inicializar población aleatoria"""
        try:
            self.population = []
            
            for _ in range(self.population_size):
                individual = {}
                
                for gene_name, gene_def in self.gene_definitions.items():
                    if gene_def['type'] == 'int':
                        value = random.randint(gene_def['min'], gene_def['max'])
                    else:  # float
                        value = random.uniform(gene_def['min'], gene_def['max'])
                    
                    individual[gene_name] = value
                
                self.population.append(individual)
            
            self.fitness_scores = [0.0] * self.population_size
            logger.info(f"🧬 Población genética inicializada: {self.population_size} individuos")
            
        except Exception as e:
            logger.error(f"Error inicializando población genética: {e}")
    
    def evaluate_fitness(self, individual: Dict, trade_results: List[Dict]) -> float:
        """Evaluar fitness de un individuo basado en resultados de trading"""
        try:
            if not trade_results:
                return 0.0
            
            # Métricas de rendimiento
            total_trades = len(trade_results)
            winning_trades = sum(1 for trade in trade_results if trade.get('profit', 0) > 0)
            total_profit = sum(trade.get('profit', 0) for trade in trade_results)
            
            if total_trades == 0:
                return 0.0
            
            # Calcular métricas
            win_rate = winning_trades / total_trades
            avg_profit = total_profit / total_trades
            
            # Calcular drawdown máximo
            cumulative_profit = 0
            peak = 0
            max_drawdown = 0
            
            for trade in trade_results:
                cumulative_profit += trade.get('profit', 0)
                if cumulative_profit > peak:
                    peak = cumulative_profit
                drawdown = peak - cumulative_profit
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Calcular Sharpe ratio simplificado
            profits = [trade.get('profit', 0) for trade in trade_results]
            if len(profits) > 1:
                profit_std = np.std(profits)
                sharpe_ratio = (avg_profit / profit_std) if profit_std > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Función de fitness compuesta
            fitness = (
                win_rate * 40 +  # 40% peso para win rate
                (total_profit / max(1, abs(max_drawdown))) * 30 +  # 30% profit/drawdown ratio
                sharpe_ratio * 20 +  # 20% Sharpe ratio
                min(total_trades / 50, 1.0) * 10  # 10% número de trades (hasta 50)
            )
            
            # Penalizar parámetros extremos
            penalty = self._calculate_parameter_penalty(individual)
            fitness -= penalty
            
            return max(0, fitness)
            
        except Exception as e:
            logger.error(f"Error evaluando fitness: {e}")
            return 0.0
    
    def _calculate_parameter_penalty(self, individual: Dict) -> float:
        """Calcular penalización por parámetros extremos"""
        try:
            penalty = 0.0
            
            # Penalizar configuraciones ilógicas
            if individual.get('rsi_oversold', 30) >= individual.get('rsi_overbought', 70):
                penalty += 20  # RSI oversold debe ser menor que overbought
            
            if individual.get('ema_fast', 12) >= individual.get('ema_slow', 26):
                penalty += 15  # EMA rápida debe ser menor que lenta
            
            if individual.get('stop_loss_atr', 1.5) >= individual.get('take_profit_atr', 3.0):
                penalty += 10  # SL debe ser menor que TP
            
            # Penalizar valores muy extremos
            for gene_name, value in individual.items():
                gene_def = self.gene_definitions.get(gene_name, {})
                if gene_def:
                    min_val = gene_def['min']
                    max_val = gene_def['max']
                    range_val = max_val - min_val
                    
                    # Penalizar si está en el 10% extremo
                    if value <= min_val + range_val * 0.1 or value >= max_val - range_val * 0.1:
                        penalty += 2
            
            return penalty
            
        except Exception as e:
            logger.error(f"Error calculando penalización: {e}")
            return 0.0
    
    def selection(self) -> List[Dict]:
        """Selección por torneo"""
        try:
            selected = []
            tournament_size = 3
            
            for _ in range(self.population_size - self.elite_size):
                # Torneo
                tournament_indices = random.sample(range(len(self.population)), tournament_size)
                tournament_fitness = [self.fitness_scores[i] for i in tournament_indices]
                
                # Seleccionar el mejor del torneo
                winner_idx = tournament_indices[np.argmax(tournament_fitness)]
                selected.append(copy.deepcopy(self.population[winner_idx]))
            
            return selected
            
        except Exception as e:
            logger.error(f"Error en selección genética: {e}")
            return self.population[:self.population_size - self.elite_size]
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """Cruzamiento de dos padres"""
        try:
            if random.random() > self.crossover_rate:
                return copy.deepcopy(parent1), copy.deepcopy(parent2)
            
            child1 = copy.deepcopy(parent1)
            child2 = copy.deepcopy(parent2)
            
            # Cruzamiento uniforme
            for gene_name in self.gene_definitions.keys():
                if random.random() < 0.5:
                    child1[gene_name], child2[gene_name] = child2[gene_name], child1[gene_name]
            
            return child1, child2
            
        except Exception as e:
            logger.error(f"Error en cruzamiento: {e}")
            return parent1, parent2
    
    def mutate(self, individual: Dict) -> Dict:
        """Mutación de un individuo"""
        try:
            mutated = copy.deepcopy(individual)
            
            for gene_name, gene_def in self.gene_definitions.items():
                if random.random() < self.mutation_rate:
                    if gene_def['type'] == 'int':
                        # Mutación gaussiana para enteros
                        current_value = mutated[gene_name]
                        mutation_range = (gene_def['max'] - gene_def['min']) * 0.1
                        new_value = int(current_value + random.gauss(0, mutation_range))
                        new_value = max(gene_def['min'], min(gene_def['max'], new_value))
                        mutated[gene_name] = new_value
                    else:
                        # Mutación gaussiana para floats
                        current_value = mutated[gene_name]
                        mutation_range = (gene_def['max'] - gene_def['min']) * 0.1
                        new_value = current_value + random.gauss(0, mutation_range)
                        new_value = max(gene_def['min'], min(gene_def['max'], new_value))
                        mutated[gene_name] = new_value
            
            return mutated
            
        except Exception as e:
            logger.error(f"Error en mutación: {e}")
            return individual
    
    def evolve_generation(self, trade_results_per_individual: List[List[Dict]]):
        """Evolucionar una generación"""
        try:
            # Evaluar fitness de toda la población
            for i, individual in enumerate(self.population):
                trade_results = trade_results_per_individual[i] if i < len(trade_results_per_individual) else []
                self.fitness_scores[i] = self.evaluate_fitness(individual, trade_results)
            
            # Actualizar mejor individuo
            best_idx = np.argmax(self.fitness_scores)
            if self.fitness_scores[best_idx] > self.best_fitness:
                self.best_fitness = self.fitness_scores[best_idx]
                self.best_individual = copy.deepcopy(self.population[best_idx])
            
            # Guardar estadísticas de la generación
            generation_stats = {
                'generation': self.generation,
                'best_fitness': max(self.fitness_scores),
                'avg_fitness': np.mean(self.fitness_scores),
                'worst_fitness': min(self.fitness_scores),
                'std_fitness': np.std(self.fitness_scores)
            }
            self.evolution_history.append(generation_stats)
            
            # Selección de élite
            elite_indices = np.argsort(self.fitness_scores)[-self.elite_size:]
            elite = [copy.deepcopy(self.population[i]) for i in elite_indices]
            
            # Selección, cruzamiento y mutación
            selected = self.selection()
            new_population = elite.copy()
            
            # Generar nueva población
            while len(new_population) < self.population_size:
                if len(selected) >= 2:
                    parent1 = random.choice(selected)
                    parent2 = random.choice(selected)
                    
                    child1, child2 = self.crossover(parent1, parent2)
                    child1 = self.mutate(child1)
                    child2 = self.mutate(child2)
                    
                    new_population.append(child1)
                    if len(new_population) < self.population_size:
                        new_population.append(child2)
                else:
                    # Si no hay suficientes seleccionados, generar aleatoriamente
                    new_individual = {}
                    for gene_name, gene_def in self.gene_definitions.items():
                        if gene_def['type'] == 'int':
                            value = random.randint(gene_def['min'], gene_def['max'])
                        else:
                            value = random.uniform(gene_def['min'], gene_def['max'])
                        new_individual[gene_name] = value
                    new_population.append(new_individual)
            
            self.population = new_population[:self.population_size]
            self.generation += 1
            
            logger.info(f"🧬 Generación {self.generation}: Mejor fitness = {generation_stats['best_fitness']:.2f}")
            
        except Exception as e:
            logger.error(f"Error evolucionando generación: {e}")
    
    def get_best_parameters(self) -> Dict:
        """Obtener mejores parámetros encontrados"""
        return copy.deepcopy(self.best_individual) if self.best_individual else {}
    
    def get_evolution_statistics(self) -> Dict:
        """Obtener estadísticas de evolución"""
        try:
            if not self.evolution_history:
                return {}
            
            best_fitnesses = [gen['best_fitness'] for gen in self.evolution_history]
            avg_fitnesses = [gen['avg_fitness'] for gen in self.evolution_history]
            
            return {
                'total_generations': len(self.evolution_history),
                'best_fitness_ever': max(best_fitnesses) if best_fitnesses else 0,
                'current_best_fitness': best_fitnesses[-1] if best_fitnesses else 0,
                'fitness_improvement': best_fitnesses[-1] - best_fitnesses[0] if len(best_fitnesses) > 1 else 0,
                'convergence_rate': self._calculate_convergence_rate(),
                'population_diversity': self._calculate_population_diversity(),
                'evolution_history': self.evolution_history[-10:]  # Últimas 10 generaciones
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de evolución: {e}")
            return {}
    
    def _calculate_convergence_rate(self) -> float:
        """Calcular tasa de convergencia"""
        try:
            if len(self.evolution_history) < 5:
                return 0.0
            
            recent_best = [gen['best_fitness'] for gen in self.evolution_history[-5:]]
            improvement = max(recent_best) - min(recent_best)
            
            return improvement / 5  # Mejora promedio por generación
            
        except Exception as e:
            logger.error(f"Error calculando convergencia: {e}")
            return 0.0
    
    def _calculate_population_diversity(self) -> float:
        """Calcular diversidad de la población"""
        try:
            if not self.population:
                return 0.0
            
            # Calcular diversidad basada en diferencias en parámetros
            total_diversity = 0.0
            comparisons = 0
            
            for i in range(len(self.population)):
                for j in range(i + 1, len(self.population)):
                    individual1 = self.population[i]
                    individual2 = self.population[j]
                    
                    diversity = 0.0
                    for gene_name in self.gene_definitions.keys():
                        val1 = individual1.get(gene_name, 0)
                        val2 = individual2.get(gene_name, 0)
                        gene_def = self.gene_definitions[gene_name]
                        
                        # Normalizar diferencia
                        range_val = gene_def['max'] - gene_def['min']
                        normalized_diff = abs(val1 - val2) / range_val if range_val > 0 else 0
                        diversity += normalized_diff
                    
                    total_diversity += diversity / len(self.gene_definitions)
                    comparisons += 1
            
            return total_diversity / comparisons if comparisons > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando diversidad: {e}")
            return 0.0
    
    def save_evolution_state(self, filepath: str):
        """Guardar estado de evolución"""
        try:
            import json
            
            state = {
                'population': self.population,
                'fitness_scores': self.fitness_scores,
                'generation': self.generation,
                'best_individual': self.best_individual,
                'best_fitness': self.best_fitness,
                'evolution_history': self.evolution_history,
                'gene_definitions': self.gene_definitions
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            logger.info(f"Estado de evolución guardado en: {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando estado de evolución: {e}")
    
    def load_evolution_state(self, filepath: str):
        """Cargar estado de evolución"""
        try:
            import json
            
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.population = state.get('population', [])
            self.fitness_scores = state.get('fitness_scores', [])
            self.generation = state.get('generation', 0)
            self.best_individual = state.get('best_individual')
            self.best_fitness = state.get('best_fitness', -float('inf'))
            self.evolution_history = state.get('evolution_history', [])
            
            logger.info(f"Estado de evolución cargado desde: {filepath}")
            
        except Exception as e:
            logger.error(f"Error cargando estado de evolución: {e}")
    
    def reset_evolution(self):
        """Reiniciar evolución"""
        try:
            self.population = []
            self.fitness_scores = []
            self.generation = 0
            self.best_individual = None
            self.best_fitness = -float('inf')
            self.evolution_history = []
            
            logger.info("🧬 Evolución genética reiniciada")
            
        except Exception as e:
            logger.error(f"Error reiniciando evolución: {e}")
    
    def suggest_parameter_ranges(self, current_performance: Dict) -> Dict:
        """Sugerir nuevos rangos de parámetros basado en rendimiento"""
        try:
            suggestions = {}
            
            if not self.best_individual:
                return suggestions
            
            # Analizar parámetros del mejor individuo
            for gene_name, best_value in self.best_individual.items():
                gene_def = self.gene_definitions[gene_name]
                current_range = gene_def['max'] - gene_def['min']
                
                # Sugerir rango más estrecho alrededor del mejor valor
                new_range = current_range * 0.3  # 30% del rango original
                new_min = max(gene_def['min'], best_value - new_range / 2)
                new_max = min(gene_def['max'], best_value + new_range / 2)
                
                suggestions[gene_name] = {
                    'current_best': best_value,
                    'suggested_min': new_min,
                    'suggested_max': new_max,
                    'confidence': min(100, self.best_fitness * 2)  # Confianza basada en fitness
                }
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error sugiriendo rangos de parámetros: {e}")
            return {}
    
    def get_optimization_summary(self) -> Dict:
        """Obtener resumen de optimización"""
        try:
            return {
                'optimizer_type': 'Genetic Algorithm',
                'population_size': self.population_size,
                'current_generation': self.generation,
                'total_parameters': len(self.gene_definitions),
                'best_fitness': self.best_fitness,
                'convergence_status': 'converged' if self._calculate_convergence_rate() < 0.1 else 'evolving',
                'population_diversity': self._calculate_population_diversity(),
                'optimization_progress': min(100, (self.generation / self.max_generations) * 100)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de optimización: {e}")
            return {'error': str(e)}
