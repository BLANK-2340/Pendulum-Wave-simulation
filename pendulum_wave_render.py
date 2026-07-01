
import math
from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1100, 620
N = 27
GRAVITY = 9.81
PIXELS_PER_METER = 185
SYNC_TIME = 32.0
BASE_OSCILLATIONS = 25
START_ANGLE = math.radians(24)
DAMPING = 0.0006
FPS = 30
DURATION = 16.0
FRAMES = int(FPS * DURATION)
DT = 1 / FPS
OUT_GIF = "pendulum_wave_simulation.gif"

def lerp(a, b, t): return int(a + (b - a) * t)
def color_lerp(c1, c2, t): return tuple(lerp(c1[i], c2[i], t) for i in range(3))

def palette_color(i, total):
    palette = [(80,220,255),(135,120,255),(220,95,255),(255,105,185),(255,170,70),(245,240,120),(100,255,185)]
    x = i / max(1, total - 1)
    s = x * (len(palette) - 1)
    a = int(s)
    b = min(a + 1, len(palette) - 1)
    return color_lerp(palette[a], palette[b], s - a)

class Pendulum:
    def __init__(self, pivot, length_m, theta0, color):
        self.pivot = pivot
        self.length_m = length_m
        self.length_px = length_m * PIXELS_PER_METER
        self.theta = theta0
        self.omega = 0.0
        self.color = color
        self.trail = []

    def acceleration(self, theta, omega):
        return -(GRAVITY / self.length_m) * math.sin(theta) - DAMPING * omega

    def update(self, dt):
        th, om = self.theta, self.omega
        k1_th, k1_om = om, self.acceleration(th, om)
        k2_th = om + 0.5 * dt * k1_om
        k2_om = self.acceleration(th + 0.5 * dt * k1_th, om + 0.5 * dt * k1_om)
        k3_th = om + 0.5 * dt * k2_om
        k3_om = self.acceleration(th + 0.5 * dt * k2_th, om + 0.5 * dt * k2_om)
        k4_th = om + dt * k3_om
        k4_om = self.acceleration(th + dt * k3_th, om + dt * k3_om)
        self.theta += (dt / 6) * (k1_th + 2*k2_th + 2*k3_th + k4_th)
        self.omega += (dt / 6) * (k1_om + 2*k2_om + 2*k3_om + k4_om)
        self.trail.append(self.position())
        if len(self.trail) > 75:
            self.trail.pop(0)

    def position(self):
        x = self.pivot[0] + self.length_px * math.sin(self.theta)
        y = self.pivot[1] + self.length_px * math.cos(self.theta)
        return int(x), int(y)

def make_pendulums():
    pendulums = []
    usable_width = WIDTH * 0.82
    start_x = (WIDTH - usable_width) / 2
    spacing = usable_width / (N - 1)
    pivot_y = 82
    for i in range(N):
        oscillations = BASE_OSCILLATIONS + i
        period = SYNC_TIME / oscillations
        length_m = GRAVITY * (period / (2 * math.pi)) ** 2
        pivot = (int(start_x + i * spacing), pivot_y)
        pendulums.append(Pendulum(pivot, length_m, START_ANGLE, palette_color(i, N)))
    return pendulums

def draw_background():
    img = Image.new("RGB", (WIDTH, HEIGHT))
    px = img.load()
    top = (6, 8, 18)
    bottom = (13, 19, 39)
    for y in range(HEIGHT):
        c = color_lerp(top, bottom, y / HEIGHT)
        for x in range(WIDTH):
            px[x, y] = c
    return img.convert("RGBA")

def draw_soft_circle(layer, pos, radius, color, max_alpha):
    draw = ImageDraw.Draw(layer, "RGBA")
    for r in range(radius, 0, -2):
        alpha = int(max_alpha * (1 - r / radius) ** 1.7)
        draw.ellipse([pos[0]-r, pos[1]-r, pos[0]+r, pos[1]+r], fill=(*color, alpha))

def render_frame(base_bg, pendulums, frame_idx):
    img = base_bg.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    t = frame_idx / FPS

    for k in range(85):
        x = (k * 137 + int(t * 12)) % WIDTH
        y = (k * 223) % HEIGHT
        pulse = 0.5 + 0.5 * math.sin(t * 1.7 + k * 0.41)
        a = int(20 + 55 * pulse)
        draw.ellipse([x-1, y-1, x+1, y+1], fill=(180,215,255,a))

    beam_y = 82
    draw.line([(60, beam_y), (WIDTH-60, beam_y)], fill=(110,120,150,220), width=4)
    draw.line([(60, beam_y-2), (WIDTH-60, beam_y-2)], fill=(220,230,250,150), width=1)

    trail_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    trail_draw = ImageDraw.Draw(trail_layer, "RGBA")
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    positions = []

    for p in pendulums:
        bob = p.position()
        positions.append(bob)
        for j, point in enumerate(p.trail):
            q = j / max(1, len(p.trail) - 1)
            alpha = int(8 + 95 * q)
            r = int(1 + 4 * q)
            trail_draw.ellipse([point[0]-r, point[1]-r, point[0]+r, point[1]+r], fill=(*p.color, alpha))
        draw_soft_circle(glow_layer, bob, 35, p.color, 130)

    trail_layer = trail_layer.filter(ImageFilter.GaussianBlur(0.25))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(7))
    img = Image.alpha_composite(img, trail_layer)
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img, "RGBA")

    for p in pendulums:
        bob = p.position()
        draw.line([p.pivot, bob], fill=(160,170,195,185), width=1)
        draw.ellipse([p.pivot[0]-3, p.pivot[1]-3, p.pivot[0]+3, p.pivot[1]+3], fill=(225,232,255,220))

    for i in range(len(positions)-1):
        c = palette_color(i, len(positions))
        draw.line([positions[i], positions[i+1]], fill=(*c, 120), width=2)

    for p in pendulums:
        bob = p.position()
        r = 8
        draw.ellipse([bob[0]-r-2, bob[1]-r-2, bob[0]+r+2, bob[1]+r+2], fill=(245,248,255,230))
        draw.ellipse([bob[0]-r, bob[1]-r, bob[0]+r, bob[1]+r], fill=(*p.color,255))
        draw.ellipse([bob[0]-4, bob[1]-5, bob[0]-1, bob[1]-2], fill=(255,255,255,230))

    return img.convert("P", palette=Image.ADAPTIVE)

pendulums = make_pendulums()
base_bg = draw_background()
frames = []

for frame_idx in range(FRAMES):
    for _ in range(2):
        for p in pendulums:
            p.update(DT / 2)
    frames.append(render_frame(base_bg, pendulums, frame_idx))

frames[0].save(
    OUT_GIF,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True,
)

print("Saved:", OUT_GIF)
