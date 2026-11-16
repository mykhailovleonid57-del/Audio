import pygame
import pygame_gui
import sounddevice as sd
import numpy as np

width, height = 800, 400
chunk = 1024

Ev = 0

# До першої порції звуку на екрані буде рівна лінія
data = np.zeros(chunk, dtype=np.float32)

is_recording = False
recording_chunks = []


def audio_callback(indata, frames, time_info, status):
    global data

    if is_recording:
        data = indata[:, 0].copy()
        recording_chunks.append(indata.copy())


pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Звукова хвиля з мікрофона")
clock = pygame.time.Clock()

from pathlib import Path

manager = pygame_gui.UIManager(
    (width, height),
    str(Path(__file__).with_name("theme.json"))
)

button1 = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((290, 150), (200, 100)),
    text="Запис",
    manager=manager
)

button2 = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((290, 50), (200, 100)),
    text="Почати",
    manager=manager
)

try:
    # Потік відкривається на вході в with і закривається на виході
    with sd.InputStream(
        channels=1,
        blocksize=chunk,
        dtype="float32",
        callback=audio_callback,
    ):
        running = True

        while running:
            time_delta = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == button1:
                        if Ev == 0:
                            button1.set_text("Пауза")
                            recording_chunks.clear()
                            is_recording = True

                            Ev = 1
                        elif Ev == 1:
                            button1.set_text("Запис")
                            audio_data = np.concatenate(recording_chunks)
                            np.save("recording.npy", audio_data)
                            Ev = 0
                            is_recording = False

                    if event.ui_element == button2:
                        if Ev == 0:
                            button2.set_text("Стоп")
                            audio_data = np.load("recording.npy")
                            sd.play(audio_data, samplerate=44100)
                            Ev = 2
                        elif Ev == 2:
                            button2.set_text("Почати")
                            sd.stop()
                            Ev = 0

            
            manager.update(time_delta)

            screen.fill((200, 0, 0))
            samples = data
            points = []

            for i, sample in enumerate(samples):
                x = int(i * (width - 1) / (len(samples) - 1))
                y = int(height * 0.7 - sample * (height * 0.3 - 1))
                points.append((x, y))

            pygame.draw.lines(screen, (0, 255, 0), False, points, 2)
            manager.draw_ui(screen)
            pygame.display.flip()
            

except sd.PortAudioError as error:
    print(f"Помилка мікрофона: {error}")

finally:
    pygame.quit()