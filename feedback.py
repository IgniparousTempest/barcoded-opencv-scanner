import pygame

pygame.mixer.init()
pygame.mixer.music.load("beep.mp3")


def play_sound():
    pygame.mixer.music.play()
