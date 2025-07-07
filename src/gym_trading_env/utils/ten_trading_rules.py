import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import datetime
import pytz
from .intermarket_dataset_manager import IntermarketDatasetManager
from .fa_ta_ia_framework import FATAIAFramework

class TradingRule(Enum):
    RULE_1_MARKET_SENTIMENT = "rule_1_market_sentiment"
    RULE_2_CONTROL_YOURSELF = "rule_2_control_yourself"
    RULE_3_BIG_PICTURE = "rule_3_big_picture"
    RULE_4_AVOID_EXTREMES = "rule_4_avoid_extremes"
    RULE_5_FOLLOW_TREND = "rule_5_follow_trend"
    RULE_6_TIMEFRAME_ANALYSIS = "rule_6_timeframe_analysis"
    RULE_7_METHOD_VS_SYSTEM = "rule_7_method_vs_system"
    RULE_8_ACCEPT_LOSSES = "rule_8_accept_losses"
    RULE_9_LET_PROFITS_RUN = "rule_9_let_profits_run"
    RULE_10_STOP_LOSS = "rule_10_stop_loss"

@dataclass
class RuleCompliance:
    rule: TradingRule
    compliance_score: float
    current_status: str
    recommendations: List[str]
    risk_level: str
    supporting_data: Dict
    timestamp: datetime.datetime

class TenTradingRulesFramework:
    
    def __init__(self, dataset_manager: IntermarketDatasetManager, framework: FATAIAFramework):
        self.dataset_manager = dataset_manager
        self.framework = framework
        
        # Rule compliance thresholds
        self.compliance_thresholds = {
            'excellent': 0.9,
            'good': 0.7,
            'acceptable': 0.5,
            'poor': 0.3
        }
        
        # Risk management parameters
        self.risk_parameters = {
            'max_position_size': 0.1,  # 10% max position
            'stop_loss_percentage': 0.02,  # 2% stop loss
            'profit_target_ratio': 2.0,  # 2:1 reward/risk
            'correlation_limit': 0.7,  # Max correlation between positions
            'drawdown_limit': 0.05  # 5% max drawdown
        }
        
        # Trading state tracking
        self.trading_state = {
            'current_positions': {},
            'recent_trades': [],
            'profit_loss_history': [],
            'psychological_state': 'neutral',
            'market_regime': 'normal'
        }
    
    def evaluate_all_rules(self, current_market_data: Dict, trading_context: Dict):
        rule_evaluations = {}
        
        rule_evaluations[TradingRule.RULE_1_MARKET_SENTIMENT] = self.evaluate_rule_1_market_sentiment(current_market_data)
        rule_evaluations[TradingRule.RULE_2_CONTROL_YOURSELF] = self.evaluate_rule_2_control_yourself(trading_context)
        rule_evaluations[TradingRule.RULE_3_BIG_PICTURE] = self.evaluate_rule_3_big_picture(current_market_data)
        rule_evaluations[TradingRule.RULE_4_AVOID_EXTREMES] = self.evaluate_rule_4_avoid_extremes(current_market_data)
        rule_evaluations[TradingRule.RULE_5_FOLLOW_TREND] = self.evaluate_rule_5_follow_trend(current_market_data)
        rule_evaluations[TradingRule.RULE_6_TIMEFRAME_ANALYSIS] = self.evaluate_rule_6_timeframe_analysis(current_market_data)
        rule_evaluations[TradingRule.RULE_7_METHOD_VS_SYSTEM] = self.evaluate_rule_7_method_vs_system(trading_context)
        rule_evaluations[TradingRule.RULE_8_ACCEPT_LOSSES] = self.evaluate_rule_8_accept_losses(trading_context)
        rule_evaluations[TradingRule.RULE_9_LET_PROFITS_RUN] = self.evaluate_rule_9_let_profits_run(trading_context)
        rule_evaluations[TradingRule.RULE_10_STOP_LOSS] = self.evaluate_rule_10_stop_loss(trading_context)
        
        return rule_evaluations
    
    def evaluate_rule_1_market_sentiment(self, market_data: Dict):
        compliance_score = 0.0
        recommendations = []
        
        # Check if sentiment analysis is being used for direction
        fa_analysis = market_data.get('fa_analysis', {})
        ia_analysis = market_data.get('ia_analysis', {})
        
        # Sentiment score from FA
        sentiment_score = fa_analysis.get('market_sentiment', {}).get('sentiment_score', 0)
        sentiment_confidence = fa_analysis.get('market_sentiment', {}).get('confidence', 0)
        
        # Risk sentiment from IA
        risk_sentiment = ia_analysis.get('risk_sentiment', {})
        vix_spike = risk_sentiment.get('vix_spike', {}).get('signal') == 'risk_off'
        safe_haven_flow = risk_sentiment.get('safe_haven_flow', {}).get('signal')
        
        # Evaluate sentiment-driven decision making
        if abs(sentiment_score) > 0.3 and sentiment_confidence > 0.6:
            compliance_score += 0.4
            recommendations.append("Strong sentiment signal detected - align positions")
        
        if safe_haven_flow in ['risk_off', 'risk_on']:
            compliance_score += 0.3
            recommendations.append(f"Risk sentiment clear: {safe_haven_flow}")
        
        if vix_spike:
            compliance_score += 0.3
            recommendations.append("VIX spike confirms risk-off sentiment")
        
        # Check for sentiment confirmation across markets
        murphy_signals = ia_analysis.get('murphy_principles', {})
        confirmation_count = sum(1 for signal in murphy_signals.values() 
                               if signal.get('signal') in ['confirmed', 'leading'])
        
        if confirmation_count >= 2:
            compliance_score += 0.2
            recommendations.append("Cross-market sentiment confirmation")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_1_MARKET_SENTIMENT,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="low" if compliance_score > 0.7 else "medium",
            supporting_data={
                'sentiment_score': sentiment_score,
                'sentiment_confidence': sentiment_confidence,
                'risk_sentiment': safe_haven_flow,
                'vix_spike': vix_spike,
                'cross_market_confirmations': confirmation_count
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_2_control_yourself(self, trading_context: Dict):
        compliance_score = 0.0
        recommendations = []
        
        # Check emotional discipline indicators
        recent_trades = trading_context.get('recent_trades', [])
        current_drawdown = trading_context.get('current_drawdown', 0)
        consecutive_losses = trading_context.get('consecutive_losses', 0)
        
        # Position sizing discipline
        current_positions = trading_context.get('current_positions', {})
        total_exposure = sum(abs(pos) for pos in current_positions.values())
        
        if total_exposure <= self.risk_parameters['max_position_size']:
            compliance_score += 0.3
            recommendations.append("Position sizing within limits")
        else:
            recommendations.append("Reduce position size - exceeding risk limits")
        
        # Drawdown control
        if abs(current_drawdown) <= self.risk_parameters['drawdown_limit']:
            compliance_score += 0.3
            recommendations.append("Drawdown under control")
        else:
            recommendations.append("Stop trading - drawdown limit exceeded")
        
        # Emotional state assessment
        if consecutive_losses >= 3:
            compliance_score -= 0.2
            recommendations.append("Take break after consecutive losses")
            self.trading_state['psychological_state'] = 'stressed'
        elif consecutive_losses == 0:
            compliance_score += 0.2
            self.trading_state['psychological_state'] = 'confident'
        
        # Overtrading check
        trades_today = len([t for t in recent_trades 
                          if (datetime.datetime.now() - t.get('timestamp', datetime.datetime.now())).days == 0])
        
        if trades_today <= 3:
            compliance_score += 0.2
            recommendations.append("Trading frequency appropriate")
        else:
            recommendations.append("Reduce trading frequency - possible overtrading")
        
        status = self.get_compliance_status(compliance_score)
        risk_level = "high" if compliance_score < 0.5 else "medium" if compliance_score < 0.7 else "low"
        
        return RuleCompliance(
            rule=TradingRule.RULE_2_CONTROL_YOURSELF,
            compliance_score=max(0.0, min(1.0, compliance_score)),
            current_status=status,
            recommendations=recommendations,
            risk_level=risk_level,
            supporting_data={
                'total_exposure': total_exposure,
                'current_drawdown': current_drawdown,
                'consecutive_losses': consecutive_losses,
                'trades_today': trades_today,
                'psychological_state': self.trading_state['psychological_state']
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_3_big_picture(self, market_data: Dict):
        compliance_score = 0.0
        recommendations = []
        
        # Check cross-market analysis usage
        ia_analysis = market_data.get('ia_analysis', {})
        murphy_principles = ia_analysis.get('murphy_principles', {})
        cross_market_confirmations = ia_analysis.get('confirmations', {})
        
        # Multi-asset correlation awareness
        active_principles = sum(1 for principle in murphy_principles.values()
                              if principle.get('signal') in ['confirmed', 'leading'])
        
        if active_principles >= 3:
            compliance_score += 0.4
            recommendations.append("Strong cross-market perspective")
        elif active_principles >= 2:
            compliance_score += 0.3
            recommendations.append("Good multi-market awareness")
        else:
            recommendations.append("Expand cross-market analysis")
        
        # Check for single-market myopia
        if len(cross_market_confirmations) >= 2:
            compliance_score += 0.3
            recommendations.append("Multiple market confirmations")
        
        # Time horizon consideration
        ta_analysis = market_data.get('ta_analysis', {})
        trend_analysis = ta_analysis.get('trend', 'Neutral')
        
        if trend_analysis != 'Neutral':
            compliance_score += 0.2
            recommendations.append(f"Trend context: {trend_analysis}")
        
        # Global macro awareness
        fa_analysis = market_data.get('fa_analysis', {})
        if fa_analysis:
            compliance_score += 0.1
            recommendations.append("Fundamental backdrop considered")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_3_BIG_PICTURE,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="low",
            supporting_data={
                'active_principles': active_principles,
                'cross_market_confirmations': len(cross_market_confirmations),
                'trend_context': trend_analysis,
                'multi_asset_awareness': compliance_score > 0.6
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_4_avoid_extremes(self, market_data: Dict):
        compliance_score = 0.0
        recommendations = []
        
        ta_analysis = market_data.get('ta_analysis', {})
        
        # RSI extreme levels
        rsi = ta_analysis.get('rsi', 50)
        if 30 <= rsi <= 70:
            compliance_score += 0.3
            recommendations.append("RSI in reasonable range")
        elif rsi > 80 or rsi < 20:
            recommendations.append("Avoid trading at RSI extremes")
        else:
            compliance_score += 0.1
            recommendations.append("RSI approaching extreme levels")
        
        # Bollinger Band position
        bb = ta_analysis.get('bollinger_bands', {})
        bb_position = bb.get('position', 'normal')
        
        if bb_position == 'normal':
            compliance_score += 0.3
            recommendations.append("Price in normal BB range")
        else:
            recommendations.append(f"Price at BB extreme: {bb_position}")
        
        # Support/Resistance proximity
        support_resistance = ta_analysis.get('support_resistance', {})
        nearest_resistance = support_resistance.get('nearest_resistance')
        nearest_support = support_resistance.get('nearest_support')
        
        # Check if current price is too close to major levels
        current_price = market_data.get('current_price', 0)
        if nearest_resistance and current_price:
            resistance_distance = abs(nearest_resistance - current_price) / current_price
            if resistance_distance > 0.005:  # More than 0.5% away
                compliance_score += 0.2
                recommendations.append("Good distance from resistance")
            else:
                recommendations.append("Too close to resistance level")
        
        # Volatility extremes
        recent_volatility = market_data.get('recent_volatility', 0)
        if 0.01 <= recent_volatility <= 0.03:  # Normal volatility range
            compliance_score += 0.2
            recommendations.append("Normal volatility environment")
        else:
            recommendations.append("Extreme volatility - exercise caution")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_4_AVOID_EXTREMES,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="medium" if compliance_score < 0.6 else "low",
            supporting_data={
                'rsi': rsi,
                'bb_position': bb_position,
                'resistance_distance': resistance_distance if 'resistance_distance' in locals() else None,
                'volatility_level': recent_volatility
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_5_follow_trend(self, market_data: Dict):
        compliance_score = 0.0
        recommendations = []
        
        ta_analysis = market_data.get('ta_analysis', {})
        ia_analysis = market_data.get('ia_analysis', {})
        
        # Primary trend identification
        trend = ta_analysis.get('trend', 'Neutral')
        
        if trend in ['Uptrend', 'Downtrend']:
            compliance_score += 0.4
            recommendations.append(f"Clear trend identified: {trend}")
            
            # Check if trading with the trend
            entry_signals = ta_analysis.get('entry_signals', [])
            trend_aligned_signals = [s for s in entry_signals 
                                   if (trend == 'Uptrend' and s['type'] == 'long') or
                                      (trend == 'Downtrend' and s['type'] == 'short')]
            
            if trend_aligned_signals:
                compliance_score += 0.3
                recommendations.append("Entry signals align with trend")
            else:
                recommendations.append("Wait for trend-aligned entry signals")
        
        # Cross-market trend confirmation
        confirmations = ia_analysis.get('confirmations', {})
        positive_confirmations = sum(1 for conf in confirmations.values()
                                   if conf.get('confirmation') == 'positive' and conf.get('strength', 0) > 0.5)
        
        if positive_confirmations >= 2:
            compliance_score += 0.2
            recommendations.append("Cross-market trend confirmation")
        
        # Leading indicators alignment
        leading_indicators = ia_analysis.get('leading_indicators', {})
        for indicator, data in leading_indicators.items():
            if data.get('signal') == 'leading' and data.get('strength', 0) > 0.6:
                compliance_score += 0.1
                recommendations.append(f"Leading indicator confirms: {indicator}")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_5_FOLLOW_TREND,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="low" if trend != 'Neutral' else "medium",
            supporting_data={
                'primary_trend': trend,
                'cross_market_confirmations': positive_confirmations,
                'trend_strength': compliance_score,
                'leading_confirmations': len(leading_indicators)
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_6_timeframe_analysis(self, market_data: Dict):
        compliance_score = 0.0
        recommendations = []
        
        # Check for multi-timeframe analysis
        ta_analysis = market_data.get('ta_analysis', {})
        
        # Simulated multi-timeframe data (in real implementation, would have actual multi-TF data)
        timeframes_analyzed = market_data.get('timeframes_analyzed', ['1H'])
        
        if len(timeframes_analyzed) >= 2:
            compliance_score += 0.4
            recommendations.append("Multi-timeframe analysis conducted")
        else:
            recommendations.append("Expand to multiple timeframes")
        
        # Trend consistency across timeframes
        if len(timeframes_analyzed) >= 2:
            # Simulate trend alignment check
            trend_alignment = market_data.get('trend_alignment', 0.7)  # Placeholder
            
            if trend_alignment > 0.8:
                compliance_score += 0.3
                recommendations.append("Strong trend alignment across timeframes")
            elif trend_alignment > 0.6:
                compliance_score += 0.2
                recommendations.append("Good trend alignment")
            else:
                recommendations.append("Mixed signals across timeframes - be cautious")
        
        # Entry timing on smaller timeframe
        entry_signals = ta_analysis.get('entry_signals', [])
        if entry_signals and len(timeframes_analyzed) >= 2:
            compliance_score += 0.3
            recommendations.append("Entry timing refined on smaller timeframe")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_6_TIMEFRAME_ANALYSIS,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="medium" if len(timeframes_analyzed) < 2 else "low",
            supporting_data={
                'timeframes_analyzed': timeframes_analyzed,
                'trend_alignment': market_data.get('trend_alignment', 0),
                'multi_tf_signals': len(entry_signals) if entry_signals else 0
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_7_method_vs_system(self, trading_context: Dict):
        compliance_score = 0.0
        recommendations = []
        
        # Check for adaptive approach vs rigid system
        recent_market_regime = trading_context.get('market_regime', 'normal')
        adaptation_score = trading_context.get('adaptation_score', 0.5)
        
        if adaptation_score > 0.7:
            compliance_score += 0.4
            recommendations.append("Good adaptation to market conditions")
        elif adaptation_score > 0.5:
            compliance_score += 0.2
            recommendations.append("Some adaptation to market changes")
        else:
            recommendations.append("Increase flexibility in approach")
        
        # Methodology consistency
        method_consistency = trading_context.get('method_consistency', 0.7)
        
        if 0.6 <= method_consistency <= 0.8:
            compliance_score += 0.3
            recommendations.append("Good balance of consistency and flexibility")
        elif method_consistency > 0.8:
            compliance_score += 0.1
            recommendations.append("May be too rigid - consider more flexibility")
        else:
            recommendations.append("Lacking consistency in approach")
        
        # Response to changing correlations
        correlation_regime_changes = trading_context.get('correlation_changes', 0)
        if correlation_regime_changes > 0 and adaptation_score > 0.6:
            compliance_score += 0.3
            recommendations.append("Adapting to correlation regime changes")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_7_METHOD_VS_SYSTEM,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="medium",
            supporting_data={
                'adaptation_score': adaptation_score,
                'method_consistency': method_consistency,
                'market_regime': recent_market_regime,
                'correlation_changes': correlation_regime_changes
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_8_accept_losses(self, trading_context: Dict):
        compliance_score = 0.0
        recommendations = []
        
        recent_trades = trading_context.get('recent_trades', [])
        
        # Check for proper loss acceptance
        losing_trades = [t for t in recent_trades if t.get('pnl', 0) < 0]
        
        if losing_trades:
            # Check if stops were honored
            stops_honored = sum(1 for t in losing_trades if t.get('stop_honored', False))
            stop_compliance = stops_honored / len(losing_trades) if losing_trades else 0
            
            if stop_compliance >= 0.9:
                compliance_score += 0.4
                recommendations.append("Excellent stop-loss discipline")
            elif stop_compliance >= 0.7:
                compliance_score += 0.3
                recommendations.append("Good stop-loss compliance")
            else:
                recommendations.append("Improve stop-loss discipline")
            
            # Check for revenge trading after losses
            revenge_trading_detected = trading_context.get('revenge_trading', False)
            if not revenge_trading_detected:
                compliance_score += 0.3
                recommendations.append("No revenge trading detected")
            else:
                recommendations.append("Avoid revenge trading after losses")
            
            # Loss size relative to account
            avg_loss_size = np.mean([abs(t.get('pnl', 0)) for t in losing_trades])
            account_size = trading_context.get('account_size', 10000)
            loss_percentage = avg_loss_size / account_size
            
            if loss_percentage <= self.risk_parameters['stop_loss_percentage']:
                compliance_score += 0.3
                recommendations.append("Loss sizes within acceptable range")
            else:
                recommendations.append("Reduce position sizes - losses too large")
        else:
            compliance_score += 0.2
            recommendations.append("No recent losses to evaluate")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_8_ACCEPT_LOSSES,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="high" if compliance_score < 0.5 else "medium",
            supporting_data={
                'stop_compliance': stop_compliance if 'stop_compliance' in locals() else 1.0,
                'avg_loss_percentage': loss_percentage if 'loss_percentage' in locals() else 0,
                'revenge_trading': trading_context.get('revenge_trading', False),
                'losing_trades_count': len(losing_trades)
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_9_let_profits_run(self, trading_context: Dict):
        compliance_score = 0.0
        recommendations = []
        
        recent_trades = trading_context.get('recent_trades', [])
        winning_trades = [t for t in recent_trades if t.get('pnl', 0) > 0]
        
        if winning_trades:
            # Check profit/loss ratio
            losing_trades = [t for t in recent_trades if t.get('pnl', 0) < 0]
            
            if losing_trades:
                avg_win = np.mean([t.get('pnl', 0) for t in winning_trades])
                avg_loss = np.mean([abs(t.get('pnl', 0)) for t in losing_trades])
                profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
                
                if profit_loss_ratio >= self.risk_parameters['profit_target_ratio']:
                    compliance_score += 0.4
                    recommendations.append(f"Excellent P/L ratio: {profit_loss_ratio:.2f}")
                elif profit_loss_ratio >= 1.5:
                    compliance_score += 0.3
                    recommendations.append(f"Good P/L ratio: {profit_loss_ratio:.2f}")
                else:
                    recommendations.append(f"Improve P/L ratio: {profit_loss_ratio:.2f}")
            
            # Check for premature profit taking
            premature_exits = sum(1 for t in winning_trades if t.get('premature_exit', False))
            premature_rate = premature_exits / len(winning_trades) if winning_trades else 0
            
            if premature_rate <= 0.2:
                compliance_score += 0.3
                recommendations.append("Good profit management")
            else:
                recommendations.append("Reduce premature profit taking")
            
            # Trailing stop usage
            trailing_stops_used = sum(1 for t in winning_trades if t.get('trailing_stop_used', False))
            trailing_usage = trailing_stops_used / len(winning_trades) if winning_trades else 0
            
            if trailing_usage >= 0.7:
                compliance_score += 0.3
                recommendations.append("Good use of trailing stops")
            else:
                recommendations.append("Increase trailing stop usage")
        else:
            compliance_score += 0.1
            recommendations.append("No recent winning trades to evaluate")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_9_LET_PROFITS_RUN,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="medium" if compliance_score < 0.6 else "low",
            supporting_data={
                'profit_loss_ratio': profit_loss_ratio if 'profit_loss_ratio' in locals() else 0,
                'premature_exit_rate': premature_rate if 'premature_rate' in locals() else 0,
                'trailing_stop_usage': trailing_usage if 'trailing_usage' in locals() else 0,
                'winning_trades_count': len(winning_trades)
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def evaluate_rule_10_stop_loss(self, trading_context: Dict):
        compliance_score = 0.0
        recommendations = []
        
        current_positions = trading_context.get('current_positions', {})
        
        # Check if all positions have stop losses
        positions_with_stops = trading_context.get('positions_with_stops', 0)
        total_positions = len(current_positions)
        
        if total_positions > 0:
            stop_coverage = positions_with_stops / total_positions
            
            if stop_coverage >= 0.95:
                compliance_score += 0.4
                recommendations.append("Excellent stop-loss coverage")
            elif stop_coverage >= 0.8:
                compliance_score += 0.3
                recommendations.append("Good stop-loss coverage")
            else:
                recommendations.append("Ensure all positions have stop losses")
        else:
            compliance_score += 0.2
            recommendations.append("No current positions")
        
        # Stop loss placement appropriateness
        stop_distances = trading_context.get('stop_distances', [])
        if stop_distances:
            avg_stop_distance = np.mean(stop_distances)
            
            if 0.01 <= avg_stop_distance <= 0.03:  # 1-3% stop distance
                compliance_score += 0.3
                recommendations.append("Appropriate stop-loss distances")
            elif avg_stop_distance > 0.05:
                recommendations.append("Stop losses too wide - reduce risk")
            else:
                recommendations.append("Stop losses too tight - may get stopped out frequently")
        
        # Stop loss adjustment for volatility
        volatility_adjusted_stops = trading_context.get('volatility_adjusted_stops', False)
        if volatility_adjusted_stops:
            compliance_score += 0.2
            recommendations.append("Stops adjusted for volatility")
        else:
            recommendations.append("Consider volatility when setting stops")
        
        # Intermarket-based stop adjustment
        intermarket_stops = trading_context.get('intermarket_stop_adjustment', False)
        if intermarket_stops:
            compliance_score += 0.1
            recommendations.append("Stops consider intermarket factors")
        
        status = self.get_compliance_status(compliance_score)
        
        return RuleCompliance(
            rule=TradingRule.RULE_10_STOP_LOSS,
            compliance_score=min(1.0, compliance_score),
            current_status=status,
            recommendations=recommendations,
            risk_level="high" if compliance_score < 0.6 else "low",
            supporting_data={
                'stop_coverage': stop_coverage if 'stop_coverage' in locals() else 1.0,
                'avg_stop_distance': avg_stop_distance if 'avg_stop_distance' in locals() else 0.02,
                'volatility_adjusted': volatility_adjusted_stops,
                'intermarket_adjusted': intermarket_stops,
                'total_positions': total_positions
            },
            timestamp=datetime.datetime.now(pytz.UTC)
        )
    
    def get_compliance_status(self, score: float):
        if score >= self.compliance_thresholds['excellent']:
            return "excellent"
        elif score >= self.compliance_thresholds['good']:
            return "good"
        elif score >= self.compliance_thresholds['acceptable']:
            return "acceptable"
        else:
            return "poor"
    
    def get_overall_compliance_summary(self, market_data: Dict, trading_context: Dict):
        all_rules = self.evaluate_all_rules(market_data, trading_context)
        
        summary = {
            'total_rules': len(all_rules),
            'excellent_compliance': sum(1 for r in all_rules.values() if r.current_status == 'excellent'),
            'good_compliance': sum(1 for r in all_rules.values() if r.current_status == 'good'),
            'poor_compliance': sum(1 for r in all_rules.values() if r.current_status == 'poor'),
            'average_compliance_score': np.mean([r.compliance_score for r in all_rules.values()]),
            'high_risk_rules': [r.rule.value for r in all_rules.values() if r.risk_level == 'high'],
            'key_recommendations': [],
            'overall_trading_health': 'good'
        }
        
        # Collect key recommendations
        for rule_compliance in all_rules.values():
            if rule_compliance.current_status == 'poor':
                summary['key_recommendations'].extend(rule_compliance.recommendations[:2])
        
        # Overall health assessment
        if summary['average_compliance_score'] >= 0.8:
            summary['overall_trading_health'] = 'excellent'
        elif summary['average_compliance_score'] >= 0.6:
            summary['overall_trading_health'] = 'good'
        elif summary['average_compliance_score'] >= 0.4:
            summary['overall_trading_health'] = 'acceptable'
        else:
            summary['overall_trading_health'] = 'poor'
        
        return summary
    
    def get_trading_permissions(self, compliance_summary: Dict):
        permissions = {
            'can_open_new_positions': True,
            'can_increase_position_size': True,
            'should_reduce_risk': False,
            'trading_halt_recommended': False,
            'max_position_multiplier': 1.0
        }
        
        # Risk-based permissions
        high_risk_count = len(compliance_summary['high_risk_rules'])
        avg_score = compliance_summary['average_compliance_score']
        
        if high_risk_count >= 3 or avg_score < 0.3:
            permissions['trading_halt_recommended'] = True
            permissions['can_open_new_positions'] = False
            permissions['can_increase_position_size'] = False
        elif high_risk_count >= 2 or avg_score < 0.5:
            permissions['should_reduce_risk'] = True
            permissions['can_increase_position_size'] = False
            permissions['max_position_multiplier'] = 0.5
        elif avg_score < 0.7:
            permissions['max_position_multiplier'] = 0.75
        
        return permissions