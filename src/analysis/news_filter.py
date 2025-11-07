"""
Filtro de Noticias Económicas
Evita operar durante eventos de alto impacto para proteger el capital
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)

class EconomicNewsFilter:
    def __init__(self):
        # Configuración de noticias de alto impacto
        self.high_impact_events = [
            'NFP', 'Non-Farm Payrolls', 'Employment Change',
            'Interest Rate Decision', 'FOMC', 'ECB',
            'GDP', 'CPI', 'Inflation', 'PPI',
            'Retail Sales', 'Industrial Production',
            'PMI', 'ISM', 'Consumer Confidence',
            'Trade Balance', 'Current Account'
        ]
        
        # Ventanas de tiempo para evitar trading (en minutos)
        self.avoid_before = 30  # 30 min antes del evento
        self.avoid_after = 60   # 60 min después del evento
        
        # Cache de noticias
        self.news_cache = []
        self.last_update = None
        self.cache_duration = 3600  # 1 hora
        
    def should_avoid_trading(self, current_time: datetime = None) -> tuple[bool, str]:
        """
        Determinar si se debe evitar el trading por noticias
        Returns: (should_avoid: bool, reason: str)
        """
        try:
            if current_time is None:
                current_time = datetime.utcnow()
            
            # Verificar eventos programados
            upcoming_events = self._get_upcoming_high_impact_events(current_time)
            
            for event in upcoming_events:
                event_time = event['time']
                time_diff = (event_time - current_time).total_seconds() / 60  # en minutos
                
                # Verificar si estamos en la ventana de evitación
                if -self.avoid_after <= time_diff <= self.avoid_before:
                    reason = f"Evento de alto impacto: {event['title']} en {abs(time_diff):.0f} min"
                    return True, reason
            
            # Verificar horarios de alto riesgo
            if self._is_high_risk_time(current_time):
                return True, "Horario de alto riesgo (overlap de sesiones principales)"
            
            return False, "Sin eventos de alto impacto detectados"
            
        except Exception as e:
            logger.error(f"Error verificando filtro de noticias: {e}")
            return False, "Error en filtro de noticias"
    
    def _get_upcoming_high_impact_events(self, current_time: datetime) -> List[Dict]:
        """Obtener eventos de alto impacto próximos"""
        try:
            # Usar cache si está disponible y es reciente
            if (self.last_update and 
                (current_time - self.last_update).total_seconds() < self.cache_duration and
                self.news_cache):
                return self._filter_relevant_events(self.news_cache, current_time)
            
            # Actualizar cache de noticias
            self._update_news_cache(current_time)
            return self._filter_relevant_events(self.news_cache, current_time)
            
        except Exception as e:
            logger.error(f"Error obteniendo eventos económicos: {e}")
            return []
    
    def _update_news_cache(self, current_time: datetime):
        """Actualizar cache de noticias económicas"""
        try:
            # Simulación de eventos económicos importantes
            # En producción, esto se conectaría a una API de noticias económicas
            self.news_cache = [
                {
                    'time': current_time.replace(hour=14, minute=30, second=0, microsecond=0),
                    'title': 'US Non-Farm Payrolls',
                    'impact': 'HIGH',
                    'currency': 'USD'
                },
                {
                    'time': current_time.replace(hour=12, minute=30, second=0, microsecond=0),
                    'title': 'ECB Interest Rate Decision',
                    'impact': 'HIGH',
                    'currency': 'EUR'
                },
                {
                    'time': current_time.replace(hour=8, minute=30, second=0, microsecond=0),
                    'title': 'UK GDP Release',
                    'impact': 'MEDIUM',
                    'currency': 'GBP'
                }
            ]
            
            self.last_update = current_time
            logger.info(f"Cache de noticias actualizado: {len(self.news_cache)} eventos")
            
        except Exception as e:
            logger.error(f"Error actualizando cache de noticias: {e}")
            self.news_cache = []
    
    def _filter_relevant_events(self, events: List[Dict], current_time: datetime) -> List[Dict]:
        """Filtrar eventos relevantes para EUR/USD"""
        try:
            relevant_events = []
            
            for event in events:
                # Solo eventos que afecten EUR o USD
                if event.get('currency') in ['EUR', 'USD']:
                    # Solo eventos de alto impacto
                    if event.get('impact') == 'HIGH':
                        # Solo eventos en las próximas 4 horas
                        time_diff = (event['time'] - current_time).total_seconds() / 3600
                        if -2 <= time_diff <= 4:  # 2 horas atrás a 4 horas adelante
                            relevant_events.append(event)
            
            return relevant_events
            
        except Exception as e:
            logger.error(f"Error filtrando eventos relevantes: {e}")
            return []
    
    def _is_high_risk_time(self, current_time: datetime) -> bool:
        """Verificar si es un horario de alto riesgo"""
        try:
            hour = current_time.hour
            minute = current_time.minute
            weekday = current_time.weekday()
            
            # Evitar viernes tarde (después de las 20:00 UTC)
            if weekday == 4 and hour >= 20:
                return True
            
            # Evitar domingo noche/lunes temprano (gap de apertura)
            if weekday == 6 and hour >= 21:  # Domingo después 21:00
                return True
            if weekday == 0 and hour <= 1:   # Lunes antes 01:00
                return True
            
            # Evitar primeros 15 minutos de cada hora (posibles noticias)
            if minute <= 15:
                # Solo en horarios típicos de noticias
                if hour in [8, 9, 12, 13, 14, 15, 16]:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando horario de alto riesgo: {e}")
            return False
    
    def get_next_safe_time(self, current_time: datetime = None) -> Optional[datetime]:
        """Obtener el próximo momento seguro para operar"""
        try:
            if current_time is None:
                current_time = datetime.utcnow()
            
            # Buscar el próximo momento sin eventos de alto impacto
            check_time = current_time
            max_checks = 48  # Máximo 48 horas hacia adelante
            
            for _ in range(max_checks):
                should_avoid, _ = self.should_avoid_trading(check_time)
                if not should_avoid:
                    return check_time
                
                check_time += timedelta(minutes=30)  # Verificar cada 30 minutos
            
            return None  # No se encontró momento seguro
            
        except Exception as e:
            logger.error(f"Error calculando próximo momento seguro: {e}")
            return None
    
    def get_risk_level(self, current_time: datetime = None) -> str:
        """Obtener nivel de riesgo actual"""
        try:
            should_avoid, reason = self.should_avoid_trading(current_time)
            
            if should_avoid:
                if "alto impacto" in reason.lower():
                    return "VERY_HIGH"
                else:
                    return "HIGH"
            
            if current_time is None:
                current_time = datetime.utcnow()
            
            # Verificar proximidad a eventos
            upcoming_events = self._get_upcoming_high_impact_events(current_time)
            if upcoming_events:
                min_time_diff = min(
                    abs((event['time'] - current_time).total_seconds() / 60)
                    for event in upcoming_events
                )
                
                if min_time_diff <= 60:  # Menos de 1 hora
                    return "MEDIUM"
            
            return "LOW"
            
        except Exception as e:
            logger.error(f"Error calculando nivel de riesgo: {e}")
            return "UNKNOWN"
