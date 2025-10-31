import pygame
import random
from enum import Enum
from collections import Counter
import os
import math

# Card suits and ranks
class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class HandType(Enum):
    HIGH_CARD = ("High Card", 10, 1)
    PAIR = ("Pair", 15, 2)
    TWO_PAIR = ("Two Pair", 25, 2)
    THREE_OF_A_KIND = ("Three of a Kind", 30, 3)
    STRAIGHT = ("Straight", 30, 4)
    FLUSH = ("Flush", 35, 4)
    FULL_HOUSE = ("Full House", 40, 4)
    FOUR_OF_A_KIND = ("Four of a Kind", 60, 7)
    STRAIGHT_FLUSH = ("Straight Flush", 100, 8)
    ROYAL_FLUSH = ("Royal Flush", 100, 10)

    def __init__(self, label, chips, mult):
        self.label = label
        self.chips = chips
        self.mult = mult

class Card:
    def __init__(self, suit, rank, is_joker=False):
        self.suit = suit
        self.rank = rank
        self.multiplier = 1.0
        self.is_joker = is_joker
        self.selected = False
        # Convert rank to numeric value for comparison
        self.value = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, 
                     '9':9, '10':10, 'J':11, 'Q':12, 'K':13, 'A':14}.get(rank, 0)
    
    def __str__(self):
        return "🃏" if self.is_joker else f"{self.rank}{self.suit.value}"

    def get_display_str(self):
        if self.is_joker:
            return "JKR"
        suit_symbols = {
            Suit.HEARTS: "H",
            Suit.DIAMONDS: "D",
            Suit.CLUBS: "C",
            Suit.SPADES: "S"
        }
        return f"{self.rank}{suit_symbols[self.suit]}"

    def get_chip_value(self):
        # Return numeric value for calculating additional chips
        return self.value

class JokerType(Enum):
    STEEL = ("Steel Joker", "Adds +2 to base multiplier")
    GLASS = ("Glass Joker", "x4 multiplier but breaks after use")
    LUCKY = ("Lucky Joker", "Adds +1 to all card values")
    BRONZE = ("Bronze Joker", "x1.5 multiplier for pairs")
    SILVER = ("Silver Joker", "x2 multiplier for three of a kind")
    GOLD = ("Gold Joker", "x3 multiplier for straights")
    DIAMOND = ("Diamond Joker", "x2.5 multiplier for flushes")
    COSMIC = ("Cosmic Joker", "x2 all multipliers")
    FOOL = ("Fool Joker", "Adds +5 chips to base")
    STONE = ("Stone Joker", "x1.5 multiplier, +3 chips")

class Joker:
    def __init__(self, joker_type):
        self.type = joker_type
        self.used = False
        
        # Updated costs for jokers
        self.cost = {
            JokerType.STEEL: 4,
            JokerType.GLASS: 7,
            JokerType.LUCKY: 3,
            JokerType.BRONZE: 2,
            JokerType.SILVER: 5,
            JokerType.GOLD: 6,
            JokerType.DIAMOND: 6,
            JokerType.COSMIC: 9,
            JokerType.FOOL: 3,
            JokerType.STONE: 4
        }[joker_type]
        
        # Define multipliers for all joker types
        self.multiplier = {
            JokerType.STEEL: 2.0,
            JokerType.GLASS: 4.0,
            JokerType.LUCKY: 1.0,
            JokerType.BRONZE: 1.5,
            JokerType.SILVER: 2.0,
            JokerType.GOLD: 3.0,
            JokerType.DIAMOND: 2.5,
            JokerType.COSMIC: 2.0,
            JokerType.STONE: 1.5,
            JokerType.FOOL: 1.0
        }[joker_type]

    def apply_effect(self, hand):
        if self.type == JokerType.LUCKY:
            for card in hand:
                if not card.is_joker:
                    card.value += 1
        return hand

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 768))
        pygame.display.set_caption("Balatro-like")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize sorting preference before dealing cards
        self.sort_by_rank = True  # Default sorting by rank
        
        self.deck = self.create_deck()
        self.hand = []
        self.jokers = []
        self.money = 3  # Starting money (changed from chips)
        self.base_mult = 1.0
        self.current_score = 0
        self.hand_size = 8
        self.preview_score = 0
        self.preview_chips = 0
        self.preview_mult = 0
        self.max_selected = 5  # Maximum cards that can be selected
        self.max_jokers = 6  # Maximum number of jokers allowed
        
        # Deal initial hand after setting sort preference
        self.deal_initial_hand()
        self.discard_pile = []
        self.shop_jokers = self.generate_shop_jokers()
        self.phase = "play"
        self.discards_remaining = 3
        self.hands_remaining = 4
        self.round = 1
        self.ante = 1
        self.ante_round = 1
        self.base_target = 200  # Doubled the base target score
        self.target_score = self.calculate_target_score()
        self.round_complete = False
        
        # Card display settings
        self.card_width = 120
        self.card_height = 168
        self.card_spacing = 125
        self.card_back = pygame.Surface((self.card_width, self.card_height))
        self.card_back.fill((255, 255, 255))
        
        # Initialize fonts
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.large_font = pygame.font.Font(None, 40)
            self.medium_font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 24)
            self.card_rank_font = pygame.font.Font(None, 36)
            self.card_suit_font = pygame.font.Font(None, 48)
            self.card_center_font = pygame.font.Font(None, 72)
        except:
            self.title_font = pygame.font.SysFont("arial", 48)
            self.large_font = pygame.font.SysFont("arial", 40)
            self.medium_font = pygame.font.SysFont("arial", 32)
            self.small_font = pygame.font.SysFont("arial", 24)
            self.card_rank_font = pygame.font.SysFont("arial", 36)
            self.card_suit_font = pygame.font.SysFont("arial", 48)
            self.card_center_font = pygame.font.SysFont("arial", 72)

    def create_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = []
        for suit in Suit:
            for rank in ranks:
                deck.append(Card(suit, rank))
        random.shuffle(deck)
        return deck

    def deal_initial_hand(self):
        for _ in range(self.hand_size):
            if self.deck:
                self.hand.append(self.deck.pop())
        self.sort_cards()  # Sort the initial hand

    def evaluate_selected_hand(self, selected_cards):
        if not selected_cards:
            return HandType.HIGH_CARD
        
        # Count ranks and suits of selected cards only
        ranks = [card.value for card in selected_cards if not card.is_joker]
        suits = [card.suit for card in selected_cards if not card.is_joker]
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        
        # Check for different hand types
        is_flush = len(suit_counts) == 1 and len(suits) >= 5
        is_straight = False
        if ranks:
            sorted_ranks = sorted(set(ranks))
            is_straight = len(sorted_ranks) >= 5 and max(sorted_ranks) - min(sorted_ranks) == len(sorted_ranks) - 1
        
        # Determine hand type
        if is_straight and is_flush and max(ranks) == 14:
            return HandType.ROYAL_FLUSH
        elif is_straight and is_flush:
            return HandType.STRAIGHT_FLUSH
        elif 4 in rank_counts.values():
            return HandType.FOUR_OF_A_KIND
        elif set(rank_counts.values()) == {2, 3}:
            return HandType.FULL_HOUSE
        elif is_flush:
            return HandType.FLUSH
        elif is_straight:
            return HandType.STRAIGHT
        elif 3 in rank_counts.values():
            return HandType.THREE_OF_A_KIND
        elif list(rank_counts.values()).count(2) == 2:
            return HandType.TWO_PAIR
        elif 2 in rank_counts.values():
            return HandType.PAIR
        else:
            return HandType.HIGH_CARD

    def calculate_target_score(self):
        # Scale target score based on ante and round (reverting to original values)
        base_multiplier = 1.5 ** (self.ante - 1)  # Changed from 2.0 back to 1.5
        round_multiplier = 1.2 ** (self.ante_round - 1)  # Changed from 1.5 back to 1.2
        return int(self.base_target * base_multiplier * round_multiplier)

    def calculate_score(self):
        selected_cards = [card for card in self.hand if card.selected]
        if not selected_cards:
            return 0
        
        hand_type = self.evaluate_selected_hand(selected_cards)
        
        # Start with base values from hand type
        base_chips = hand_type.chips
        base_mult = hand_type.mult
        
        # Calculate chips first
        final_chips = base_chips
        
        # Add chips from card values based on hand type
        non_joker_cards = [c for c in selected_cards if not c.is_joker]
        
        # Apply Lucky Joker effect first
        if any(joker.type == JokerType.LUCKY for joker in self.jokers):
            for card in non_joker_cards:
                card.value += 1
        
        # Calculate chips based on hand type
        if hand_type == HandType.HIGH_CARD:
            highest_card = max(non_joker_cards, key=lambda x: x.value)
            final_chips += highest_card.get_chip_value()
        elif hand_type == HandType.PAIR:
            paired_value = next(value for value, count in Counter([c.value for c in non_joker_cards]).items() if count == 2)
            paired_cards = [c for c in non_joker_cards if c.value == paired_value]
            final_chips += sum(c.get_chip_value() for c in paired_cards)
        elif hand_type == HandType.TWO_PAIR:
            pairs = [value for value, count in Counter([c.value for c in non_joker_cards]).items() if count == 2]
            paired_cards = [c for c in non_joker_cards if c.value in pairs]
            final_chips += sum(c.get_chip_value() for c in paired_cards)
        elif hand_type == HandType.THREE_OF_A_KIND:
            three_value = next(value for value, count in Counter([c.value for c in non_joker_cards]).items() if count >= 3)
            matching_cards = [c for c in non_joker_cards if c.value == three_value][:3]
            final_chips += sum(c.get_chip_value() for c in matching_cards)
        elif hand_type in [HandType.STRAIGHT, HandType.FLUSH, HandType.STRAIGHT_FLUSH, HandType.ROYAL_FLUSH]:
            final_chips += sum(c.get_chip_value() for c in non_joker_cards)
        elif hand_type == HandType.FULL_HOUSE:
            final_chips += sum(c.get_chip_value() for c in non_joker_cards)
        elif hand_type == HandType.FOUR_OF_A_KIND:
            four_value = next(value for value, count in Counter([c.value for c in non_joker_cards]).items() if count == 4)
            four_cards = [c for c in non_joker_cards if c.value == four_value]
            final_chips += sum(c.get_chip_value() for c in four_cards)
        
        # Apply chip-adding joker effects
        for joker in self.jokers:
            if joker.type == JokerType.LUCKY:
                final_chips += 10
            elif joker.type == JokerType.FOOL:
                final_chips += 5
            elif joker.type == JokerType.STONE:
                final_chips += 3
        
        # Calculate final multiplier
        final_mult = base_mult
        
        # First apply additive multipliers
        for joker in self.jokers:
            if joker.type == JokerType.STEEL:
                final_mult += 2.0
        
        # Then apply multiplicative multipliers
        for joker in self.jokers:
            if joker.type == JokerType.GLASS and not joker.used:
                final_mult *= 4.0
                joker.used = True
            elif joker.type == JokerType.BRONZE and hand_type == HandType.PAIR:
                final_mult *= 1.5
            elif joker.type == JokerType.SILVER and hand_type == HandType.THREE_OF_A_KIND:
                final_mult *= 2.0
            elif joker.type == JokerType.GOLD and hand_type == HandType.STRAIGHT:
                final_mult *= 3.0
            elif joker.type == JokerType.DIAMOND and hand_type == HandType.FLUSH:
                final_mult *= 2.5
            elif joker.type == JokerType.COSMIC:
                final_mult *= 2.0
            elif joker.type == JokerType.STONE:
                final_mult *= 1.5
        
        # Reset card values after Lucky Joker effect
        if any(joker.type == JokerType.LUCKY for joker in self.jokers):
            for card in non_joker_cards:
                card.value -= 1
        
        return int(final_chips * final_mult)

    def generate_shop_jokers(self):
        available_jokers = list(JokerType)
        return [Joker(random.choice(available_jokers)) for _ in range(3)]

    def discard_selected_cards(self):
        if not self.hands_remaining > 0:
            return False
        
        # Move selected cards to discard pile
        selected_cards = [card for card in self.hand if card.selected]
        self.hand = [card for card in self.hand if not card.selected]
        self.discard_pile.extend(selected_cards)
        
        # Draw new cards
        cards_needed = self.hand_size - len(self.hand)
        for _ in range(cards_needed):
            if self.deck:
                self.hand.append(self.deck.pop())
            elif self.discard_pile:
                self.deck = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.deck)
                if self.deck:
                    self.hand.append(self.deck.pop())
        
        self.discards_remaining -= 1
        return True

    def buy_joker(self, index):
        if index < len(self.shop_jokers):
            joker = self.shop_jokers[index]
            if self.money >= joker.cost and len(self.jokers) < self.max_jokers:
                self.money -= joker.cost
                self.jokers.append(joker)
                self.shop_jokers.pop(index)

    def sell_joker(self, index):
        if index < len(self.jokers):
            joker = self.jokers[index]
            sell_price = joker.cost // 2  # Get half the original cost back
            self.money += sell_price
            self.jokers.pop(index)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.phase == "play":
                    if event.button == 3:  # Right click
                        self.handle_joker_sell(mouse_pos)
                    else:
                        # Check sort buttons first
                        button_width = 100
                        # Position buttons at top-right with 20px right margin
                        button_x = 1280 - 20 - (button_width * 2 + 5)
                        button_y = 5
                        button_height = 28
                        
                        if (button_x <= mouse_pos[0] <= button_x + button_width and
                            button_y <= mouse_pos[1] <= button_y + button_height):
                            self.sort_by_rank = True
                            self.sort_cards()
                        elif (button_x + button_width + 5 <= mouse_pos[0] <= button_x + button_width * 2 + 5 and
                              button_y <= mouse_pos[1] <= button_y + button_height):
                            self.sort_by_rank = False
                            self.sort_cards()
                        else:
                            self.handle_card_click(mouse_pos)
                            self.update_preview_score()
                elif self.phase == "shop":
                    self.handle_shop_click(mouse_pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.hands_remaining > 0:
                    if not any(card.selected for card in self.hand):
                        continue  # Don't process if no cards selected
                        
                    # Add to current_score instead of replacing it
                    self.current_score += self.calculate_score()
                    self.hands_remaining -= 1
                    
                    # Only discard selected cards
                    selected_cards = [card for card in self.hand if card.selected]
                    self.hand = [card for card in self.hand if not card.selected]
                    self.discard_pile.extend(selected_cards)
                    
                    # Draw new cards to replace discarded ones
                    cards_needed = self.hand_size - len(self.hand)
                    for _ in range(cards_needed):
                        if self.deck:
                            self.hand.append(self.deck.pop())
                    
                    # Reset all card selections
                    for card in self.hand:
                        card.selected = False
                    
                    # Sort the new hand
                    self.sort_cards()
                    
                    # Check win/loss conditions
                    if self.current_score >= self.target_score:
                        self.round_complete = True
                        self.win_round()
                    elif self.hands_remaining == 0 and not self.round_complete:
                        print(f"Final score: {self.current_score}, Target: {self.target_score}")
                        self.game_over()
                elif event.key == pygame.K_d and self.discards_remaining > 0:
                    if self.discard_selected_cards():
                        self.sort_cards()
                        self.update_preview_score()
                elif event.key == pygame.K_n and self.phase == "shop":
                    self.next_round()
                elif event.key == pygame.K_s and self.phase == "play":
                    # Allow skipping only on rounds 1 and 2
                    if self.ante_round < 3:
                        self.skip_round()

    def handle_card_click(self, pos):
        x, y = pos
        # Calculate card starting position (same as in draw_play_phase)
        screen_width = 1280
        max_card_end_x = screen_width - 20
        left_margin = 250
        
        total_card_width = len(self.hand) * self.card_spacing - (self.card_spacing - self.card_width)
        available_width = max_card_end_x - left_margin
        
        if total_card_width <= available_width:
            start_x = left_margin + (available_width - total_card_width) // 2
        else:
            start_x = left_margin
        
        card_y = 340
        
        card_x = start_x
        for card in self.hand:
            if (card_x <= x <= card_x + self.card_width and 
                card_y <= y <= card_y + self.card_height):
                # Only allow selection if under max or card is already selected
                if not card.selected and sum(1 for c in self.hand if c.selected) >= self.max_selected:
                    continue
                card.selected = not card.selected
                break
            card_x += self.card_spacing

    def handle_shop_click(self, pos):
        x, y = pos
        shop_start_y = 150
        joker_width = 350
        joker_height = 160
        joker_spacing = 180
        center_x = 640
        joker_x = center_x - (joker_width // 2)
        
        for i in range(len(self.shop_jokers)):
            joker_click_y = shop_start_y + i * joker_spacing
            if (joker_x <= x <= joker_x + joker_width and 
                joker_click_y <= y <= joker_click_y + joker_height):
                self.buy_joker(i)
                break

    def handle_joker_sell(self, pos):
        x, y = pos
        # Top horizontal joker bar layout must match draw_play_phase
        bar_x = 350
        bar_y = 30
        bar_width = 1280 - bar_x - 20
        # Joker card size and spacing in the bar
        joker_width = 140
        joker_height = 85
        joker_spacing = 150
        start_x = bar_x + 15
        start_y = bar_y + 45

        for i, _ in enumerate(self.jokers):
            if i >= 6:
                break
            jx = start_x + i * joker_spacing
            jy = start_y
            if (jx <= x <= jx + joker_width and jy <= y <= jy + joker_height):
                self.sell_joker(i)
                break

    def win_round(self):
        # Award money for the winning hand
        money_reward = self.calculate_money_reward()
        self.money += money_reward
        print(f"Won ${money_reward}! New total: ${self.money}")
        
        # Reset all card selections
        for card in self.hand:
            card.selected = False
        
        # Automatically go to shop
        self.phase = "shop"
        self.shop_jokers = self.generate_shop_jokers()

    def game_over(self):
        print("Game Over! You didn't reach the target score.")
        # Reset game
        self.__init__()

    def next_round(self):
        if self.phase == "play":
            # Can't skip round 3 of any ante
            if self.ante_round == 3:
                return
            
        self.ante_round += 1
        if self.ante_round > 3:
            self.ante_round = 1
            self.ante += 1
            if self.ante > 8:
                self.game_over()
                return

        self.round += 1
        self.target_score = self.calculate_target_score()
        self.phase = "play"
        self.discards_remaining = 3
        self.hands_remaining = 4
        self.round_complete = False
        self.current_score = 0
        
        # Reset glass joker usage
        for joker in self.jokers:
            if joker.type == JokerType.GLASS:
                joker.used = False
                
        # Reset deck and hand
        self.deck = self.create_deck()
        self.hand = []
        self.deal_initial_hand()
        
        # Reset all card selections
        for card in self.hand:
            card.selected = False

    def update(self):
        # Game logic updates here
        pass

    def draw(self):
        self.screen.fill((20, 71, 41))  # Darker green background

        if self.phase == "play":
            self.draw_play_phase()
        else:
            self.draw_shop_phase()

        pygame.display.flip()

    def draw_play_phase(self):
        self.screen.fill((15, 25, 35))  # Dark blue-gray background
        
        # Calculate card positioning - cards use full width minus right margin
        max_card_end_x = 1280 - 20  # 20px right margin
        left_margin = 250  # Align just right of the left info panel
        
        # Calculate total width needed for all cards
        total_card_width = len(self.hand) * self.card_spacing - (self.card_spacing - self.card_width)
        
        # Calculate available width
        available_width = max_card_end_x - left_margin
        
        # If cards fit, center them. Otherwise, scale spacing or start from left margin
        if total_card_width <= available_width:
            start_x = left_margin + (available_width - total_card_width) // 2
        else:
            # Cards don't fit with current spacing, start from left margin
            start_x = left_margin
        
        card_y = 340  # Lower the row of cards slightly
        
        # Draw cards in hand
        x = start_x
        for card in self.hand:
            self.draw_card(self.screen, x, card_y, card, card.selected)
            x += self.card_spacing

        # Draw game info panel (left side)
        panel_width = 320
        panel_height = 240
        panel_x = 30
        panel_y = 30
        self.draw_panel(self.screen, panel_x, panel_y, panel_width, panel_height, (30, 40, 50))
        
        y_offset = panel_y + 20
        line_height = 28
        
        # Title
        title_text = self.large_font.render("Game Info", True, (255, 220, 100))
        self.screen.blit(title_text, (panel_x + 15, y_offset))
        y_offset += line_height + 5
        
        # Info items
        info_items = [
            ("Ante", str(self.ante)),
            ("Round", f"{self.ante_round}/3"),
            ("Target", str(self.target_score)),
            ("Score", str(self.current_score)),
            ("Money", f"${self.money}"),
            ("Discards", str(self.discards_remaining)),
            ("Hands", str(self.hands_remaining))
        ]
        
        for label, value in info_items:
            label_text = self.small_font.render(f"{label}:", True, (180, 180, 200))
            value_text = self.medium_font.render(value, True, (255, 255, 255))
            self.screen.blit(label_text, (panel_x + 20, y_offset))
            self.screen.blit(value_text, (panel_x + 120, y_offset))
            y_offset += line_height

        # Draw jokers bar (top horizontal)
        joker_bar_x = left_margin
        joker_bar_y = 30
        joker_bar_width = 1280 - joker_bar_x - 20
        joker_bar_height = 110
        self.draw_panel(self.screen, joker_bar_x, joker_bar_y, joker_bar_width, joker_bar_height, (40, 35, 25))

        # Joker title
        joker_title = self.medium_font.render("Jokers", True, (255, 220, 100))
        self.screen.blit(joker_title, (joker_bar_x + 15, joker_bar_y + 12))

        # Draw jokers horizontally
        j_start_x = joker_bar_x + 15
        j_start_y = joker_bar_y + 45
        j_width = 140
        j_height = 85
        j_spacing = 150
        for i, joker in enumerate(self.jokers[:6]):
            jx = j_start_x + i * j_spacing
            jy = j_start_y
            joker_card_rect = pygame.Rect(jx, jy, j_width, j_height)
            pygame.draw.rect(self.screen, (250, 220, 50), joker_card_rect, border_radius=6)
            pygame.draw.rect(self.screen, (200, 170, 0), joker_card_rect, width=2, border_radius=6)

            name = joker.type.value[0]
            if len(name) > 16:
                name = name[:13] + "..."
            name_text = self.small_font.render(name, True, (40, 20, 0))
            self.screen.blit(name_text, (jx + 8, jy + 6))

            desc = joker.type.value[1]
            if len(desc) > 18:
                desc = desc[:15] + "..."
            desc_text = self.small_font.render(desc, True, (80, 60, 0))
            self.screen.blit(desc_text, (jx + 8, jy + 28))

            sell_text = self.small_font.render(f"Sell: ${joker.cost//2}", True, (100, 50, 0))
            self.screen.blit(sell_text, (jx + 8, jy + 52))
        
        # Draw preview panel (below cards)
        if any(card.selected for card in self.hand):
            preview_x = start_x
            preview_y = card_y + self.card_height + 20
            preview_width = min(total_card_width, 500)
            self.draw_panel(self.screen, preview_x, preview_y, preview_width, 100, (20, 30, 40))
            
            preview_y_offset = preview_y + 15
            preview_items = [
                ("Chips", str(self.preview_chips)),
                ("Mult", f"x{self.preview_mult:.1f}"),
                ("Score", str(self.preview_score))
            ]
            
            item_spacing = preview_width // 3
            for i, (label, value) in enumerate(preview_items):
                x_pos = preview_x + 20 + i * item_spacing
                label_text = self.small_font.render(label, True, (180, 180, 200))
                value_text = self.medium_font.render(value, True, (100, 255, 150))
                self.screen.blit(label_text, (x_pos, preview_y_offset))
                self.screen.blit(value_text, (x_pos, preview_y_offset + 25))

        # Draw instructions panel (bottom left)
        inst_panel_x = 30
        inst_panel_y = 680
        inst_panel_width = 350
        inst_panel_height = 70
        self.draw_panel(self.screen, inst_panel_x, inst_panel_y, inst_panel_width, inst_panel_height, (25, 30, 35))
        
        instructions = [
            "SPACE: Play  |  D: Discard  |  N: Next  |  S: Skip"
        ]
        y_pos = inst_panel_y + 12
        for inst in instructions:
            text = self.small_font.render(inst, True, (200, 200, 220))
            self.screen.blit(text, (inst_panel_x + 15, y_pos))
            y_pos += 20

        # Draw sort buttons (top right)
        button_width = 100
        button_x = 1280 - 20 - (button_width * 2 + 5)
        button_y = 5
        button_height = 28
        
        # Rank sort button
        rank_bg = (80, 120, 150) if self.sort_by_rank else (50, 70, 90)
        rank_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, rank_bg, rank_rect, border_radius=4)
        pygame.draw.rect(self.screen, (120, 160, 200) if self.sort_by_rank else (70, 90, 110), 
                        rank_rect, width=2, border_radius=4)
        rank_text = self.small_font.render("Sort: Rank", True, (255, 255, 255))
        self.screen.blit(rank_text, (button_x + 10, button_y + 6))
        
        # Suit sort button
        suit_bg = (80, 120, 150) if not self.sort_by_rank else (50, 70, 90)
        suit_rect = pygame.Rect(button_x + button_width + 5, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, suit_bg, suit_rect, border_radius=4)
        pygame.draw.rect(self.screen, (120, 160, 200) if not self.sort_by_rank else (70, 90, 110), 
                        suit_rect, width=2, border_radius=4)
        suit_text = self.small_font.render("Sort: Suit", True, (255, 255, 255))
        self.screen.blit(suit_text, (button_x + button_width + 15, button_y + 6))

    def draw_shop_phase(self):
        self.screen.fill((15, 25, 35))  # Same background as play phase
        
        # Title panel
        title_panel_x = 100
        title_panel_y = 30
        title_panel_width = 1080
        title_panel_height = 80
        self.draw_panel(self.screen, title_panel_x, title_panel_y, title_panel_width, title_panel_height, (40, 50, 60))
        
        title_text = self.title_font.render("SHOP", True, (255, 220, 100))
        title_rect = title_text.get_rect(center=(title_panel_x + title_panel_width//2, title_panel_y + 25))
        self.screen.blit(title_text, title_rect)
        
        money_text = self.large_font.render(f"Money: ${self.money}", True, (100, 255, 150))
        money_rect = money_text.get_rect(center=(title_panel_x + title_panel_width//2, title_panel_y + 60))
        self.screen.blit(money_text, money_rect)
        
        instruction_text = self.small_font.render("Press N to continue to next round", True, (200, 200, 220))
        inst_rect = instruction_text.get_rect(center=(title_panel_x + title_panel_width//2, title_panel_y + title_panel_height - 15))
        self.screen.blit(instruction_text, inst_rect)

        # Draw shop jokers
        shop_start_y = 150
        joker_width = 350
        joker_height = 160
        joker_spacing = 180
        center_x = 640  # Center of screen
        
        for i, joker in enumerate(self.shop_jokers):
            joker_x = center_x - (joker_width // 2)
            joker_y = shop_start_y + i * joker_spacing
            
            # Joker card background with shadow
            self.draw_panel(self.screen, joker_x, joker_y, joker_width, joker_height, (250, 220, 50), alpha=255)
            
            # Inner border
            joker_rect = pygame.Rect(joker_x + 5, joker_y + 5, joker_width - 10, joker_height - 10)
            pygame.draw.rect(self.screen, (200, 170, 0), joker_rect, width=2, border_radius=6)
            
            # Joker name
            name = joker.type.value[0]
            name_text = self.large_font.render(name, True, (40, 20, 0))
            self.screen.blit(name_text, (joker_x + 20, joker_y + 15))
            
            # Cost
            cost_text = self.medium_font.render(f"Cost: ${joker.cost}", True, (150, 100, 0))
            self.screen.blit(cost_text, (joker_x + 20, joker_y + 55))
            
            # Description (split into multiple lines if needed)
            desc = joker.type.value[1]
            desc_lines = []
            if len(desc) > 40:
                words = desc.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) > 40:
                        desc_lines.append(current_line.strip())
                        current_line = word + " "
                    else:
                        current_line += word + " "
                desc_lines.append(current_line.strip())
            else:
                desc_lines = [desc]
            
            desc_y = joker_y + 90
            for line in desc_lines:
                desc_text = self.small_font.render(line, True, (80, 60, 0))
                self.screen.blit(desc_text, (joker_x + 20, desc_y))
                desc_y += 22
            
            # Click instruction
            click_text = self.small_font.render("Click to buy", True, (100, 70, 0))
            self.screen.blit(click_text, (joker_x + 20, joker_y + joker_height - 30))

    def update_preview_score(self):
        selected_cards = [card for card in self.hand if card.selected]
        if not selected_cards:
            self.preview_chips = 0
            self.preview_mult = 0
            self.preview_score = 0
            return

        hand_type = self.evaluate_selected_hand(selected_cards)
        
        # Start with base values from hand type
        self.preview_chips = hand_type.chips
        self.preview_mult = hand_type.mult
        
        # Add chips from card values based on hand type
        non_joker_cards = [c for c in selected_cards if not c.is_joker]
        
        # Apply Lucky Joker effect first
        if any(joker.type == JokerType.LUCKY for joker in self.jokers):
            for card in non_joker_cards:
                card.value += 1
        
        # Calculate chips based on hand type
        if hand_type == HandType.HIGH_CARD:
            highest_card = max(non_joker_cards, key=lambda x: x.value)
            self.preview_chips += highest_card.get_chip_value()
        elif hand_type == HandType.PAIR:
            paired_value = next(value for value, count in Counter([c.value for c in non_joker_cards]).items() if count == 2)
            paired_cards = [c for c in non_joker_cards if c.value == paired_value]
            self.preview_chips += sum(c.get_chip_value() for c in paired_cards)
        elif hand_type == HandType.TWO_PAIR:
            pairs = [value for value, count in Counter([c.value for c in non_joker_cards]).items() if count == 2]
            paired_cards = [c for c in non_joker_cards if c.value in pairs]
            self.preview_chips += sum(c.get_chip_value() for c in paired_cards)
        elif hand_type == HandType.THREE_OF_A_KIND:
            three_value = next(value for value, count in Counter([c.value for c in non_joker_cards]).items() if count >= 3)
            matching_cards = [c for c in non_joker_cards if c.value == three_value][:3]
            self.preview_chips += sum(c.get_chip_value() for c in matching_cards)
        elif hand_type in [HandType.STRAIGHT, HandType.FLUSH, HandType.STRAIGHT_FLUSH, HandType.ROYAL_FLUSH]:
            self.preview_chips += sum(c.get_chip_value() for c in non_joker_cards)
        elif hand_type == HandType.FULL_HOUSE:
            self.preview_chips += sum(c.get_chip_value() for c in non_joker_cards)
        elif hand_type == HandType.FOUR_OF_A_KIND:
            four_value = next(value for value, count in Counter([c.value for c in non_joker_cards]).items() if count == 4)
            four_cards = [c for c in non_joker_cards if c.value == four_value]
            self.preview_chips += sum(c.get_chip_value() for c in four_cards)
        
        # Apply chip-adding joker effects
        for joker in self.jokers:
            if joker.type == JokerType.LUCKY:
                self.preview_chips += 10
            elif joker.type == JokerType.FOOL:
                self.preview_chips += 5
            elif joker.type == JokerType.STONE:
                self.preview_chips += 3
        
        # First apply additive multipliers
        for joker in self.jokers:
            if joker.type == JokerType.STEEL:
                self.preview_mult += 2.0
        
        # Then apply multiplicative multipliers
        for joker in self.jokers:
            if joker.type == JokerType.GLASS and not joker.used:
                self.preview_mult *= 4.0
            elif joker.type == JokerType.BRONZE and hand_type == HandType.PAIR:
                self.preview_mult *= 1.5
            elif joker.type == JokerType.SILVER and hand_type == HandType.THREE_OF_A_KIND:
                self.preview_mult *= 2.0
            elif joker.type == JokerType.GOLD and hand_type == HandType.STRAIGHT:
                self.preview_mult *= 3.0
            elif joker.type == JokerType.DIAMOND and hand_type == HandType.FLUSH:
                self.preview_mult *= 2.5
            elif joker.type == JokerType.COSMIC:
                self.preview_mult *= 2.0
            elif joker.type == JokerType.STONE:
                self.preview_mult *= 1.5
        
        # Reset card values after Lucky Joker effect
        if any(joker.type == JokerType.LUCKY for joker in self.jokers):
            for card in non_joker_cards:
                card.value -= 1
        
        self.preview_score = int(self.preview_chips * self.preview_mult)

    def sort_cards(self):
        if self.sort_by_rank:
            self.hand.sort(key=lambda card: (card.value, card.suit.value))
        else:  # sort by suit
            self.hand.sort(key=lambda card: (card.suit.value, card.value))
    
    def draw_card(self, surface, x, y, card, selected=False):
        """Draw a professional-looking playing card"""
        # Card dimensions
        width = self.card_width
        height = self.card_height
        
        # Shadow
        shadow_offset = 4
        shadow_rect = pygame.Rect(x + shadow_offset, y + shadow_offset, width, height)
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 100), (0, 0, width, height), border_radius=8)
        surface.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))
        
        # Main card background
        if selected:
            bg_color = (200, 220, 255)  # Light blue when selected
            border_color = (100, 150, 255)
            border_width = 3
        else:
            bg_color = (255, 255, 255)
            border_color = (0, 0, 0)
            border_width = 2
        
        # Draw card with rounded corners
        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, bg_color, card_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, card_rect, width=border_width, border_radius=8)
        
        # Draw card content
        if card.is_joker:
            # Joker card design
            joker_color = (200, 0, 200)
            joker_text = self.medium_font.render("JKR", True, joker_color)
            joker_rect = joker_text.get_rect(center=(x + width//2, y + height//2))
            surface.blit(joker_text, joker_rect)
        else:
            # Regular card
            is_red = card.suit in [Suit.HEARTS, Suit.DIAMONDS]
            text_color = (220, 0, 0) if is_red else (0, 0, 0)
            
            # Get suit symbol and letter
            suit_symbol = card.suit.value
            suit_letter = {"♥": "H", "♦": "D", "♣": "C", "♠": "S"}.get(suit_symbol, "?")
            
            # Top left rank and suit with letter
            rank_text = self.card_rank_font.render(card.rank, True, text_color)
            suit_text = self.card_suit_font.render(suit_symbol, True, text_color)
            suit_letter_text = self.small_font.render(suit_letter, True, text_color)
            
            # Position at top-left - rank, suit symbol, and letter
            surface.blit(rank_text, (x + 10, y + 10))
            surface.blit(suit_text, (x + 10, y + 35))
            surface.blit(suit_letter_text, (x + 10, y + 58))
            
            # Center suit symbol (much larger and more visible)
            center_suit = self.card_center_font.render(suit_symbol, True, text_color)
            center_rect = center_suit.get_rect(center=(x + width//2, y + height//2 + 5))
            surface.blit(center_suit, center_rect)
            
            # Add suit letter below center symbol for extra clarity
            center_letter = self.medium_font.render(suit_letter, True, text_color)
            center_letter_rect = center_letter.get_rect(center=(x + width//2, y + height//2 + 50))
            surface.blit(center_letter, center_letter_rect)
            
            # Bottom right rank and suit (rotated)
            rank_rotated = pygame.transform.rotate(rank_text, 180)
            suit_rotated = pygame.transform.rotate(suit_text, 180)
            suit_letter_rotated = pygame.transform.rotate(suit_letter_text, 180)
            
            surface.blit(rank_rotated, (x + width - rank_rotated.get_width() - 10, 
                                       y + height - rank_rotated.get_height() - 10))
            surface.blit(suit_rotated, (x + width - suit_rotated.get_width() - 10, 
                                       y + height - suit_rotated.get_height() - 35))
            surface.blit(suit_letter_rotated, (x + width - suit_letter_rotated.get_width() - 10, 
                                               y + height - suit_letter_rotated.get_height() - 58))
    
    def draw_panel(self, surface, x, y, width, height, bg_color=(40, 40, 50), alpha=230):
        """Draw a professional UI panel with shadow"""
        # Shadow
        shadow_offset = 3
        shadow_rect = pygame.Rect(x + shadow_offset, y + shadow_offset, width, height)
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 100), (0, 0, width, height), border_radius=6)
        surface.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))
        
        # Main panel
        panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        panel_surf.fill((*bg_color, alpha))
        pygame.draw.rect(panel_surf, (100, 100, 120), (0, 0, width, height), width=2, border_radius=6)
        surface.blit(panel_surf, (x, y))

    def calculate_money_reward(self):
        # Base money from hand type
        selected_cards = [c for c in self.hand if c.selected]
        hand_type = self.evaluate_selected_hand(selected_cards)
        
        # Money rewards for each hand type
        base_money = {
            HandType.HIGH_CARD: 2,
            HandType.PAIR: 3,
            HandType.TWO_PAIR: 4,
            HandType.THREE_OF_A_KIND: 5,
            HandType.STRAIGHT: 6,
            HandType.FLUSH: 7,
            HandType.FULL_HOUSE: 8,
            HandType.FOUR_OF_A_KIND: 10,
            HandType.STRAIGHT_FLUSH: 15,
            HandType.ROYAL_FLUSH: 20
        }[hand_type]

        # Money from jokers
        joker_money = sum(1 for joker in self.jokers if joker.type == JokerType.FOOL)
        
        # Money for remaining hands
        hands_left_money = self.hands_remaining
        
        # Calculate interest
        interest = self.calculate_interest()
        
        total_money = base_money + joker_money + hands_left_money + interest
        print(f"Money breakdown: Base: ${base_money}, Jokers: ${joker_money}, Hands left: ${hands_left_money}, Interest: ${interest}")
        
        return total_money

    def calculate_interest(self):
        return self.money // 5  # $1 for every $5

    def skip_round(self):
        """Skip the current round and go to the next one"""
        self.ante_round += 1
        if self.ante_round > 3:
            self.ante_round = 1
            self.ante += 1
            if self.ante > 8:
                self.game_over()
                return

        self.round += 1
        self.target_score = self.calculate_target_score()
        self.discards_remaining = 3
        self.hands_remaining = 4
        self.round_complete = False
        self.current_score = 0
        
        # Reset glass joker usage
        for joker in self.jokers:
            if joker.type == JokerType.GLASS:
                joker.used = False
                
        # Reset deck and hand
        self.deck = self.create_deck()
        self.hand = []
        self.deal_initial_hand()
        
        # Reset all card selections
        for card in self.hand:
            card.selected = False

if __name__ == "__main__":
    game = Game()
    game.run()
