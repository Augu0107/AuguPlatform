import pygame
import os
import uuid
import base64
import hashlib
import json
import socket
import threading
import time
import struct

# =========================
# HELPER FUNCTIONS
# =========================

def send_msg(sock, msg_dict):
    """Send a length-prefixed JSON message"""
    msg_json = json.dumps(msg_dict)
    msg_bytes = msg_json.encode('utf-8')
    msg_len = len(msg_bytes)
    # Send 4-byte length prefix, then the message
    sock.sendall(struct.pack('!I', msg_len) + msg_bytes)

def recv_msg(sock):
    """Receive a length-prefixed JSON message"""
    # Read 4-byte length prefix
    raw_msglen = recv_all(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('!I', raw_msglen)[0]
    # Read the message data
    msg_bytes = recv_all(sock, msglen)
    if not msg_bytes:
        return None
    return json.loads(msg_bytes.decode('utf-8'))

def recv_all(sock, n):
    """Helper to receive exactly n bytes"""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

# =========================
# CONFIG
# =========================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60
PLAYER_FILE = "player.dat"
SECRET_KEY = "AUGU_SUPER_SECRET_KEY_2026"
SERVERS_FILE = "servers.json"
SETTINGS_FILE = "settings.json"

BLOCK_SIZE = 32
PLAYER_WIDTH = 28
PLAYER_HEIGHT = 64  # 2 blocks high

# Colors
SKY_BLUE = (135, 206, 235)
GROUND_BROWN = (139, 90, 43)
STONE_GRAY = (128, 128, 128)
GRASS_GREEN = (34, 139, 34)
WOOD_BROWN = (160, 82, 45)
SAND_YELLOW = (238, 214, 175)
DIRT_BROWN = (101, 67, 33)
BEDROCK_GRAY = (64, 64, 64)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
PINK = (255, 192, 203)

# Block colors
BLOCK_COLORS = {
    "air": SKY_BLUE,
    "stone": STONE_GRAY,
    "grass": GRASS_GREEN,
    "dirt": DIRT_BROWN,
    "wood": WOOD_BROWN,
    "sand": SAND_YELLOW,
    "bedrock": BEDROCK_GRAY,
}

# Player colors (for body/clothes)
PLAYER_COLORS = {
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "green": (0, 200, 0),
    "yellow": (255, 255, 0),
    "purple": (200, 0, 200),
    "orange": (255, 165, 0),
    "cyan": (0, 255, 255),
    "pink": (255, 105, 180),
}

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D Multiplayer Platform Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 14)

# =========================
# DEFAULT CONTROLS
# =========================
DEFAULT_CONTROLS = {
    "move_left": pygame.K_a,
    "move_right": pygame.K_d,
    "jump": pygame.K_SPACE,
    "chat": pygame.K_t,
    "break_block": 1,  # Left mouse button
    "place_block": 3,  # Right mouse button
}

DEFAULT_APPEARANCE = {
    "player_color": "blue"
}

DEFAULT_LANGUAGE = "english"

# =========================
# TRANSLATIONS
# =========================
TRANSLATIONS = {
    "english": {
        # Main Menu
        "title": "Platform Multiplayer",
        "your_id": "Your ID",
        "play": "Play",
        "settings": "Settings",
        "exit": "Exit",
        
        # Settings
        "controls": "Controls",
        "appearance": "Appearance",
        "language": "Language",
        "back": "Back",
        "reset": "Reset",
        
        # Controls
        "move_left": "Move Left",
        "move_right": "Move Right",
        "jump": "Jump",
        "open_chat": "Open Chat",
        "break_block": "Break Block",
        "place_block": "Place Block",
        "press_key": "Press a key...",
        "press_esc_cancel": "Press ESC to cancel",
        
        # Appearance
        "player_appearance": "Player Appearance",
        
        # Server List
        "add_server": "Add Server",
        "refresh": "Refresh",
        "join": "Join",
        "modify": "Modify",
        "delete": "Delete",
        "offline": "Offline",
        "server_offline": "Server is offline",
        
        # Server Dialog
        "enter_ip": "Enter Server IP:",
        "enter_port": "Enter Server Port:",
        "enter_password": "Enter Server Password (0 if none):",
        "edit_ip": "Edit IP",
        "edit_port": "Edit Port",
        "edit_password": "Edit Password",
        
        # In-Game
        "paused": "Paused",
        "resume": "Resume",
        "disconnect": "Disconnect",
        "server": "Server",
        "position": "Position",
        "players": "Players",
        "level": "Level",
        "press_enter_send": "Press Enter to send, ESC to close",
        
        # Messages
        "connection_failed": "Connection Failed",
        "ok": "OK",
        "yes": "Yes",
        "no": "No",
    },
    "italiano": {
        # Main Menu
        "title": "Platform Multiplayer",
        "your_id": "Il Tuo ID",
        "play": "Gioca",
        "settings": "Impostazioni",
        "exit": "Esci",
        
        # Settings
        "controls": "Controlli",
        "appearance": "Aspetto",
        "language": "Lingua",
        "back": "Indietro",
        "reset": "Ripristina",
        
        # Controls
        "move_left": "Muovi Sinistra",
        "move_right": "Muovi Destra",
        "jump": "Salta",
        "open_chat": "Apri Chat",
        "break_block": "Rompi Blocco",
        "place_block": "Piazza Blocco",
        "press_key": "Premi un tasto...",
        "press_esc_cancel": "Premi ESC per annullare",
        
        # Appearance
        "player_appearance": "Aspetto Giocatore",
        
        # Server List
        "add_server": "Aggiungi Server",
        "refresh": "Aggiorna",
        "join": "Entra",
        "modify": "Modifica",
        "delete": "Elimina",
        "offline": "Offline",
        "server_offline": "Server offline",
        
        # Server Dialog
        "enter_ip": "Inserisci IP Server:",
        "enter_port": "Inserisci Porta Server:",
        "enter_password": "Inserisci Password Server (0 se nessuna):",
        "edit_ip": "Modifica IP",
        "edit_port": "Modifica Porta",
        "edit_password": "Modifica Password",
        
        # In-Game
        "paused": "In Pausa",
        "resume": "Riprendi",
        "disconnect": "Disconnetti",
        "server": "Server",
        "position": "Posizione",
        "players": "Giocatori",
        "level": "Livello",
        "press_enter_send": "Premi Invio per inviare, ESC per chiudere",
        
        # Messages
        "connection_failed": "Connessione Fallita",
        "ok": "OK",
        "yes": "Sì",
        "no": "No",
    }
}

def t(key):
    """Get translation for current language"""
    lang = settings.get("language", DEFAULT_LANGUAGE)
    return TRANSLATIONS.get(lang, TRANSLATIONS["english"]).get(key, key)

# =========================
# SETTINGS
# =========================
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        settings = {
            "controls": DEFAULT_CONTROLS.copy(),
            "appearance": DEFAULT_APPEARANCE.copy(),
            "language": DEFAULT_LANGUAGE
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    with open(SETTINGS_FILE) as f:
        loaded = json.load(f)
        # Ensure appearance exists
        if "appearance" not in loaded:
            loaded["appearance"] = DEFAULT_APPEARANCE.copy()
        if "language" not in loaded:
            loaded["language"] = DEFAULT_LANGUAGE
        return loaded

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

settings = load_settings()
controls = settings.get("controls", DEFAULT_CONTROLS.copy())
appearance = settings.get("appearance", DEFAULT_APPEARANCE.copy())

# =========================
# PLAYER ID SAFE
# =========================
def sign(player_id):
    return hashlib.sha256((player_id + SECRET_KEY).encode()).hexdigest()

def save_player_id(player_id):
    signature = sign(player_id)
    raw = f"{player_id}|{signature}"
    encoded = base64.b64encode(raw.encode()).decode()
    with open(PLAYER_FILE, "w") as f:
        f.write(encoded)

def load_player_id():
    if not os.path.exists(PLAYER_FILE):
        pid = str(uuid.uuid4())[:6]
        save_player_id(pid)
        return pid
    try:
        encoded = open(PLAYER_FILE).read()
        raw = base64.b64decode(encoded).decode()
        player_id, signature = raw.split("|")
        if sign(player_id) != signature:
            raise ValueError("Invalid signature")
        return player_id
    except:
        pid = str(uuid.uuid4())[:6]
        save_player_id(pid)
        return pid

PLAYER_ID = load_player_id()

# =========================
# SERVERS STORAGE
# =========================
def load_servers():
    if not os.path.exists(SERVERS_FILE):
        with open(SERVERS_FILE, "w") as f:
            json.dump([], f)
    with open(SERVERS_FILE) as f:
        return json.load(f)

def save_servers(servers):
    with open(SERVERS_FILE, "w") as f:
        json.dump(servers, f, indent=4)

servers = load_servers()

# =========================
# TCP CLIENT
# =========================
class ServerConnection:
    def __init__(self, ip, port, password=""):
        self.ip = ip
        self.port = port
        self.password = password
        self.sock = None
        self.connected = False
        self.player_level = 0
        self.server_name = ""
        self.motd = ""
        self.world = []
        self.players = {}  # other_pid -> (x, y)
        self.player_colors = {}  # other_pid -> color
        self.player_x = 10
        self.player_y = 3
        self.hotbar = [None] * 7
        self.chat_messages = []
        self.max_chat_display = 5
        self.last_position_send = time.time()
        self.disconnect_reason = None
        self.respawn_flag = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.ip, self.port))
            
            # Send login packet with password and color
            send_msg(self.sock, {
                "type": "login",
                "id": PLAYER_ID,
                "password": self.password,
                "color": appearance.get("player_color", "blue")
            })
            
            # Remove timeout for ongoing communication
            self.sock.settimeout(None)
            
            self.connected = True
            threading.Thread(target=self.listen_server, daemon=True).start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False

    def listen_server(self):
        while self.connected:
            try:
                msg = recv_msg(self.sock)
                if not msg:
                    print("Connection closed by server")
                    self.connected = False
                    break
                
                # Process the message
                if msg.get("type") == "welcome":
                    self.server_name = msg.get("server", "")
                    self.motd = msg.get("motd", "")
                    self.world = msg.get("world", [])
                    self.player_x = msg.get("x", 10)
                    self.player_y = msg.get("y", 3)
                    self.hotbar = msg.get("hotbar", [None] * 7)
                    self.player_level = msg.get("level", 0)
                    print(f"Received welcome: world size {len(self.world)}x{len(self.world[0]) if self.world else 0}")
                
                elif msg.get("type") == "respawn":
                    self.player_x = msg.get("x", 10)
                    self.player_y = msg.get("y", 3)
                    self.respawn_flag = True
                    print(f"Respawned at ({self.player_x}, {self.player_y})")
                    
                elif msg.get("type") == "chat":
                    pid = msg.get("from", "???")
                    level = msg.get("level", 0)
                    text = msg.get("message", "")
                    chat_line = f"{pid} [{level}] >> {text}"
                    self.chat_messages.append(chat_line)
                    if len(self.chat_messages) > 100:
                        self.chat_messages.pop(0)
                
                elif msg.get("type") == "update_block":
                    x, y = msg.get("x"), msg.get("y")
                    block = msg.get("block")
                    if 0 <= y < len(self.world) and 0 <= x < len(self.world[0]):
                        self.world[y][x] = block
                
                elif msg.get("type") == "player_join":
                    pid = msg.get("id")
                    x, y = msg.get("x"), msg.get("y")
                    color = msg.get("color", "blue")
                    self.players[pid] = (x, y)
                    self.player_colors[pid] = color
                    print(f"Player {pid} joined at ({x}, {y}) with color {color}")
                
                elif msg.get("type") == "player_move":
                    pid = msg.get("id")
                    x, y = msg.get("x"), msg.get("y")
                    self.players[pid] = (x, y)
                
                elif msg.get("type") == "player_color":
                    pid = msg.get("id")
                    color = msg.get("color", "blue")
                    self.player_colors[pid] = color
                    print(f"Player {pid} changed color to {color}")
                
                elif msg.get("type") == "player_leave":
                    pid = msg.get("id")
                    if pid in self.players:
                        del self.players[pid]
                    if pid in self.player_colors:
                        del self.player_colors[pid]
                    print(f"Player {pid} left")
                
                elif msg.get("type") == "hotbar_update":
                    self.hotbar = msg.get("hotbar", [None] * 7)
                
                elif msg.get("type") == "disconnect":
                    reason = msg.get("reason", "Disconnected")
                    self.disconnect_reason = reason
                    print(f"Disconnected: {reason}")
                    self.connected = False
                    break
                    
            except Exception as e:
                print(f"Listen error: {e}")
                self.connected = False
                break

    def send_chat(self, message):
        if self.connected:
            packet = {"type": "chat", "message": message}
            try:
                send_msg(self.sock, packet)
            except:
                self.connected = False

    def send_position(self, x, y):
        if self.connected:
            current_time = time.time()
            if current_time - self.last_position_send > 0.05:  # Send max 20 times per second
                packet = {"type": "move", "x": x, "y": y}
                try:
                    send_msg(self.sock, packet)
                    self.last_position_send = current_time
                except:
                    self.connected = False

    def break_block(self, x, y):
        if self.connected:
            packet = {"type": "break_block", "x": x, "y": y}
            try:
                send_msg(self.sock, packet)
            except:
                self.connected = False

    def place_block(self, x, y, slot):
        if self.connected:
            packet = {"type": "place_block", "x": x, "y": y, "slot": slot}
            try:
                send_msg(self.sock, packet)
            except:
                self.connected = False

    def update_color(self, color):
        if self.connected:
            packet = {"type": "update_color", "color": color}
            try:
                send_msg(self.sock, packet)
            except:
                self.connected = False

# =========================
# BUTTON CLASS
# =========================
class Button:
    def __init__(self, rect, text, color=(200,200,200)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover = False
    
    def draw(self, surf):
        color = tuple(min(c + 30, 255) for c in self.color) if self.hover else self.color
        pygame.draw.rect(surf, color, self.rect)
        pygame.draw.rect(surf, BLACK, self.rect, 2)
        label = font.render(self.text, True, BLACK)
        text_rect = label.get_rect(center=self.rect.center)
        surf.blit(label, text_rect)
    
    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# =========================
# MESSAGE BOX
# =========================
def show_message(title, message):
    """Show a message box"""
    ok_btn = Button((SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 + 50, 100, 40), "OK")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        screen.fill((30, 30, 30))
        
        # Title
        title_surf = pygame.font.SysFont("Arial", 28, bold=True).render(title, True, WHITE)
        screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, SCREEN_HEIGHT//2 - 80))
        
        # Message
        msg_surf = font.render(message, True, WHITE)
        screen.blit(msg_surf, (SCREEN_WIDTH//2 - msg_surf.get_width()//2, SCREEN_HEIGHT//2 - 20))
        
        ok_btn.update(mouse_pos)
        ok_btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ok_btn.is_clicked(event.pos):
                    running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    running = False
        
        pygame.display.flip()
        clock.tick(FPS)

# =========================
# TEXT INPUT BOX
# =========================
def text_input_box(prompt, width=400, height=35):
    input_text = ""
    active = True
    box_rect = pygame.Rect(SCREEN_WIDTH//2 - width//2, SCREEN_HEIGHT//2, width, height)
    
    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text
                elif event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if len(input_text) < 50:
                        input_text += event.unicode
        
        screen.fill((50,50,50))
        
        # Draw prompt
        label = font.render(prompt, True, WHITE)
        screen.blit(label, (SCREEN_WIDTH//2 - label.get_width()//2, SCREEN_HEIGHT//2 - 50))
        
        # Draw input box
        pygame.draw.rect(screen, WHITE, box_rect)
        pygame.draw.rect(screen, BLACK, box_rect, 2)
        
        # Draw text
        text_surface = font.render(input_text, True, BLACK)
        screen.blit(text_surface, (box_rect.x + 5, box_rect.y + 8))
        
        # Draw cursor
        if int(time.time() * 2) % 2:
            cursor_x = box_rect.x + 5 + text_surface.get_width()
            pygame.draw.line(screen, BLACK, (cursor_x, box_rect.y + 5), (cursor_x, box_rect.y + height - 5), 2)
        
        pygame.display.flip()
        clock.tick(FPS)

# =========================
# MAIN MENU
# =========================
def main_menu():
    play_btn = Button((SCREEN_WIDTH//2-75, 250, 150, 50), t("play"))
    settings_btn = Button((SCREEN_WIDTH//2-75, 320, 150, 50), t("settings"))
    exit_btn = Button((SCREEN_WIDTH//2-75, 390, 150, 50), t("exit"))
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button texts in case language changed
        play_btn.text = t("play")
        settings_btn.text = t("settings")
        exit_btn.text = t("exit")
        
        screen.fill((40, 40, 70))
        
        # Title
        title = pygame.font.SysFont("Arial", 48, bold=True).render(t("title"), True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 120))
        
        # Player ID
        id_text = font.render(f"{t('your_id')}: {PLAYER_ID}", True, (255, 255, 100))
        screen.blit(id_text, (SCREEN_WIDTH//2 - id_text.get_width()//2, 180))
        
        play_btn.update(mouse_pos)
        settings_btn.update(mouse_pos)
        exit_btn.update(mouse_pos)
        
        play_btn.draw(screen)
        settings_btn.draw(screen)
        exit_btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if play_btn.is_clicked(event.pos):
                    server_list_screen()
                elif settings_btn.is_clicked(event.pos):
                    settings_screen()
                elif exit_btn.is_clicked(event.pos):
                    return False
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return False

# =========================
# SETTINGS SCREEN
# =========================
def settings_screen():
    controls_btn = Button((SCREEN_WIDTH//2-100, 180, 200, 50), t("controls"))
    appearance_btn = Button((SCREEN_WIDTH//2-100, 250, 200, 50), t("appearance"))
    language_btn = Button((SCREEN_WIDTH//2-100, 320, 200, 50), t("language"))
    back_btn = Button((50, 30, 100, 40), t("back"))
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button texts
        controls_btn.text = t("controls")
        appearance_btn.text = t("appearance")
        language_btn.text = t("language")
        back_btn.text = t("back")
        
        screen.fill((30,30,30))
        
        # Title
        title = pygame.font.SysFont("Arial", 36, bold=True).render(t("settings"), True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        controls_btn.update(mouse_pos)
        appearance_btn.update(mouse_pos)
        language_btn.update(mouse_pos)
        back_btn.update(mouse_pos)
        
        controls_btn.draw(screen)
        appearance_btn.draw(screen)
        language_btn.draw(screen)
        back_btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(event.pos):
                    running = False
                elif controls_btn.is_clicked(event.pos):
                    controls_screen()
                elif appearance_btn.is_clicked(event.pos):
                    appearance_screen()
                elif language_btn.is_clicked(event.pos):
                    language_screen()
        
        pygame.display.flip()
        clock.tick(FPS)

# =========================
# CONTROLS SCREEN
# =========================
def get_key_name(key):
    if isinstance(key, int):
        if key >= 1 and key <= 3:
            return f"Mouse {key}"
        return pygame.key.name(key).upper()
    return str(key)

def controls_screen():
    global controls
    
    back_btn = Button((50, 30, 100, 40), "Back")
    reset_btn = Button((SCREEN_WIDTH - 150, 30, 100, 40), "Reset")
    
    control_actions = [
        ("move_left", "Move Left"),
        ("move_right", "Move Right"),
        ("jump", "Jump"),
        ("chat", "Open Chat"),
        ("break_block", "Break Block"),
        ("place_block", "Place Block"),
    ]
    
    waiting_for_key = None
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        screen.fill((30,30,30))
        
        # Title
        title = pygame.font.SysFont("Arial", 36, bold=True).render("Controls", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        back_btn.update(mouse_pos)
        reset_btn.update(mouse_pos)
        
        back_btn.draw(screen)
        reset_btn.draw(screen)
        
        # Draw controls
        y = 180
        control_btns = []
        for action, display_name in control_actions:
            # Action name
            action_text = font.render(display_name + ":", True, WHITE)
            screen.blit(action_text, (200, y))
            
            # Current key button
            current_key = controls.get(action, DEFAULT_CONTROLS[action])
            key_name = get_key_name(current_key)
            
            if waiting_for_key == action:
                key_name = "Press a key..."
                color = (255, 200, 100)
            else:
                color = (150, 150, 200)
            
            key_btn = Button((500, y - 5, 150, 35), key_name, color)
            key_btn.update(mouse_pos)
            key_btn.draw(screen)
            control_btns.append((key_btn, action))
            
            y += 60
        
        if waiting_for_key:
            info_text = small_font.render("Press ESC to cancel", True, (255, 255, 100))
            screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, SCREEN_HEIGHT - 50))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if waiting_for_key:
                    if event.button <= 3:  # Left, Middle, Right mouse buttons
                        controls[waiting_for_key] = event.button
                        settings["controls"] = controls
                        save_settings(settings)
                        waiting_for_key = None
                else:
                    if back_btn.is_clicked(event.pos):
                        running = False
                    elif reset_btn.is_clicked(event.pos):
                        controls = DEFAULT_CONTROLS.copy()
                        settings["controls"] = controls
                        save_settings(settings)
                    else:
                        for btn, action in control_btns:
                            if btn.is_clicked(event.pos):
                                waiting_for_key = action
                                break
            elif event.type == pygame.KEYDOWN:
                if waiting_for_key:
                    if event.key == pygame.K_ESCAPE:
                        waiting_for_key = None
                    else:
                        controls[waiting_for_key] = event.key
                        settings["controls"] = controls
                        save_settings(settings)
                        waiting_for_key = None
        
        pygame.display.flip()
        clock.tick(FPS)

# =========================
# LANGUAGE SCREEN
# =========================
def language_screen():
    global settings
    
    back_btn = Button((50, 30, 100, 40), t("back"))
    
    languages = [
        ("english", "English 🇬🇧"),
        ("italiano", "Italiano 🇮🇹")
    ]
    
    lang_buttons = []
    start_y = 200
    for i, (lang_code, lang_name) in enumerate(languages):
        btn = Button((SCREEN_WIDTH//2 - 150, start_y + i * 80, 300, 60), lang_name)
        lang_buttons.append((lang_code, lang_name, btn))
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        back_btn.text = t("back")
        
        screen.fill((30,30,30))
        
        # Title
        title = pygame.font.SysFont("Arial", 36, bold=True).render(t("language"), True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        back_btn.update(mouse_pos)
        back_btn.draw(screen)
        
        # Draw language buttons
        current_lang = settings.get("language", DEFAULT_LANGUAGE)
        for lang_code, lang_name, btn in lang_buttons:
            # Highlight selected language
            if lang_code == current_lang:
                highlight = pygame.Rect(btn.rect.x - 5, btn.rect.y - 5, btn.rect.width + 10, btn.rect.height + 10)
                pygame.draw.rect(screen, (255, 255, 100), highlight, 4)
            
            btn.update(mouse_pos)
            btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(event.pos):
                    running = False
                else:
                    for lang_code, lang_name, btn in lang_buttons:
                        if btn.is_clicked(event.pos):
                            settings["language"] = lang_code
                            save_settings(settings)
        
        pygame.display.flip()
        clock.tick(FPS)

# =========================
# APPEARANCE SCREEN
# =========================
def appearance_screen(active_connection=None):
    global appearance
    
    back_btn = Button((50, 30, 100, 40), "Back")
    
    color_buttons = []
    colors = list(PLAYER_COLORS.keys())
    cols = 4
    start_x = SCREEN_WIDTH // 2 - (cols * 100) // 2
    start_y = 200
    
    for i, color_name in enumerate(colors):
        row = i // cols
        col = i % cols
        x = start_x + col * 100
        y = start_y + row * 80
        color_buttons.append((color_name, pygame.Rect(x, y, 80, 60)))
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        screen.fill((30,30,30))
        
        # Title
        title = pygame.font.SysFont("Arial", 36, bold=True).render("Player Appearance", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        back_btn.update(mouse_pos)
        back_btn.draw(screen)
        
        # Draw color selection buttons with preview
        for color_name, rect in color_buttons:
            # Draw button background
            if appearance.get("player_color") == color_name:
                pygame.draw.rect(screen, (255, 255, 100), rect.inflate(6, 6))
            
            # Draw player preview
            body_color = PLAYER_COLORS[color_name]
            head_color = PINK
            
            # Body (bottom half)
            body_rect = pygame.Rect(rect.x + 20, rect.y + 30, 40, 30)
            pygame.draw.rect(screen, body_color, body_rect)
            pygame.draw.rect(screen, BLACK, body_rect, 2)
            
            # Head (top half)
            head_rect = pygame.Rect(rect.x + 20, rect.y, 40, 30)
            pygame.draw.rect(screen, head_color, head_rect)
            pygame.draw.rect(screen, BLACK, head_rect, 2)
            
            # Color name
            name_text = small_font.render(color_name.capitalize(), True, WHITE)
            name_rect = name_text.get_rect(center=(rect.centerx, rect.bottom + 15))
            screen.blit(name_text, name_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(event.pos):
                    running = False
                else:
                    for color_name, rect in color_buttons:
                        if rect.collidepoint(event.pos):
                            appearance["player_color"] = color_name
                            settings["appearance"] = appearance
                            save_settings(settings)
                            
                            # If connected to a server, send color update
                            if active_connection and active_connection.connected:
                                active_connection.update_color(color_name)
        
        pygame.display.flip()
        clock.tick(FPS)

# =========================
# SERVER LIST SCREEN
# =========================
def server_list_screen():
    add_btn = Button((SCREEN_WIDTH-220, 30, 150, 40), t("add_server"))
    refresh_btn = Button((SCREEN_WIDTH-220, 80, 150, 40), t("refresh"))
    back_btn = Button((50, 30, 100, 40), t("back"))
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button texts
        add_btn.text = t("add_server")
        refresh_btn.text = t("refresh")
        back_btn.text = t("back")
        
        screen.fill((50,50,80))
        
        # Player ID
        id_label = font.render(f"{t('your_id')}: {PLAYER_ID}", True, (255,255,100))
        screen.blit(id_label, (SCREEN_WIDTH//2 - id_label.get_width()//2, 10))
        
        add_btn.update(mouse_pos)
        refresh_btn.update(mouse_pos)
        back_btn.update(mouse_pos)
        
        add_btn.draw(screen)
        refresh_btn.draw(screen)
        back_btn.draw(screen)

        # Lista server
        y = 150
        server_buttons = []
        for s in servers:
            name = s.get('name', '???')
            motd = s.get('motd', '???')
            current = s.get('current', 0)
            max_p = s.get('max', 10)
            
            text = f"{s['ip']}:{s['port']} - {name} - {motd} - {current}/{max_p}"
            label = small_font.render(text, True, WHITE)
            screen.blit(label, (50, y))
            
            join_btn = Button((SCREEN_WIDTH-380, y-3, 70, 30), t("join"), (100, 200, 100))
            modify_btn = Button((SCREEN_WIDTH-300, y-3, 70, 30), t("modify"), (200, 200, 100))
            delete_btn = Button((SCREEN_WIDTH-220, y-3, 70, 30), t("delete"), (200, 100, 100))
            
            join_btn.update(mouse_pos)
            modify_btn.update(mouse_pos)
            delete_btn.update(mouse_pos)
            
            join_btn.draw(screen)
            modify_btn.draw(screen)
            delete_btn.draw(screen)
            
            server_buttons.append((join_btn, modify_btn, delete_btn, s))
            y += 40

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(event.pos):
                    running = False
                elif add_btn.is_clicked(event.pos):
                    add_server_dialog()
                elif refresh_btn.is_clicked(event.pos):
                    refresh_servers()
                else:
                    for join_btn, modify_btn, delete_btn, s in server_buttons:
                        if join_btn.is_clicked(event.pos):
                            try:
                                conn = ServerConnection(s['ip'], s['port'], s.get('password', '0'))
                                if conn.connect():
                                    # Wait a bit to see if we get disconnected
                                    time.sleep(0.3)
                                    if not conn.connected:
                                        # We were disconnected, show reason
                                        reason = conn.disconnect_reason or t("connection_failed")
                                        show_message(t("connection_failed"), reason)
                                    else:
                                        game_screen(conn)
                                else:
                                    s['name'] = t("offline")
                                    s['motd'] = t("server_offline")
                                    s['current'] = 0
                                    s['max'] = 0
                            except Exception as e:
                                print(f"Failed to connect: {e}")
                                s['name'] = t("offline")
                                s['motd'] = t("server_offline")
                                s['current'] = 0
                                s['max'] = 0
                        elif modify_btn.is_clicked(event.pos):
                            modify_server_dialog(s)
                        elif delete_btn.is_clicked(event.pos):
                            servers.remove(s)
                            save_servers(servers)

        pygame.display.flip()
        clock.tick(FPS)

def add_server_dialog():
    ip = text_input_box("Enter Server IP:")
    if ip is None:
        return
    port = text_input_box("Enter Server Port:")
    if port is None:
        return
    password = text_input_box("Enter Server Password (0 if none):")
    if password is None:
        return
    try:
        port = int(port)
    except:
        return
    s = {"ip": ip, "port": port, "password": password, "name": "???", "motd": "???", "current": 0, "max": 0}
    servers.append(s)
    save_servers(servers)

def modify_server_dialog(s):
    ip = text_input_box(f"Edit IP ({s['ip']}):")
    if ip is None:
        return
    port = text_input_box(f"Edit Port ({s['port']}):")
    if port is None:
        return
    password = text_input_box(f"Edit Password ({s.get('password', '0')}):")
    if password is None:
        return
    try:
        port = int(port)
    except:
        return
    s['ip'] = ip
    s['port'] = port
    s['password'] = password
    save_servers(servers)

def refresh_servers():
    for s in servers:
        try:
            conn = ServerConnection(s['ip'], s['port'], s.get('password', ''))
            if conn.connect():
                # Wait for welcome packet with server info
                max_wait = 2.0
                elapsed = 0
                while (not conn.server_name or not conn.motd) and elapsed < max_wait:
                    time.sleep(0.1)
                    elapsed += 0.1
                
                s['name'] = conn.server_name if conn.server_name else "???"
                s['motd'] = conn.motd if conn.motd else "???"
                s['current'] = len(conn.players) + 1  # +1 for ourselves
                s['max'] = 10
                try:
                    conn.sock.close()
                except:
                    pass
                conn.connected = False
            else:
                s['name'] = "Offline"
                s['motd'] = "Server is offline"
                s['current'] = 0
                s['max'] = 0
        except Exception as e:
            print(f"Refresh error for {s['ip']}:{s['port']}: {e}")
            s['name'] = "Offline"
            s['motd'] = "Server is offline"
            s['current'] = 0
            s['max'] = 0
    save_servers(servers)

# =========================
# IN-GAME MENU
# =========================
def ingame_menu(conn):
    """Show pause menu during gameplay. Returns 'quit', 'settings', or 'resume'"""
    resume_btn = Button((SCREEN_WIDTH//2-100, 250, 200, 50), "Resume")
    settings_btn = Button((SCREEN_WIDTH//2-100, 320, 200, 50), "Settings")
    quit_btn = Button((SCREEN_WIDTH//2-100, 390, 200, 50), "Disconnect")
    
    running = True
    result = "resume"
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Title
        title = pygame.font.SysFont("Arial", 48, bold=True).render("Paused", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        
        resume_btn.update(mouse_pos)
        settings_btn.update(mouse_pos)
        quit_btn.update(mouse_pos)
        
        resume_btn.draw(screen)
        settings_btn.draw(screen)
        quit_btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                result = "quit"
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    result = "resume"
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if resume_btn.is_clicked(event.pos):
                    result = "resume"
                    running = False
                elif settings_btn.is_clicked(event.pos):
                    # Open settings with connection
                    ingame_settings(conn)
                    result = "settings"
                elif quit_btn.is_clicked(event.pos):
                    result = "quit"
                    running = False
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return result

def ingame_settings(conn):
    """Settings menu accessible during gameplay"""
    controls_btn = Button((SCREEN_WIDTH//2-100, 180, 200, 50), "Controls")
    appearance_btn = Button((SCREEN_WIDTH//2-100, 250, 200, 50), "Appearance")
    back_btn = Button((50, 30, 100, 40), "Back")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        screen.fill((30,30,30))
        
        # Title
        title = pygame.font.SysFont("Arial", 36, bold=True).render("Settings", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        controls_btn.update(mouse_pos)
        appearance_btn.update(mouse_pos)
        back_btn.update(mouse_pos)
        
        controls_btn.draw(screen)
        appearance_btn.draw(screen)
        back_btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(event.pos):
                    running = False
                elif controls_btn.is_clicked(event.pos):
                    controls_screen()
                elif appearance_btn.is_clicked(event.pos):
                    appearance_screen(conn)  # Pass connection!
        
        pygame.display.flip()
        clock.tick(FPS)

# =========================
# GAME SCREEN
# =========================
def game_screen(conn: ServerConnection):
    # Wait for welcome packet with world data
    print("Waiting for server welcome packet...")
    wait_time = 0
    max_wait = 5
    while wait_time < max_wait:
        if conn.world and len(conn.world) > 0:
            print(f"World received! Size: {len(conn.world)}x{len(conn.world[0])}")
            break
        if not conn.connected:
            print("Connection lost while waiting for world data")
            return
        time.sleep(0.1)
        wait_time += 0.1
    
    if not conn.world or len(conn.world) == 0:
        print("Failed to receive world data from server")
        return
    
    # Player physics
    player_x = float(conn.player_x)
    player_y = float(conn.player_y)
    print(f"Starting position: ({player_x}, {player_y})")
    
    player_vx = 0
    player_vy = 0
    on_ground = False
    
    # Camera
    camera_x = 0
    camera_y = 0
    
    # Hotbar
    selected_slot = 0
    
    # Chat
    chat_open = False
    chat_input = ""
    
    running = True
    frame_count = 0
    
    while running and conn.connected:
        delta_time = clock.tick(FPS) / 1000.0
        frame_count += 1
        
        # Check if we got a respawn command from server
        if conn.respawn_flag:
            player_x = float(conn.player_x)
            player_y = float(conn.player_y)
            player_vx = 0
            player_vy = 0
            conn.respawn_flag = False
            print(f"Respawned to ({player_x}, {player_y})")
        
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if chat_open:
                        chat_open = False
                        chat_input = ""
                    else:
                        # Open in-game menu
                        choice = ingame_menu(conn)
                        if choice == "quit":
                            running = False
                        elif choice == "settings":
                            # Settings was opened from menu, continue playing
                            pass
                elif chat_open:
                    # When chat is open, handle text input
                    if event.key == pygame.K_RETURN:
                        if chat_input.strip():
                            conn.send_chat(chat_input)
                        chat_open = False
                        chat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    else:
                        if len(chat_input) < 100:
                            chat_input += event.unicode
                else:
                    # When chat is NOT open
                    if event.key == controls.get("chat", pygame.K_t):
                        chat_open = True
                        chat_input = ""
                    # Hotbar selection
                    elif event.key >= pygame.K_1 and event.key <= pygame.K_7:
                        selected_slot = event.key - pygame.K_1
            elif event.type == pygame.MOUSEWHEEL:
                if not chat_open:
                    selected_slot = (selected_slot - event.y) % 7
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not chat_open:
                    # Get block position under mouse
                    world_mouse_x = (mouse_pos[0] + camera_x) // BLOCK_SIZE
                    world_mouse_y = (mouse_pos[1] + camera_y) // BLOCK_SIZE
                    
                    # Check if within 1 block distance from player
                    player_block_x = int(player_x)
                    player_block_y = int(player_y)
                    
                    # Distance check: can only interact with blocks 1 block away (horizontally or vertically)
                    dx = abs(world_mouse_x - player_block_x)
                    dy_bottom = abs(world_mouse_y - player_block_y)
                    dy_top = abs(world_mouse_y - (player_block_y + 1))
                    dy = min(dy_bottom, dy_top)
                    
                    # Can reach if within 1 block horizontally and 2 blocks vertically (since player is 2 blocks tall)
                    can_reach = (dx <= 1 and dy <= 2)
                    
                    if event.button == controls.get("break_block", 1):
                        # Break block
                        if can_reach and 0 <= world_mouse_y < len(conn.world) and 0 <= world_mouse_x < len(conn.world[0]):
                            conn.break_block(world_mouse_x, world_mouse_y)
                    elif event.button == controls.get("place_block", 3):
                        # Place block
                        if can_reach and 0 <= world_mouse_y < len(conn.world) and 0 <= world_mouse_x < len(conn.world[0]):
                            # Check if slot is not empty
                            if conn.hotbar[selected_slot] is not None:
                                # Check if not placing inside player
                                if not ((world_mouse_x == player_block_x and (world_mouse_y == player_block_y or world_mouse_y == player_block_y + 1))):
                                    conn.place_block(world_mouse_x, world_mouse_y, selected_slot)
        
        # Player movement (only if not in chat)
        if not chat_open:
            move_speed = 5
            
            if keys[controls.get("move_left", pygame.K_a)]:
                player_vx = -move_speed
            elif keys[controls.get("move_right", pygame.K_d)]:
                player_vx = move_speed
            else:
                player_vx = 0
            
            # Gravity
            player_vy += 25 * delta_time
            if player_vy > 15:
                player_vy = 15
            
            # Jump
            if keys[controls.get("jump", pygame.K_SPACE)] and on_ground:
                player_vy = -12
            
            # Apply horizontal velocity first
            if player_vx != 0:
                new_x = player_x + player_vx * delta_time
                
                # Check horizontal collisions BEFORE moving
                player_grid_x_new = int(new_x)
                can_move_x = True
                
                for check_y in [player_grid_y, player_grid_y + 1]:
                    for offset in [-1, 0, 1]:
                        check_x = player_grid_x_new + offset
                        if 0 <= check_y < len(conn.world) and 0 <= check_x < len(conn.world[0]):
                            if conn.world[check_y][check_x] != "air":
                                block_left = check_x
                                block_right = check_x + 1
                                block_top = check_y
                                block_bottom = check_y + 1
                                
                                new_player_left = new_x - 0.4
                                new_player_right = new_x + 0.4
                                player_top = player_y
                                player_bottom = player_y + 2
                                
                                # Check if we would collide
                                if (player_bottom > block_top + 0.1 and 
                                    player_top < block_bottom - 0.1 and
                                    new_player_right > block_left and 
                                    new_player_left < block_right):
                                    can_move_x = False
                                    break
                    if not can_move_x:
                        break
                
                if can_move_x:
                    player_x = new_x
            
            # Apply vertical velocity
            player_y += player_vy * delta_time
            
            # Clamp to world bounds to prevent going outside
            player_x = max(0.5, min(player_x, len(conn.world[0]) - 1.5))
            player_y = max(0, min(player_y, len(conn.world) - 2.5))
            
            # Collision detection
            player_grid_x = int(player_x)
            player_grid_y = int(player_y)
            
            # Check collisions with blocks - vertical only now
            on_ground = False
            
            # Vertical collision
            for check_y in [player_grid_y, player_grid_y + 1, player_grid_y + 2]:
                for check_x in [player_grid_x - 1, player_grid_x, player_grid_x + 1]:
                    if 0 <= check_y < len(conn.world) and 0 <= check_x < len(conn.world[0]):
                        if conn.world[check_y][check_x] != "air":
                            block_left = check_x
                            block_right = check_x + 1
                            block_top = check_y
                            block_bottom = check_y + 1
                            
                            player_left = player_x - 0.4
                            player_right = player_x + 0.4
                            player_top = player_y
                            player_bottom = player_y + 2
                            
                            if player_right > block_left and player_left < block_right:
                                if player_bottom > block_top and player_top < block_bottom:
                                    # Collision detected
                                    if player_vy > 0:  # Falling
                                        player_y = block_top - 2
                                        player_vy = 0
                                        on_ground = True
                                    elif player_vy < 0:  # Jumping into ceiling
                                        player_y = block_bottom
                                        player_vy = 0
            
            # Keep player in bounds
            if player_x < 0.5:
                player_x = 0.5
            if player_x > len(conn.world[0]) - 1.5:
                player_x = len(conn.world[0]) - 1.5
            if player_y < 0:
                player_y = 0
            
            # Player-to-player collisions
            for other_pid, (other_x, other_y) in conn.players.items():
                # Check if players overlap
                dx = abs(player_x - other_x)
                dy = abs(player_y - other_y)
                
                # Players are 2 blocks tall and ~0.8 blocks wide
                if dx < 0.8 and dy < 2.0:
                    # Push players apart horizontally
                    if player_x < other_x:
                        player_x -= 0.1
                    else:
                        player_x += 0.1
            
            # Send position to server
            conn.send_position(player_x, player_y)
        
        # Update camera
        camera_x = int(player_x * BLOCK_SIZE - SCREEN_WIDTH // 2)
        camera_y = int(player_y * BLOCK_SIZE - SCREEN_HEIGHT // 2)
        
        # Keep camera in bounds
        if camera_x < 0:
            camera_x = 0
        if camera_y < 0:
            camera_y = 0
        world_width = len(conn.world[0]) * BLOCK_SIZE
        world_height = len(conn.world) * BLOCK_SIZE
        if camera_x > world_width - SCREEN_WIDTH:
            camera_x = max(0, world_width - SCREEN_WIDTH)
        if camera_y > world_height - SCREEN_HEIGHT:
            camera_y = max(0, world_height - SCREEN_HEIGHT)
        
        # RENDER
        screen.fill(SKY_BLUE)
        
        # Draw world
        for y, row in enumerate(conn.world):
            for x, block in enumerate(row):
                screen_x = x * BLOCK_SIZE - camera_x
                screen_y = y * BLOCK_SIZE - camera_y
                
                if -BLOCK_SIZE < screen_x < SCREEN_WIDTH and -BLOCK_SIZE < screen_y < SCREEN_HEIGHT:
                    if block != "air":
                        color = BLOCK_COLORS.get(block, GRAY)
                        pygame.draw.rect(screen, color, (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE))
                        pygame.draw.rect(screen, BLACK, (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw other players
        for other_pid, (ox, oy) in conn.players.items():
            screen_x = int(ox * BLOCK_SIZE - camera_x)
            screen_y = int(oy * BLOCK_SIZE - camera_y)
            
            # Get player's color
            other_color_name = conn.player_colors.get(other_pid, "cyan")
            other_body_color = PLAYER_COLORS.get(other_color_name, (0, 255, 255))
            
            # Body (bottom block)
            body_rect = pygame.Rect(screen_x - PLAYER_WIDTH // 2, screen_y + PLAYER_HEIGHT // 2, PLAYER_WIDTH, PLAYER_HEIGHT // 2)
            pygame.draw.rect(screen, other_body_color, body_rect)
            pygame.draw.rect(screen, BLACK, body_rect, 2)
            
            # Head (top block)
            head_rect = pygame.Rect(screen_x - PLAYER_WIDTH // 2, screen_y, PLAYER_WIDTH, PLAYER_HEIGHT // 2)
            pygame.draw.rect(screen, PINK, head_rect)
            pygame.draw.rect(screen, BLACK, head_rect, 2)
            
            # Draw name
            name_label = small_font.render(other_pid, True, WHITE)
            name_rect = name_label.get_rect(center=(screen_x, screen_y - 10))
            screen.blit(name_label, name_rect)
        
        # Draw player
        screen_x = int(player_x * BLOCK_SIZE - camera_x)
        screen_y = int(player_y * BLOCK_SIZE - camera_y)
        
        # Get player's chosen color
        player_body_color = PLAYER_COLORS.get(appearance.get("player_color", "blue"), (0, 0, 255))
        
        # Body (bottom block)
        body_rect = pygame.Rect(screen_x - PLAYER_WIDTH // 2, screen_y + PLAYER_HEIGHT // 2, PLAYER_WIDTH, PLAYER_HEIGHT // 2)
        pygame.draw.rect(screen, player_body_color, body_rect)
        pygame.draw.rect(screen, BLACK, body_rect, 2)
        
        # Head (top block)
        head_rect = pygame.Rect(screen_x - PLAYER_WIDTH // 2, screen_y, PLAYER_WIDTH, PLAYER_HEIGHT // 2)
        pygame.draw.rect(screen, PINK, head_rect)
        pygame.draw.rect(screen, BLACK, head_rect, 2)
        
        # Draw hotbar
        hotbar_width = 7 * 50 + 20
        hotbar_x = SCREEN_WIDTH // 2 - hotbar_width // 2
        hotbar_y = SCREEN_HEIGHT - 70
        
        # Hotbar background
        hotbar_bg = pygame.Surface((hotbar_width, 60))
        hotbar_bg.set_alpha(200)
        hotbar_bg.fill((50, 50, 50))
        screen.blit(hotbar_bg, (hotbar_x - 10, hotbar_y - 10))
        
        for i in range(7):
            slot_x = hotbar_x + i * 50
            slot_y = hotbar_y
            
            # Draw slot background
            if i == selected_slot:
                pygame.draw.rect(screen, (255, 255, 100), (slot_x - 2, slot_y - 2, 44, 44), 3)
            else:
                pygame.draw.rect(screen, WHITE, (slot_x, slot_y, 40, 40), 2)
            
            # Draw item
            if conn.hotbar[i] is not None:
                block_type = conn.hotbar[i]["block"]
                count = conn.hotbar[i]["count"]
                
                # Draw block preview
                block_color = BLOCK_COLORS.get(block_type, GRAY)
                pygame.draw.rect(screen, block_color, (slot_x + 5, slot_y + 5, 30, 30))
                
                # Draw count
                count_text = small_font.render(str(count), True, WHITE)
                screen.blit(count_text, (slot_x + 25, slot_y + 25))
        
        # Draw chat preview (last 5 messages)
        chat_y = 10
        for msg in conn.chat_messages[-5:]:
            chat_surface = small_font.render(msg, True, WHITE)
            # Semi-transparent background
            bg_rect = pygame.Rect(10, chat_y, chat_surface.get_width() + 10, 20)
            s = pygame.Surface((bg_rect.width, bg_rect.height))
            s.set_alpha(180)
            s.fill((0, 0, 0))
            screen.blit(s, bg_rect)
            screen.blit(chat_surface, (15, chat_y + 2))
            chat_y += 22
        
        # Draw chat input if open
        if chat_open:
            # Full chat overlay
            chat_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            chat_bg.set_alpha(200)
            chat_bg.fill((0, 0, 0))
            screen.blit(chat_bg, (0, 0))
            
            # Chat messages
            y = 50
            for msg in conn.chat_messages[-20:]:
                msg_surface = font.render(msg, True, WHITE)
                screen.blit(msg_surface, (20, y))
                y += 25
            
            # Input box
            input_y = SCREEN_HEIGHT - 100
            pygame.draw.rect(screen, WHITE, (20, input_y, SCREEN_WIDTH - 40, 40))
            pygame.draw.rect(screen, BLACK, (20, input_y, SCREEN_WIDTH - 40, 40), 2)
            
            input_surface = font.render(chat_input, True, BLACK)
            screen.blit(input_surface, (30, input_y + 10))
            
            # Cursor
            if int(time.time() * 2) % 2:
                cursor_x = 30 + input_surface.get_width()
                pygame.draw.line(screen, BLACK, (cursor_x, input_y + 8), (cursor_x, input_y + 32), 2)
            
            # Instructions
            info = small_font.render("Press Enter to send, ESC to close", True, (200, 200, 200))
            screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, input_y - 30))
        
        # Draw HUD
        info_bg = pygame.Surface((280, 90))
        info_bg.set_alpha(180)
        info_bg.fill((0, 0, 0))
        screen.blit(info_bg, (10, SCREEN_HEIGHT - 170))
        
        hud_text = [
            f"Server: {conn.server_name}",
            f"Position: ({int(player_x)}, {int(player_y)})",
            f"Players: {len(conn.players) + 1}",
            f"Level: {conn.player_level}",
        ]
        hud_y = SCREEN_HEIGHT - 165
        for line in hud_text:
            text_surface = small_font.render(line, True, WHITE)
            screen.blit(text_surface, (15, hud_y))
            hud_y += 20
        
        pygame.display.flip()
    
    # Cleanup
    print("Disconnecting from server...")
    if conn.connected:
        try:
            conn.sock.close()
        except:
            pass
        conn.connected = False

# =========================
# RUN
# =========================
if __name__ == "__main__":
    if main_menu():
        pass
    pygame.quit()
