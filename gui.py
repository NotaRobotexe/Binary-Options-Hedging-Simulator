"""GUI for binary options simulator"""
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models import BinaryOptionParams, HedgeParams
from simulator import BinaryOptionsSimulator
from plotter import PlotManager


class SimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Binary Options Hedging Simulator")
        self.root.geometry("1600x900")
        
        self.simulator = BinaryOptionsSimulator()
        self.plotter = PlotManager()
        self.auto_refresh = tk.BooleanVar(value=True)
        self.setup_ui()
        
        # Run initial simulation
        self.run_simulation()
        
    def create_slider_with_label(self, parent, row, label_text, from_, to, initial_value, resolution=1):
        """Create a slider with label, value display, and manual entry"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(frame, text=label_text, width=25, anchor='w').pack(side=tk.LEFT)
        
        var = tk.DoubleVar(value=initial_value)
        
        # Manual entry field
        entry = ttk.Entry(frame, width=10)
        entry.insert(0, f"{initial_value:.2f}" if resolution < 1 else f"{int(initial_value)}")
        entry.pack(side=tk.RIGHT, padx=5)
        
        # Bind entry to update slider
        def on_entry_change(event):
            try:
                value = float(entry.get())
                if from_ <= value <= to:
                    var.set(value)
                    if self.auto_refresh.get():
                        # Force immediate simulation update
                        self.root.after(100, self.run_simulation)
                else:
                    # Value out of range, adjust slider range if needed
                    if value > to:
                        entry.delete(0, tk.END)
                        entry.insert(0, str(to))
                        var.set(to)
                    elif value < from_:
                        entry.delete(0, tk.END)
                        entry.insert(0, str(from_))
                        var.set(from_)
            except ValueError:
                pass
        
        entry.bind('<Return>', on_entry_change)
        entry.bind('<FocusOut>', on_entry_change)
        
        # Slider with logarithmic scale for large ranges
        range_size = to - from_
        use_log_scale = range_size > 1000
        
        if use_log_scale:
            # Use logarithmic scale for better control across wide ranges
            log_from = np.log10(max(from_, 1))
            log_to = np.log10(to)
            
            def log_to_linear(log_val):
                return 10 ** log_val
            
            def linear_to_log(linear_val):
                return np.log10(max(linear_val, 1))
            
            log_var = tk.DoubleVar(value=linear_to_log(initial_value))
            
            slider = ttk.Scale(frame, from_=log_from, to=log_to, variable=log_var, orient=tk.HORIZONTAL,
                              command=lambda v: self.on_slider_change_log(var, log_var, entry, resolution, log_to_linear))
        else:
            slider = ttk.Scale(frame, from_=from_, to=to, variable=var, orient=tk.HORIZONTAL,
                              command=lambda v: self.on_slider_change(var, entry, resolution))
        
        slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        return var
    
    def on_slider_change_log(self, var, log_var, entry, resolution, log_to_linear):
        """Handle slider value changes with logarithmic scaling"""
        log_value = log_var.get()
        value = log_to_linear(log_value)
        
        if resolution >= 1:
            value = round(value / resolution) * resolution
        
        var.set(value)
        entry.delete(0, tk.END)
        entry.insert(0, f"{value:.2f}" if resolution < 1 else f"{int(value)}")
        
        self.update_strike_distance()
        
        if self.auto_refresh.get():
            self.run_simulation()
        
    def on_slider_change(self, var, entry, resolution):
        """Handle slider value changes"""
        value = var.get()
        if resolution >= 1:
            value = round(value / resolution) * resolution
            var.set(value)
        
        entry.delete(0, tk.END)
        entry.insert(0, f"{value:.2f}" if resolution < 1 else f"{int(value)}")
        
        self.update_strike_distance()
        
        if self.auto_refresh.get():
            self.run_simulation()
    
    def update_strike_distance(self):
        """Update the strike distance label"""
        try:
            current = float(self.current_price.get())
            strike = float(self.strike_price.get())
            if current > 0:
                distance_pct = ((strike - current) / current) * 100
                color = 'green' if abs(distance_pct) < 5 else 'orange' if abs(distance_pct) < 20 else 'red'
                self.strike_distance_label.config(text=f"{distance_pct:+.2f}%", foreground=color)
        except:
            self.strike_distance_label.config(text="N/A", foreground='gray')
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Input frame with scrollbar
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Auto-refresh checkbox
        ttk.Checkbutton(input_frame, text="Auto-Refresh", variable=self.auto_refresh).grid(
            row=0, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        # Binary Option Parameters
        ttk.Label(input_frame, text="Binary Option Parameters", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, columnspan=3, pady=(10,5))
        
        self.current_price = self.create_slider_with_label(
            input_frame, 2, "Current Price ($):", 1, 150000, 100, resolution=1)
        
        self.strike_price = self.create_slider_with_label(
            input_frame, 3, "Strike Price ($):", 1, 150000, 100, resolution=1)
        
        # Strike distance display
        strike_distance_frame = ttk.Frame(input_frame)
        strike_distance_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(strike_distance_frame, text="Strike Distance:", width=25, anchor='w', 
                 font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.strike_distance_label = ttk.Label(strike_distance_frame, text="0.00%", width=15, anchor='e',
                                               font=('Arial', 10, 'bold'), foreground='purple')
        self.strike_distance_label.pack(side=tk.RIGHT, padx=5)
        
        self.investment = self.create_slider_with_label(
            input_frame, 5, "Investment Amount ($):", 1, 100000, 1000, resolution=1)
        
        self.payout_up = self.create_slider_with_label(
            input_frame, 6, "Payout Multiplier Up:", 1.0, 20.0, 1.6, resolution=0.1)
        
        self.payout_down = self.create_slider_with_label(
            input_frame, 7, "Payout Multiplier Down:", 1.0, 20.0, 1.2, resolution=0.1)
        
        self.prob_up = self.create_slider_with_label(
            input_frame, 8, "Probability Up:", 0.0, 1.0, 0.5, resolution=0.05)
        
        self.implied_volatility = self.create_slider_with_label(
            input_frame, 9, "Implied Volatility (%):", 5, 200, 30, resolution=5)
        
        self.time_to_expiry = self.create_slider_with_label(
            input_frame, 10, "Time to Expiry (days):", 0.1, 30, 7, resolution=0.5)
        
        # Binary Direction
        direction_frame = ttk.Frame(input_frame)
        direction_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(direction_frame, text="Binary Direction:", width=25, anchor='w').pack(side=tk.LEFT)
        self.binary_direction = ttk.Combobox(direction_frame, values=['up', 'down'], width=10, state='readonly')
        self.binary_direction.set('up')
        self.binary_direction.bind('<<ComboboxSelected>>', lambda e: self.on_combo_change())
        self.binary_direction.pack(side=tk.RIGHT, padx=5)
        
        # Hedge Parameters
        ttk.Label(input_frame, text="Hedging Parameters", font=('Arial', 10, 'bold')).grid(
            row=12, column=0, columnspan=3, pady=(15,5))
        
        self.hedge_amount = self.create_slider_with_label(
            input_frame, 13, "Hedge Amount ($):", 0, 100000, 500, resolution=1)
        
        self.leverage = self.create_slider_with_label(
            input_frame, 14, "Leverage:", 1, 300, 5, resolution=1)
        
        # Fees checkbox and slider
        fees_frame = ttk.Frame(input_frame)
        fees_frame.grid(row=15, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.apply_fees = tk.BooleanVar(value=False)
        fees_check = ttk.Checkbutton(fees_frame, text="Apply Trading Fees", variable=self.apply_fees,
                                     command=self.on_fees_toggle)
        fees_check.pack(side=tk.LEFT)
        
        self.fee_rate = self.create_slider_with_label(
            input_frame, 16, "Fee Rate (%):", 0.0, 1.0, 0.1, resolution=0.01)
        
        # Hedge Direction
        hedge_dir_frame = ttk.Frame(input_frame)
        hedge_dir_frame.grid(row=17, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(hedge_dir_frame, text="Hedge Direction:", width=25, anchor='w').pack(side=tk.LEFT)
        self.hedge_direction = ttk.Combobox(hedge_dir_frame, values=['long', 'short'], width=10, state='readonly')
        self.hedge_direction.set('short')
        self.hedge_direction.bind('<<ComboboxSelected>>', lambda e: self.on_combo_change())
        self.hedge_direction.pack(side=tk.RIGHT, padx=5)
        
        # Manual refresh button
        ttk.Button(input_frame, text="Refresh Now", command=self.run_simulation).grid(
            row=18, column=0, columnspan=3, pady=20)
        
        # Results display frame
        results_info_frame = ttk.LabelFrame(input_frame, text="Position Summary", padding="10")
        results_info_frame.grid(row=19, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=5)
        
        # Create text widget for results
        self.results_text = tk.Text(results_info_frame, height=20, width=40, font=('Courier', 9),
                                    bg='lightyellow', fg='black', relief=tk.SUNKEN, borderwidth=2)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Canvas for matplotlib
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=results_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def on_combo_change(self):
        """Handle combobox changes"""
        if self.auto_refresh.get():
            self.run_simulation()
    
    def on_fees_toggle(self):
        """Handle fees checkbox toggle"""
        if self.auto_refresh.get():
            self.run_simulation()
        
    def run_simulation(self):
        try:
            # Get parameters
            binary_params = BinaryOptionParams(
                current_price=float(self.current_price.get()),
                strike_price=float(self.strike_price.get()),
                payout_multiplier_up=float(self.payout_up.get()),
                payout_multiplier_down=float(self.payout_down.get()),
                investment_amount=float(self.investment.get()),
                probability_up=float(self.prob_up.get()),
                implied_volatility=float(self.implied_volatility.get()) / 100.0,  # Convert % to decimal
                time_to_expiry=float(self.time_to_expiry.get())
            )
            
            hedge_params = HedgeParams(
                hedge_amount=float(self.hedge_amount.get()),
                leverage=float(self.leverage.get()),
                hedge_direction=self.hedge_direction.get(),
                apply_fees=self.apply_fees.get(),
                fee_rate=float(self.fee_rate.get()) / 100.0  # Convert % to decimal
            )
            
            # Run simulation
            self.simulator.simulate_scenarios(
                binary_params,
                hedge_params,
                self.binary_direction.get()
            )
            
            # Plot results
            self.plotter.plot_results(self.simulator.results, self.fig)
            self.canvas.draw()
            
            # Update results text
            self.update_results_text()
            
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
    
    def update_results_text(self):
        """Update the results text widget with current simulation results"""
        results = self.simulator.results
        
        strike_distance_pct = ((results['strike_price'] - results['current_price']) / 
                              results['current_price']) * 100
        price_range_min = results['current_price'] * (1 + results['price_changes'][0])
        price_range_max = results['current_price'] * (1 + results['price_changes'][-1])
        
        info_text = "═══ POSITION DETAILS ═══\n"
        info_text += f"Current Price:    ${results['current_price']:,.2f}\n"
        info_text += f"Strike Price:     ${results['strike_price']:,.2f}\n"
        info_text += f"Strike Distance:  {strike_distance_pct:+.2f}%\n"
        info_text += f"Price Range:      ${price_range_min:,.2f}\n"
        info_text += f"                  to ${price_range_max:,.2f}\n\n"
        
        info_text += "═══ RISK METRICS ═══\n"
        info_text += f"Max Profit:       ${results['max_profit']:,.2f}\n"
        info_text += f"Max Loss:         ${results['max_loss']:,.2f}\n"
        info_text += f"Expected Value:   ${results['expected_value']:,.2f}\n"
        
        if results['break_even_points']:
            info_text += f"\nBreak-even Points:\n"
            for i, be in enumerate(results['break_even_points'], 1):
                be_price = results['current_price'] * (1 + be)
                info_text += f"  #{i}: {be*100:+.2f}% (${be_price:,.2f})\n"
        
        info_text += "\n═══ LEVERAGE & LIQUIDATION ═══\n"
        info_text += f"Leverage:         {results['leverage']:.0f}x\n"
        info_text += f"Hedge Direction:  {results['hedge_direction'].upper()}\n"
        
        # Get the actual hedge amount used
        hedge_amount_value = float(self.hedge_amount.get())
        position_size = hedge_amount_value * results['leverage']
        info_text += f"Hedge Collateral: ${hedge_amount_value:,.2f}\n"
        info_text += f"Position Size:    ${position_size:,.2f}\n"
        
        # Show fees if enabled
        if results.get('apply_fees'):
            total_fees = position_size * results['fee_rate'] * 2  # Entry + exit
            info_text += f"\nTrading Fees:     ENABLED\n"
            info_text += f"Fee Rate:         {results['fee_rate']*100:.3f}%\n"
            info_text += f"Total Fees:       ${total_fees:,.2f}\n"
        else:
            info_text += f"\nTrading Fees:     DISABLED\n"
        
        # Liquidation info
        if results['leverage'] > 1:
            if results.get('liquidation_long') is not None:
                liq_price_long = results['current_price'] * (1 + results['liquidation_long'])
                info_text += f"\nLiquidation:      {results['liquidation_long']*100:.2f}%\n"
                info_text += f"Liquidation $:    ${liq_price_long:,.2f}\n"
            elif results.get('liquidation_short') is not None:
                liq_price_short = results['current_price'] * (1 + results['liquidation_short'])
                info_text += f"\nLiquidation:      {results['liquidation_short']*100:.2f}%\n"
                info_text += f"Liquidation $:    ${liq_price_short:,.2f}\n"
        else:
            info_text += f"\nLiquidation:      No leverage (1x)\n"
        
        info_text += "\n═══ MARKET DATA ═══\n"
        info_text += f"Implied Vol:      {results['implied_volatility']*100:.1f}%\n"
        info_text += f"Time to Expiry:   {results['time_to_expiry']:.1f} days\n"
        info_text += f"Expected Move:    ${results['expected_move']:,.2f}\n"
        info_text += f"                  ({results['expected_move']/results['current_price']*100:.2f}%)\n"
        info_text += f"Win Probability:  {results['realistic_probability']*100:.1f}%"
        
        # Update text widget
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, info_text)
        self.results_text.config(state=tk.DISABLED)
