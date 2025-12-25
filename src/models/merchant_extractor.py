"""
Merchant Name Extractor
Extracts clean merchant names from transaction descriptions.
"""

import re
from typing import Optional, Dict


class MerchantExtractor:
    """Extracts merchant names from transaction descriptions."""
    
    def __init__(self):
        """Initialize the merchant extractor."""
        # Common patterns to clean up merchant names
        # These patterns help extract the actual merchant name from transaction descriptions
        
        # Known merchant name mappings (common abbreviations/patterns)
        self.merchant_mappings = {
            r'AMZN\s*MKTP?\s*US': 'Amazon',
            r'AMAZON\.COM': 'Amazon',
            r'AMAZON MARKETPLACE': 'Amazon',
            r'UBER\s*\*': 'Uber',
            r'UBER\s*TRIP': 'Uber',
            r'UBER\s*EATS': 'Uber Eats',
            r'LYFT\s*\*': 'Lyft',
            r'SQ\s*\*': 'Square',
            r'PAYPAL\s*\*': 'PayPal',
            r'GOOGLE\s*\*': 'Google',
            r'APPLE\.COM': 'Apple',
            r'MICROSOFT': 'Microsoft',
            r'NETFLIX': 'Netflix',
            r'SPOTIFY': 'Spotify',
            r'STARBUCKS': 'Starbucks',
            r'MCDONALD': 'McDonald\'s',
            r'BURGER\s*KING|BK\s+': 'Burger King',
            r'WENDY\'?S': 'Wendy\'s',
            r'TACO\s*BELL': 'Taco Bell',
            r'KFC': 'KFC',
            r'SUBWAY': 'Subway',
            r'DUNKIN|DUNKIN\'?\s*DONUTS': 'Dunkin\' Donuts',
            r'PIZZA\s*HUT': 'Pizza Hut',
            r'DOMINO\'?S': 'Domino\'s',
            r'PAPA\s*JOHN': 'Papa John\'s',
            r'CHIPOTLE': 'Chipotle',
            r'PANERA': 'Panera Bread',
            r'OLIVE\s*GARDEN': 'Olive Garden',
            r'APPLEBEE\'?S': 'Applebee\'s',
            r'CHILI\'?S': 'Chili\'s',
            r'OUTBACK': 'Outback Steakhouse',
            r'RED\s*LOBSTER': 'Red Lobster',
            r'FIVE\s*GUYS': 'Five Guys',
            r'IN-N-OUT': 'In-N-Out Burger',
            r'SHake\s*SHACK': 'Shake Shack',
            r'ARBY\'?S': 'Arby\'s',
            r'SONIC': 'Sonic',
            r'JACK\s*IN\s*THE\s*BOX': 'Jack in the Box',
            r'WHITE\s*CASTLE': 'White Castle',
            r'CARL\'?S\s*JR': 'Carl\'s Jr.',
            r'HARDEE\'?S': 'Hardee\'s',
            r'WHATABURGER': 'Whataburger',
            r'CULVER\'?S': 'Culver\'s',
            r'POPEYES': 'Popeyes',
            r'CHICK-FIL-A|CHICKFILA': 'Chick-fil-A',
            r'BOJANGLES': 'Bojangles',
            r'ZAXBY\'?S': 'Zaxby\'s',
            r'RAISING\s*CANE\'?S': 'Raising Cane\'s',
            r'LITTLE\s*CAESAR': 'Little Caesars',
            r'PAPA\s*MURPHY': 'Papa Murphy\'s',
            r'CALIFORNIA\s*PIZZA': 'California Pizza Kitchen',
            r'BUFFALO\s*WILD\s*WINGS|BW3': 'Buffalo Wild Wings',
            r'WINGSTOP': 'Wingstop',
            r'QDOBA': 'Qdoba',
            r'MOE\'?S': 'Moe\'s Southwest Grill',
            r'CAVA': 'Cava',
            r'SWEETGREEN': 'Sweetgreen',
            r'JAMBA': 'Jamba Juice',
            r'SMOOTHIE\s*KING': 'Smoothie King',
            r'DAIRY\s*QUEEN|DQ\s+': 'Dairy Queen',
            r'BASKIN\s*ROBBINS': 'Baskin-Robbins',
            r'COLD\s*STONE': 'Cold Stone Creamery',
            r'IHOP': 'IHOP',
            r'DENNY\'?S': 'Denny\'s',
            r'Waffle\s*HOUSE': 'Waffle House',
            r'CRACKER\s*BARREL': 'Cracker Barrel',
            r'RED\s*ROBIN': 'Red Robin',
            r'BOSTON\s*MARKET': 'Boston Market',
            r'WALMART': 'Walmart',
            r'TARGET': 'Target',
            r'COSTCO': 'Costco',
            r'HOME DEPOT': 'Home Depot',
            r'LOWE\'?S': 'Lowe\'s',
            r'BEST BUY': 'Best Buy',
            r'MACY\'?S': 'Macy\'s',
            r'NORDSTROM': 'Nordstrom',
            r'KOHL\'?S': 'Kohl\'s',
            r'JCPENNEY|JC\s*PENNEY': 'JCPenney',
            r'SEARS': 'Sears',
            r'DILLARD\'?S': 'Dillard\'s',
            r'BELK': 'Belk',
            r'DICK\'?S\s*SPORTING': 'Dick\'s Sporting Goods',
            r'ACADEMY': 'Academy Sports',
            r'BASS\s*PRO': 'Bass Pro Shops',
            r'CABELA\'?S': 'Cabela\'s',
            r'REI': 'REI',
            r'PETCO': 'Petco',
            r'PETSMART': 'PetSmart',
            r'BED\s*BATH\s*&\s*BEYOND|BEDBATH': 'Bed Bath & Beyond',
            r'CONTAINER\s*STORE': 'The Container Store',
            r'MICHAELS': 'Michaels',
            r'JOANN': 'Jo-Ann',
            r'HOBBY\s*LOBBY': 'Hobby Lobby',
            r'ULTA': 'Ulta Beauty',
            r'Sephora': 'Sephora',
            r'GAMESTOP': 'GameStop',
            r'BARNES\s*&\s*NOBLE': 'Barnes & Noble',
            r'OFFICE\s*DEPOT': 'Office Depot',
            r'OFFICE\s*MAX': 'OfficeMax',
            r'STAPLES': 'Staples',
            r'AUTOZONE': 'AutoZone',
            r'ADVANCE\s*AUTO': 'Advance Auto Parts',
            r'OREILLY': 'O\'Reilly Auto Parts',
            r'NAPA': 'NAPA Auto Parts',
            r'PEP\s*BOYS': 'Pep Boys',
            r'CARQUEST': 'CARQUEST',
            r'JIFFY\s*LUBE': 'Jiffy Lube',
            r'VALVOLINE': 'Valvoline',
            r'QUICK\s*LUBE|QUICKLUBE': 'Quick Lube',
            r'TAKE\s*5': 'Take 5 Oil Change',
            r'DISCOUNT\s*TIRE': 'Discount Tire',
            r'FIRESTONE': 'Firestone',
            r'GOODYEAR': 'Goodyear',
            r'BRIDGESTONE': 'Bridgestone',
            r'MICHELIN': 'Michelin',
            r'NTB|NATIONAL\s*TIRE': 'NTB',
            r'BIG\s*O\s*TIRE': 'Big O Tires',
            r'LES\s*SCHWAB': 'Les Schwab Tires',
            r'TOWN\s*FAIR\s*TIRE': 'Town Fair Tire',
            r'TIRE\s*KINGDOM': 'Tire Kingdom',
            r'MR\s*TIRE': 'Mr. Tire',
            r'CAR\s*WASH': 'Car Wash',
            r'ZIPPER\s*CAR\s*WASH': 'Zipper Car Wash',
            r'MISTER\s*CAR\s*WASH': 'Mister Car Wash',
            r'TOUCHLESS\s*CAR\s*WASH': 'Touchless Car Wash',
            r'AUTO\s*REPAIR': 'Auto Repair',
            r'MECHANIC': 'Mechanic',
            r'AUTO\s*BODY': 'Auto Body',
            r'BODY\s*SHOP': 'Body Shop',
            r'EMISSIONS\s*TEST': 'Emissions Test',
            r'SMOG\s*CHECK': 'Smog Check',
            r'DMV|DEPARTMENT\s*OF\s*MOTOR': 'DMV',
            r'VEHICLE\s*REGISTRATION': 'Vehicle Registration',
            r'AAA|TRIPLE\s*A': 'AAA',
            r'ROADSIDE\s*ASSISTANCE': 'Roadside Assistance',
            r'TOWING|TOW\s*TRUCK': 'Towing',
            r'DEALER\s*SERVICE|DEALERSHIP': 'Dealership Service',
            r'FORD\s*SERVICE': 'Ford Service',
            r'CHEVROLET\s*SERVICE|CHEVY\s*SERVICE': 'Chevrolet Service',
            r'TOYOTA\s*SERVICE': 'Toyota Service',
            r'HONDA\s*SERVICE': 'Honda Service',
            r'NISSAN\s*SERVICE': 'Nissan Service',
            r'BMW\s*SERVICE': 'BMW Service',
            r'MERCEDES\s*SERVICE|MERCEDES-BENZ': 'Mercedes Service',
            r'AUDI\s*SERVICE': 'Audi Service',
            r'VOLKSWAGEN\s*SERVICE|VW\s*SERVICE': 'Volkswagen Service',
            r'MAZDA\s*SERVICE': 'Mazda Service',
            r'SUBARU\s*SERVICE': 'Subaru Service',
            r'HYUNDAI\s*SERVICE': 'Hyundai Service',
            r'KIA\s*SERVICE': 'Kia Service',
            r'JEEP\s*SERVICE': 'Jeep Service',
            r'DODGE\s*SERVICE': 'Dodge Service',
            r'CHRYSLER\s*SERVICE': 'Chrysler Service',
            r'RAM\s*SERVICE': 'Ram Service',
            r'GMC\s*SERVICE': 'GMC Service',
            r'CADILLAC\s*SERVICE': 'Cadillac Service',
            r'BUICK\s*SERVICE': 'Buick Service',
            r'LINCOLN\s*SERVICE': 'Lincoln Service',
            r'ACURA\s*SERVICE': 'Acura Service',
            r'INFINITI\s*SERVICE': 'Infiniti Service',
            r'LEXUS\s*SERVICE': 'Lexus Service',
            r'VOLVO\s*SERVICE': 'Volvo Service',
            r'JAGUAR\s*SERVICE': 'Jaguar Service',
            r'LAND\s*ROVER\s*SERVICE': 'Land Rover Service',
            r'PORSCHE\s*SERVICE': 'Porsche Service',
            r'MINI\s*SERVICE': 'Mini Service',
            r'WHOLE FOODS': 'Whole Foods',
            r'TRADER JOE': 'Trader Joe\'s',
            r'SAFEWAY': 'Safeway',
            r'KROGER': 'Kroger',
            r'KING\s+SOOPERS?': 'King Soopers',
            r'ALDI': 'Aldi',
            r'PUBLIX': 'Publix',
            r'WEGMANS': 'Wegmans',
            r'FOOD\s*LION': 'Food Lion',
            r'STOP\s*&\s*SHOP': 'Stop & Shop',
            r'GIANT\s*(?:FOOD|EAGLE)?': 'Giant',
            r'SHOPRITE': 'ShopRite',
            r'HEB': 'H-E-B',
            r'RALPHS': 'Ralphs',
            r'VONS': 'Vons',
            r'ALBERTSONS': 'Albertsons',
            r'FRED\s*MEYER': 'Fred Meyer',
            r'QFC': 'QFC',
            r'SMITH\'?S': 'Smith\'s',
            r'FOOD\s*4\s*LESS': 'Food 4 Less',
            r'JEWEL\s*OSCO': 'Jewel-Osco',
            r'ACME': 'Acme',
            r'SHOP\'?N\s*SAVE': 'Shop \'n Save',
            r'HY-VEE': 'Hy-Vee',
            r'MEIJER': 'Meijer',
            r'WINN-DIXIE': 'Winn-Dixie',
            r'BI-LO': 'BI-LO',
            r'HARRIS\s*TEETER': 'Harris Teeter',
            r'INGLES': 'Ingles',
            r'WEIS': 'Weis Markets',
            r'GIANT\s*EAGLE': 'Giant Eagle',
            r'MARKET\s*BASKET': 'Market Basket',
            r'PRICE\s*CHOPPER': 'Price Chopper',
            r'HANNAFORD': 'Hannaford',
            r'SHOPPERS': 'Shoppers',
            r'SAVE-A-LOT': 'Save-A-Lot',
            r'LIDL': 'Lidl',
            r'SPROUTS': 'Sprouts Farmers Market',
            r'FRESH\s*MARKET': 'The Fresh Market',
            r'WHOLE\s*FOODS\s*MARKET': 'Whole Foods Market',
            r'SHELL': 'Shell',
            r'EXXON': 'Exxon',
            r'MOBIL': 'Mobil',
            r'BP\s+': 'BP',
            r'CHEVRON': 'Chevron',
            r'TEXACO': 'Texaco',
            r'ARCO': 'ARCO',
            r'VALERO': 'Valero',
            r'CITGO': 'Citgo',
            r'SUNOCO': 'Sunoco',
            r'PHILLIPS\s*66': 'Phillips 66',
            r'CONOCO': 'Conoco',
            r'MARATHON': 'Marathon',
            r'SPEEDWAY': 'Speedway',
            r'7-ELEVEN|7ELEVEN|SEVEN\s*ELEVEN': '7-Eleven',
            r'CIRCLE\s*K': 'Circle K',
            r'QUIKTRIP|QT\s+': 'QuikTrip',
            r'WAWA': 'Wawa',
            r'SHEETZ': 'Sheetz',
            r'CASEY\'?S': 'Casey\'s',
            r'KUM\s*&\s*GO': 'Kum & Go',
            r'LOVE\'?S': 'Love\'s',
            r'PILOT|FLYING\s*J': 'Pilot/Flying J',
            r'TA\s+TRAVEL': 'TA Travel Centers',
            r'RACETRAC': 'RaceTrac',
            r'MURPHY\s*USA': 'Murphy USA',
            r'COSTCO\s*GAS': 'Costco Gas',
            r'SAM\'?S\s*CLUB\s*GAS': 'Sam\'s Club Gas',
            r'KROGER\s*FUEL': 'Kroger Fuel',
            r'SAFEWAY\s*FUEL': 'Safeway Fuel',
            r'CVS': 'CVS',
            r'WALGREENS': 'Walgreens',
            r'RITE\s*AID': 'Rite Aid',
            r'PLANET\s*FITNESS': 'Planet Fitness',
            r'24\s*HOUR\s*FITNESS|24HR\s*FITNESS': '24 Hour Fitness',
            r'LA\s*FITNESS': 'LA Fitness',
            r'GOLD\'?S\s*GYM': 'Gold\'s Gym',
            r'YMCA|Y\s*M\s*C\s*A': 'YMCA',
            r'ANYTIME\s*FITNESS': 'Anytime Fitness',
            r'ORANGETHEORY': 'OrangeTheory',
            r'CROSSFIT': 'CrossFit',
            r'PURE\s*BARRE': 'Pure Barre',
            r'SOULCYCLE': 'SoulCycle',
            r'OLD\s*NAVY': 'Old Navy',
            r'GAP': 'Gap',
            r'BANANA\s*REPUBLIC': 'Banana Republic',
            r'AMERICAN\s*EAGLE': 'American Eagle',
            r'AEROPOSTALE': 'Aeropostale',
            r'H\s*&\s*M|H\s*AND\s*M': 'H&M',
            r'FOREVER\s*21': 'Forever 21',
            r'ZARA': 'Zara',
            r'ROSS': 'Ross',
            r'MARSHALLS': 'Marshalls',
            r'TJ\s*MAXX': 'TJ Maxx',
            r'BURLINGTON': 'Burlington',
            r'NIKE': 'Nike',
            r'ADIDAS': 'Adidas',
            r'UNDER\s*ARMOUR': 'Under Armour',
            r'LULULEMON': 'Lululemon',
            r'BLUE\s*APRON': 'Blue Apron',
            r'HELLO\s*FRESH': 'HelloFresh',
            r'INSTACART': 'Instacart',
            r'SHIPT': 'Shipt',
            r'MARRIOTT': 'Marriott',
            r'HILTON': 'Hilton',
            r'HOLIDAY\s*INN': 'Holiday Inn',
            r'HYATT': 'Hyatt',
            r'SHERATON': 'Sheraton',
            r'EXPEDIA': 'Expedia',
            r'BOOKING\.COM': 'Booking.com',
            r'AIRBNB': 'Airbnb',
            r'VRBO': 'VRBO',
            r'DOORDASH': 'DoorDash',
            r'GRUBHUB': 'Grubhub',
            r'POSTMATES': 'Postmates',
        }
        
        # Compile patterns for faster matching
        self.compiled_mappings = {}
        for pattern, merchant in self.merchant_mappings.items():
            self.compiled_mappings[pattern] = (re.compile(pattern, re.IGNORECASE), merchant)
        
        # Patterns to remove from descriptions
        self.cleanup_patterns = [
            r'\*[^*]*\*',  # Remove text between asterisks (e.g., *MERCHANT*)
            r'#\d+',  # Remove reference numbers (e.g., #1234)
            r'\d{4,}',  # Remove long number sequences (likely transaction IDs)
            r'[A-Z]{2,}\s*\d+',  # Remove codes like "US1234"
            r'ONLINE',  # Remove "ONLINE" suffix
            r'POS\s*',  # Remove "POS" prefix
            r'DEBIT\s*',  # Remove "DEBIT" prefix
            r'CREDIT\s*',  # Remove "CREDIT" prefix
            r'PURCHASE\s*',  # Remove "PURCHASE" suffix
            r'PAYMENT\s*',  # Remove "PAYMENT" suffix
        ]
        
        self.compiled_cleanup = [re.compile(pattern, re.IGNORECASE) for pattern in self.cleanup_patterns]
    
    def extract(self, description: str) -> Optional[str]:
        """Extract merchant name from transaction description.
        
        Args:
            description: Transaction description text
            
        Returns:
            Clean merchant name if extractable, None otherwise
        """
        if not description:
            return None
        
        # First, check known merchant mappings
        for pattern, (compiled_pattern, merchant_name) in self.compiled_mappings.items():
            if compiled_pattern.search(description):
                return merchant_name
        
        # Try to extract merchant name by cleaning up the description
        cleaned = description.strip()
        
        # Remove common prefixes/suffixes
        for pattern in self.compiled_cleanup:
            cleaned = pattern.sub('', cleaned)
        
        # Extract the first meaningful word/phrase (usually the merchant)
        # Look for words in ALL CAPS (common in bank statements)
        caps_match = re.search(r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\b', cleaned)
        if caps_match:
            merchant = caps_match.group(1).strip()
            # Clean up further
            merchant = re.sub(r'\s+', ' ', merchant)  # Normalize spaces
            if len(merchant) > 2:  # Only return if meaningful
                return merchant.title()  # Convert to Title Case
        
        # If no ALL CAPS found, try to extract first few words
        words = cleaned.split()
        if words:
            # Take first 2-3 words as merchant name
            merchant = ' '.join(words[:3]).strip()
            # Remove common suffixes
            merchant = re.sub(r'\s+(LLC|INC|CORP|LTD|CO)\.?$', '', merchant, flags=re.IGNORECASE)
            if len(merchant) > 2:
                return merchant.title()
        
        return None
    
    def add_merchant_mapping(self, pattern: str, merchant_name: str):
        """Add a custom merchant name mapping.
        
        Args:
            pattern: Regex pattern to match in description
            merchant_name: Name to return when pattern matches
        """
        self.merchant_mappings[pattern] = merchant_name
        self.compiled_mappings[pattern] = (re.compile(pattern, re.IGNORECASE), merchant_name)

