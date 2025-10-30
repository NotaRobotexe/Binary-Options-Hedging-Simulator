"""Binary options simulator with hedging calculations"""
import numpy as np
from typing import Dict
from models import BinaryOptionParams, HedgeParams


class BinaryOptionsSimulator:
    def __init__(self):
        self.results = {}
    
    def calculate_expected_move(self, current_price: float, iv: float, time_days: float) -> float:
        """Calculate expected price move based on IV and time"""
        # Expected move = Price * IV * sqrt(Time in years)
        time_years = time_days / 365.0
        expected_move = current_price * iv * np.sqrt(time_years)
        return expected_move
    
    def calculate_probability_itm(self, current_price: float, strike_price: float, 
                                  iv: float, time_days: float, direction: str) -> float:
        """
        Calculate probability of being in-the-money using simplified Black-Scholes
        This gives a more realistic probability based on IV and time
        """
        if time_days <= 0:
            return 1.0 if (direction == 'up' and current_price > strike_price) or \
                         (direction == 'down' and current_price < strike_price) else 0.0
        
        time_years = time_days / 365.0
        
        # Calculate d2 from Black-Scholes (simplified without interest rate)
        if current_price == strike_price:
            d2 = 0
        else:
            d2 = (np.log(current_price / strike_price)) / (iv * np.sqrt(time_years))
        
        # Cumulative normal distribution
        from scipy import stats
        prob_up = stats.norm.cdf(d2)
        
        if direction == 'up':
            return prob_up
        else:
            return 1 - prob_up
    
    def generate_price_scenarios(self, current_price: float, strike_price: float, iv: float, 
                                time_days: float, num_points: int = 100) -> np.ndarray:
        """
        Generate realistic price scenarios based on IV and time
        Uses the expected move to determine reasonable price range
        Also considers the distance to strike price
        """
        expected_move = self.calculate_expected_move(current_price, iv, time_days)
        
        # Calculate how far strike is from current price (in percentage)
        strike_distance_pct = abs(strike_price - current_price) / current_price
        
        # Price range should cover ±3 standard deviations OR the strike distance, whichever is larger
        max_move_pct = max(3 * (expected_move / current_price), strike_distance_pct * 1.5)
        
        # Generate prices centered around current price
        price_changes = np.linspace(-max_move_pct, max_move_pct, num_points)
        
        return price_changes
    
    def calculate_binary_option_payout(self, params: BinaryOptionParams, price_goes_up: bool) -> float:
        """Calculate payout for binary option (profit, not total return)"""
        if price_goes_up:
            # Profit = investment * (multiplier - 1)
            # E.g., $1000 at 1.6x = $1000 * (1.6 - 1) = $600 profit
            return params.investment_amount * (params.payout_multiplier_up - 1)
        else:
            # Profit = investment * (multiplier - 1)
            return params.investment_amount * (params.payout_multiplier_down - 1)
    
    def calculate_hedge_pnl(self, hedge: HedgeParams, price_change_pct: float) -> float:
        """
        Calculate P&L from hedging position with liquidation protection and fees
        Loss is capped at the hedge amount (collateral)
        """
        # If leverage is 1 or less, no liquidation possible (not leveraged)
        if hedge.leverage <= 1:
            # Simple linear P&L
            if hedge.hedge_direction == 'long':
                pnl = hedge.hedge_amount * price_change_pct
            else:  # short
                pnl = hedge.hedge_amount * (-price_change_pct)
            
            # Apply fees
            if hedge.apply_fees:
                position_size = hedge.hedge_amount * hedge.leverage
                total_fees = position_size * hedge.fee_rate * 2
                pnl -= total_fees
            
            return pnl
        
        # Calculate position size (notional value)
        position_size = hedge.hedge_amount * hedge.leverage
        
        # Check if liquidated FIRST
        if hedge.hedge_direction == 'long':
            # Long: liquidated when price drops by 1/leverage
            liquidation_point = -1.0 / hedge.leverage  # As decimal (negative)
            if price_change_pct <= liquidation_point:
                # Already liquidated - total loss is collateral (including fees paid at entry)
                if hedge.apply_fees:
                    entry_fee = position_size * hedge.fee_rate
                    return -(hedge.hedge_amount + entry_fee)
                return -hedge.hedge_amount
        else:  # short
            # Short: liquidated when price rises by 1/leverage  
            liquidation_point = 1.0 / hedge.leverage  # As decimal (positive)
            if price_change_pct >= liquidation_point:
                # Already liquidated - total loss is collateral (including fees paid at entry)
                if hedge.apply_fees:
                    entry_fee = position_size * hedge.fee_rate
                    return -(hedge.hedge_amount + entry_fee)
                return -hedge.hedge_amount
        
        # Not liquidated - calculate normal P&L
        if hedge.hedge_direction == 'long':
            raw_pnl = hedge.hedge_amount * hedge.leverage * price_change_pct
        else:  # short
            raw_pnl = hedge.hedge_amount * hedge.leverage * (-price_change_pct)
        
        # Apply fees (entry + exit)
        if hedge.apply_fees:
            total_fees = position_size * hedge.fee_rate * 2  # Entry + exit
            raw_pnl -= total_fees
        
        return raw_pnl
    
    def simulate_scenarios(self, binary_params: BinaryOptionParams, 
                          hedge_params: HedgeParams,
                          binary_direction: str,  # 'up' or 'down' - what we're betting on
                          num_points: int = 100) -> Dict:
        """
        Simulate various price scenarios with IV and time consideration
        
        Args:
            binary_params: Binary option parameters
            hedge_params: Hedging parameters
            binary_direction: Direction of binary option bet ('up' or 'down')
            num_points: Number of simulation points
        """
        # Calculate base price range from IV and time
        expected_move = self.calculate_expected_move(
            binary_params.current_price,
            binary_params.implied_volatility,
            binary_params.time_to_expiry
        )
        
        strike_distance_pct = abs(binary_params.strike_price - binary_params.current_price) / binary_params.current_price
        max_move_pct = max(3 * (expected_move / binary_params.current_price), strike_distance_pct * 1.5)
        
        # Extend range to include liquidation points if leveraged
        if hedge_params.leverage > 1:
            liquidation_range = 1.5 / hedge_params.leverage  # Add 50% beyond liquidation
            max_move_pct = max(max_move_pct, liquidation_range)
        
        # Generate price changes
        price_changes = np.linspace(-max_move_pct, max_move_pct, num_points)
        
        # Calculate realistic probability based on IV and time
        realistic_prob = self.calculate_probability_itm(
            binary_params.current_price,
            binary_params.strike_price,
            binary_params.implied_volatility,
            binary_params.time_to_expiry,
            binary_direction
        )
        
        total_pnl = []
        binary_pnl = []
        hedge_pnl = []
        
        for price_change in price_changes:
            # Calculate binary option outcome
            actual_price = binary_params.current_price * (1 + price_change)
            
            # Check if price is above or below strike
            price_went_up = actual_price > binary_params.strike_price
            
            # Did our binary bet win?
            binary_wins = (binary_direction == 'up' and price_went_up) or \
                         (binary_direction == 'down' and not price_went_up)
            
            if binary_wins:
                if binary_direction == 'up':
                    b_pnl = self.calculate_binary_option_payout(binary_params, True)
                else:
                    b_pnl = self.calculate_binary_option_payout(binary_params, False)
            else:
                # Lose the investment
                b_pnl = -binary_params.investment_amount
            
            # Calculate hedge P&L
            h_pnl = self.calculate_hedge_pnl(hedge_params, price_change)
            
            # Total P&L
            t_pnl = b_pnl + h_pnl
            
            total_pnl.append(t_pnl)
            binary_pnl.append(b_pnl)
            hedge_pnl.append(h_pnl)
        
        # Calculate key metrics
        total_pnl_array = np.array(total_pnl)
        max_profit = np.max(total_pnl_array)
        max_loss = np.min(total_pnl_array)
        
        # Find break-even points
        break_even_points = []
        for i in range(len(total_pnl) - 1):
            if (total_pnl[i] <= 0 and total_pnl[i+1] > 0) or \
               (total_pnl[i] >= 0 and total_pnl[i+1] < 0):
                # Interpolate to find exact break-even
                be_price = price_changes[i] + (price_changes[i+1] - price_changes[i]) * \
                          (-total_pnl[i] / (total_pnl[i+1] - total_pnl[i]))
                break_even_points.append(be_price)
        
        # Calculate expected value using realistic probability from IV
        expected_move = self.calculate_expected_move(
            binary_params.current_price,
            binary_params.implied_volatility,
            binary_params.time_to_expiry
        )
        expected_move_pct = expected_move / binary_params.current_price
        
        # Find indices for expected outcomes
        up_idx = np.argmin(np.abs(price_changes - expected_move_pct))
        down_idx = np.argmin(np.abs(price_changes + expected_move_pct))
        
        expected_value = realistic_prob * total_pnl[up_idx] + (1 - realistic_prob) * total_pnl[down_idx]
        
        # Calculate liquidation prices for leveraged position
        # Liquidation occurs when loss = collateral (hedge_amount)
        # For long: liquidation when price drops by (1/leverage) * 100%
        # For short: liquidation when price rises by (1/leverage) * 100%
        liquidation_long = None
        liquidation_short = None
        
        if hedge_params.leverage > 1:
            liquidation_pct = -100.0 / hedge_params.leverage  # Negative for long position
            
            if hedge_params.hedge_direction == 'long':
                liquidation_long = liquidation_pct / 100.0  # Convert to decimal
            else:  # short
                liquidation_short = -liquidation_pct / 100.0  # Positive for short position
        
        self.results = {
            'price_changes': price_changes,
            'total_pnl': total_pnl,
            'binary_pnl': binary_pnl,
            'hedge_pnl': hedge_pnl,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'break_even_points': break_even_points,
            'expected_value': expected_value,
            'current_price': binary_params.current_price,
            'strike_price': binary_params.strike_price,
            'realistic_probability': realistic_prob,
            'expected_move': expected_move,
            'implied_volatility': binary_params.implied_volatility,
            'time_to_expiry': binary_params.time_to_expiry,
            'liquidation_long': liquidation_long,
            'liquidation_short': liquidation_short,
            'leverage': hedge_params.leverage,
            'hedge_direction': hedge_params.hedge_direction,
            'apply_fees': hedge_params.apply_fees,
            'fee_rate': hedge_params.fee_rate
        }
        
        return self.results
