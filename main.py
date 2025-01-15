import gpiozero
import pygame
import time
import tkinter as tk
import json
import os

# Function to load the configuration file (with all rooms and their clues)
def load_config(config_file='config.json'):
    if not os.path.exists(config_file):
        print(f"Config file '{config_file}' not found.")
        return {}

    with open(config_file, 'r') as file:
        try:
            config = json.load(file)
            return config.get("rooms", {})
        except json.JSONDecodeError:
            print(f"Error reading the config file '{config_file}'. Make sure it is valid JSON.")
            return {}

# Load the rooms configuration
rooms_config = load_config()

# Initialize pygame mixer for sound playback
pygame.mixer.init()

# Create a tkinter window for displaying text
root = tk.Tk()
root.title("Clue Box")

# Make the window full screen
root.attributes('-fullscreen', True)
root.configure(bg='black')

# Set up a label to display text on the screen
label = tk.Label(root, text="", font=("Helvetica", 48), fg="white", bg="black", justify="center", wraplength=root.winfo_screenwidth()-50)
label.pack(expand=True)

# Variables for each room
button_press_start_time = None
button_hold_duration = 3  # seconds for reset
reset_triggered = False  # Variable to ensure reset happens only once
press_counts = {room: 0 for room in rooms_config}  # Dictionary to track press counts for each room

# Function to dynamically adjust the font size based on window size
def adjust_font_size(event=None):
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    font_size = int(min(window_width, window_height) / 10)
    label.config(font=("Helvetica", font_size), wraplength=window_width-50)

# Function to handle the reset action
def reset_app():
    global reset_triggered
    if not reset_triggered:
        print("Resetting the app...")  # Optional: print reset in the terminal
        label.config(text="")  # Clear text on screen
        pygame.mixer.stop()  # Stop any sounds if still playing
        for room in rooms_config:
            press_counts[room] = 0  # Reset the press count for all rooms
        reset_triggered = True  # Mark reset as triggered

# Function to smoothly transition between clues
def transition_to_clue(clue):
    """Handle the transition between clues smoothly"""
    label.config(text="")
    label.after(500, play_new_clue, clue)  # Delay before showing new clue

# Function to play a new clue
def play_new_clue(clue):
    """Play the sound and display the new clue text"""
    pygame.mixer.stop()  # Stop the current sound if still playing
    
    # Play the sound associated with the current clue
    try:
        sound = pygame.mixer.Sound(clue["sound"])
        sound.play()
    except pygame.error as e:
        print(f"Error loading sound {clue['sound']}: {e}")
    
    # Display the associated text on the screen
    label.config(text=clue["text"])

# Define the button press actions for each room dynamically
def create_button_handler(room_name, clues):
    def on_button_pressed():
        global button_press_start_time, reset_triggered
        
        button_press_start_time = time.time()
        print(f"{room_name} Button Pressed!")
        
        press_count = press_counts[room_name]
        if press_count < len(clues):
            clue = clues[press_count]
            transition_to_clue(clue)
        else:
            print(f"No more clues for {room_name}.")
            label.config(text=f"No more clues for {room_name}.")
        
        press_counts[room_name] += 1
        reset_triggered = False

    return on_button_pressed

# Set up buttons dynamically based on the rooms configuration
buttons = {}
for room_name, room_data in rooms_config.items():
    gpio_pin = room_data["gpio_pin"]
    clues = room_data["clues"]
    
    # Create a button for the room and assign its handler
    button = gpiozero.Button(gpio_pin, pull_up=True)
    button.when_pressed = create_button_handler(room_name, clues)
    buttons[room_name] = button

# Define the button hold check
def check_button_hold():
    global button_press_start_time, reset_triggered

    if any(button.is_pressed for button in buttons.values()):
        if button_press_start_time and (time.time() - button_press_start_time) >= button_hold_duration:
            reset_app()
    else:
        button_press_start_time = None

    root.after(100, check_button_hold)  # Recheck every 100ms

# Start the continuous button hold check
root.after(100, check_button_hold)  # Check hold status every 100ms

# Bind the resize event to adjust the font size dynamically
root.bind('<Configure>', adjust_font_size)

# Run the Tkinter event loop
root.mainloop()
