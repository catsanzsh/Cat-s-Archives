import tkinter as tk
from tkinter import ttk, messagebox, font
import time
import webbrowser
import multiprocessing # Added for Ursina process

# This function will run in a separate process for the Ursina app
# It needs to be defined at the top level of a module for multiprocessing
def launch_ursina_doom_process():
    try:
        from ursina import Ursina, Entity, color, Sky, camera, window
        from ursina.prefabs.first_person_controller import FirstPersonController
        from ursina import PointLight, AmbientLight, Text, load_texture

        app = Ursina(title='Mini Doom (Ursina) - CATOS25', borderless=False, development_mode=False)

        # Ground
        ground_texture = load_texture('brick') # Using a built-in texture, 'brick' often available
        if not ground_texture: # Fallback if 'brick' is not found by default path
            ground_texture = 'white_cube' # Ursina's default
            
        ground = Entity(model='quad', color=color.rgb(100,100,100), scale=(40, 40),
                        rotation_x=90, collider='box', texture=ground_texture)
        if ground_texture != 'white_cube': # Avoid scaling if it's just a color
             ground.texture_scale = (20,20)


        # Simple Walls
        wall_texture = load_texture('brick')
        if not wall_texture:
            wall_texture = 'shore' # Another texture often available

        wall_color = color.dark_gray
        
        walls_data = [
            {'scale': (40, 10, 1), 'position': (0, 5, 20)}, # Back
            {'scale': (40, 10, 1), 'position': (0, 5, -20)},# Front
            {'scale': (1, 10, 40), 'position': (20, 5, 0)},  # Right
            {'scale': (1, 10, 40), 'position': (-20, 5, 0)}  # Left
        ]
        for data in walls_data:
            wall = Entity(model='cube', color=wall_color, scale=data['scale'],
                   position=data['position'], collider='box', texture=wall_texture)
            if wall_texture not in ['white_cube', 'shore']: # Avoid scaling if it's a fallback color/simple texture
                if data['scale'][0] == 1: # Side walls
                    wall.texture_scale = (data['scale'][2]/2, data['scale'][1]/2)
                else: # Front/Back walls
                    wall.texture_scale = (data['scale'][0]/2, data['scale'][1]/2)


        # Player
        player = FirstPersonController(y=1, origin_y=-.5, speed=8)
        player.collider = 'box' # Add a collider to the player
        player.gravity = 1 # Standard gravity

        # A simple "target" or decoration
        Entity(model='sphere', color=color.red, position=(0, 1.5, 10), scale=2, collider='sphere')
        Entity(model='cube', color=color.blue, position=(-5, 1, 8), scale=(1,2,1), collider='box')
        Entity(model='cube', color=color.green, position=(5, 0.5, 12), scale=(1,1,1), collider='box')

        # Lighting
        AmbientLight(color=color.rgba(100, 100, 100, 0.2))
        PointLight(position=(0,10,0), color=color.white, shadows=False) # No shadows for simplicity

        # Sky
        sky_texture = load_texture('sky_sunset')
        if sky_texture:
            Sky(texture=sky_texture)
        else:
            Sky(color=color.rgb(80, 50, 50)) # A more doom-like sky color if texture fails

        # Instructions
        Text("CATOS25 - Ursina Doom Demo\nWASD/Arrows:Move | Mouse:Look | Space:Jump | P:Pause | Esc:Quit Ursina",
             origin=(0,0.5), scale=1.2, background=True, color=color.white, position=(0, 0.48), parent=camera.ui)

        # Simple pause state
        paused = False
        pause_text = Text("PAUSED\nPress P to Resume", origin=(0,0), scale=2, enabled=False, parent=camera.ui)

        def input(key):
            nonlocal paused
            if key == 'escape':
                app.quit()
            if key == 'p':
                paused = not paused
                player.enabled = not paused
                camera.enabled = not paused
                pause_text.enabled = paused
                if paused:
                    window.exit_button.enabled = True # Show exit button if game paused
                else:
                    window.exit_button.enabled = False # Hide when unpaused


        window.exit_button.enabled = False # Initially hide Ursina's default exit button
        window.fps_counter.enabled = True
        
        app.run()

    except ImportError:
        print("URSINA_ERROR: Ursina library not found. Please install it: pip install ursina")
    except Exception as e:
        print(f"URSINA_ERROR: An error occurred in the Ursina process: {e}")


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
            master.register_open_window(self, self.title_str) # Pass a unique identifier

    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.bring_to_front() # Also bring to front when starting drag

    def do_drag(self, event):
        x = self.winfo_x() - self._drag_start_x + event.x
        y = self.winfo_y() - self._drag_start_y + event.y
        
        main_app_x = self.master_app.winfo_x()
        main_app_y = self.master_app.winfo_y()
        main_app_width = self.master_app.winfo_width()
        main_app_height = self.master_app.winfo_height() - 30 # Account for taskbar

        min_x = main_app_x 
        min_y = main_app_y
        max_x = main_app_x + main_app_width - self.winfo_width()
        max_y = main_app_y + main_app_height - self.winfo_height() 

        final_x = max(min_x, min(x, max_x))
        final_y = max(min_y, min(y, max_y))

        self.geometry(f"+{final_x}+{final_y}")

    def close_window(self):
        if hasattr(self.master_app, 'unregister_open_window'):
            self.master_app.unregister_open_window(self) # Pass self to unregister
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

    def bring_to_front(self, event=None): # event is optional
        self.lift()

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
        if hasattr(self, 'text_area') and self.text_area:
            self.text_area.focus_set()


class CalculatorApp(AppWindow):
    def __init__(self, master, x=100, y=100):
        super().__init__(master, "Calculator", 250, 320, x, y) 
        self.content_frame.config(bg="#c0c0c0")

        self.display_var = tk.StringVar(value="0")
        self.current_input = "0"
        self.first_operand = None
        self.operator = None
        self.waiting_for_second_operand = False

        display_font = ("Consolas", 16, "bold")
        button_font = ("Arial", 10, "bold")

        display_label = tk.Label(
            self.content_frame, textvariable=self.display_var, font=display_font,
            anchor="e", bg="#e0e0e0", fg="black", relief="sunken", bd=2, padx=5, pady=5
        )
        display_label.pack(pady=5, padx=5, fill="x")

        buttons_frame = tk.Frame(self.content_frame, bg="#c0c0c0")
        buttons_frame.pack(expand=True, fill="both", padx=5, pady=5)

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3), # Added decimal point
            ('C', 0, 0, 2) # Clear button spanning 2 columns
        ]

        for btn_data in buttons:
            text = btn_data[0]
            r = btn_data[1]
            c = btn_data[2]
            cspan = btn_data[3] if len(btn_data) > 3 else 1
            
            btn = tk.Button(
                buttons_frame, text=text, font=button_font,
                relief="raised", bd=2, bg="#c0c0c0", activebackground="#b0b0b0",
                command=lambda t=text: self.on_button_press(t)
            )
            btn.grid(row=r, column=c, columnspan=cspan, sticky="nsew", padx=2, pady=2, ipady=5)
            if text == 'C': # Special style for C
                 btn.config(bg="#ff8080", activebackground="#ff6060")


        for i in range(5): 
            buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4): 
            buttons_frame.grid_columnconfigure(i, weight=1)
            
    def on_button_press(self, char):
        if char.isdigit() or (char == '.' and '.' not in self.current_input):
            if self.waiting_for_second_operand:
                self.current_input = char
                self.waiting_for_second_operand = False
            else:
                if self.current_input == "0" and char != '.':
                    self.current_input = char
                elif self.current_input == "Error": # Start new input after error
                    self.current_input = char
                else:
                    self.current_input += char
        elif char in ['/', '*', '-', '+']:
            if self.current_input == "Error": return # Don't process operators after error

            if self.first_operand is not None and self.operator and not self.waiting_for_second_operand:
                self.calculate_result()
                if self.current_input == "Error": return # Stop if calc resulted in error
            
            try:
                self.first_operand = float(self.current_input)
            except ValueError:
                self.current_input = "Error"
                self.display_var.set(self.current_input)
                return

            self.operator = char
            self.waiting_for_second_operand = True
        elif char == '=':
            if self.current_input == "Error": return
            self.calculate_result()
        elif char == 'C':
            self.clear_calculator()
        
        if self.current_input != "Error":
            self.display_var.set(self.current_input[:15]) # Limit display length


    def calculate_result(self):
        if self.operator is None or self.first_operand is None:
            return
        
        second_val_str = self.current_input
        # If waiting for second operand and '=' is pressed without new input, reuse first_operand or current_input if it's a result
        if self.waiting_for_second_operand and self.current_input == str(self.first_operand): 
            # This logic implies an operation like "5 * =" should result in 25
            # Or if current_input is already the result of a previous operation, reuse it.
            try:
                second_operand = float(self.current_input) # This will be the first_operand value
            except ValueError:
                 self.current_input = "Error"
                 self.operator = None
                 self.display_var.set(self.current_input)
                 return
        else:
            try:
                second_operand = float(self.current_input)
            except ValueError:
                self.current_input = "Error"
                self.operator = None # Reset operator on error
                self.display_var.set(self.current_input)
                return

        result = 0
        if self.operator == '+': result = self.first_operand + second_operand
        elif self.operator == '-': result = self.first_operand - second_operand
        elif self.operator == '*': result = self.first_operand * second_operand
        elif self.operator == '/':
            if second_operand == 0:
                self.current_input = "Error"
                self.display_var.set(self.current_input)
                self.operator = None 
                self.first_operand = None
                self.waiting_for_second_operand = False
                return
            result = self.first_operand / second_operand
        
        if result == int(result):
            self.current_input = str(int(result))
        else:
            self.current_input = str(round(result, 8))

        self.display_var.set(self.current_input[:15])
        try:
            self.first_operand = float(self.current_input) # Result becomes the new first_operand
        except ValueError: # Error case
             self.first_operand = None
        # self.operator = None # Clear operator after '=' if you want single operation
        self.waiting_for_second_operand = True # Ready for new number or new operator (chaining)


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
        self.root.resizable(False, False) 
        self.root.configure(bg="#008080") 

        self.open_app_windows = {} 
        self.window_id_counter = 0
        self.doom_process = None # MODIFIED: To keep track of the Doom process

        self.desktop = tk.Frame(self.root, bg="#008080") 
        self.desktop.place(x=0, y=0, relwidth=1, height=370) 

        self.create_desktop_icons()

        self.taskbar = tk.Frame(self.root, bg="#c0c0c0", height=30, relief="raised", bd=1)
        self.taskbar.pack(side="bottom", fill="x")

        self.create_start_button()
        self.create_clock()
        
        self.start_menu_visible = False
        self.start_menu = None 

        self.root.bind("<Button-1>", self.hide_start_menu_if_outside, add='+')
        self.desktop.bind("<Button-1>", self.hide_start_menu_if_outside, add='+') 

        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

        print("CATOS25 purred to life! Meow! So exciting! ^_^ Welcome by CATSEEKV3!")

    def get_next_window_id(self):
        self.window_id_counter += 1
        return f"app_win_{self.window_id_counter}"

    def register_open_window(self, window_instance, window_title_id):
        # Use a combination of title and a counter for more robust unique IDs if needed
        # For now, window_instance itself or its winfo_id() can serve as a key
        self.open_app_windows[window_instance] = window_instance # Store instance itself

    def unregister_open_window(self, window_instance):
        if window_instance in self.open_app_windows:
            del self.open_app_windows[window_instance]


    def create_desktop_icons(self):
        icon_font = ("Arial", 8)
        icon_bg = "#008080" 
        icon_fg = "white"
        
        icons_data = [
            ("📝\nNotepad", self.open_notepad),
            ("🧮\nCalculator", self.open_calculator),
            ("💣\nMines", self.open_minesweeper),
            ("🚀\nDoom", self.open_doom) # Changed icon for Doom
        ]
        
        current_x, current_y = 10, 10
        icon_height_pixels = 60 
        icon_width_pixels = 75

        for text, command in icons_data:
            icon_frame = tk.Frame(self.desktop, bg=icon_bg) 
            
            icon_symbol = text.split('\n')[0]
            icon_name = text.split('\n')[1]

            icon_label_part = tk.Label(
                icon_frame, text=icon_symbol, font=("Arial", 16), 
                bg="#c0c0c0", fg="black", relief="raised", bd=1, width=2, height=1
            )
            if "Doom" in icon_name: 
                 icon_label_part.config(font=("Segoe UI Emoji", 16) if "🚀" in icon_symbol else ("Arial", 8, "bold"), width=4 if "🚀" not in icon_symbol else 2, height=2 if "🚀" not in icon_symbol else 1)


            icon_label_part.pack(pady=(0,2))
            
            icon_text_part = tk.Label(
                icon_frame, text=icon_name, font=icon_font, 
                bg=icon_bg, fg=icon_fg, wraplength=icon_width_pixels - 10
            )
            icon_text_part.pack()

            icon_frame.place(x=current_x, y=current_y, width=icon_width_pixels, height=icon_height_pixels)
            
            icon_frame.bind("<Double-Button-1>", lambda e, cmd=command: cmd())
            icon_label_part.bind("<Double-Button-1>", lambda e, cmd=command: cmd())
            icon_text_part.bind("<Double-Button-1>", lambda e, cmd=command: cmd())

            current_y += icon_height_pixels + 10 
            if current_y + icon_height_pixels > 370: 
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
        time_string = time.strftime("%I:%M %p") 
        self.clock_label.config(text=time_string)
        self.root.after(1000, self.update_clock) 

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
            games_menu.add_command(label="Doom (Ursina)", command=self.open_doom) # MODIFIED
            self.start_menu.add_cascade(label="Games", menu=games_menu)
            
            self.start_menu.add_separator()
            self.start_menu.add_command(label="Shut Down...", command=self.show_shutdown_message)

            # Helper to wrap commands for hiding menu
            def create_menu_command(cmd_func):
                def wrapper():
                    self.hide_start_menu()
                    if cmd_func:
                        self.root.after(10, cmd_func) # Delay to allow menu to hide
                return wrapper

            for i in range(programs_menu.index(tk.END) + 1 if programs_menu.index(tk.END) is not None else 0):
                original_cmd = programs_menu.entrycget(i, "command")
                if original_cmd: # Ensure it's not a separator or cascade
                     programs_menu.entryconfig(i, command=create_menu_command(self.root.tk.eval(str(original_cmd))))


            for i in range(games_menu.index(tk.END) + 1 if games_menu.index(tk.END) is not None else 0):
                original_cmd = games_menu.entrycget(i, "command")
                if original_cmd:
                    games_menu.entryconfig(i, command=create_menu_command(self.root.tk.eval(str(original_cmd))))
            
            original_shutdown_cmd = self.start_menu.entrycget(self.start_menu.index("Shut Down..."), "command")
            if original_shutdown_cmd:
                self.start_menu.entryconfig(self.start_menu.index("Shut Down..."), command=create_menu_command(self.root.tk.eval(str(original_shutdown_cmd))))


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
        # Adjust menu_y to correctly position above the button
        self.start_menu.update_idletasks() # Ensure menu size is calculated
        menu_y = start_button_y - self.start_menu.winfo_reqheight() 
        self.start_menu.tk_popup(start_button_x, menu_y)
        self.start_menu_visible = True
        self.start_button.config(relief="sunken")

    def hide_start_menu(self, event=None): # event parameter for binding
        if self.start_menu and self.start_menu_visible:
            self.start_menu.unpost()
            self.start_menu_visible = False
            self.start_button.config(relief="raised")

    def hide_start_menu_if_outside(self, event):
        if self.start_menu_visible:
            # Check if the click was on the start button itself
            if event.widget == self.start_button:
                return 

            # Check if the click was inside the start menu
            # This is a bit tricky as the menu is a separate Toplevel
            try:
                if self.start_menu.winfo_geometry(): # Check if menu exists and has geometry
                    menu_x = self.start_menu.winfo_rootx()
                    menu_y = self.start_menu.winfo_rooty()
                    menu_width = self.start_menu.winfo_width()
                    menu_height = self.start_menu.winfo_height()

                    if not (menu_x <= event.x_root < menu_x + menu_width and \
                            menu_y <= event.y_root < menu_y + menu_height):
                        self.hide_start_menu()
                else: # Menu might not be fully realized yet or already gone
                    self.hide_start_menu()
            except tk.TclError: # If menu widget is destroyed
                self.hide_start_menu()


    def _open_app_if_not_exists(self, app_class, unique_id_prefix, *args, **kwargs):
        # Allow multiple instances by always creating a new one
        win_id = self.get_next_window_id() 
        
        num_open = len(self.open_app_windows)
        offset_x = 20 + (num_open % 5) * 30
        offset_y = 20 + (num_open % 5) * 30
        
        desktop_width = self.desktop.winfo_width() if self.desktop.winfo_width() > 1 else 600
        desktop_height = self.desktop.winfo_height() if self.desktop.winfo_height() > 1 else 370
        
        app_width = kwargs.get('width', 300) 
        app_height = kwargs.get('height', 200)

        # Ensure initial position is within desktop bounds roughly
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()

        final_x = root_x + min(offset_x, desktop_width - app_width - 10 if desktop_width > app_width else 5)
        final_y = root_y + min(offset_y, desktop_height - app_height - 10 if desktop_height > app_height else 5)
        
        app_instance = app_class(self.root, x=final_x, y=final_y, *args, **kwargs)
        # self.open_app_windows[win_id] = app_instance # Registration is now in AppWindow.__init__
        app_instance.bring_to_front()
        return app_instance

    def open_notepad(self):
        self._open_app_if_not_exists(NotepadApp, "notepad", width=400, height=300)

    def open_calculator(self):
        self._open_app_if_not_exists(CalculatorApp, "calculator", width=250, height=320)

    def open_minesweeper(self):
        self._open_app_if_not_exists(MinesweeperApp, "minesweeper", width=300, height=280)

    def open_doom(self): # MODIFIED for Ursina
        self.hide_start_menu() 

        if self.doom_process and self.doom_process.is_alive():
            messagebox.showinfo("Doom Launcher", "Doom (Ursina) is already running!", parent=self.root)
            # Optionally bring Ursina window to front if possible (OS dependent, not easy)
            return

        info_win = None
        try:
            # Show a small info dialog that it's opening
            dialog_x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
            dialog_y = self.root.winfo_y() + (self.root.winfo_height() - 120) // 2
            info_win = AppWindow(self.root, "Doom Launcher", 300, 120, dialog_x, dialog_y)
            tk.Label(info_win.content_frame,
                     text="Attempting to launch Ursina Doom Demo\nin a new window...\n\nThis may take a moment.\n(Press Esc in Ursina window to quit it)",
                     font=("Arial", 10), bg="#c0c0c0", pady=10, justify="center").pack(expand=True)
            info_win.content_frame.config(bg="#c0c0c0")
            self.root.update_idletasks() 

            # Launch Ursina in a new process
            self.doom_process = multiprocessing.Process(target=launch_ursina_doom_process, daemon=True)
            self.doom_process.start()

            if info_win:
                info_win.after(4000, info_win.close_window) 

        except Exception as e:
            messagebox.showerror("Doom Launcher Error", f"Could not launch Ursina Doom: {e}", parent=self.root)
            if self.doom_process and self.doom_process.is_alive():
                self.doom_process.terminate()
            self.doom_process = None
            if info_win and info_win.winfo_exists():
                info_win.close_window()


    def show_shutdown_message(self):
        self.hide_start_menu()
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
        # shutdown_dialog.attributes("-topmost", True) # Already set by AppWindow

        tk.Label(shutdown_dialog.content_frame, text=shutdown_msg, justify="center", bg="#c0c0c0", font=("Arial", 10)).pack(pady=10, expand=True)
        
        ok_button = tk.Button(shutdown_dialog.content_frame, text="OK", width=10, bg="#c0c0c0", relief="raised", bd=2,
                              command=shutdown_dialog.close_window, font=("Arial", 9, "bold"))
        ok_button.pack(pady=10)
        ok_button.focus_set()
        shutdown_dialog.close_button.config(command=shutdown_dialog.close_window)


    def confirm_exit(self): # MODIFIED to handle Doom process
        if messagebox.askokcancel("Quit CATOS25", "Are you sure you want to exit CATOS25?"):
            # Terminate Doom process if it's running
            if self.doom_process and self.doom_process.is_alive():
                print("Terminating Doom (Ursina) process...")
                self.doom_process.terminate() # Send SIGTERM
                # Wait a bit for the process to terminate gracefully
                self.doom_process.join(timeout=2) 
                if self.doom_process.is_alive():
                     print("Doom process did not terminate gracefully, killing...")
                     self.doom_process.kill() # Force kill
                     self.doom_process.join(timeout=1) # Wait for kill
                self.doom_process = None
                print("Doom (Ursina) process terminated.")

            # Cleanly destroy all open AppWindow Toplevel windows
            # Iterating over a copy of values because unregister_open_window modifies the dict
            for app_win_instance in list(self.open_app_windows.values()):
                if app_win_instance and app_win_instance.winfo_exists():
                    try:
                        app_win_instance.destroy()
                    except tk.TclError:
                        pass # Window might have been destroyed already
            self.open_app_windows.clear()
            
            self.root.destroy()


if __name__ == "__main__":
    multiprocessing.freeze_support() # MODIFIED: Important for multiprocessing

    root = tk.Tk()
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="Arial", size=9) # Or "Segoe UI" for a more modern Windows feel
    root.option_add("*Font", default_font)
    # For better Marlett 'X' on close button (might need specific font install)
    try:
        close_button_font = font.Font(family="Marlett", size=7)
        root.option_add("*Button.font", close_button_font) # This is too broad
    except tk.TclError:
        print("Marlett font not found, using default for close button.")
        # The AppWindow explicitly sets font for its close button, so this global option is less critical here.

    app = CATOS25App(root)
    root.mainloop()
