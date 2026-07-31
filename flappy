import pygame
import sys
import random

pygame.init()

# Screen settings
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("happy hour")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 180, 0)
RED = (255, 0, 0)

# Bird
bird = pygame.Rect(100, 250, 30, 30)
gravity = 0.5
jump_strength = -10
bird_velocity = 0

# Pipes
pipes = []
pipe_width = 70
pipe_gap = 150
pipe_speed = 3
pipe_frequency = 100   # frames
frame_count = 0

score = 0
game_over = False
font = pygame.font.SysFont("Arial", 50)

def create_pipe():
    height = random.randint(80, 380)
    top_pipe = pygame.Rect(WIDTH, 0, pipe_width, height)
    bottom_pipe = pygame.Rect(WIDTH, height + pipe_gap, pipe_width, HEIGHT)
    return top_pipe, bottom_pipe

# Game Loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not game_over:
                    bird_velocity = jump_strength
                else:
                    # Restart game
                    bird.y = 250
                    bird_velocity = 0
                    pipes.clear()
                    score = score+1
                    game_over = False

    if not game_over:
        # Bird movement
        bird_velocity += gravity
        bird.y += int(bird_velocity)

        # Pipe generation
        frame_count += 1
        if frame_count % pipe_frequency == 0:
            pipes.extend(create_pipe())

        # Move pipes
        for pipe in pipes[:]:
            pipe.x -= pipe_speed
            
            # Remove off-screen pipes and score
            if pipe.x + pipe_width < 0:
                pipes.remove(pipe)
                # Only score when bottom pipe passes (to avoid double counting)
                if pipe.y > HEIGHT:
                    score += 1

        # Collisions
        if bird.y < 0 or bird.y + 30 > HEIGHT:
            game_over = True

        for pipe in pipes:
            if bird.colliderect(pipe):
                game_over = True

    # Drawing
    screen.fill((135, 206, 235))  # Sky blue background

    # Draw bird
    pygame.draw.rect(screen, RED, bird)

    # Draw pipes
    for pipe in pipes:
        pygame.draw.rect(screen, GREEN, pipe)

    # Score
    score_text = font.render(str(int(score)), True, (255, 255, 255))
    screen.blit(score_text, (WIDTH//2 - 20, 50))

    if game_over:
        game_over_text = font.render("GAME OVER", True, (200, 0, 0))
        screen.blit(game_over_text, (WIDTH//2 - 150, HEIGHT//2 - 50))
        restart_text = pygame.font.SysFont("Arial", 30).render("Press SPACE to Restart", True, (255, 255, 255))
        screen.blit(restart_text, (WIDTH//2 - 140, HEIGHT//2 + 20))

    pygame.display.update()
    clock.tick(60)
