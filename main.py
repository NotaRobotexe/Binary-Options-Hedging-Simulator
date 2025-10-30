"""
Binary Options Hedging Simulator
Main entry point for the application
"""
import tkinter as tk
import signal
import sys

from gui import SimulatorGUI


def main():
    # Signal handler for clean exit on Ctrl+C
    def signal_handler(sig, frame):
        print("\nExiting gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    root = tk.Tk()
    
    # Also handle window close button properly
    def on_closing():
        root.quit()
        root.destroy()
        sys.exit(0)
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    app = SimulatorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
