"""Plotting functionality for binary options simulator"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, AutoMinorLocator


class PlotManager:
    def __init__(self):
        pass
    
    def plot_results(self, results: dict, fig: Figure = None) -> Figure:
        """Plot simulation results"""
        if not results:
            raise ValueError("No simulation results to plot. Run simulate_scenarios first.")
        
        if fig is None:
            fig = plt.figure(figsize=(16, 10))
        else:
            fig.clear()
        
        # Main P&L plot - FULL SCREEN
        ax1 = fig.add_subplot(1, 1, 1)
        price_changes_pct = results['price_changes'] * 100
        
        # Plot main lines with thicker, more visible styling
        ax1.plot(price_changes_pct, results['total_pnl'], 'b-', linewidth=3, label='Total P&L', zorder=5)
        ax1.plot(price_changes_pct, results['binary_pnl'], 'r--', linewidth=2.5, label='Binary Option P&L', zorder=4)
        ax1.plot(price_changes_pct, results['hedge_pnl'], 'g--', linewidth=2.5, label='Hedge P&L', zorder=3)
        
        # Reference lines
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7, zorder=2)
        ax1.axvline(x=0, color='gray', linestyle='--', linewidth=2, alpha=0.6, label='Current Price', zorder=2)
        
        # Mark strike price location
        strike_move_pct = ((results['strike_price'] - results['current_price']) / 
                          results['current_price']) * 100
        ax1.axvline(x=strike_move_pct, color='purple', linestyle='-.', linewidth=2.5, 
                   label=f'Strike: ${results["strike_price"]:.2f} ({strike_move_pct:+.1f}%)', zorder=2)
        
        # Mark liquidation points for leverage
        if 'liquidation_long' in results and results['liquidation_long'] is not None:
            liq_pct_long = results['liquidation_long'] * 100
            ax1.axvline(x=liq_pct_long, color='red', linestyle='--', linewidth=2.5, alpha=0.8,
                       label=f'Liquidation (Long) ({liq_pct_long:.2f}%)', zorder=2)
        
        if 'liquidation_short' in results and results['liquidation_short'] is not None:
            liq_pct_short = results['liquidation_short'] * 100
            ax1.axvline(x=liq_pct_short, color='darkred', linestyle='--', linewidth=2.5, alpha=0.8,
                       label=f'Liquidation (Short) ({liq_pct_short:.2f}%)', zorder=2)
        
        # Mark break-even points
        for i, be in enumerate(results['break_even_points']):
            label = f'Break-even ({be*100:.1f}%)' if i == 0 else None
            ax1.axvline(x=be*100, color='orange', linestyle=':', linewidth=2.5, label=label, zorder=2)
        
        # Fill profit/loss regions
        ax1.fill_between(price_changes_pct, results['total_pnl'], 0, 
                         where=np.array(results['total_pnl']) >= 0, 
                         color='green', alpha=0.15, label='Profit Region', zorder=1)
        ax1.fill_between(price_changes_pct, results['total_pnl'], 0, 
                         where=np.array(results['total_pnl']) < 0, 
                         color='red', alpha=0.15, label='Loss Region', zorder=1)
        
        # Labels and title
        ax1.set_xlabel('Price Change from Current (%)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Profit/Loss ($)', fontsize=14, fontweight='bold')
        ax1.set_title('Binary Options P&L Analysis with Hedging', fontsize=16, fontweight='bold', pad=20)
        
        # Add more detailed grid
        ax1.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, which='major')
        ax1.grid(True, alpha=0.2, linestyle=':', linewidth=0.5, which='minor')
        ax1.minorticks_on()
        
        # Format axis to show more tick marks
        ax1.xaxis.set_major_locator(MaxNLocator(nbins=20, prune=None))
        ax1.yaxis.set_major_locator(MaxNLocator(nbins=15, prune=None))
        ax1.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax1.yaxis.set_minor_locator(AutoMinorLocator(4))
        
        ax1.legend(loc='best', fontsize=11, framealpha=0.9)
        
        plt.tight_layout()
        return fig
