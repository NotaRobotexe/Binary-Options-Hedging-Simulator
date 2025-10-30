"""Data models for binary options simulator"""
from dataclasses import dataclass


@dataclass
class BinaryOptionParams:
    """Parameters for binary option trade"""
    current_price: float
    strike_price: float
    payout_multiplier_up: float  # e.g., 1.6 means 60% profit if correct
    payout_multiplier_down: float  # e.g., 1.2 means 20% profit if correct
    investment_amount: float
    probability_up: float  # Probability price goes up (0-1)
    implied_volatility: float  # Annualized IV (e.g., 0.3 = 30%)
    time_to_expiry: float  # Time to expiry in days


@dataclass
class HedgeParams:
    """Parameters for hedging position"""
    hedge_amount: float  # Amount to hedge
    leverage: float  # Leverage on futures position
    hedge_direction: str  # 'long' or 'short'
    apply_fees: bool  # Whether to apply trading fees
    fee_rate: float  # Fee rate as decimal (e.g., 0.001 = 0.1%)
