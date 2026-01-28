"""
AutoSaveManager - Handles automatic saving of annotations with timer.

This manager is responsible for:
- Managing auto-save timer
- Triggering saves at specified intervals
- Managing auto-save state (enabled/disabled)
"""

import logging
from PyQt5.QtCore import QTimer


class AutoSaveManager:
    """Manages automatic saving of annotations."""
    
    DEFAULT_INTERVAL_MS = 5000  # 5 seconds
    
    def __init__(self, save_callback=None):
        """
        Initialize the AutoSaveManager.
        
        Args:
            save_callback: Function to call when auto-save triggers
        """
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_timeout)
        self.save_callback = save_callback
        self.enabled = False
        self.interval_ms = self.DEFAULT_INTERVAL_MS
        logging.debug("AutoSaveManager initialized")
    
    def set_save_callback(self, callback) -> None:
        """
        Set the callback function to call when auto-save triggers.
        
        Args:
            callback: Function to call on auto-save
        """
        self.save_callback = callback
        logging.debug("Auto-save callback set")
    
    def enable(self) -> None:
        """Enable auto-save."""
        if not self.enabled:
            self.enabled = True
            self.timer.start(self.interval_ms)
            logging.info(f"Auto-save enabled (interval: {self.interval_ms}ms)")
    
    def disable(self) -> None:
        """Disable auto-save."""
        if self.enabled:
            self.enabled = False
            self.timer.stop()
            logging.info("Auto-save disabled")
    
    def toggle(self) -> bool:
        """
        Toggle auto-save on/off.
        
        Returns:
            bool: New state (True if enabled, False if disabled)
        """
        if self.enabled:
            self.disable()
        else:
            self.enable()
        return self.enabled
    
    def is_enabled(self) -> bool:
        """
        Check if auto-save is enabled.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return self.enabled
    
    def set_interval(self, interval_ms: int) -> None:
        """
        Set the auto-save interval.
        
        Args:
            interval_ms: Interval in milliseconds
        """
        if interval_ms <= 0:
            logging.warning(f"Invalid interval {interval_ms}ms, using default")
            interval_ms = self.DEFAULT_INTERVAL_MS
        
        self.interval_ms = interval_ms
        
        # If timer is running, restart with new interval
        if self.enabled:
            self.timer.stop()
            self.timer.start(self.interval_ms)
        
        logging.info(f"Auto-save interval set to {interval_ms}ms")
    
    def get_interval(self) -> int:
        """
        Get the current auto-save interval.
        
        Returns:
            int: Interval in milliseconds
        """
        return self.interval_ms
    
    def _on_timer_timeout(self) -> None:
        """Internal handler for timer timeout."""
        if self.save_callback:
            logging.debug("Auto-save triggered")
            try:
                self.save_callback()
            except Exception as e:
                logging.error(f"Error during auto-save: {e}")
        else:
            logging.warning("Auto-save triggered but no callback set")
    
    def reset(self) -> None:
        """Reset the timer."""
        if self.enabled:
            self.timer.stop()
            self.timer.start(self.interval_ms)
            logging.debug("Auto-save timer reset")
