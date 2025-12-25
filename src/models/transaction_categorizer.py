"""
Transaction Categorizer
Automatically categorizes transactions based on description keywords.
"""

import re
from typing import Optional, Dict, List


class TransactionCategorizer:
    """Categorizes transactions based on merchant names and keywords."""
    
    def __init__(self):
        """Initialize the categorizer with category rules."""
        # Category rules: map keywords to categories
        # Keywords are case-insensitive and can be partial matches
        self.category_rules = {
            'Groceries': [
                'walmart', 'target', 'safeway', 'kroger', 'whole foods', 'trader joe',
                'aldi', 'costco', 'sam\'s club', 'publix', 'wegmans', 'food lion',
                'stop & shop', 'giant', 'king soopers', 'king sooper', 'kings', 'shoprite',
                'heb', 'h-e-b', 'ralphs', 'vons', 'albertsons', 'fred meyer', 'qfc',
                'smith\'s', 'food 4 less', 'jewel-osco', 'acme', 'shop n save', 'shop\'n save',
                'hy-vee', 'meijer', 'winn-dixie', 'bi-lo', 'harris teeter', 'ingles',
                'weis', 'giant eagle', 'market basket', 'price chopper', 'hannaford',
                'shoppers', 'save-a-lot', 'lidl', 'sprouts', 'fresh market',
                'food', 'grocery', 'supermarket', 'market', 'grocery store'
            ],
            'Restaurants': [
                'mcdonald', 'burger king', 'bk', 'wendy', 'taco bell', 'kfc', 'subway',
                'starbucks', 'dunkin', 'dunkin donuts', 'pizza hut', 'domino', 'dominos',
                'papa john', 'chipotle', 'panera', 'olive garden', 'applebees', 'chili',
                'outback', 'red lobster', 'five guys', 'in-n-out', 'shake shack',
                'arby', 'sonic', 'jack in the box', 'white castle', 'carl\'s jr',
                'hardee', 'whataburger', 'culver', 'popeyes', 'chick-fil-a', 'chickfila',
                'bojangles', 'zaxby', 'raising cane', 'little caesar', 'papa murphy',
                'california pizza', 'buffalo wild wings', 'bw3', 'wingstop', 'qdoba',
                'moe\'s', 'cava', 'sweetgreen', 'jamba', 'smoothie king', 'dairy queen',
                'dq', 'baskin robbins', 'cold stone', 'ihop', 'denny', 'waffle house',
                'cracker barrel', 'red robin', 'boston market', 'restaurant', 'cafe',
                'coffee', 'diner', 'bistro', 'grill', 'bar & grill', 'food truck',
                'uber eats', 'doordash', 'grubhub', 'postmates', 'delivery', 'fast food',
                'takeout', 'take out'
            ],
            'Gas': [
                'shell', 'exxon', 'mobil', 'bp', 'chevron', 'texaco',
                'arco', 'valero', 'citgo', 'sunoco', 'phillips 66',
                'conoco', 'marathon', 'speedway', '7-eleven', '7eleven',
                'circle k', 'quiktrip', 'qt', 'wawa', 'sheetz', 'casey\'s',
                'caseys', 'kum & go', 'kum and go', 'love\'s', 'loves',
                'pilot', 'flying j', 'ta travel', 'racetrac', 'murphy usa',
                'costco gas', 'sam\'s club gas', 'sams club gas',
                'kroger fuel', 'safeway fuel', 'gas station', 'fuel',
                'gas', 'petrol', 'filling station', 'service station'
            ],
            'Utilities': [
                'electric', 'power', 'gas company', 'water', 'sewer',
                'trash', 'waste', 'utility', 'duke energy', 'pg&e',
                'southern california edison', 'con edison', 'comcast',
                'xfinity', 'verizon', 'at&t', 't-mobile', 'sprint',
                'internet', 'cable', 'phone bill', 'cell phone'
            ],
            'Subscriptions': [
                'netflix', 'spotify', 'amazon prime', 'hulu', 'disney',
                'apple music', 'youtube premium', 'hbo', 'max', 'paramount',
                'peacock', 'audible', 'adobe', 'microsoft 365', 'office 365',
                'dropbox', 'icloud', 'google drive', 'subscription',
                'monthly', 'annual', 'recurring'
            ],
            'Shopping': [
                'amazon', 'ebay', 'etsy', 'walmart.com', 'target.com',
                'best buy', 'home depot', 'lowes', 'macy', 'nordstrom',
                'kohl', 'jcpenney', 'sears', 'dillard', 'belk', 'online purchase',
                'shop', 'retail', 'store purchase', 'gamestop', 'barnes & noble'
            ],
            'Pets': [
                'petco', 'petsmart', 'pet store', 'pet supply', 'veterinary',
                'vet', 'pet care', 'animal hospital'
            ],
            'Auto Parts': [
                'autozone', 'advance auto', 'oreilly', 'napa', 'auto parts',
                'car parts', 'automotive', 'pep boys', 'carquest'
            ],
            'Vehicle Maintenance': [
                'jiffy lube', 'valvoline', 'quick lube', 'oil change', 'lube',
                'discount tire', 'firestone', 'goodyear', 'bridgestone', 'michelin',
                'ntb', 'national tire', 'big o tire', 'les schwab', 'town fair tire',
                'tire kingdom', 'mr tire', 'tire', 'tires', 'tire shop',
                'car wash', 'carwash', 'auto wash', 'mister car wash', 'zipper car wash',
                'auto repair', 'mechanic', 'auto service', 'car service', 'vehicle service',
                'auto body', 'body shop', 'collision', 'auto body shop',
                'emissions test', 'smog check', 'emissions', 'smog',
                'dmv', 'department of motor vehicles', 'vehicle registration',
                'registration', 'license plate', 'tags',
                'aaa', 'triple a', 'roadside assistance', 'towing', 'tow',
                'brake', 'brakes', 'transmission', 'engine', 'battery', 'alternator',
                'oil change', 'tune up', 'inspection', 'state inspection',
                'dealer service', 'dealership', 'ford service', 'chevrolet service',
                'chevy service', 'toyota service', 'honda service', 'nissan service',
                'bmw service', 'mercedes service', 'audi service', 'volkswagen service',
                'vw service', 'mazda service', 'subaru service', 'hyundai service',
                'kia service', 'jeep service', 'dodge service', 'chrysler service',
                'ram service', 'gmc service', 'cadillac service', 'buick service',
                'lincoln service', 'acura service', 'infiniti service', 'lexus service',
                'volvo service', 'jaguar service', 'land rover service', 'porsche service',
                'mini service', 'car maintenance', 'vehicle maintenance', 'auto maintenance'
            ],
            'Office Supplies': [
                'office depot', 'officemax', 'staples', 'office supply',
                'stationery', 'office store'
            ],
            'Sports & Outdoors': [
                'dick\'s sporting', 'academy sports', 'bass pro', 'cabela',
                'rei', 'sporting goods', 'outdoor', 'camping', 'hunting'
            ],
            'Books & Media': [
                'barnes & noble', 'books', 'bookstore', 'library'
            ],
            'Crafts & Hobbies': [
                'michaels', 'jo-ann', 'hobby lobby', 'craft store', 'fabric',
                'art supply', 'hobby'
            ],
            'Beauty & Personal Care': [
                'ulta', 'sephora', 'beauty supply', 'cosmetic', 'makeup',
                'hair salon', 'nail salon', 'spa'
            ],
            'Entertainment': [
                'movie', 'cinema', 'theater', 'concert', 'ticketmaster',
                'stubhub', 'eventbrite', 'amc', 'regal', 'cinemark',
                'netflix', 'hulu', 'disney', 'streaming', 'game',
                'video game', 'steam', 'playstation', 'xbox', 'nintendo'
            ],
            'Transportation': [
                'uber', 'lyft', 'taxi', 'metro', 'subway', 'bus',
                'train', 'airline', 'delta', 'united', 'american',
                'southwest', 'jetblue', 'parking', 'toll', 'ez pass',
                'car rental', 'hertz', 'avis', 'enterprise'
            ],
            'Healthcare': [
                'pharmacy', 'cvs', 'walgreens', 'rite aid', 'doctor',
                'hospital', 'medical', 'dental', 'vision', 'insurance',
                'prescription', 'clinic', 'urgent care', 'lab', 'test'
            ],
            'Education': [
                'tuition', 'school', 'university', 'college', 'course',
                'textbook', 'student', 'education', 'learning', 'class'
            ],
            'Insurance': [
                'insurance', 'geico', 'state farm', 'allstate', 'progressive',
                'farmers', 'liberty mutual', 'auto insurance', 'home insurance',
                'life insurance', 'health insurance'
            ],
            'Banking': [
                'atm', 'withdrawal', 'deposit', 'transfer', 'fee',
                'overdraft', 'interest', 'bank', 'credit union'
            ],
            'Charity': [
                'donation', 'charity', 'nonprofit', 'red cross', 'unicef',
                'salvation army', 'goodwill', 'contribution', 'give'
            ],
            'Business': [
                'business', 'office', 'supplies', 'equipment', 'software',
                'saas', 'service', 'professional', 'consulting', 'freelance'
            ],
            'Home & Garden': [
                'home depot', 'lowes', 'homedepot', 'hardware', 'garden',
                'furniture', 'ikea', 'wayfair', 'bed bath', 'home goods'
            ],
            'Personal Care': [
                'haircut', 'salon', 'spa', 'gym', 'fitness', 'yoga',
                'personal care', 'beauty', 'cosmetic', 'pharmacy'
            ],
            'Fitness & Gym': [
                'planet fitness', '24 hour fitness', '24hr fitness', 'la fitness',
                'gold\'s gym', 'golds gym', 'ymca', 'anytime fitness', 'orangetheory',
                'crossfit', 'pure barre', 'soulcycle', 'gym', 'fitness', 'workout',
                'personal trainer', 'yoga studio', 'pilates', 'spin class'
            ],
            'Clothing & Apparel': [
                'old navy', 'gap', 'banana republic', 'american eagle', 'aeropostale',
                'h&m', 'h and m', 'forever 21', 'zara', 'ross', 'marshalls',
                'tj maxx', 'burlington', 'nike', 'adidas', 'under armour', 'lululemon',
                'clothing', 'apparel', 'clothes', 'fashion', 'boutique', 'outlet'
            ],
            'Meal Kits & Delivery': [
                'blue apron', 'hellofresh', 'hello fresh', 'instacart', 'shipt',
                'meal kit', 'food delivery', 'grocery delivery'
            ],
            'Travel & Hotels': [
                'marriott', 'hilton', 'holiday inn', 'hyatt', 'sheraton', 'expedia',
                'booking.com', 'airbnb', 'vrbo', 'hotel', 'motel', 'resort', 'lodging',
                'travel', 'vacation', 'trip'
            ],
            'Home Services': [
                'plumber', 'electrician', 'hvac', 'heating', 'cooling', 'ac repair',
                'appliance repair', 'handyman', 'landscaping', 'lawn care', 'pest control',
                'home repair', 'contractor', 'roofing', 'siding', 'painting', 'flooring'
            ]
        }
        
        # Compile regex patterns for faster matching
        self.compiled_patterns = {}
        for category, keywords in self.category_rules.items():
            # Create a regex pattern that matches any of the keywords
            pattern = '|'.join(re.escape(keyword) for keyword in keywords)
            self.compiled_patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def categorize(self, description: str) -> Optional[str]:
        """Categorize a transaction based on its description.
        
        Args:
            description: Transaction description text
            
        Returns:
            Category name if matched, None otherwise
        """
        if not description:
            return None
        
        description_lower = description.lower()
        
        # Check each category in order (first match wins)
        for category, pattern in self.compiled_patterns.items():
            if pattern.search(description_lower):
                return category
        
        return None
    
    def get_all_categories(self) -> List[str]:
        """Get list of all available categories.
        
        Returns:
            List of category names
        """
        return list(self.category_rules.keys())
    
    def add_category_rule(self, category: str, keywords: List[str]):
        """Add or update a category rule.
        
        Args:
            category: Category name
            keywords: List of keywords to match for this category
        """
        self.category_rules[category] = keywords
        pattern = '|'.join(re.escape(keyword) for keyword in keywords)
        self.compiled_patterns[category] = re.compile(pattern, re.IGNORECASE)

