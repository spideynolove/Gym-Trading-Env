import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import datetime
import pytz
from .intermarket_dataset_manager import IntermarketDatasetManager, AssetType
from .fa_ta_ia_framework import FATAIAFramework

class ThiduScenario(Enum):
    THIDU_1_LONG_GOLD = "thidu_1_long_gold"
    THIDU_2_DEFLATION_FEAR = "thidu_2_deflation_fear"
    THIDU_3_FED_AMBIGUITY = "thidu_3_fed_ambiguity"
    THIDU_4_ECB_QE_EARNINGS = "thidu_4_ecb_qe_earnings"
    THIDU_5_FOMC_SENTIMENT = "thidu_5_fomc_sentiment"
    THIDU_6_GERMAN_EQUITIES_QE = "thidu_6_german_equities_qe"
    THIDU_7_EUR_CAD_UPDATE = "thidu_7_eur_cad_update"
    THIDU_8_GOLD_ECB_QE = "thidu_8_gold_ecb_qe"
    THIDU_9_NFP_RATE_HIKE = "thidu_9_nfp_rate_hike"

@dataclass
class ScenarioDetection:
    scenario: ThiduScenario
    detected: bool
    confidence: float
    trigger_conditions: Dict
    recommended_actions: List[str]
    risk_level: str
    timestamp: datetime.datetime

class ThiduScenariosEngine:
    
    def __init__(self, dataset_manager: IntermarketDatasetManager, framework: FATAIAFramework):
        self.dataset_manager = dataset_manager
        self.framework = framework
        self.scenario_thresholds = {
            'high_confidence': 0.8,
            'medium_confidence': 0.6,
            'low_confidence': 0.4
        }
    
    def detect_all_scenarios(self):
        scenarios = {}
        
        scenarios[ThiduScenario.THIDU_1_LONG_GOLD] = self.detect_thidu_1_long_gold()
        scenarios[ThiduScenario.THIDU_2_DEFLATION_FEAR] = self.detect_thidu_2_deflation_fear()
        scenarios[ThiduScenario.THIDU_3_FED_AMBIGUITY] = self.detect_thidu_3_fed_ambiguity()
        scenarios[ThiduScenario.THIDU_4_ECB_QE_EARNINGS] = self.detect_thidu_4_ecb_qe_earnings()
        scenarios[ThiduScenario.THIDU_5_FOMC_SENTIMENT] = self.detect_thidu_5_fomc_sentiment()
        scenarios[ThiduScenario.THIDU_6_GERMAN_EQUITIES_QE] = self.detect_thidu_6_german_equities_qe()
        scenarios[ThiduScenario.THIDU_7_EUR_CAD_UPDATE] = self.detect_thidu_7_eur_cad_update()
        scenarios[ThiduScenario.THIDU_8_GOLD_ECB_QE] = self.detect_thidu_8_gold_ecb_qe()
        scenarios[ThiduScenario.THIDU_9_NFP_RATE_HIKE] = self.detect_thidu_9_nfp_rate_hike()
        
        return scenarios
    
    def detect_thidu_1_long_gold(self):
        commodities_data = self.dataset_manager.get_asset_data(AssetType.COMMODITIES)
        forex_data = self.dataset_manager.get_asset_data(AssetType.FOREX)
        
        trigger_conditions = {}
        confidence = 0.0
        detected = False
        
        # Step 1: Observe rising commodity prices (CRB Index)
        crb_index = commodities_data.get('commodities_CRB_INDEX')
        if crb_index:
            crb_changes = crb_index.data['close'].pct_change()
            recent_crb_trend = crb_changes.tail(20).mean()
            
            trigger_conditions['crb_rising'] = recent_crb_trend > 0.005  # 0.5% average daily rise
            trigger_conditions['crb_trend_strength'] = recent_crb_trend
        
        # Step 2: Note inverse USD movement
        usd_pairs = {}
        for pair in ['EURUSD', 'GBPUSD', 'AUDUSD']:
            pair_data = forex_data.get(f'forex_{pair}')
            if pair_data:
                usd_pairs[pair] = 1 / pair_data.data['close']  # Invert to get USD strength
        
        if usd_pairs:
            usd_values = pd.DataFrame(usd_pairs)
            usd_index = usd_values.mean(axis=1)
            usd_changes = usd_index.pct_change()
            recent_usd_trend = usd_changes.tail(20).mean()
            
            trigger_conditions['usd_weakness'] = recent_usd_trend < -0.003  # USD weakening
            trigger_conditions['usd_trend_strength'] = recent_usd_trend
        
        # Step 3: Gold buying opportunity via intermarket analysis
        gold = commodities_data.get('commodities_XAUUSD')
        if gold:
            gold_changes = gold.data['close'].pct_change()
            
            # Check USD/Gold inverse correlation
            if usd_pairs and len(gold_changes) > 60:
                recent_correlation = gold_changes.tail(60).corr(usd_changes.tail(60))
                trigger_conditions['gold_usd_inverse'] = recent_correlation < -0.5
                trigger_conditions['gold_usd_correlation'] = recent_correlation
            
            # Gold momentum
            gold_momentum = gold_changes.tail(10).mean()
            trigger_conditions['gold_momentum'] = gold_momentum > 0.002
        
        # Calculate overall confidence
        condition_scores = []
        if trigger_conditions.get('crb_rising', False):
            condition_scores.append(0.3)
        if trigger_conditions.get('usd_weakness', False):
            condition_scores.append(0.3)
        if trigger_conditions.get('gold_usd_inverse', False):
            condition_scores.append(0.2)
        if trigger_conditions.get('gold_momentum', False):
            condition_scores.append(0.2)
        
        confidence = sum(condition_scores)
        detected = confidence > 0.6
        
        recommended_actions = []
        if detected:
            recommended_actions = [
                "Long Gold (XAU/USD)",
                "Short USD pairs (EUR/USD, GBP/USD)",
                "Monitor CRB Index for continued strength",
                "Set stop-loss below recent gold support"
            ]
        
        return ScenarioDetection(
            scenario=ThiduScenario.THIDU_1_LONG_GOLD,
            detected=detected,
            confidence=confidence,
            trigger_conditions=trigger_conditions,
            recommended_actions=recommended_actions,
            risk_level="medium" if confidence > 0.7 else "low",
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def detect_thidu_9_nfp_rate_hike(self):
        equities_data = self.dataset_manager.get_asset_data(AssetType.EQUITIES)
        forex_data = self.dataset_manager.get_asset_data(AssetType.FOREX)
        bonds_data = self.dataset_manager.get_asset_data(AssetType.BONDS)
        
        trigger_conditions = {}
        confidence = 0.0
        detected = False
        
        # Step 1: Strong NFP data (simulated as strong employment surprise)
        # In real implementation, this would check economic calendar
        trigger_conditions['strong_nfp_assumption'] = True  # Placeholder for actual NFP data
        
        # Step 2: USD rally observation
        usd_pairs = {}
        for pair in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']:
            pair_data = forex_data.get(f'forex_{pair}')
            if pair_data:
                if pair == 'USDJPY':
                    usd_pairs[pair] = pair_data.data['close']  # Direct USD strength
                else:
                    usd_pairs[pair] = 1 / pair_data.data['close']  # Invert for USD strength
        
        if usd_pairs:
            usd_values = pd.DataFrame(usd_pairs)
            usd_index = usd_values.mean(axis=1)
            recent_usd_change = usd_index.pct_change().tail(5).mean()
            
            trigger_conditions['usd_rally'] = recent_usd_change > 0.005  # Strong USD rally
            trigger_conditions['usd_strength'] = recent_usd_change
        
        # Step 3: U.S. equity sell-off
        spx = equities_data.get('equities_SPX')
        if spx:
            spx_changes = spx.data['close'].pct_change()
            recent_spx_change = spx_changes.tail(5).mean()
            
            trigger_conditions['equity_selloff'] = recent_spx_change < -0.01  # 1% average decline
            trigger_conditions['equity_performance'] = recent_spx_change
        
        # Step 4: Bond yield divergence confirmation
        us10y = bonds_data.get('bonds_US10Y')
        if us10y and spx:
            bond_yield_changes = us10y.data['close'].pct_change()
            recent_yield_change = bond_yield_changes.tail(5).mean()
            
            # Rising yields should accompany falling equities
            yield_equity_divergence = recent_yield_change > 0.02 and recent_spx_change < -0.005
            trigger_conditions['bond_yield_divergence'] = yield_equity_divergence
            trigger_conditions['yield_change'] = recent_yield_change
        
        # EUR/JPY confirmation signal
        eurjpy = forex_data.get('forex_EURJPY')
        if eurjpy:
            eurjpy_changes = eurjpy.data['close'].pct_change()
            recent_eurjpy_change = eurjpy_changes.tail(5).mean()
            
            # EUR/JPY weakness often confirms risk-off sentiment
            trigger_conditions['eurjpy_weakness'] = recent_eurjpy_change < -0.005
            trigger_conditions['eurjpy_signal'] = recent_eurjpy_change
        
        # Calculate confidence based on conditions met
        condition_scores = []
        if trigger_conditions.get('usd_rally', False):
            condition_scores.append(0.25)
        if trigger_conditions.get('equity_selloff', False):
            condition_scores.append(0.25)
        if trigger_conditions.get('bond_yield_divergence', False):
            condition_scores.append(0.25)
        if trigger_conditions.get('eurjpy_weakness', False):
            condition_scores.append(0.15)
        if trigger_conditions.get('strong_nfp_assumption', False):
            condition_scores.append(0.1)
        
        confidence = sum(condition_scores)
        detected = confidence > 0.6
        
        recommended_actions = []
        if detected:
            recommended_actions = [
                "Long USD across major pairs",
                "Short U.S. equities (SPX futures)",
                "Monitor bond yields for continued rise",
                "Short EUR/JPY for risk-off confirmation",
                "Prepare for Fed rate hike speculation"
            ]
        
        return ScenarioDetection(
            scenario=ThiduScenario.THIDU_9_NFP_RATE_HIKE,
            detected=detected,
            confidence=confidence,
            trigger_conditions=trigger_conditions,
            recommended_actions=recommended_actions,
            risk_level="high" if confidence > 0.8 else "medium",
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def detect_thidu_4_ecb_qe_earnings(self):
        forex_data = self.dataset_manager.get_asset_data(AssetType.FOREX)
        equities_data = self.dataset_manager.get_asset_data(AssetType.EQUITIES)
        
        trigger_conditions = {}
        confidence = 0.0
        detected = False
        
        # Step 1: ECB QE expectations (simulated)
        trigger_conditions['ecb_qe_expectations'] = True  # Placeholder for actual ECB policy detection
        
        # Step 2: EUR weakness monitoring
        eurusd = forex_data.get('forex_EURUSD')
        if eurusd:
            eur_changes = eurusd.data['close'].pct_change()
            recent_eur_trend = eur_changes.tail(10).mean()
            
            trigger_conditions['eur_weakness'] = recent_eur_trend < -0.003  # EUR weakening
            trigger_conditions['eur_trend'] = recent_eur_trend
        
        # Step 3: Equity volatility from earnings
        spx = equities_data.get('equities_SPX')
        dax = equities_data.get('equities_DAX')
        
        equity_volatility = 0
        if spx:
            spx_volatility = spx.data['close'].pct_change().tail(20).std()
            equity_volatility += spx_volatility
        
        if dax:
            dax_volatility = dax.data['close'].pct_change().tail(20).std()
            equity_volatility += dax_volatility
            
            # DAX should outperform on QE expectations
            dax_changes = dax.data['close'].pct_change()
            recent_dax_performance = dax_changes.tail(10).mean()
            trigger_conditions['dax_strength'] = recent_dax_performance > 0.005
        
        trigger_conditions['equity_volatility'] = equity_volatility > 0.02  # High volatility
        trigger_conditions['volatility_level'] = equity_volatility
        
        # Calculate confidence
        condition_scores = []
        if trigger_conditions.get('ecb_qe_expectations', False):
            condition_scores.append(0.3)
        if trigger_conditions.get('eur_weakness', False):
            condition_scores.append(0.3)
        if trigger_conditions.get('equity_volatility', False):
            condition_scores.append(0.2)
        if trigger_conditions.get('dax_strength', False):
            condition_scores.append(0.2)
        
        confidence = sum(condition_scores)
        detected = confidence > 0.6
        
        recommended_actions = []
        if detected:
            recommended_actions = [
                "Short EUR/USD on QE expectations",
                "Long DAX futures (German equity strength)",
                "Monitor ECB policy announcements",
                "Trade equity volatility via options",
                "Hedge EUR exposure in portfolios"
            ]
        
        return ScenarioDetection(
            scenario=ThiduScenario.THIDU_4_ECB_QE_EARNINGS,
            detected=detected,
            confidence=confidence,
            trigger_conditions=trigger_conditions,
            recommended_actions=recommended_actions,
            risk_level="medium",
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def detect_thidu_7_eur_cad_update(self):
        forex_data = self.dataset_manager.get_asset_data(AssetType.FOREX)
        bonds_data = self.dataset_manager.get_asset_data(AssetType.BONDS)
        
        trigger_conditions = {}
        confidence = 0.0
        detected = False
        
        # Step 1: EUR sell-off without clear news
        eurusd = forex_data.get('forex_EURUSD')
        if eurusd:
            eur_changes = eurusd.data['close'].pct_change()
            recent_eur_decline = eur_changes.tail(5).mean()
            
            trigger_conditions['eur_selloff'] = recent_eur_decline < -0.005
            trigger_conditions['eur_performance'] = recent_eur_decline
        
        # Step 2: CAD strength despite USD rally
        usdcad = forex_data.get('forex_USDCAD')
        usdjpy = forex_data.get('forex_USDJPY')
        
        if usdcad and usdjpy:
            # USD strength from USD/JPY
            usd_strength = usdjpy.data['close'].pct_change().tail(5).mean()
            
            # CAD performance (inverse of USD/CAD)
            cad_performance = -usdcad.data['close'].pct_change().tail(5).mean()
            
            # CAD should be strong despite USD rally
            trigger_conditions['usd_rally'] = usd_strength > 0.003
            trigger_conditions['cad_resilience'] = cad_performance > 0.002
            trigger_conditions['cad_vs_usd'] = cad_performance > 0 and usd_strength > 0
        
        # Step 3: Interest rate differential analysis
        us10y = bonds_data.get('bonds_US10Y')
        ca10y = bonds_data.get('bonds_CA10Y')
        
        if us10y and ca10y:
            us_yield = us10y.data['close'].iloc[-1]
            ca_yield = ca10y.data['close'].iloc[-1]
            
            # As mentioned in book: CAD 1% vs NZD 2.75%, AUD 2.5%
            # Here we simulate the interest rate differential effect
            rate_differential = ca_yield - us_yield
            
            trigger_conditions['favorable_rate_diff'] = rate_differential > -1.0  # CAD not too weak vs USD
            trigger_conditions['rate_differential'] = rate_differential
        
        # Step 4: Commodity currency correlation
        audusd = forex_data.get('forex_AUDUSD')
        nzdusd = forex_data.get('forex_NZDUSD')
        
        commodity_currency_strength = []
        if audusd:
            aud_performance = audusd.data['close'].pct_change().tail(5).mean()
            commodity_currency_strength.append(aud_performance)
        
        if nzdusd:
            nzd_performance = nzdusd.data['close'].pct_change().tail(5).mean()
            commodity_currency_strength.append(nzd_performance)
        
        if commodity_currency_strength:
            avg_commodity_performance = np.mean(commodity_currency_strength)
            trigger_conditions['commodity_currency_context'] = avg_commodity_performance
            
            # CAD outperforming other commodity currencies
            if usdcad:
                cad_outperformance = cad_performance > avg_commodity_performance
                trigger_conditions['cad_outperformance'] = cad_outperformance
        
        # Calculate confidence
        condition_scores = []
        if trigger_conditions.get('eur_selloff', False):
            condition_scores.append(0.2)
        if trigger_conditions.get('cad_vs_usd', False):
            condition_scores.append(0.3)
        if trigger_conditions.get('favorable_rate_diff', False):
            condition_scores.append(0.2)
        if trigger_conditions.get('cad_outperformance', False):
            condition_scores.append(0.3)
        
        confidence = sum(condition_scores)
        detected = confidence > 0.6
        
        recommended_actions = []
        if detected:
            recommended_actions = [
                "Long CAD against USD (short USD/CAD)",
                "Short EUR/USD continuation",
                "Monitor interest rate differentials",
                "Compare CAD vs other commodity currencies",
                "Watch for BoC policy divergence"
            ]
        
        return ScenarioDetection(
            scenario=ThiduScenario.THIDU_7_EUR_CAD_UPDATE,
            detected=detected,
            confidence=confidence,
            trigger_conditions=trigger_conditions,
            recommended_actions=recommended_actions,
            risk_level="medium",
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    # Placeholder implementations for remaining scenarios
    def detect_thidu_2_deflation_fear(self):
        return self.create_placeholder_scenario(ThiduScenario.THIDU_2_DEFLATION_FEAR, 
                                              ["Long bonds", "Long gold", "Short equities", "Monitor yields"])
    
    def detect_thidu_3_fed_ambiguity(self):
        return self.create_placeholder_scenario(ThiduScenario.THIDU_3_FED_AMBIGUITY,
                                              ["Avoid aggressive USD trades", "Focus on TA signals", "Wait for clarity"])
    
    def detect_thidu_5_fomc_sentiment(self):
        return self.create_placeholder_scenario(ThiduScenario.THIDU_5_FOMC_SENTIMENT,
                                              ["Trade market reactions", "Follow sentiment", "Monitor bonds/USD"])
    
    def detect_thidu_6_german_equities_qe(self):
        return self.create_placeholder_scenario(ThiduScenario.THIDU_6_GERMAN_EQUITIES_QE,
                                              ["Long DAX futures", "Monitor ECB QE", "Trade thin conditions"])
    
    def detect_thidu_8_gold_ecb_qe(self):
        return self.create_placeholder_scenario(ThiduScenario.THIDU_8_GOLD_ECB_QE,
                                              ["Avoid late gold entries", "Short NZD/USD", "Monitor profit-taking"])
    
    def create_placeholder_scenario(self, scenario: ThiduScenario, actions: List[str]):
        return ScenarioDetection(
            scenario=scenario,
            detected=False,
            confidence=0.0,
            trigger_conditions={'placeholder': True, 'implemented': False},
            recommended_actions=actions,
            risk_level="low",
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def get_active_scenarios(self):
        all_scenarios = self.detect_all_scenarios()
        active_scenarios = {k: v for k, v in all_scenarios.items() if v.detected}
        return active_scenarios
    
    def get_scenario_summary(self):
        all_scenarios = self.detect_all_scenarios()
        
        summary = {
            'total_scenarios': len(all_scenarios),
            'active_scenarios': sum(1 for s in all_scenarios.values() if s.detected),
            'high_confidence_scenarios': sum(1 for s in all_scenarios.values() if s.confidence > 0.8),
            'recommended_actions': [],
            'overall_risk_level': 'low'
        }
        
        # Collect all recommended actions from active scenarios
        for scenario in all_scenarios.values():
            if scenario.detected:
                summary['recommended_actions'].extend(scenario.recommended_actions)
        
        # Determine overall risk level
        risk_levels = [s.risk_level for s in all_scenarios.values() if s.detected]
        if 'high' in risk_levels:
            summary['overall_risk_level'] = 'high'
        elif 'medium' in risk_levels:
            summary['overall_risk_level'] = 'medium'
        
        return summary