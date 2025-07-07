import datetime
import pytz
import json
from typing import Dict, List, Optional
from dataclasses import asdict
from .news_risk_manager import EconomicEvent, EventImpact, EventCategory


class EconomicCalendarAPI:
    
    def __init__(self):
        self.api_endpoints = {
            'forexfactory': 'https://nfs.faireconomy.media/ff_calendar_thisweek.json',
            # 'fxstreet': 'https://calendar.fxstreet.com/eventapi/calendar',
            'investing': 'https://www.investing.com/economic-calendar/',
            'marketwatch': 'https://www.marketwatch.com/economy-politics/calendar'
        }
        
        self.currency_mapping = {
            'USD': ['United States', 'US', 'USA'],
            'EUR': ['European Union', 'EU', 'Eurozone', 'Germany', 'France'],
            'GBP': ['United Kingdom', 'UK', 'Britain'],
            'JPY': ['Japan', 'JP'],
            'CHF': ['Switzerland', 'CH'],
            'CAD': ['Canada', 'CA'],
            'AUD': ['Australia', 'AU'],
            'NZD': ['New Zealand', 'NZ']
        }
        
        self.event_impact_keywords = {
            EventImpact.EXTREME: [
                'Interest Rate Decision', 'Federal Reserve', 'ECB Rate', 'BoE Rate',
                'BoJ Rate', 'FOMC', 'Monetary Policy', 'Central Bank'
            ],
            EventImpact.HIGH: [
                'Non-Farm Payrolls', 'NFP', 'CPI', 'Inflation', 'GDP',
                'Employment', 'Unemployment Rate', 'Retail Sales',
                'Industrial Production', 'Trade Balance'
            ],
            EventImpact.MEDIUM: [
                'PMI', 'Consumer Confidence', 'Housing', 'Durable Goods',
                'Factory Orders', 'Business Confidence', 'Current Account'
            ],
            EventImpact.LOW: [
                'Speeches', 'Testimony', 'Minutes', 'Building Permits',
                'Existing Home Sales', 'Leading Indicators'
            ]
        }
    
    def parse_currency_from_country(self, country: str) -> str:
        for currency, countries in self.currency_mapping.items():
            if any(c.lower() in country.lower() for c in countries):
                return currency
        return 'USD'  # Default to USD if not found
    
    def classify_event_impact(self, event_name: str, description: str = "") -> EventImpact:
        text = f"{event_name} {description}".lower()
        
        for impact, keywords in self.event_impact_keywords.items():
            if any(keyword.lower() in text for keyword in keywords):
                return impact
        
        return EventImpact.LOW
    
    def classify_event_category(self, event_name: str) -> EventCategory:
        name_lower = event_name.lower()
        
        if any(word in name_lower for word in ['rate', 'interest', 'monetary', 'fomc', 'ecb', 'boe', 'boj']):
            return EventCategory.INTEREST_RATE
        elif any(word in name_lower for word in ['employment', 'payroll', 'unemployment', 'jobs']):
            return EventCategory.EMPLOYMENT
        elif any(word in name_lower for word in ['cpi', 'inflation', 'ppi', 'price']):
            return EventCategory.INFLATION
        elif any(word in name_lower for word in ['gdp', 'growth', 'economic']):
            return EventCategory.GDP
        elif any(word in name_lower for word in ['pmi', 'manufacturing', 'services']):
            return EventCategory.PMI
        elif any(word in name_lower for word in ['retail', 'sales', 'consumer']):
            return EventCategory.RETAIL_SALES
        elif any(word in name_lower for word in ['trade', 'balance', 'export', 'import']):
            return EventCategory.TRADE_BALANCE
        elif any(word in name_lower for word in ['fed', 'central', 'bank', 'speech', 'testimony']):
            return EventCategory.CENTRAL_BANK
        else:
            return EventCategory.CENTRAL_BANK
    
    def create_sample_calendar_data(self) -> List[Dict]:
        base_date = datetime.datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        
        sample_events = [
            {
                'date': (base_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '13:30',
                'timezone': 'GMT',
                'currency': 'USD',
                'event': 'Non-Farm Payrolls',
                'importance': 'High',
                'actual': '',
                'forecast': '180K',
                'previous': '199K'
            },
            {
                'date': (base_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '14:00',
                'timezone': 'GMT',
                'currency': 'USD',
                'event': 'Federal Reserve Interest Rate Decision',
                'importance': 'High',
                'actual': '',
                'forecast': '5.25%',
                'previous': '5.00%'
            },
            {
                'date': (base_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                'time': '09:30',
                'timezone': 'GMT',
                'currency': 'GBP',
                'event': 'UK CPI Year over Year',
                'importance': 'High',
                'actual': '',
                'forecast': '4.2%',
                'previous': '4.6%'
            },
            {
                'date': (base_date + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
                'time': '01:30',
                'timezone': 'GMT',
                'currency': 'JPY',
                'event': 'Japan Core CPI',
                'importance': 'Medium',
                'actual': '',
                'forecast': '2.8%',
                'previous': '2.9%'
            },
            {
                'date': (base_date + datetime.timedelta(days=4)).strftime('%Y-%m-%d'),
                'time': '15:00',
                'timezone': 'GMT',
                'currency': 'USD',
                'event': 'US Retail Sales',
                'importance': 'Medium',
                'actual': '',
                'forecast': '0.3%',
                'previous': '0.6%'
            },
            {
                'date': (base_date + datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
                'time': '10:00',
                'timezone': 'GMT',
                'currency': 'EUR',
                'event': 'Eurozone PMI Manufacturing',
                'importance': 'Medium',
                'actual': '',
                'forecast': '48.5',
                'previous': '47.9'
            }
        ]
        
        return sample_events
    
    def parse_calendar_data(self, calendar_data: List[Dict]) -> List[EconomicEvent]:
        events = []
        
        for data in calendar_data:
            try:
                date_str = data.get('date', '')
                time_str = data.get('time', '00:00')
                
                if not date_str or not time_str:
                    continue
                
                dt_str = f"{date_str} {time_str}"
                timestamp = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
                timestamp = timestamp.replace(tzinfo=pytz.UTC)
                
                event_name = data.get('event', '')
                currency = data.get('currency', 'USD')
                
                impact_str = data.get('importance', 'Low').lower()
                if 'high' in impact_str:
                    impact = EventImpact.HIGH
                elif 'medium' in impact_str:
                    impact = EventImpact.MEDIUM
                else:
                    impact = EventImpact.LOW
                
                if any(keyword in event_name.lower() for keyword in ['fed', 'rate decision', 'monetary policy']):
                    impact = EventImpact.EXTREME
                
                category = self.classify_event_category(event_name)
                
                forecast_str = data.get('forecast', '')
                previous_str = data.get('previous', '')
                actual_str = data.get('actual', '')
                
                def parse_numeric_value(value_str: str) -> Optional[float]:
                    if not value_str:
                        return None
                    try:
                        cleaned = value_str.replace('%', '').replace('K', '000').replace('M', '000000')
                        return float(cleaned)
                    except (ValueError, AttributeError):
                        return None
                
                event = EconomicEvent(
                    timestamp=timestamp,
                    name=event_name,
                    currency=currency,
                    impact=impact,
                    category=category,
                    forecast_value=parse_numeric_value(forecast_str),
                    previous_value=parse_numeric_value(previous_str),
                    actual_value=parse_numeric_value(actual_str) if actual_str else None,
                    description=f"{currency} {event_name}"
                )
                
                events.append(event)
                
            except Exception as e:
                print(f"Error parsing event data: {e}")
                continue
        
        return sorted(events, key=lambda e: e.timestamp)
    
    def fetch_calendar_data(self, source: str = 'sample') -> List[EconomicEvent]:
        if source == 'sample':
            calendar_data = self.create_sample_calendar_data()
            return self.parse_calendar_data(calendar_data)
        else:
            print(f"Real API integration for {source} not implemented yet")
            return self.fetch_calendar_data('sample')
    
    def export_events_to_json(self, events: List[EconomicEvent], filename: str):
        events_data = []
        for event in events:
            event_dict = asdict(event)
            event_dict['timestamp'] = event.timestamp.isoformat()
            event_dict['impact'] = event.impact.value
            event_dict['category'] = event.category.value
            events_data.append(event_dict)
        
        with open(filename, 'w') as f:
            json.dump(events_data, f, indent=2)
    
    def import_events_from_json(self, filename: str) -> List[EconomicEvent]:
        try:
            with open(filename, 'r') as f:
                events_data = json.load(f)
            
            events = []
            for data in events_data:
                data['timestamp'] = datetime.datetime.fromisoformat(data['timestamp'])
                data['impact'] = EventImpact(data['impact'])
                data['category'] = EventCategory(data['category'])
                
                event = EconomicEvent(**data)
                events.append(event)
            
            return sorted(events, key=lambda e: e.timestamp)
        
        except Exception as e:
            print(f"Error importing events from JSON: {e}")
            return []
    
    def get_events_for_currency_pairs(self, currency_pairs: List[str], hours_ahead: int = 72) -> List[EconomicEvent]:
        events = self.fetch_calendar_data()
        
        relevant_currencies = set()
        for pair in currency_pairs:
            pair_clean = pair.replace('/', '').replace('_', '')
            relevant_currencies.add(pair_clean[:3])
            relevant_currencies.add(pair_clean[3:])
        
        current_time = datetime.datetime.now(pytz.UTC)
        end_time = current_time + datetime.timedelta(hours=hours_ahead)
        
        filtered_events = []
        for event in events:
            if (current_time <= event.timestamp <= end_time and 
                event.currency in relevant_currencies):
                filtered_events.append(event)
        
        return filtered_events
    
    def update_event_with_actual_value(self, event_name: str, actual_value: float, events: List[EconomicEvent]):
        for event in events:
            if event.name == event_name:
                event.actual_value = actual_value
                break