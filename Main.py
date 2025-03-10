import pygame
import random
from enum import Enum
from collections import Counter
import os

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
        self.card_width = 100
        self.card_height = 150
        self.card_spacing = 110
        self.card_back = pygame.Surface((self.card_width, self.card_height))
        self.card_back.fill((255, 255, 255))

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
                        if 900 <= mouse_pos[0] <= 1000:  # X position for sort buttons
                            if 50 <= mouse_pos[1] <= 80:  # Rank sort button
                                self.sort_by_rank = True
                                self.sort_cards()
                            elif 90 <= mouse_pos[1] <= 120:  # Suit sort button
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
        card_x = 100
        
        for card in self.hand:
            if (card_x <= x <= card_x + self.card_width and 
                250 <= y <= 250 + self.card_height):
                # Only allow selection if under max or card is already selected
                if not card.selected and sum(1 for c in self.hand if c.selected) >= self.max_selected:
                    continue
                card.selected = not card.selected
            card_x += self.card_spacing

    def handle_shop_click(self, pos):
        x, y = pos
        for i in range(len(self.shop_jokers)):
            # Expand clickable area to match the visual joker card size
            if 100 <= x <= 400 and 150 + i * 100 <= y <= 230 + i * 100:
                self.buy_joker(i)

    def handle_joker_sell(self, pos):
        x, y = pos
        base_x = 750
        
        for i, joker in enumerate(self.jokers):
            joker_x = base_x + (260 if i >= 3 else 0)
            joker_y = 50 + (70 * (i % 3))
            
            if (joker_x <= x <= joker_x + 250 and 
                joker_y <= y <= joker_y + 60):
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
        self.screen.fill((20, 71, 41))
        
        # Draw cards in hand with adjusted spacing
        x = 100  # Start further left
        for card in self.hand:
            color = (180, 180, 180) if card.selected else (255, 255, 255)
            pygame.draw.rect(self.screen, color, (x, 250, self.card_width, self.card_height))
            pygame.draw.rect(self.screen, (0, 0, 0), (x, 250, self.card_width, self.card_height), 2)
            
            font = pygame.font.Font(None, 48)
            text_color = (255, 0, 0) if card.suit in [Suit.HEARTS, Suit.DIAMONDS] else (0, 0, 0)
            
            card_text = card.get_display_str()
            text = font.render(card_text, True, text_color)
            text_x = x + (self.card_width - text.get_width()) // 2
            text_y = 250 + (self.card_height - text.get_height()) // 2
            self.screen.blit(text, (text_x, text_y))
            
            x += self.card_spacing

        # Draw game info panel
        info_font = pygame.font.Font(None, 36)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), (20, 20, 300, 200))
        
        texts = [
            f"Ante: {self.ante}",
            f"Round: {self.ante_round}/3",
            f"Target: {self.target_score}",
            f"Score: {self.current_score}",
            f"Money: ${self.money}",  # Changed from chips to money
            f"Base Mult: x{self.base_mult:.1f}",
            f"Discards Left: {self.discards_remaining}",
            f"Hands Left: {self.hands_remaining}"
        ]
        
        y = 30
        for text in texts:
            text_surface = info_font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (30, y))
            y += 25

        # Draw jokers with descriptions (adjusted layout)
        joker_font = pygame.font.Font(None, 24)
        x = 750
        y = 50
        for i, joker in enumerate(self.jokers):
            # Move to next column after 3 jokers
            if i == 3:
                x += 260
                y = 50
            
            pygame.draw.rect(self.screen, (255, 255, 0), (x, y, 250, 60))
            name_text = joker_font.render(joker.type.value[0], True, (0, 0, 0))
            desc_text = joker_font.render(joker.type.value[1], True, (0, 0, 0))
            sell_text = joker_font.render(f"Right click to sell (${joker.cost//2})", True, (0, 0, 0))
            
            self.screen.blit(name_text, (x + 5, y + 5))
            self.screen.blit(desc_text, (x + 5, y + 25))
            self.screen.blit(sell_text, (x + 5, y + 45))
            
            if i < 3:
                y += 70

        # Draw instructions
        inst_font = pygame.font.Font(None, 24)
        instructions = [
            "SPACE: Play hand",
            "D: Discard selected",
            "N: Next round",
            "S: Skip round (not on round 3)",
            "Click cards to select"
        ]
        y = 650
        for inst in instructions:
            text = inst_font.render(inst, True, (255, 255, 255))
            self.screen.blit(text, (20, y))
            y += 25

        # Draw preview information if cards are selected
        if any(card.selected for card in self.hand):
            preview_font = pygame.font.Font(None, 36)
            preview_texts = [
                f"Preview Chips: {self.preview_chips}",
                f"Preview Mult: x{self.preview_mult:.1f}",
                f"Preview Score: {self.preview_score}"
            ]
            
            y = 450  # Position below cards
            for text in preview_texts:
                text_surface = preview_font.render(text, True, (255, 255, 0))
                self.screen.blit(text_surface, (30, y))
                y += 30

        # Draw sort buttons
        button_font = pygame.font.Font(None, 32)
        
        # Rank sort button
        rank_color = (180, 180, 180) if self.sort_by_rank else (255, 255, 255)
        pygame.draw.rect(self.screen, rank_color, (900, 50, 100, 30))
        rank_text = button_font.render("Sort Rank", True, (0, 0, 0))
        self.screen.blit(rank_text, (905, 55))
        
        # Suit sort button
        suit_color = (180, 180, 180) if not self.sort_by_rank else (255, 255, 255)
        pygame.draw.rect(self.screen, suit_color, (900, 90, 100, 30))
        suit_text = button_font.render("Sort Suit", True, (0, 0, 0))
        self.screen.blit(suit_text, (905, 95))

    def draw_shop_phase(self):
        self.screen.fill((20, 71, 41))  # Keep same background as play phase
        
        font = pygame.font.Font(None, 36)
        title = font.render(f"Shop (Press N to continue) - Money: ${self.money}", True, (255, 255, 255))
        self.screen.blit(title, (300, 50))

        for i, joker in enumerate(self.shop_jokers):
            # Draw joker card
            pygame.draw.rect(self.screen, (255, 255, 0), (100, 150 + i * 100, 300, 80))
            
            # Draw joker info
            name_text = font.render(f"{joker.type.value[0]}", True, (0, 0, 0))
            cost_text = font.render(f"Cost: ${joker.cost}", True, (0, 0, 0))  # Changed to show $
            desc_text = font.render(f"{joker.type.value[1]}", True, (0, 0, 0))
            
            self.screen.blit(name_text, (110, 160 + i * 100))
            self.screen.blit(cost_text, (110, 190 + i * 100))
            self.screen.blit(desc_text, (110, 220 + i * 100))

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
