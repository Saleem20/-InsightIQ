import random
from datetime import datetime, timedelta
from typing import List, Dict


def _spread_dates(n: int, days_back: int = 180) -> List[datetime]:
    now = datetime.now()
    return sorted(
        now - timedelta(days=random.randint(0, days_back), hours=random.randint(0, 23))
        for _ in range(n)
    )


_RAW: Dict[str, List[Dict]] = {
    "oral care": [
        {"text": "Switched to neem-based toothpaste 3 months ago and my gums have never felt healthier. No more bleeding when I floss!", "source": "Reddit", "engagement": 312},
        {"text": "Herbal toothpaste is a game changer. Fresh breath all day without the harsh chemical taste. Completely natural and it actually works.", "source": "Twitter", "engagement": 189},
        {"text": "Tried three different herbal toothpastes. The whitening claims are completely overblown — zero difference after 6 weeks.", "source": "Reviews", "engagement": 234},
        {"text": "Finally found a fluoride-free toothpaste that doesn't feel like brushing with chalk. The charcoal + neem combo is brilliant.", "source": "Reddit", "engagement": 145},
        {"text": "My dentist actually warned me against herbal-only toothpaste. Said fluoride is essential for cavity prevention. Conflicted now.", "source": "Reddit", "engagement": 567},
        {"text": "Love the natural ingredients but the gritty texture takes getting used to. My kids refuse to use it though.", "source": "Reviews", "engagement": 78},
        {"text": "Ayurvedic toothpaste has been used for centuries. Why do we trust synthetic chemicals more than proven traditional remedies?", "source": "Blogs", "engagement": 203},
        {"text": "Switched the whole family to herbal toothpaste. Works great for adults but finding kid-friendly herbal options is genuinely hard.", "source": "Twitter", "engagement": 94},
        {"text": "The price difference is insane. Herbal toothpastes cost 3x more for the same volume. Companies exploiting the 'natural' trend.", "source": "Reddit", "engagement": 445},
        {"text": "After reading about microplastics in conventional toothpaste I made the switch. No regrets. Teeth feel just as clean.", "source": "YouTube", "engagement": 2341},
        {"text": "Neem toothpaste has a strong bitter taste that I actually love now. Feels medicinal in a good way.", "source": "Reviews", "engagement": 67},
        {"text": "My herbal toothpaste left white residue on my electric toothbrush. Minor annoyance but the clean feeling is worth it.", "source": "Reviews", "engagement": 32},
        {"text": "Why isn't herbal toothpaste more mainstream? Every ingredient in my old toothpaste was a chemical I couldn't pronounce.", "source": "Twitter", "engagement": 512},
        {"text": "As a periodontist I see patients switching to herbal toothpaste. Some are fine, but please don't skip fluoride if you're cavity-prone.", "source": "Blogs", "engagement": 1203},
        {"text": "The packaging on herbal toothpastes is so much better. Sustainable, recyclable, just thoughtfully designed.", "source": "Twitter", "engagement": 88},
        {"text": "Herbal toothpaste completely fixed my sensitive gums issue. Dentist was surprised at my last checkup.", "source": "Reviews", "engagement": 156},
        {"text": "Tried the trending oil pulling alongside herbal toothpaste. My whole oral care routine feels intentional and natural now.", "source": "Instagram", "engagement": 891},
        {"text": "Disappointed — the natural toothpaste dried out fast and the pump dispenser clogged within a month.", "source": "Reviews", "engagement": 234},
        {"text": "Gen Z is driving the herbal oral care market. We want transparency in ingredients and don't trust legacy brands anymore.", "source": "Blogs", "engagement": 678},
        {"text": "Mixed feelings. Herbal toothpaste feels gentler but I had two cavities this year after years with none. Coincidence? Maybe not.", "source": "Reddit", "engagement": 789},
        {"text": "The lack of clinical evidence for most herbal toothpaste brands is concerning. Marketing is ahead of the science.", "source": "Twitter", "engagement": 345},
        {"text": "My teen daughter only uses herbal toothpaste now. She researched ingredients herself. Proud parent moment honestly.", "source": "Reddit", "engagement": 123},
        {"text": "Herbal mouthwash + herbal toothpaste combo transformed my morning routine. Feel so much better about what goes in my mouth.", "source": "YouTube", "engagement": 1456},
        {"text": "Some herbal brands are just greenwashing. Check the labels — many still have SLS and artificial flavors buried in there.", "source": "Reddit", "engagement": 892},
        {"text": "Started using clove oil toothpaste for toothache. The numbing effect is real and the taste is intense but effective.", "source": "Reviews", "engagement": 203},
        {"text": "Oral care is such a personal thing. I respect herbal choices but after a root canal I'm sticking to fluoride.", "source": "Twitter", "engagement": 267},
        {"text": "Just launched our herbal toothpaste review series. Tested 12 brands — results are surprising. Link in bio.", "source": "Instagram", "engagement": 3421},
        {"text": "The whitening ingredients in herbal toothpastes like baking soda and charcoal can be abrasive long-term. Use sparingly.", "source": "Blogs", "engagement": 567},
    ],
    "skincare": [
        {"text": "My dermatologist recommended hyaluronic acid serum over heavy moisturizers for my combination skin. Life changing honestly.", "source": "Reddit", "engagement": 423},
        {"text": "Retinol ruined my skin barrier for 6 months. Now I use bakuchiol — same results, none of the irritation. Natural alternatives work.", "source": "Twitter", "engagement": 567},
        {"text": "SPF 50 every day even indoors. People think I'm obsessed but my skin at 35 looks better than it did at 25.", "source": "Instagram", "engagement": 2341},
        {"text": "The skincare industry pushes so many unnecessary products. You really just need a cleanser, moisturizer, and SPF.", "source": "Reddit", "engagement": 1234},
        {"text": "Niacinamide cleared my hyperpigmentation in 8 weeks. Cheap, effective, backed by science. Why did it take me so long to try this.", "source": "YouTube", "engagement": 4512},
        {"text": "Natural skincare brands are amazing until they start going rancid in the bottle. Preservatives exist for a reason.", "source": "Reddit", "engagement": 789},
        {"text": "Finally found a moisturizer that doesn't pill under makeup. Game changer for my morning routine.", "source": "Reviews", "engagement": 234},
        {"text": "Ceramide-based products have completely fixed my damaged skin barrier. Wish I'd known about this years ago.", "source": "Blogs", "engagement": 456},
        {"text": "The 10-step Korean skincare routine is not sustainable for most people. Simplified to 4 steps and my skin is better than ever.", "source": "Twitter", "engagement": 892},
        {"text": "Vitamin C serums are trending but most people don't know they degrade rapidly. Keep them refrigerated or they're useless.", "source": "Blogs", "engagement": 1203},
        {"text": "Been using sunflower oil as a moisturizer for 6 months. My skin loves it and it costs nothing. Don't believe the hype.", "source": "Reddit", "engagement": 567},
        {"text": "Peptides are the most underrated skincare ingredient. Better collagen support than most luxury creams I've tried.", "source": "YouTube", "engagement": 3241},
        {"text": "Sensitive skin people — please patch test EVERYTHING. I had a severe reaction to a 'clean beauty' product with essential oils.", "source": "Twitter", "engagement": 2134},
        {"text": "The clean beauty movement has good intentions but 'natural' doesn't mean safe. Poison ivy is natural too.", "source": "Reddit", "engagement": 1567},
        {"text": "Found my holy grail moisturizer after years of searching. Works for dry skin, non-comedogenic, fragrance-free. Will not name brands.", "source": "Reddit", "engagement": 892},
        {"text": "Azelaic acid is doing what retinol couldn't for my rosacea-prone skin. Gentle, brightening, and anti-inflammatory.", "source": "Reviews", "engagement": 345},
        {"text": "Skincare influencers pushing $200 serums when drugstore equivalents exist with identical ingredients is criminal.", "source": "Twitter", "engagement": 3421},
        {"text": "After switching to a gentle fragrance-free routine my skin stopped being oily. Counter-intuitive but stripping skin makes it produce more oil.", "source": "Blogs", "engagement": 2341},
        {"text": "Mushroom extracts in skincare is the next big thing. Beta-glucan is deeply moisturizing and chaga has incredible antioxidant properties.", "source": "Instagram", "engagement": 1234},
        {"text": "My 60 year old mom started using a basic peptide cream and people ask if she's had work done. Consistency beats expensive treatments.", "source": "Reddit", "engagement": 4512},
        {"text": "Disappointed with the 'luxury' moisturizer I splurged on. Same ingredients as my $8 drugstore option just nicer packaging.", "source": "Reviews", "engagement": 567},
        {"text": "Barrier repair is all anyone talks about in skincare right now. And honestly for good reason — most of us have damaged ours.", "source": "Blogs", "engagement": 789},
        {"text": "Men's skincare market is finally growing up. Basic SPF and moisturizer is now mainstream. Took long enough.", "source": "Twitter", "engagement": 423},
        {"text": "Probiotic skincare sounds like pseudoscience but there's emerging research on the skin microbiome that's actually compelling.", "source": "Reddit", "engagement": 1023},
        {"text": "The amount of microplastics in face scrubs is horrifying. Switched to enzyme exfoliants and never going back.", "source": "YouTube", "engagement": 2134},
        {"text": "Ingredient layering order matters so much. Applying vitamin C and niacinamide together can cancel both out.", "source": "Blogs", "engagement": 3421},
        {"text": "Snail mucin is weird but I don't care — my skin has never been more hydrated. Korean beauty wins again.", "source": "Instagram", "engagement": 5612},
        {"text": "Can we talk about how sunscreen is still not normalized for men? SPF is literally the most evidence-backed anti-aging tool.", "source": "Twitter", "engagement": 1892},
    ],
    "beverages": [
        {"text": "Zero sugar energy drinks are everywhere now but the artificial sweetener aftertaste is still awful. Need better alternatives.", "source": "Reddit", "engagement": 423},
        {"text": "Switched from regular soda to sparkling water 6 months ago. Cravings for sweet drinks completely gone. Didn't expect this.", "source": "Twitter", "engagement": 892},
        {"text": "The stevia aftertaste in most sugar-free drinks is a dealbreaker for me. Monk fruit sweetened options are so much better.", "source": "Reviews", "engagement": 234},
        {"text": "Kombucha is the only functional beverage that actually delivers on its promise. 2 years of daily drinking and gut health is noticeably improved.", "source": "Reddit", "engagement": 1203},
        {"text": "Sugar-free doesn't mean healthy. Artificial sweeteners still spike insulin and mess with gut bacteria according to recent research.", "source": "Blogs", "engagement": 2341},
        {"text": "Electrolyte drinks without sugar are a godsend for endurance athletes. LMNT changed my performance metrics dramatically.", "source": "YouTube", "engagement": 3412},
        {"text": "Why do all protein shakes taste like plastic? The texture is always wrong too. Huge gap in the market for a genuinely good tasting one.", "source": "Reddit", "engagement": 567},
        {"text": "My doctor told me to cut sugar so I explored sugar-free options. Honestly most of them taste better now — I was just biased before.", "source": "Twitter", "engagement": 345},
        {"text": "Energy drink brands targeting teens with 200mg caffeine and zero nutritional value is genuinely irresponsible.", "source": "Blogs", "engagement": 1892},
        {"text": "The functional beverage market is booming — adaptogens, nootropics, collagen. People are drinking their supplements now.", "source": "Instagram", "engagement": 4231},
        {"text": "Tried 8 different sugar-free protein shakes. Only 2 were actually drinkable. The rest tasted like sweetened chalk.", "source": "YouTube", "engagement": 2341},
        {"text": "Infused water is genuinely underrated. Cucumber mint water completely replaced my need for sweet drinks.", "source": "Reddit", "engagement": 567},
        {"text": "The 'health halo' around sports drinks is marketing nonsense. Unless you're exercising 90+ minutes you don't need electrolytes.", "source": "Twitter", "engagement": 1234},
        {"text": "Mushroom coffee is trending and I'm here for it. Half the caffeine, adaptogens included, better sustained energy without the crash.", "source": "Instagram", "engagement": 3421},
        {"text": "Probiotic sodas are the most exciting thing in beverages right now. Gut health benefits + carbonation + no sugar? Where has this been.", "source": "Reddit", "engagement": 892},
        {"text": "My kids refuse sugar-free anything. The sweetener taste is too strong for children's palates apparently. Struggle is real.", "source": "Twitter", "engagement": 234},
        {"text": "Cold brew coffee without sugar is genuinely one of life's great pleasures. Smooth, no bitterness, high caffeine. Perfect.", "source": "YouTube", "engagement": 5612},
        {"text": "The 'zero sugar' label on drinks is misleading when there's still 25g of carbs from other sources. Regulation is needed.", "source": "Blogs", "engagement": 1023},
        {"text": "Hydration is the most underrated health hack. Since tracking my water intake everything improved — sleep, skin, energy, focus.", "source": "Instagram", "engagement": 7823},
        {"text": "Plant-based protein drinks are finally catching up in taste. Pea protein has come a long way from 3 years ago.", "source": "Reviews", "engagement": 456},
        {"text": "The price gap between sugar beverages and healthy alternatives needs to close. Health shouldn't be a luxury.", "source": "Twitter", "engagement": 1567},
        {"text": "Matcha latte with oat milk, no sugar. This is the drink that replaced my daily cappuccino and I feel so much better.", "source": "Reddit", "engagement": 2134},
        {"text": "Collagen drinks are everywhere. The bioavailability questions are real though — does oral collagen actually reach your skin?", "source": "Blogs", "engagement": 892},
        {"text": "Wellness beverages are genuinely helping people make healthier choices. Don't dismiss the trend — it's moving the needle.", "source": "Instagram", "engagement": 3241},
        {"text": "Sparkling water with natural fruit essence satisfies my carbonation craving without any sweeteners. Simple solution.", "source": "Reviews", "engagement": 178},
        {"text": "The sugar tax worked. Beverage companies reformulated products and consumer health outcomes improved. Policy matters.", "source": "Blogs", "engagement": 2341},
    ],
    "wellness": [
        {"text": "Ashwagandha genuinely helped my cortisol levels. Blood test confirmed it. Adaptogens aren't pseudoscience after all.", "source": "Reddit", "engagement": 1234},
        {"text": "The supplement industry is largely unregulated. Half of what's on shelves doesn't contain what the label says. Terrifying.", "source": "Blogs", "engagement": 2341},
        {"text": "Magnesium glycinate for sleep is the most underrated supplement. Cheap, effective, no dependency. Why isn't this mainstream.", "source": "Twitter", "engagement": 3421},
        {"text": "Started taking vitamin D + K2 combo. My SAD symptoms improved significantly over the winter. Will track this properly next year.", "source": "Reddit", "engagement": 892},
        {"text": "Probiotics changed my digestion completely. Took 8 weeks to see results but the change is undeniable. Consistency is key.", "source": "Reviews", "engagement": 567},
        {"text": "Collagen supplements are the biggest wellness grift. The molecule is too large to absorb intact. You're buying expensive glycine.", "source": "Blogs", "engagement": 1892},
        {"text": "Omega-3 from whole fish vs supplement form — bioavailability difference is significant according to my nutrition research.", "source": "Reddit", "engagement": 456},
        {"text": "Lion's mane mushroom has measurably improved my focus and recall. I was skeptical but the research is actually solid.", "source": "YouTube", "engagement": 4512},
        {"text": "My doctor told me I was wasting money on a 12-supplement stack. Bloodwork showed I only needed D3 and B12. Get tested first.", "source": "Twitter", "engagement": 2134},
        {"text": "The wellness industry targets anxiety. They profit from making healthy people feel like they need to optimize everything.", "source": "Reddit", "engagement": 3421},
        {"text": "Creatine is the most scientifically validated supplement and it costs almost nothing. Why do people still avoid it?", "source": "YouTube", "engagement": 6234},
        {"text": "Turmeric with black pepper for inflammation. Stopped taking ibuprofen daily after adding this to my routine. Anecdotal but meaningful.", "source": "Reviews", "engagement": 345},
        {"text": "Third-party tested supplements are the only ones worth buying. NSF and Informed Sport certifications matter enormously.", "source": "Blogs", "engagement": 1023},
        {"text": "Berberine is being called 'nature's metformin' for blood sugar management. Clinical evidence is surprisingly strong.", "source": "Reddit", "engagement": 2341},
        {"text": "The sleep supplement market is exploding — melatonin, magnesium, L-theanine, glycine. People are prioritizing sleep finally.", "source": "Instagram", "engagement": 4231},
        {"text": "Protein intake is the most impactful nutrition lever most people ignore. Getting adequate protein should precede any supplementation.", "source": "YouTube", "engagement": 5612},
        {"text": "Wellness supplements are increasingly marketed to men. The stigma around men caring for their health is finally dissolving.", "source": "Twitter", "engagement": 892},
        {"text": "NAD+ precursors for longevity is the newest trend. NMN vs NR debate is fascinating but evidence is still preliminary.", "source": "Blogs", "engagement": 1567},
        {"text": "Kids' gummy vitamins have more sugar than candy. The wellness industry infantilizing adult supplements is a problem too.", "source": "Reddit", "engagement": 2134},
        {"text": "Spent $300 a month on supplements. Stopped everything for 6 months. Felt the same. Now I take 3 evidence-based ones only.", "source": "Reddit", "engagement": 4512},
        {"text": "Personalized nutrition based on microbiome testing is the future. Generic supplement advice is too blunt an instrument.", "source": "Instagram", "engagement": 3241},
        {"text": "Electrolyte supplements during Ramadan have been life-changing for fasting endurance. Practical wellness solution.", "source": "Twitter", "engagement": 678},
        {"text": "The placebo effect in wellness is underestimated. But if it works and it's harmless, does the mechanism actually matter?", "source": "Reddit", "engagement": 1892},
        {"text": "Hormone health supplements for women are booming. Perimenopause support is finally getting mainstream attention.", "source": "Instagram", "engagement": 5612},
        {"text": "B12 deficiency is wildly common in vegans and is causing real neurological issues. Supplement non-negotiably if plant-based.", "source": "Blogs", "engagement": 2341},
        {"text": "Gut-brain axis research is the most exciting thing in health science. Prebiotics and probiotics may be mental health tools.", "source": "YouTube", "engagement": 7823},
    ],
    "haircare": [
        {"text": "Sulphate-free shampoo took 6 weeks to adjust to. First month hair felt weird. Now it's the only thing I'll use.", "source": "Reddit", "engagement": 567},
        {"text": "Hair loss at 28 sent me down a rabbit hole. Minoxidil works but the finasteride decision is complicated and personal.", "source": "Reddit", "engagement": 1234},
        {"text": "Castor oil for hair growth is mostly myth. The few studies that exist are tiny and low quality. Save your money.", "source": "Blogs", "engagement": 892},
        {"text": "Scalp health is the root cause of most hair issues. Nobody talks about this enough. Focus on scalp, hair follows.", "source": "YouTube", "engagement": 3421},
        {"text": "Rice water rinse for hair strength — been doing this for 3 months. My stylist noticed a real difference in hair texture.", "source": "Instagram", "engagement": 2341},
        {"text": "Hair porosity matters more than any ingredient. Understanding your hair's porosity unlocks what products will actually work.", "source": "Twitter", "engagement": 1567},
        {"text": "Protein overload is real. Too many protein treatments made my hair brittle and caused breakage. Balance is everything.", "source": "Reviews", "engagement": 456},
        {"text": "Natural hair community has the best advice on moisture retention. Techniques developed for curly hair work for everyone.", "source": "Reddit", "engagement": 892},
        {"text": "Biotin supplements did nothing for my hair. Iron deficiency was the actual culprit. Get bloodwork before buying supplements.", "source": "Twitter", "engagement": 2134},
        {"text": "The 'no-poo' method genuinely doesn't work for everyone. If you have an oily scalp you need actual cleansing.", "source": "Blogs", "engagement": 1023},
        {"text": "Found a shampoo bar that replaced my plastic bottle routine. Zero waste, works amazingly, and my hair is healthier.", "source": "Instagram", "engagement": 4512},
        {"text": "Keratin treatment gave me silky hair for 4 months. But the formaldehyde risk is real and the cost every 4 months adds up.", "source": "YouTube", "engagement": 2341},
        {"text": "DHT blocking shampoos are trending for hair loss. Clinical evidence is modest but anecdotally many people swear by them.", "source": "Reddit", "engagement": 1892},
        {"text": "My hairstylist said heat protectant is non-negotiable. I ignored her for years. I now have heat damage I'm growing out.", "source": "Twitter", "engagement": 892},
        {"text": "Olaplex actually works. Chemist Warehouse comparison vs. the expensive salon version showed identical active ingredients.", "source": "Blogs", "engagement": 3421},
        {"text": "Postpartum hair loss is devastating and nobody warns you. Support communities online made me feel less alone.", "source": "Reddit", "engagement": 5612},
        {"text": "Traditional hair oiling practices from India are getting mainstream recognition. Grandmothers were right all along.", "source": "Instagram", "engagement": 4231},
        {"text": "My 4C hair finally thriving after finding the right routine. It took years and hundreds of dollars of trial and error.", "source": "YouTube", "engagement": 6234},
        {"text": "Scalp massage for 4 minutes daily — been consistent for 6 months and baby hairs are visibly growing. Circulation matters.", "source": "Twitter", "engagement": 1567},
        {"text": "Affordable drugstore shampoos often outperform expensive salon brands. Check the active ingredients, not the packaging.", "source": "Blogs", "engagement": 2134},
        {"text": "Dry shampoo dependency is damaging scalps. Products that mask grease are not the same as washing your hair.", "source": "Reddit", "engagement": 1892},
        {"text": "The gendered pricing of hair products is infuriating. Men's and women's versions of identical formulas at wildly different prices.", "source": "Twitter", "engagement": 3421},
        {"text": "Rosemary oil for hair growth has actual research behind it. Comparable to minoxidil in one study. I'm convinced.", "source": "Instagram", "engagement": 7823},
        {"text": "Detangling natural hair correctly has saved me so much breakage. Finger detangle before any tool, always on wet conditioned hair.", "source": "YouTube", "engagement": 4512},
    ],
}

_CATEGORY_MAP = {
    "oral care": "oral care",
    "toothpaste": "oral care",
    "fluoride": "oral care",
    "neem": "oral care",
    "dental": "oral care",
    "skincare": "skincare",
    "moisturizer": "skincare",
    "serum": "skincare",
    "sunscreen": "skincare",
    "retinol": "skincare",
    "beverage": "beverages",
    "drink": "beverages",
    "sugar": "beverages",
    "kombucha": "beverages",
    "energy drink": "beverages",
    "wellness": "wellness",
    "supplement": "wellness",
    "vitamin": "wellness",
    "probiotic": "wellness",
    "adaptogen": "wellness",
    "haircare": "haircare",
    "hair": "haircare",
    "shampoo": "haircare",
    "scalp": "haircare",
    "conditioner": "haircare",
}


def get_conversations(classification: dict) -> List[Dict]:
    topic = classification.get("topic", "").lower()
    category = classification.get("category", "").lower()
    keywords = [k.lower() for k in classification.get("keywords", [])]

    all_text = " ".join([topic, category] + keywords)
    matched_key = None

    for map_key, data_key in _CATEGORY_MAP.items():
        if map_key in all_text:
            matched_key = data_key
            break

    if not matched_key:
        matched_key = "oral care"

    raw = _RAW[matched_key]
    dates = _spread_dates(len(raw))

    conversations = []
    for i, item in enumerate(raw):
        conversations.append({
            "text": item["text"],
            "source": item["source"],
            "engagement": item["engagement"],
            "timestamp": dates[i],
        })

    return conversations
