

# ============================================================================
# UI PANELS
# ============================================================================

import pygame
from utils.config import WIDTH, HEIGHT
from test9.components.get_color import get_color
from test9.main import brightness

class DraggablePanel:
    def __init__(self, x, y, width, height, title="Panel", collapsible=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.dragging = False
        self.drag_offset = (0, 0)
        self.visible = True
        self.collapsible = collapsible
        self.collapsed = False
        self.original_height = height
        self.collapsed_height = 25
        
    def handle_event(self, event):
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 25)
                if title_rect.collidepoint(event.pos):
                    # Check if clicked on collapse button
                    if self.collapsible:
                        collapse_rect = pygame.Rect(self.rect.x + self.rect.width - 20, self.rect.y + 5, 15, 15)
                        if collapse_rect.collidepoint(event.pos):
                            self.toggle_collapse()
                            return True
                    
                    self.dragging = True
                    self.drag_offset = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = event.pos[0] - self.drag_offset[0]
                self.rect.y = event.pos[1] - self.drag_offset[1]
                self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
                self.rect.y = max(0, min(self.rect.y, HEIGHT - self.rect.height))
                return True
                
        return False
    
    def toggle_collapse(self):
        """Toggle panel collapse state"""
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.rect.height = self.collapsed_height
        else:
            self.rect.height = self.original_height
    
    def draw(self, screen):
        if not self.visible:
            return
            
        # Apply brightness
        bg_color = tuple(int(c * brightness) for c in get_color("bg"))
        border_color = tuple(int(c * brightness) for c in get_color("primary"))
        
        # Draw panel background
        pygame.draw.rect(screen, bg_color, self.rect)
        
        # Draw title bar
        title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 25)
        title_bg = tuple(int(c * brightness * 0.3) for c in get_color("secondary"))
        pygame.draw.rect(screen, title_bg, title_rect)
        pygame.draw.rect(screen, border_color, title_rect, 1)
        
        # Draw title
        font_title = pygame.font.SysFont("Courier New", 13, bold=True)
        title_text = font_title.render(self.title, True, get_color("accent"))
        screen.blit(title_text, (self.rect.x + 10, self.rect.y + 5))
        
        # Draw collapse button
        if self.collapsible:
            collapse_symbol = "−" if not self.collapsed else "+"
            collapse_text = font_title.render(collapse_symbol, True, get_color("accent"))
            screen.blit(collapse_text, (self.rect.x + self.rect.width - 18, self.rect.y + 5))
        
        # Draw panel border
        pygame.draw.rect(screen, border_color, self.rect, 2)
        
        return title_rect
