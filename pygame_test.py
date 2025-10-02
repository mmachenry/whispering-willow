import pygame
import random
import os

SECRETS_DIR = "/home/ivyblossom/secrets"

pygame.mixer.init()

def play_audio_file(filepath):
    sound = pygame.mixer.Sound(filepath)
    sound.play()
    pygame.time.wait(int(sound.get_length() * 1000))

def get_secrets():
    return [f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')]

def play_random_secret():
    files = get_secrets()
    filepath = os.path.join(SECRETS_DIR, random.choice(files))
    print("Playing secret: ", filepath)
    play_audio_file(filepath)

while True:
    play_random_secret()
