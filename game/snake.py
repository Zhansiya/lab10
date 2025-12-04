import pygame
import random
import sys
import psycopg2 # Added for DB
from config import load_config # Added for DB

pygame.init()

width = 600
height = 600
snake_size = 20
FPS = 10
PAUSE_MESSAGE = "PAUSED. Press P to resume, S to save & resume."

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")

clock = pygame.time.Clock()

black = (0,0,0)
green = (0,255,0)
red = (255,0,0)
white = (255,255,255)

font = pygame.font.SysFont("Arial", 20)
large_font = pygame.font.SysFont("Arial", 30, bold=True) # For pause message

# --- Database Functions (Integrated) ---

def db_connect():
    """ Establish a database connection """
    config = load_config()
    try:
        return psycopg2.connect(**config)
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Database connection error: {error}")
        sys.exit(1)

def get_or_create_user(username):
    """ Check if user exists, return current level/score, or create new user """
    sql_select = "SELECT current_level, current_score FROM users WHERE username = %s;"
    sql_insert = "INSERT INTO users(username, current_level, current_score) VALUES(%s, 1, 0);"
    
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_select, (username,))
            user_data = cur.fetchone()
            if user_data:
                print(f"Welcome back, {username}. Continuing from Level {user_data[0]} with Score {user_data[1]}.")
                return user_data[0], user_data[1] # level, score
            else:
                cur.execute(sql_insert, (username,))
                conn.commit()
                print(f"New user {username} created.")
                return 1, 0 # Default starting level and score

def save_game_state(username, level, score):
    """ Save current level and score to the users table """
    sql_update = "UPDATE users SET current_level = %s, current_score = %s WHERE username = %s;"
    sql_highscore = "INSERT INTO highscores(username, score, level_reached) VALUES(%s, %s, %s);"

    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_update, (level, score, username))
                cur.execute(sql_highscore, (username, score, level)) # Log this game session score
                conn.commit()
            print(f"Game state and score saved successfully for {username}.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Save failed: {error}")

# --- Game Rendering Functions ---

# Snake body
def draw_snake(snake_list):
    for x, y in snake_list:
        pygame.draw.rect(screen, green,(x,y,snake_size, snake_size))

# Food generation
def generate_food(snake_list):
    while True:
        x = random.randrange(0,width,snake_size)
        y = random.randrange(0,height, snake_size)
        if (x,y) not in snake_list:
            return x,y


def run_game(username, initial_level, initial_score):
    global FPS 

    # Snake parameters
    snake_x = width // 2
    snake_y = height // 2
    snake_list = [(snake_x, snake_y)]
    snake_length = 1

    dx = 0
    dy = 0
    paused = False 

    score = initial_score 
    level = initial_level 
    FPS = 10 + (level * 2) 

    foods_to_next_level = 4 

    food_x, food_y = generate_food(snake_list)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_state(username, level, score) # Save on quit
                pygame.quit()
                sys.exit()

            # To control and handle pause/save shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused # Toggle pause
                if event.key == pygame.K_s and paused:
                    save_game_state(username, level, score) # Save state when paused
                    
                if not paused: # Only allow movement if not paused
                    if event.key == pygame.K_LEFT  and dx == 0:
                        dx = -snake_size
                        dy = 0
                    elif event.key == pygame.K_RIGHT and dx == 0:
                        dx = snake_size 
                        dy = 0
                    elif event.key == pygame.K_UP and dy == 0:
                        dx = 0
                        dy = -snake_size
                    elif event.key == pygame.K_DOWN and dy == 0:
                        dx = 0
                        dy = snake_size

        if not paused:
            # Update position 
            snake_x += dx
            snake_y += dy

            # Collision check
            if snake_x < 0 or snake_x >= width or snake_y < 0 or snake_y >= height:
                save_game_state(username, level, score) # Save on game over/exit
                pygame.quit()
                sys.exit()

            snake_list.append((snake_x, snake_y))
            if len(snake_list) > snake_length:
                snake_list.pop(0)

            if (snake_x, snake_y) in snake_list[:-1]:
                save_game_state(username, level, score) # Save on game over/exit
                pygame.quit()
                sys.exit()

            # Eating
            if snake_x == food_x and snake_y == food_y:
                score += 1
                snake_length += 1
                food_x, food_y = generate_food(snake_list)

                if score % foods_to_next_level == 0:
                    level += 1
                    FPS += 2

       
        screen.fill(black)
        pygame.draw.rect(screen, red, (food_x, food_y, snake_size, snake_size))
        draw_snake(snake_list)

        score_text = font.render(f"Score: {score}", True, white)
        level_text = font.render(f"Level: {level}", True, white)
        screen.blit(score_text, (10,10))
        screen.blit(level_text, (500,10)) 

        if paused:
            pause_text = large_font.render(PAUSE_MESSAGE, True, white)
            text_rect = pause_text.get_rect(center=(width//2, height//2))
            screen.blit(pause_text, text_rect)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == '__main__':
    username = input("Please enter your username to start: ")
    if not username:
        print("Username cannot be empty. Exiting.")
        sys.exit()

    level, score = get_or_create_user(username)

    
    run_game(username, level, score)