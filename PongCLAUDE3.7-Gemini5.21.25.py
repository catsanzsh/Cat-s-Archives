import pygame
import sys
import random
import numpy as np

# --- Retro-Style Pong Configuration ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (120, 120, 120) # For visual details

PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
PADDLE_SPEED = 7 # AI paddle speed (used for AI, player paddle uses mouse)
BALL_SIZE = 15 # Square ball for a retro feel
BALL_SPEED_X_INITIAL = 5
BALL_SPEED_Y_INITIAL = 5

WINNING_SCORE = 5

# Sound generation - Improved initialization order
pygame.mixer.pre_init(44100, -16, 2, 1024)  # Increased buffer size and using stereo
pygame.init()
pygame.mixer.init()  # Ensure mixer is definitely initialized

def make_square_wave_sound_with_decay(frequency=440, duration=0.05, volume=0.3, sample_rate=44100):
    """Generates a square wave sound with a simple linear decay."""
    num_samples = int(sample_rate * duration)
    # Ensure num_samples is at least 1
    if num_samples <= 0:
        num_samples = 1
    
    # Create stereo sound array (2 channels)
    sound_array = np.zeros((num_samples, 2), dtype=np.int16)
    period_samples = sample_rate / frequency
    # Ensure period_samples is not zero
    if period_samples <= 0:
        period_samples = 1
    
    initial_amplitude = int(32767 * volume)
    
    for i in range(num_samples):
        # Calculate decay
        current_decay_factor = (num_samples - i) / num_samples
        current_amplitude = int(initial_amplitude * current_decay_factor)
        
        # Square wave generation
        if (i // int(period_samples / 2)) % 2 == 0:
            value = current_amplitude
        else:
            value = -current_amplitude
            
        # Set both channels (stereo)
        sound_array[i][0] = value
        sound_array[i][1] = value
    
    try:
        sound = pygame.sndarray.make_sound(sound_array)
        return sound
    except:
        # Fallback to simpler method if sndarray fails
        print("Falling back to alternative sound creation method")
        buffer = pygame.mixer.Sound(buffer=sound_array.tobytes())
        return buffer

def create_backup_sounds():
    """Creates simple sounds using pygame.mixer directly if sndarray fails"""
    try:
        # Create short, simple sounds of different frequencies
        s1 = pygame.mixer.Sound(buffer=bytes([128, 128, 200, 200, 128, 128, 50, 50] * 100))
        s2 = pygame.mixer.Sound(buffer=bytes([128, 200, 128, 50] * 150))
        s3 = pygame.mixer.Sound(buffer=bytes([128, 180, 128, 80] * 80))
        s4 = pygame.mixer.Sound(buffer=bytes([200, 200, 50, 50] * 200))
        s5 = pygame.mixer.Sound(buffer=bytes([200, 150, 100, 50] * 300))
        
        return s1, s2, s3, s4, s5
    except:
        print("Even backup sound creation failed")
        class DummySound:
            def play(self): pass
        return DummySound(), DummySound(), DummySound(), DummySound(), DummySound()

# Initialize sound system with better error handling
try:
    # Check if mixer was initialized successfully
    if not pygame.mixer.get_init():
        pygame.mixer.init(44100, -16, 2, 1024)
        
    # Report sound subsystem status
    print(f"Mixer initialized: {pygame.mixer.get_init()}")
    
    # --- Beep n Boop Paddle Sounds ---
    PLAYER_PADDLE_HIT_SOUND = make_square_wave_sound_with_decay(frequency=440, duration=0.07, volume=0.2)
    AI_PADDLE_HIT_SOUND = make_square_wave_sound_with_decay(frequency=280, duration=0.07, volume=0.2)
    WALL_HIT_SOUND = make_square_wave_sound_with_decay(frequency=200, duration=0.06, volume=0.15)
    SCORE_SOUND = make_square_wave_sound_with_decay(frequency=600, duration=0.15, volume=0.2)
    GAME_OVER_SOUND = make_square_wave_sound_with_decay(frequency=150, duration=0.5, volume=0.2)
    
    # Test if sounds were created successfully
    for sound in [PLAYER_PADDLE_HIT_SOUND, AI_PADDLE_HIT_SOUND, WALL_HIT_SOUND, SCORE_SOUND, GAME_OVER_SOUND]:
        if sound is None:
            raise Exception("Sound creation failed")
    
    SOUND_ENABLED = True
    print("Sound engine initialized successfully with beep n boop sounds!")
except Exception as e:
    print(f"Warning: Primary sound initialization failed: {e}")
    import traceback
    traceback.print_exc()  # Print the full error details
    
    # Try fallback sound system
    try:
        print("Attempting to create backup sounds...")
        PLAYER_PADDLE_HIT_SOUND, AI_PADDLE_HIT_SOUND, WALL_HIT_SOUND, SCORE_SOUND, GAME_OVER_SOUND = create_backup_sounds()
        SOUND_ENABLED = True
        print("Backup sound system initialized!")
    except Exception as e2:
        print(f"Backup sound system also failed: {e2}")
        SOUND_ENABLED = False
        # Dummy sound objects
        class DummySound:
            def play(self): pass
        PLAYER_PADDLE_HIT_SOUND = DummySound()
        AI_PADDLE_HIT_SOUND = DummySound()
        WALL_HIT_SOUND = DummySound()
        SCORE_SOUND = DummySound()
        GAME_OVER_SOUND = DummySound()

# --- Game Object Classes ---

class Paddle(pygame.sprite.Sprite):
    """Represents a player's paddle."""
    def __init__(self, x, y, width, height, color, is_ai=False):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.color = color
        self.is_ai = is_ai
        self.ai_speed = PADDLE_SPEED # Speed for AI paddle movement

    def move_mouse(self, y_pos):
        """Move the paddle based on mouse position."""
        self.rect.centery = y_pos # Center paddle on mouse y
        # Keep paddle on screen
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def move_ai(self, ball_rect):
        """AI movement logic for the paddle."""
        # Simple AI: try to center paddle with ball
        if self.rect.centery < ball_rect.centery:
            self.rect.y += self.ai_speed
        if self.rect.centery > ball_rect.centery:
            self.rect.y -= self.ai_speed
        
        # Keep paddle on screen
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Ball(pygame.sprite.Sprite):
    """Represents the game ball."""
    def __init__(self, x, y, size, color, speed_x, speed_y):
        super().__init__()
        self.image = pygame.Surface([size, size])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.color = color
        self.initial_speed_x_abs = abs(speed_x) 
        self.initial_speed_y_abs = abs(speed_y)
        self.speed_x = self.initial_speed_x_abs * random.choice([-1, 1]) # Start in a random X direction
        self.speed_y = self.initial_speed_y_abs * random.choice([-1, 1]) # Start in a random Y direction


    def update(self):
        """Move the ball and handle wall collisions."""
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Wall collision (top/bottom)
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.speed_y *= -1
            if SOUND_ENABLED: WALL_HIT_SOUND.play()
            # Nudge ball away from wall to prevent sticking
            if self.rect.top < 0: self.rect.top = 1 # Nudge slightly more
            if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT -1 # Nudge slightly more


    def reset(self, direction_to_serve): # Renamed parameter for clarity
        """Reset ball to center after a score."""
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        # Maintain current speed magnitude but randomize Y direction
        self.speed_y = self.initial_speed_y_abs * random.choice([-1, 1]) 
        self.speed_x = self.initial_speed_x_abs * direction_to_serve # direction depends on who scored
        
        # Slightly increase ball speed after each reset to make the game progressively harder
        self.initial_speed_x_abs = min(self.initial_speed_x_abs * 1.05, 15) # Cap max speed
        self.initial_speed_y_abs = min(self.initial_speed_y_abs * 1.05, 15) # Cap max speed


    def draw(self, screen):
        screen.blit(self.image, self.rect)

# --- Helper Functions ---

def display_text(screen, text, size, x, y, color=WHITE, font_name=None): # Added font_name
    """Displays text on the screen."""
    font = pygame.font.Font(font_name, size) # Use specified or default font
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def calculate_checksum(player_score, ai_score):
    """Generates a simple checksum for the scores (for illustrative purposes)."""
    # Simple checksum: (score1 * prime1 + score2 * prime2) mod 256
    checksum_val = (player_score * 31 + ai_score * 17 + (player_score ^ ai_score)) % 256
    return checksum_val

# --- Game Loop ---
def game_loop():
    """The main loop for the Pong game."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Retro Pong")
    clock = pygame.time.Clock()

    # Initialize game objects
    player_paddle = Paddle(30, SCREEN_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT, WHITE)
    player_paddle.rect.centery = SCREEN_HEIGHT // 2 # Ensure it's centered initially
    
    ai_paddle = Paddle(SCREEN_WIDTH - 30 - PADDLE_WIDTH, SCREEN_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT, WHITE, is_ai=True)
    ai_paddle.rect.centery = SCREEN_HEIGHT // 2 # Ensure it's centered initially

    ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_SIZE, WHITE, BALL_SPEED_X_INITIAL, BALL_SPEED_Y_INITIAL)
    ball.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) # Ensure it's centered

    player_score = 0
    ai_score = 0
    
    game_over_flag = False
    winner_message = ""
    final_checksum = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEMOTION and not game_over_flag:
                player_paddle.move_mouse(event.pos[1])
            if event.type == pygame.KEYDOWN:
                if game_over_flag:
                    if event.key == pygame.K_y: # Yes, restart
                        game_loop() # Restarts the game by calling the loop again
                        return # Exit current loop instance to prevent issues
                    if event.key == pygame.K_n: # No, quit
                        running = False
                elif event.key == pygame.K_ESCAPE: # Allow quitting anytime with ESC
                    running = False


        if not game_over_flag:
            # --- Game Logic Updates ---
            ball.update()
            ai_paddle.move_ai(ball.rect)

            # Ball collision with paddles
            if ball.rect.colliderect(player_paddle.rect):
                ball.speed_x *= -1
                # Adjust ball's Y speed based on where it hits the paddle
                delta_y = ball.rect.centery - player_paddle.rect.centery
                ball.speed_y = delta_y * 0.25  # Adjust this factor for more/less angle change
                # Clamp ball.speed_y to prevent it from becoming too fast or too slow vertically
                ball.speed_y = max(-abs(ball.initial_speed_y_abs * 1.8), min(ball.speed_y, abs(ball.initial_speed_y_abs * 1.8)))
                # Ensure ball speed_y has some minimum magnitude if it's not 0
                if abs(ball.speed_y) < 1 and ball.speed_y != 0:
                    ball.speed_y = 1 if ball.speed_y > 0 else -1

                ball.rect.left = player_paddle.rect.right + 1 # Prevent sticking by moving ball slightly past paddle
                if SOUND_ENABLED: PLAYER_PADDLE_HIT_SOUND.play()
                print(f"Player hit! Ball Y speed: {ball.speed_y:.2f}")


            elif ball.rect.colliderect(ai_paddle.rect):
                ball.speed_x *= -1
                delta_y = ball.rect.centery - ai_paddle.rect.centery
                ball.speed_y = delta_y * 0.25 
                ball.speed_y = max(-abs(ball.initial_speed_y_abs * 1.8), min(ball.speed_y, abs(ball.initial_speed_y_abs * 1.8)))
                if abs(ball.speed_y) < 1 and ball.speed_y != 0:
                    ball.speed_y = 1 if ball.speed_y > 0 else -1
                
                ball.rect.right = ai_paddle.rect.left - 1 # Prevent sticking
                if SOUND_ENABLED: AI_PADDLE_HIT_SOUND.play()
                print(f"AI hit! Ball Y speed: {ball.speed_y:.2f}")


            # Scoring logic
            if ball.rect.left <= 0: # AI scores
                ai_score += 1
                if SOUND_ENABLED: SCORE_SOUND.play()
                print(f"AI Scored! Score: Player {player_score} - AI {ai_score}")
                if ai_score >= WINNING_SCORE:
                    game_over_flag = True
                    winner_message = "AI WINS!"
                    final_checksum = calculate_checksum(player_score, ai_score)
                    if SOUND_ENABLED: GAME_OVER_SOUND.play()
                    print(f"Game Over! {winner_message} Final Checksum: {final_checksum}")
                else:
                    ball.reset(1) # Ball moves towards player


            elif ball.rect.right >= SCREEN_WIDTH: # Player scores
                player_score += 1
                if SOUND_ENABLED: SCORE_SOUND.play()
                print(f"Player Scored! Score: Player {player_score} - AI {ai_score}")
                if player_score >= WINNING_SCORE:
                    game_over_flag = True
                    winner_message = "PLAYER WINS!"
                    final_checksum = calculate_checksum(player_score, ai_score)
                    if SOUND_ENABLED: GAME_OVER_SOUND.play()
                    print(f"Game Over! {winner_message} Final Checksum: {final_checksum}")
                else:
                    ball.reset(-1) # Ball moves towards AI

        # --- Drawing Everything ---
        screen.fill(BLACK)

        # Draw center line (dashed)
        for i in range(0, SCREEN_HEIGHT, 25): # Adjusted for a more classic dashed look
            if i % 50 < 25 : # Draw dash then skip
                pygame.draw.rect(screen, GREY, (SCREEN_WIDTH // 2 - 2, i, 4, 15)) # Slightly thicker dashes

        player_paddle.draw(screen)
        ai_paddle.draw(screen)
        ball.draw(screen)

        # Display scores
        display_text(screen, str(player_score), 74, SCREEN_WIDTH // 4, 50)
        display_text(screen, str(ai_score), 74, SCREEN_WIDTH * 3 // 4, 50)

        if game_over_flag:
            display_text(screen, "GAME OVER", 90, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
            display_text(screen, winner_message, 60, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
            display_text(screen, f"Final Score: {player_score} - {ai_score}", 40, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)
            display_text(screen, f"Checksum: {final_checksum}", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
            display_text(screen, "Play Again? (Y/N)", 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
            
            # Display message if sound didn't work (only at game over)
            if not SOUND_ENABLED:
                 display_text(screen, "Note: Sounds could not be initialized.", 20, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30, GREY)


        pygame.display.flip() # Update the full screen
        clock.tick(FPS) # Limit frames per second
    
    # This part is reached if running becomes False (e.g., by pressing 'N' or ESC)
    # pygame.quit() # Moved to the main execution block to ensure it's called once
    # sys.exit()

# --- Start the Game ---
if __name__ == '__main__':
    print("Starting Retro Pong Game! Get ready for fun!")
    try:
        # Run a simple sound test before starting
        if SOUND_ENABLED:
            print("Testing sound system...")
            PLAYER_PADDLE_HIT_SOUND.play()
            pygame.time.wait(300)  # Short delay to hear the sound
            print("Sound test complete!")
        
        game_loop()
    except SystemExit: # Catch sys.exit() if it's called from within game_loop on quit
        print("Game exited normally.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
    finally:
        print("Thanks for playing! Come back soon!")
        pygame.quit() # Ensure Pygame quits properly
        sys.exit()
