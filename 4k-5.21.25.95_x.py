import tkinter as tk
from tkinter import ttk, messagebox, font
import time
import webbrowser

class AppWindow(tk.Toplevel):
    """ Base class for draggable application windows """
    def __init__(self, master, title, width, height, x, y, on_close_callback=None, resizable=(False, False)):
        super().__init__(master)
        self.overrideredirect(True) # Remove default window decorations (title bar, borders)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.attributes("-topmost", True) # Keep on top initially, can be managed by lift

        self.title_str = title
        self.on_close_callback = on_close_callback
        self.master_app = master # Reference to the main CATOS25App

        # --- Custom Title Bar ---
        self.title_bar = tk.Frame(self, bg="#000080", relief="raised", bd=1, height=20)
        self.title_bar.pack(expand=False, fill="x", side="top")

        self.title_label = tk.Label(self.title_bar, text=title, bg="#000080", fg="white", font=("Arial", 9, "bold"))
        self.title_label.pack(side="left", padx=5)

        self.close_button = tk.Button(
            self.title_bar, text="X", bg="#c0c0c0", fg="black", 
            width=2, height=1, relief="raised", bd=1, font=("Marlett", 7), # Marlett might not render X correctly, fallback
            command=self.close_window
        )
        self.close_button.pack(side="right", padx=1, pady=1)
        
        # --- Content Area ---
        self.content_frame = tk.Frame(self, bg="#c0c0c0", bd=1, relief="sunken") # Default content bg
        self.content_frame.pack(expand=True, fill="both")

        # --- Make Draggable ---
        self.title_bar.bind("<ButtonPress-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.do_drag)
        self.title_label.bind("<ButtonPress-1>", self.start_drag) # Also allow dragging by label
        self.title_label.bind("<B1-Motion>", self.do_drag)

        # --- Bring to front on click ---
        self.bind("<ButtonPress-1>", self.bring_to_front)
        self.title_bar.bind("<ButtonPress-1>", self.bring_to_front, add='+') # Add to existing bindings
        self.content_frame.bind("<ButtonPress-1>", self.bring_to_front) # Clicking content also brings to front

        # Store initial offset for dragging
        self._drag_start_x = 0
        self._drag_start_y = 0

        if hasattr(master, 'register_open_window'):
            master.register_open_window(self)

    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.bring_to_front() # Also bring to front when starting drag

    def do_drag(self, event):
        x = self.winfo_x() - self._drag_start_x + event.x
        y = self.winfo_y() - self._drag_start_y + event.y
        
        # Constrain dragging within the main desktop area (approximate)
        # The main window is 600x400. Taskbar is 30px high. Desktop area is ~600x370.
        # We need to get the main window's position and size if possible for more accuracy
        # For simplicity, let's assume main window starts at (0,0) effectively for child Toplevels
        
        # Get dimensions of the main application window (CATOS25App root)
        main_app_x = self.master_app.winfo_x()
        main_app_y = self.master_app.winfo_y()
        main_app_width = self.master_app.winfo_width()
        main_app_height = self.master_app.winfo_height() - 30 # Account for taskbar

        # New window position relative to screen
        new_screen_x = x
        new_screen_y = y

        # Keep window title bar visible
        min_x = main_app_x 
        min_y = main_app_y
        max_x = main_app_x + main_app_width - self.winfo_width()
        max_y = main_app_y + main_app_height - self.winfo_height() # Ensure bottom of window is visible

        # Clamp position
        final_x = max(min_x, min(new_screen_x, max_x))
        final_y = max(min_y, min(new_screen_y, max_y))

        self.geometry(f"+{final_x}+{final_y}")

    def close_window(self):
        if hasattr(self.master_app, 'unregister_open_window'):
            self.master_app.unregister_open_window(self)
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

    def bring_to_front(self, event=None): # event is optional
        self.lift()
        # self.attributes("-topmost", True) # This can be aggressive
        # self.after(10, lambda: self.attributes("-topmost", False)) # Release topmost after a moment

class NotepadApp(AppWindow):
    def __init__(self, master, x=60, y=60):
        super().__init__(master, "Untitled - Notepad", 400, 300, x, y)
        self.content_frame.config(bg="white") # Notepad content area is white
        
        self.text_area = tk.Text(
            self.content_frame, wrap="word", undo=True,
            font=("Courier New", 10), relief="sunken", bd=1,
            bg="white", fg="black" 
        )
        self.text_area.pack(expand=True, fill="both", padx=2, pady=2)
        self.text_area.insert("1.0", "Meow! Type your cute notes here...")
        self.text_area.bind("<FocusIn>", lambda e: self.text_area_focus_in())
        self.initial_text_cleared = False

    def text_area_focus_in(self):
        if not self.initial_text_cleared:
            current_content = self.text_area.get("1.0", "end-1c")
            if current_content == "Meow! Type your cute notes here...":
                self.text_area.delete("1.0", "end")
            self.initial_text_cleared = True
            
    def bring_to_front(self, event=None):
        super().bring_to_front(event)
        # If text area exists, ensure it gets focus after window is lifted
        if hasattr(self, 'text_area') and self.text_area:
            self.text_area.focus_set()


class CalculatorApp(AppWindow):
    def __init__(self, master, x=100, y=100):
        super().__init__(master, "Calculator", 250, 320, x, y) # Increased height for better layout
        self.content_frame.config(bg="#c0c0c0") # Calculator background

        self.display_var = tk.StringVar(value="0")
        self.current_input = "0"
        self.first_operand = None
        self.operator = None
        self.waiting_for_second_operand = False

        display_font = ("Consolas", 16, "bold")
        button_font = ("Arial", 10, "bold")

        # Display
        display_label = tk.Label(
            self.content_frame, textvariable=self.display_var, font=display_font,
            anchor="e", bg="#e0e0e0", fg="black", relief="sunken", bd=2, padx=5, pady=5
        )
        display_label.pack(pady=5, padx=5, fill="x")

        # Buttons Frame
        buttons_frame = tk.Frame(self.content_frame, bg="#c0c0c0")
        buttons_frame.pack(expand=True, fill="both", padx=5, pady=5)

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('C', 4, 1), ('=', 4, 2), ('+', 4, 3),
        ]

        for (text, r, c) in buttons:
            btn = tk.Button(
                buttons_frame, text=text, font=button_font,
                relief="raised", bd=2, bg="#c0c0c0", activebackground="#b0b0b0",
                command=lambda t=text: self.on_button_press(t)
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2, ipady=5)

        for i in range(5): # 0-4 rows
            buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4): # 0-3 columns
            buttons_frame.grid_columnconfigure(i, weight=1)
            
    def on_button_press(self, char):
        if char.isdigit() or (char == '.' and '.' not in self.current_input):
            if self.waiting_for_second_operand:
                self.current_input = char
                self.waiting_for_second_operand = False
            else:
                if self.current_input == "0" and char != '.':
                    self.current_input = char
                else:
                    self.current_input += char
        elif char in ['/', '*', '-', '+']:
            if self.first_operand is not None and self.operator and not self.waiting_for_second_operand:
                self.calculate_result() # Calculate intermediate result
            
            try:
                self.first_operand = float(self.current_input)
            except ValueError:
                self.current_input = "Error"
                self.display_var.set(self.current_input)
                return

            self.operator = char
            self.waiting_for_second_operand = True
        elif char == '=':
            self.calculate_result()
        elif char == 'C':
            self.clear_calculator()
        
        if self.current_input != "Error": # Don't update display if error is already shown by calculate_result
            self.display_var.set(self.current_input if len(self.current_input) < 15 else self.current_input[:15])


    def calculate_result(self):
        if self.operator is None or self.first_operand is None or self.waiting_for_second_operand:
            # Not enough info to calculate, or waiting for second op (e.g. 5 + =)
            if self.operator and self.first_operand is not None: # Allows 5 += to be 5+5
                 second_operand = self.first_operand 
            else:
                return
        else:
            try:
                second_operand = float(self.current_input)
            except ValueError:
                self.current_input = "Error"
                self.display_var.set(self.current_input)
                self.operator = None # Reset operator on error
                return

        result = 0
        if self.operator == '+': result = self.first_operand + second_operand
        elif self.operator == '-': result = self.first_operand - second_operand
        elif self.operator == '*': result = self.first_operand * second_operand
        elif self.operator == '/':
            if second_operand == 0:
                self.current_input = "Error"
                self.display_var.set(self.current_input)
                self.operator = None # Reset operator
                self.first_operand = None
                self.waiting_for_second_operand = False
                return
            result = self.first_operand / second_operand
        
        # Format result: if it's an integer, show as int, else float (limit precision)
        if result == int(result):
            self.current_input = str(int(result))
        else:
            self.current_input = str(round(result, 8))

        self.display_var.set(self.current_input if len(self.current_input) < 15 else self.current_input[:15])
        self.first_operand = float(self.current_input) # Result becomes the new first_operand for chained ops
        # self.operator = None # Clear operator after '='
        self.waiting_for_second_operand = True # Ready for a new number or new operator


    def clear_calculator(self):
        self.current_input = "0"
        self.first_operand = None
        self.operator = None
        self.waiting_for_second_operand = False
        self.display_var.set(self.current_input)

class MinesweeperApp(AppWindow):
    def __init__(self, master, x=150, y=150):
        super().__init__(master, "Minesweeper", 300, 280, x, y)
        self.content_frame.config(bg="#c0c0c0")
        
        label_font = ("Arial", 10)
        tk.Label(self.content_frame, text="Minesweeper - CATOS25", font=("Arial", 12, "bold"), bg="#c0c0c0").pack(pady=10)
        tk.Label(self.content_frame, text="Purrfectly under construction, nya~!\nThis is a placeholder.", font=label_font, bg="#c0c0c0").pack(pady=5)
        
        game_area_placeholder = tk.Frame(self.content_frame, width=150, height=150, bg="#bdbdbd", relief="sunken", bd=2)
        game_area_placeholder.pack(pady=10)
        tk.Label(game_area_placeholder, text="(Game Area)", font=label_font, bg="#bdbdbd").pack(expand=True)

class CATOS25App:
    def __init__(self, root):
        self.root = root
        self.root.title("CATOS25 by CATSEEKV3")
        self.root.geometry("600x400")
        self.root.resizable(False, False) # Disable resizing and maximize button
        self.root.configure(bg="#008080") # Windows 95 teal desktop

        self.open_app_windows = {} # To track unique app instances {app_id: window_object}
        self.window_id_counter = 0

        # --- Desktop Area ---
        self.desktop = tk.Frame(self.root, bg="#008080") # Teal background
        self.desktop.place(x=0, y=0, relwidth=1, height=370) # Full width, height minus taskbar

        self.create_desktop_icons()

        # --- Taskbar ---
        self.taskbar = tk.Frame(self.root, bg="#c0c0c0", height=30, relief="raised", bd=1)
        self.taskbar.pack(side="bottom", fill="x")

        self.create_start_button()
        self.create_clock()
        
        self.start_menu_visible = False
        self.start_menu = None # Will be created on first click

        # Close start menu if clicking outside
        self.root.bind("<Button-1>", self.hide_start_menu_if_outside)
        self.desktop.bind("<Button-1>", self.hide_start_menu_if_outside) # Also for desktop clicks

        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

        print("CATOS25 purred to life! Meow! So exciting! ^_^ Welcome by CATSEEKV3!")

    def get_next_window_id(self):
        self.window_id_counter += 1
        return f"app_win_{self.window_id_counter}"

    def register_open_window(self, window_instance):
        # This might not be strictly needed if AppWindow handles its own lifecycle
        # but can be useful for global management if required later.
        pass

    def unregister_open_window(self, window_instance):
        pass


    def create_desktop_icons(self):
        icon_font = ("Arial", 8)
        icon_bg = "#008080" # Desktop background
        icon_fg = "white"
        icon_width = 10 # characters
        
        icons_data = [
            ("📝\nNotepad", self.open_notepad),
            ("🧮\nCalculator", self.open_calculator),
            ("💣\nMines", self.open_minesweeper),
            ("DOOM\nDoom", self.open_doom)
        ]
        
        current_x, current_y = 10, 10
        icon_height_pixels = 60 
        icon_width_pixels = 75

        for text, command in icons_data:
            icon_frame = tk.Frame(self.desktop, bg=icon_bg) # Frame for each icon
            
            # Using a Label for the icon image/text part
            icon_label_part = tk.Label(
                icon_frame, text=text.split('\n')[0], font=("Arial", 16), 
                bg="#c0c0c0", fg="black", relief="raised", bd=1, width=2, height=1
            )
            if "DOOM" in text: # Special case for DOOM text icon
                 icon_label_part.config(font=("Arial", 8, "bold"), width=4, height=2)

            icon_label_part.pack(pady=(0,2))
            
            # Using a Label for the text part
            icon_text_part = tk.Label(
                icon_frame, text=text.split('\n')[1], font=icon_font, 
                bg=icon_bg, fg=icon_fg, wraplength=icon_width_pixels - 10
            )
            icon_text_part.pack()

            icon_frame.place(x=current_x, y=current_y, width=icon_width_pixels, height=icon_height_pixels)
            
            # Bind double click to the frame and its children
            icon_frame.bind("<Double-Button-1>", lambda e, cmd=command: cmd())
            icon_label_part.bind("<Double-Button-1>", lambda e, cmd=command: cmd())
            icon_text_part.bind("<Double-Button-1>", lambda e, cmd=command: cmd())

            current_y += icon_height_pixels + 10 # Next row
            if current_y + icon_height_pixels > 370: # If next icon goes off screen
                current_y = 10
                current_x += icon_width_pixels + 10


    def create_start_button(self):
        self.start_button = tk.Button(
            self.taskbar, text="Start", bg="#c0c0c0", relief="raised", bd=2,
            font=("Arial", 9, "bold"), command=self.toggle_start_menu,
            activebackground="#b0b0b0", padx=5
        )
        self.start_button.pack(side="left", padx=2, pady=2)

    def create_clock(self):
        self.clock_label = tk.Label(
            self.taskbar, text="", bg="#c0c0c0", relief="sunken", bd=1,
            font=("Arial", 9), padx=5
        )
        self.clock_label.pack(side="right", padx=2, pady=2)
        self.update_clock()

    def update_clock(self):
        time_string = time.strftime("%I:%M %p") # e.g., 02:30 PM
        self.clock_label.config(text=time_string)
        self.root.after(1000, self.update_clock) # Update every second

    def _create_start_menu_if_needed(self):
        if self.start_menu is None or not self.start_menu.winfo_exists():
            self.start_menu = tk.Menu(self.root, tearoff=0, bg="#c0c0c0", relief="raised", bd=2,
                                      activebackground="#000080", activeforeground="white",
                                      font=("Arial", 9))
            
            programs_menu = tk.Menu(self.start_menu, tearoff=0, bg="#c0c0c0", relief="raised", bd=1,
                                    activebackground="#000080", activeforeground="white", font=("Arial", 9))
            programs_menu.add_command(label="Notepad", command=self.open_notepad)
            programs_menu.add_command(label="Calculator", command=self.open_calculator)
            self.start_menu.add_cascade(label="Programs", menu=programs_menu)

            games_menu = tk.Menu(self.start_menu, tearoff=0, bg="#c0c0c0", relief="raised", bd=1,
                                 activebackground="#000080", activeforeground="white", font=("Arial", 9))
            games_menu.add_command(label="Mines", command=self.open_minesweeper)
            games_menu.add_command(label="Doom", command=self.open_doom)
            self.start_menu.add_cascade(label="Games", menu=games_menu)
            
            self.start_menu.add_separator()
            self.start_menu.add_command(label="Shut Down...", command=self.show_shutdown_message)

            # Bindings to hide menu when an item is clicked
            for i in range(programs_menu.index(tk.END) + 1 if programs_menu.index(tk.END) is not None else 0):
                programs_menu.entryconfig(i, command=lambda cmd=programs_menu.entrycget(i, "command"): [self.hide_start_menu(), self.root.after(10, cmd)] if cmd else self.hide_start_menu())
            for i in range(games_menu.index(tk.END) + 1 if games_menu.index(tk.END) is not None else 0):
                games_menu.entryconfig(i, command=lambda cmd=games_menu.entrycget(i, "command"): [self.hide_start_menu(), self.root.after(10, cmd)] if cmd else self.hide_start_menu())
            self.start_menu.entryconfig(self.start_menu.index("Shut Down..."), command=lambda: [self.hide_start_menu(), self.root.after(10, self.show_shutdown_message)])


    def toggle_start_menu(self):
        self._create_start_menu_if_needed()
        if self.start_menu_visible:
            self.hide_start_menu()
        else:
            self.show_start_menu()

    def show_start_menu(self):
        self._create_start_menu_if_needed()
        start_button_x = self.start_button.winfo_rootx()
        start_button_y = self.start_button.winfo_rooty()
        menu_y = start_button_y - self.start_menu.winfo_reqheight() # Position above button
        self.start_menu.tk_popup(start_button_x, menu_y)
        self.start_menu_visible = True
        self.start_button.config(relief="sunken")

    def hide_start_menu(self):
        if self.start_menu and self.start_menu_visible:
            self.start_menu.unpost()
            self.start_menu_visible = False
            self.start_button.config(relief="raised")

    def hide_start_menu_if_outside(self, event):
        # Hide if click is outside start_button and start_menu (if visible)
        if self.start_menu_visible:
            x, y = event.x_root, event.y_root
            menu_x, menu_y = self.start_menu.winfo_rootx(), self.start_menu.winfo_rooty()
            menu_width, menu_height = self.start_menu.winfo_width(), self.start_menu.winfo_height()
            
            button_x, button_y = self.start_button.winfo_rootx(), self.start_button.winfo_rooty()
            button_width, button_height = self.start_button.winfo_width(), self.start_button.winfo_height()

            in_menu = (menu_x <= x < menu_x + menu_width and
                       menu_y <= y < menu_y + menu_height)
            in_button = (button_x <= x < button_x + button_width and
                         button_y <= y < button_y + button_height)

            if not in_menu and not in_button:
                self.hide_start_menu()


    def _open_app_if_not_exists(self, app_class, unique_id_prefix, *args, **kwargs):
        # A simple way to prevent multiple instances of same "type" of app,
        # though the original HTML allowed multiple notepads/calculators.
        # For this version, let's allow multiple by generating unique IDs.
        win_id = self.get_next_window_id() # Generate a new ID for each window
        
        # Calculate initial position to be somewhat staggered or centered
        num_open = len([w for w in self.root.winfo_children() if isinstance(w, AppWindow) and w.winfo_exists()])
        offset_x = 20 + (num_open % 5) * 30
        offset_y = 20 + (num_open % 5) * 30
        
        # Ensure window opens within desktop bounds
        desktop_width = self.desktop.winfo_width()
        desktop_height = self.desktop.winfo_height()
        
        # Default app size (can be overridden by app_class specific sizes)
        app_width = kwargs.pop('width', 300) 
        app_height = kwargs.pop('height', 200)

        final_x = min(offset_x, desktop_width - app_width - 10) if desktop_width > app_width else 10
        final_y = min(offset_y, desktop_height - app_height - 10) if desktop_height > app_height else 10
        
        app_instance = app_class(self.root, x=self.root.winfo_x() + final_x, y=self.root.winfo_y() + final_y, *args, **kwargs)
        self.open_app_windows[win_id] = app_instance
        app_instance.bring_to_front()
        return app_instance

    def open_notepad(self):
        self._open_app_if_not_exists(NotepadApp, "notepad")

    def open_calculator(self):
        self._open_app_if_not_exists(CalculatorApp, "calculator")

    def open_minesweeper(self):
        self._open_app_if_not_exists(MinesweeperApp, "minesweeper")

    def open_doom(self):
        self.hide_start_menu() # Ensure start menu is hidden
        doom_url = "https://archive.org/embed/doom-shareware"
        try:
            webbrowser.open(doom_url)
            # Show a small info dialog that it's opening externally
            info_win = AppWindow(self.root, "Doom Launcher", 300, 100, 
                                 self.root.winfo_x() + 150, self.root.winfo_y() + 150)
            tk.Label(info_win.content_frame, 
                     text="Attempting to launch Doom\nin your web browser...", 
                     font=("Arial", 10), bg="#c0c0c0", pady=10).pack(expand=True)
            info_win.content_frame.config(bg="#c0c0c0")
            info_win.after(3000, info_win.close_window) # Auto-close after 3s
        except Exception as e:
            messagebox.showerror("Doom Launcher Error", f"Could not open web browser: {e}")


    def show_shutdown_message(self):
        self.hide_start_menu()
        # Use a custom AppWindow for the shutdown dialog to fit the OS theme
        shutdown_msg = (
            "Are you sure you want to 'shut down' CATOS25, sweetie?\n\n"
            "(This will just be a cute message, teehee!\n"
            "You can close the main window to really exit.)"
        )
        
        dialog_width = 350
        dialog_height = 180
        dialog_x = self.root.winfo_x() + (self.root.winfo_width() - dialog_width) // 2
        dialog_y = self.root.winfo_y() + (self.root.winfo_height() - dialog_height) // 2

        shutdown_dialog = AppWindow(self.root, "Shut Down CATOS25", dialog_width, dialog_height, dialog_x, dialog_y)
        shutdown_dialog.content_frame.config(bg="#c0c0c0", padx=10, pady=10)
        shutdown_dialog.attributes("-topmost", True) # Ensure it's on top

        tk.Label(shutdown_dialog.content_frame, text=shutdown_msg, justify="center", bg="#c0c0c0", font=("Arial", 10)).pack(pady=10, expand=True)
        
        ok_button = tk.Button(shutdown_dialog.content_frame, text="OK", width=10, bg="#c0c0c0", relief="raised", bd=2,
                              command=shutdown_dialog.close_window, font=("Arial", 9, "bold"))
        ok_button.pack(pady=10)
        ok_button.focus_set()

        # Override the 'X' button to just close this dialog
        shutdown_dialog.close_button.config(command=shutdown_dialog.close_window)


    def confirm_exit(self):
        if messagebox.askokcancel("Quit CATOS25", "Are you sure you want to exit CATOS25?"):
            # Cleanly destroy all open Toplevel windows before quitting
            children = list(self.root.children.values()) # Get a copy
            for widget_id in children:
                widget = self.root.nametowidget(widget_id)
                if isinstance(widget, AppWindow) and widget.winfo_exists():
                    widget.destroy()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    # Attempt to set a default font that's common, like Arial.
    # Tkinter's default font handling can be OS-dependent.
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="Arial", size=9)
    root.option_add("*Font", default_font)

    app = CATOS25App(root)
    root.mainloop()
