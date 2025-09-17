"""
TUI Replay Application

Interactive terminal-based application for replaying recorded MiniTel-Lite sessions.
Supports navigation through session steps with keyboard controls.
"""

import curses
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from session.replay import SessionReplayer

logger = logging.getLogger(__name__)


class ReplayTUI:
    """
    Text User Interface for replaying MiniTel-Lite sessions.
    
    Controls:
    - N/n: Next step
    - P/p: Previous step  
    - Q/q: Quit
    - R/r: Reload session
    - H/h: Help
    """
    
    def __init__(self, session_file: str):
        self.session_file = session_file
        self.replayer = SessionReplayer(session_file)
        self.stdscr = None
        self.show_help = False
        
    def initialize_curses(self):
        """Initialize curses environment"""
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        curses.curs_set(0)  # Hide cursor
        
        # Initialize color pairs if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Info
            curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Header
    
    def cleanup_curses(self):
        """Cleanup curses environment"""
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
    
    def draw_header(self, y: int = 0) -> int:
        """Draw application header"""
        max_y, max_x = self.stdscr.getmaxyx()
        
        # Title
        title = "🎬 MiniTel-Lite Session Replay - LIGHTMAN Mission Analysis"
        if len(title) <= max_x:
            self.stdscr.addstr(y, (max_x - len(title)) // 2, title, 
                             curses.color_pair(5) | curses.A_BOLD)
        
        # Session info
        session_info = self.replayer.get_session_info()
        if session_info:
            info_line = f"Session: {session_info.get('session_id', 'unknown')} | Duration: {session_info.get('duration', 0):.1f}s"
            if len(info_line) <= max_x:
                self.stdscr.addstr(y + 1, (max_x - len(info_line)) // 2, info_line, curses.color_pair(4))
        
        # Separator
        separator = "=" * min(80, max_x - 2)
        self.stdscr.addstr(y + 3, (max_x - len(separator)) // 2, separator)
        
        return y + 4
    
    def draw_controls(self, y: int) -> int:
        """Draw control instructions"""
        max_y, max_x = self.stdscr.getmaxyx()
        
        controls = [
            "Controls: [N]ext | [P]revious | [Q]uit | [R]eload | [H]elp"
        ]
        
        for i, control in enumerate(controls):
            if len(control) <= max_x:
                self.stdscr.addstr(y + i, (max_x - len(control)) // 2, control, curses.color_pair(3))
        
        return y + len(controls) + 1
    
    def draw_step_info(self, y: int) -> int:
        """Draw current step information"""
        max_y, max_x = self.stdscr.getmaxyx()
        
        current_step, total_steps = self.replayer.get_step_position()
        step_data = self.replayer.format_current_step()
        
        if "error" in step_data:
            self.stdscr.addstr(y, 2, f"Error: {step_data['error']}", curses.color_pair(2))
            return y + 2
        
        # Step position
        position_text = f"Step {current_step} of {total_steps}"
        self.stdscr.addstr(y, 2, position_text, curses.color_pair(5) | curses.A_BOLD)
        
        # Progress bar
        if total_steps > 0:
            bar_width = min(50, max_x - 20)
            progress = (current_step - 1) / max(total_steps - 1, 1)
            filled = int(progress * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            progress_text = f"[{bar}] {progress*100:.1f}%"
            self.stdscr.addstr(y, max_x - len(progress_text) - 2, progress_text, curses.color_pair(4))
        
        y += 2
        
        # Step details
        details = [
            f"Timestamp: {step_data.get('timestamp', 'N/A')}",
            f"Direction: {step_data.get('direction', 'N/A')}",
            f"Command:   {step_data.get('command', 'N/A')}",
            f"Nonce:     {step_data.get('nonce', 'N/A')}",
        ]
        
        if step_data.get('payload'):
            details.append(f"Payload:   {step_data['payload']}")
        
        for detail in details:
            if y < max_y - 2 and len(detail) <= max_x - 4:
                # Color code based on direction
                color = curses.color_pair(1) if "request" in step_data.get('direction', '').lower() else curses.color_pair(4)
                self.stdscr.addstr(y, 4, detail, color)
                y += 1
        
        # Frame hex (truncated)
        if step_data.get('frame_hex') and y < max_y - 3:
            y += 1
            self.stdscr.addstr(y, 4, "Frame (hex):", curses.color_pair(3))
            y += 1
            frame_hex = step_data['frame_hex']
            
            # Split hex into readable chunks
            chunk_size = max_x - 8
            for i in range(0, len(frame_hex), chunk_size):
                if y >= max_y - 2:
                    self.stdscr.addstr(y, 6, "... (truncated)", curses.color_pair(3))
                    break
                chunk = frame_hex[i:i + chunk_size]
                self.stdscr.addstr(y, 6, chunk, curses.color_pair(4))
                y += 1
        
        return y
    
    def draw_help(self, y: int) -> int:
        """Draw help information"""
        max_y, max_x = self.stdscr.getmaxyx()
        
        help_text = [
            "",
            "🔧 LIGHTMAN Mission Analysis Tool",
            "",
            "Navigation Controls:",
            "  N / n     - Move to next step",
            "  P / p     - Move to previous step", 
            "  Q / q     - Quit application",
            "  R / r     - Reload session file",
            "  H / h     - Toggle this help",
            "",
            "Purpose:",
            "  Analyze recorded MiniTel-Lite protocol sessions",
            "  Step through request/response sequences",
            "  Verify mission protocol compliance",
            "",
            "Press H to close help..."
        ]
        
        for i, line in enumerate(help_text):
            if y + i < max_y - 1 and len(line) <= max_x - 4:
                color = curses.color_pair(5) if line.startswith("🔧") else curses.color_pair(4)
                self.stdscr.addstr(y + i, 4, line, color)
        
        return y + len(help_text)
    
    def draw_screen(self):
        """Draw the complete screen"""
        max_y, max_x = self.stdscr.getmaxyx()
        self.stdscr.clear()
        
        y = 0
        
        # Header
        y = self.draw_header(y)
        
        # Controls
        y = self.draw_controls(y)
        
        if self.show_help:
            # Help screen
            self.draw_help(y)
        else:
            # Step information
            self.draw_step_info(y)
        
        # Status line
        status = f"File: {Path(self.session_file).name}"
        if len(status) <= max_x - 2:
            self.stdscr.addstr(max_y - 1, 1, status, curses.color_pair(3))
        
        self.stdscr.refresh()
    
    def handle_input(self, key: int) -> bool:
        """Handle keyboard input. Returns False to quit."""
        
        if key in (ord('q'), ord('Q')):
            return False
            
        elif key in (ord('n'), ord('N')):
            if not self.show_help:
                self.replayer.next_step()
                
        elif key in (ord('p'), ord('P')):
            if not self.show_help:
                self.replayer.previous_step()
                
        elif key in (ord('h'), ord('H')):
            self.show_help = not self.show_help
            
        elif key in (ord('r'), ord('R')):
            if not self.show_help:
                # Reload session
                try:
                    if self.replayer.load_session():
                        self.stdscr.addstr(0, 0, "Session reloaded!", curses.color_pair(1))
                        self.stdscr.refresh()
                        curses.napms(1000)  # Show message for 1 second
                except Exception as e:
                    logger.error(f"Failed to reload session: {e}")
        
        return True
    
    def run(self) -> bool:
        """Run the TUI application"""
        try:
            # Load session
            if not self.replayer.load_session():
                print(f"❌ Failed to load session: {self.session_file}")
                return False
            
            self.initialize_curses()
            
            # Main event loop
            while True:
                self.draw_screen()
                
                try:
                    key = self.stdscr.getch()
                    if not self.handle_input(key):
                        break
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            logger.error(f"TUI error: {e}")
            return False
        finally:
            self.cleanup_curses()
        
        return True


def main():
    """Main entry point for replay TUI"""
    if len(sys.argv) != 2:
        print("Usage: python replay_app.py <session_file.json>")
        print("Example: python replay_app.py recordings/session_20250917_124530.json")
        sys.exit(1)
    
    session_file = sys.argv[1]
    
    if not Path(session_file).exists():
        print(f"❌ Session file not found: {session_file}")
        sys.exit(1)
    
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler('replay_tui.log')]
    )
    
    print(f"🎬 Loading session: {session_file}")
    print("📋 Use N/P to navigate, H for help, Q to quit")
    
    tui = ReplayTUI(session_file)
    
    try:
        success = tui.run()
        if not success:
            print("❌ TUI session failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Session replay interrupted")
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)
    
    print("👋 Session replay completed")


if __name__ == "__main__":
    main()