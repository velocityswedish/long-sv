"""
YouTube Long-Form Video Automation - Bilingual English/Swedish Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5  # Target 5-minute videos (60 phrases)
TARGET_PHRASES = 60  # Number of phrases to generate

# English category names (for American/European learners)
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Swedish translations for display
CATEGORIES_SWEDISH = {
    "Motivation": "Motivation",
    "Love": "Kärlek",
    "Success": "Framgång",
    "Wisdom": "Visdom",
    "Happiness": "Lycka",
    "Self Improvement": "Självförbättring",
    "Gratitude": "Tacksamhet",
    "Friendship": "Vänskap",
    "Hope": "Hopp",
    "Creativity": "Kreativitet",
    "Inner Peace": "Inre Fred",
    "Confidence": "Självsäkerhet",
    "Perseverance": "Uthållighet",
    "Inspiration": "Inspiration",
    "Positive Life": "Positivt Liv",
    "Courage": "Mod",
    "Kindness": "Vänlighet",
    "Patience": "Tålamod",
    "Forgiveness": "Förlåtelse",
    "Strength": "Styrka",
    "Joy": "Glädje",
    "Balance": "Balans",
    "Growth": "Tillväxt",
    "Purpose": "Syfte",
    "Mindfulness": "Mindfulness",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
SWEDISH_VOICE = "sv-SE-SofieNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated (exact match)"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    """Check if a phrase is too similar to previously used phrases"""
    new_words = set(new_phrase.lower().split())

    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False

    for used in used_phrases:
        used_words = set(used.lower().split())

        if len(new_words) == 0 or len(used_words) == 0:
            continue

        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0

        if similarity >= similarity_threshold:
            return True

    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    """Filter out phrases that are too similar to previously used ones"""
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []

    for phrase in phrases:
        english_text = phrase.get("english", "")

        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] ⚠️ Skipping similar: {english_text[:50]}...")

    return unique_phrases


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "swedish": phrase["swedish"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    """
    Calculate how many phrases needed for target video duration.
    Average phrase takes ~5 seconds (English ~2s + pause 0.5s + Swedish ~2.5s)
    For 10 minutes (600 seconds): 600 / 5 = ~120 phrases
    """
    avg_phrase_duration = 5.0  # seconds
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def repair_and_parse_json(content: str):
    """Robustly parse JSON from LLM output with truncation repair and regex recovery."""
    import re
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    if start != -1:
        sub = cleaned[start:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            try:
                return json.loads(sub[:last_brace+1] + "]")
            except Exception:
                pass

    matches = re.findall(r'\{[^{}]*\"english\"[^{}]*\}', cleaned)
    results = []
    for m in matches:
        try:
            obj = json.loads(m)
            if isinstance(obj, dict) and "english" in obj:
                results.append(obj)
        except Exception:
            continue
    if results:
        return results

    raise ValueError("Could not parse or repair JSON from content")


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    """Generate unique bilingual phrases for long-form video"""

    category_swedish = CATEGORIES_SWEDISH[category_english]

    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]

    viral_style = random.choice(VIRAL_STYLES)

    # Generate in batches to avoid API limits and ensure quality
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)

        if current_batch_size <= 0:
            break

        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }

                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Swedish (Swedish).

Style: Make each phrase feel like a {viral_style} - something people would want to share!

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (with commas for natural pauses)
2. Swedish translation
3. Pronunciation guide (phonetic spelling, e.g., "Hej, hur mår du?")
CRITICAL: Every translation MUST be in Swedish. NEVER use German, Spanish, or any other language. Only Swedish.

Return as JSON array:
[{{"english": "...", "swedish": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a viral Swedish teacher creating engaging educational content for YouTube. Create short, natural phrases with pauses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                # Extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = repair_and_parse_json(content)

                # Filter by similarity
                filtered_phrases = filter_similar_phrases(phrases, history)

                # Filter by length and exact duplicates
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)

                # Add valid phrases
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)

                if len(all_phrases) >= num_phrases:
                    break

            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")

        # Small delay between batches
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    # Trim to exact count and save to history
    if not all_phrases:
        print(f"[content] AI generation produced 0 phrases. Loading fresh fallback phrases for '{category_english}'...")
        all_phrases = get_fresh_fallback_phrases(category_english, num_phrases)
    elif len(all_phrases) < num_phrases:
        print(f"[content] Only {len(all_phrases)} phrases generated. Padding with fresh fallback phrases...")
        extras = get_fresh_fallback_phrases(category_english, num_phrases - len(all_phrases))
        for ex in extras:
            if ex not in all_phrases:
                all_phrases.append(ex)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)

    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones with similarity check"""

    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "swedish": "相信自己。", "pronunciation": "xiāng xìn zì jǐ."},
            {"english": "You are capable of amazing things.", "swedish": "你有能力成就惊人的事情。", "pronunciation": "nǐ yǒu néng lì chéng jiù jīng rén de shì qíng."},
            {"english": "Dream big, start small.", "swedish": "胸怀大志，从小做起。", "pronunciation": "xiōng huái dà zhì, cóng xiǎo zuò qǐ."},
            {"english": "Your future is created by your actions.", "swedish": "你的未来由你的行动创造。", "pronunciation": "nǐ de wèi lái yóu nǐ de xíng dòng chuàng zào."},
            {"english": "Never give up on your dreams.", "swedish": "永不放弃梦想。", "pronunciation": "yǒng bù fàng qì mèng xiǎng."},
            {"english": "Small steps lead to big changes.", "swedish": "小步引领大变化。", "pronunciation": "xiǎo bù yǐn lǐng dà biàn huà."},
            {"english": "You are stronger than you think.", "swedish": "你比自己想象的更强大。", "pronunciation": "nǐ bǐ zì jǐ xiǎng xiàng de gèng qiáng dà."},
        ],
        "Love": [
            {"english": "Love yourself first.", "swedish": "先爱自己。", "pronunciation": "xiān ài zì jǐ."},
            {"english": "Love makes everything possible.", "swedish": "爱使一切成为可能。", "pronunciation": "ài shǐ yī qiè chéng wéi kě néng."},
            {"english": "My heart beats for you.", "swedish": "我的心为你跳动。", "pronunciation": "wǒ de xīn wèi nǐ tiào dòng."},
            {"english": "You are my everything.", "swedish": "你是我的一切。", "pronunciation": "nǐ shì wǒ de yī qiè."},
            {"english": "Together forever, hand in hand.", "swedish": "永远在一起，手牵手。", "pronunciation": "yǒng yuǎn zài yī qǐ, shǒu qiān shǒu."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "swedish": "成功来自努力。", "pronunciation": "chéng gōng lái zì nǔ lì."},
            {"english": "Keep going, you're getting there.", "swedish": "继续前进，你快到了。", "pronunciation": "jì xù qián jìn, nǐ kuài dào le."},
            {"english": "Winners never quit.", "swedish": "赢家永不放弃。", "pronunciation": "yíng jiā yǒng bù fàng qì."},
            {"english": "Your effort will pay off.", "swedish": "你的努力会有回报。", "pronunciation": "nǐ de nǔ lì huì yǒu huí bào."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "swedish": "知识就是力量。", "pronunciation": "zhī shí jiù shì lì liàng."},
            {"english": "Learn from yesterday, live for today.", "swedish": "借鉴昨天，活在今天。", "pronunciation": "jiè jiàn zuó tiān, huó zài jīn tiān."},
            {"english": "Think before you act.", "swedish": "三思而后行。", "pronunciation": "sān sī ér hòu xíng."},
            {"english": "Experience is the best teacher.", "swedish": "经验是最好的老师。", "pronunciation": "jīng yàn shì zuì hǎo de lǎo shī."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "swedish": "快乐是一种选择。", "pronunciation": "kuài lè shì yī zhǒng xuǎn zé."},
            {"english": "Find joy in the little things.", "swedish": "在小事中寻找快乐。", "pronunciation": "zài xiǎo shì zhōng xún zhǎo kuài lè."},
            {"english": "Smile, it makes others happy.", "swedish": "微笑，让别人也开心。", "pronunciation": "wēi xiào, ràng bié rén yě kāi xīn."},
            {"english": "Today is a gift.", "swedish": "今天是礼物。", "pronunciation": "jīn tiān shì lǐ wù."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "swedish": "比昨天更好。", "pronunciation": "bǐ zuó tiān gèng hǎo."},
            {"english": "Grow through what you go through.", "swedish": "在经历中成长。", "pronunciation": "zài jīng lì zhōng chéng zhǎng."},
            {"english": "Invest in yourself daily.", "swedish": "每天投资自己。", "pronunciation": "měi tiān tóu zī zì jǐ."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "swedish": "谢谢你的一切。", "pronunciation": "xiè xie nǐ de yī qiè."},
            {"english": "I appreciate your help.", "swedish": "我感激你的帮助。", "pronunciation": "wǒ gǎn jī nǐ de bāng zhù."},
            {"english": "Grateful for this moment.", "swedish": "感激这一刻。", "pronunciation": "gǎn jī zhè yī kè."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "swedish": "永远是朋友，无论如何。", "pronunciation": "yǒng yuǎn shì péng yǒu, wú lùn rú hé."},
            {"english": "You are my best friend.", "swedish": "你是我最好的朋友。", "pronunciation": "nǐ shì wǒ zuì hǎo de péng yǒu."},
            {"english": "True friends stick together.", "swedish": "真正的朋友在一起。", "pronunciation": "zhēn zhèng de péng yǒu zài yī qǐ."},
        ],
        "Hope": [
            {"english": "There is always hope.", "swedish": "总有希望。", "pronunciation": "zǒng yǒu xī wàng."},
            {"english": "Better days are coming.", "swedish": "更好的日子会来。", "pronunciation": "gèng hǎo de rì zi huì lái."},
            {"english": "Keep faith, keep going.", "swedish": "保持信念，继续前进。", "pronunciation": "bǎo chí xìn niàn, jì xù qián jìn."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "swedish": "今天创造美好的东西。", "pronunciation": "jīn tiān chuàng zào měi hǎo de dōng xī."},
            {"english": "Your imagination is unlimited.", "swedish": "你的想象力无限。", "pronunciation": "nǐ de xiǎng xiàng lì wú xiàn."},
            {"english": "Art comes from the heart.", "swedish": "艺术来自内心。", "pronunciation": "yì shù lái zì nèi xīn."},
            {"english": "Express yourself freely.", "swedish": "自由表达自己。", "pronunciation": "zì yóu biǎo dá zì jǐ."},
            {"english": "Innovation starts with curiosity.", "swedish": "创新始于好奇心。", "pronunciation": "chuàng xīn shǐ yú hào qí xīn."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "swedish": "在内心寻找平静。", "pronunciation": "zài nèi xīn xún zhǎo píng jìng."},
            {"english": "Breathe, relax, let go.", "swedish": "呼吸，放松，放下。", "pronunciation": "hū xī, fàng sōng, fàng xià."},
            {"english": "Calm mind, happy heart.", "swedish": "心静，心喜。", "pronunciation": "xīn jìng, xīn xǐ."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "swedish": "你足够了，就做你自己。", "pronunciation": "nǐ zú gòu le, jiù zuò nǐ zì jǐ."},
            {"english": "Stand tall, speak up.", "swedish": "挺直腰板，大声说话。", "pronunciation": "tǐng zhí yāo bǎn, dà shēng shuō huà."},
            {"english": "Believe in your abilities.", "swedish": "相信你的能力。", "pronunciation": "xiāng xìn nǐ de néng lì."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "swedish": "永不放弃，继续前进。", "pronunciation": "yǒng bù fàng qì, jì xù qián jìn."},
            {"english": "Storms make trees take deeper roots.", "swedish": "风暴使树根更深。", "pronunciation": "fēng bào shǐ shù gēn gèng shēn."},
            {"english": "Patience and persistence win.", "swedish": "耐心和坚持获胜。", "pronunciation": "nài xīn hé jiān chí huò shèng."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "swedish": "让你的光芒闪耀。", "pronunciation": "ràng nǐ de guāng máng shǎn yào."},
            {"english": "Inspire others by your actions.", "swedish": "用行动激励他人。", "pronunciation": "yòng xíng dòng jī lì tā rén."},
            {"english": "Be the change you want to see.", "swedish": "成为你想看到的改变。", "pronunciation": "chéng wéi nǐ xiǎng kàn dào de gǎi biàn."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "swedish": "每天选择积极。", "pronunciation": "měi tiān xuǎn zé jī jí."},
            {"english": "Good vibes only.", "swedish": "只要好氛围。", "pronunciation": "zhǐ yào hǎo fēn wéi."},
            {"english": "Life is what you make it.", "swedish": "生活由你创造。", "pronunciation": "shēng huó yóu nǐ chuàng zào."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "swedish": "勇敢，迈出第一步。", "pronunciation": "yǒng gǎn, mài chū dì yī bù."},
            {"english": "Courage is not the absence of fear.", "swedish": "勇气不是没有恐惧。", "pronunciation": "yǒng qì bù shì méi yǒu kǒng jù."},
            {"english": "Face your fears head on.", "swedish": "直面恐惧。", "pronunciation": "zhí miàn kǒng jù."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "swedish": "善待你遇到的每个人。", "pronunciation": "shàn dài nǐ yù dào de měi gè rén."},
            {"english": "Kindness costs nothing, means everything.", "swedish": "善良无需代价，意义非凡。", "pronunciation": "shàn liáng wú xū dài jià, yì yì fēi fán."},
            {"english": "Spread kindness wherever you go.", "swedish": "无论去哪里都传播善良。", "pronunciation": "wú lùn qù nǎ lǐ dōu chuán bō shàn liáng."},
        ],
        "Patience": [
            {"english": "Good things take time.", "swedish": "好事需要时间。", "pronunciation": "hǎo shì xū yào shí jiān."},
            {"english": "Wait patiently, trust the process.", "swedish": "耐心等待，相信过程。", "pronunciation": "nài xīn děng dài, xiāng xìn guò chéng."},
            {"english": "Rome wasn't built in a day.", "swedish": "罗马不是一天建成的。", "pronunciation": "luó mǎ bù shì yī tiān jiàn chéng de."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "swedish": "原谅并释放自己。", "pronunciation": "yuán liàng bìng shì fàng zì jǐ."},
            {"english": "Let go of grudges, find peace.", "swedish": "放下怨恨，找到平静。", "pronunciation": "fàng xià yuàn hèn, zhǎo dào píng jìng."},
            {"english": "Forgiveness is a gift to yourself.", "swedish": "原谅是给自己的礼物。", "pronunciation": "yuán liàng shì gěi zì jǐ de lǐ wù."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "swedish": "你比自己知道的更强大。", "pronunciation": "nǐ bǐ zì jǐ zhī dào de gèng qiáng dà."},
            {"english": "Inner strength comes from within.", "swedish": "内在力量来自内心。", "pronunciation": "nèi zài lì liàng lái zì nèi xīn."},
            {"english": "Challenges make you stronger.", "swedish": "挑战让你更强大。", "pronunciation": "tiǎo zhàn ràng nǐ gèng qiáng dà."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "swedish": "在每一刻找到快乐。", "pronunciation": "zài měi yī kè zhǎo dào kuài lè."},
            {"english": "Joy is contagious, spread it.", "swedish": "快乐会传染，传播它。", "pronunciation": "kuài lè huì chuán rǎn, chuán bō tā."},
            {"english": "Dance like nobody's watching.", "swedish": "像没人看着一样跳舞。", "pronunciation": "xiàng méi rén kàn zhe yī yàng tiào wǔ."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "swedish": "在生活中找到平衡。", "pronunciation": "zài shēng huó zhōng zhǎo dào píng héng."},
            {"english": "Work hard, rest well.", "swedish": "努力工作，好好休息。", "pronunciation": "nǔ lì gōng zuò, hǎo hǎo xiū xī."},
            {"english": "Too much of anything is not good.", "swedish": "过犹不及。", "pronunciation": "guò yóu bù jí."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "swedish": "成长发生在舒适区外。", "pronunciation": "chéng zhǎng fā shēng zài shū shì qū wài."},
            {"english": "Embrace change, grow stronger.", "swedish": "拥抱改变，变得更强大。", "pronunciation": "yōng bào gǎi biàn, biàn dé gèng qiáng dà."},
            {"english": "Every challenge is a chance to grow.", "swedish": "每个挑战都是成长机会。", "pronunciation": "měi gè tiǎo zhàn dōu shì chéng zhǎng jī huì."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "swedish": "找到你的目标，追随它。", "pronunciation": "zhǎo dào nǐ de mù biāo, zhuī suí tā."},
            {"english": "Your life has meaning.", "swedish": "你的生命有意义。", "pronunciation": "nǐ de shēng mìng yǒu yì yì."},
            {"english": "Live with intention, not accident.", "swedish": "有目的地生活，不是偶然。", "pronunciation": "yǒu mù dì de shēng huó, bù shì ǒu rán."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "swedish": "活在当下这一刻。", "pronunciation": "huó zài dāng xià zhè yī kè."},
            {"english": "Breathe deeply, stay grounded.", "swedish": "深呼吸，保持踏实。", "pronunciation": "shēn hū xī, bǎo chí tà shí."},
            {"english": "Notice the little things around you.", "swedish": "注意周围的小事。", "pronunciation": "zhù yì zhōu wéi de xiǎo shì."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])

    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    """Generate audio using Edge TTS"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        swedish_file = output_dir / f"swedish_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        # Generate English audio
        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Swedish audio
        sv_success = asyncio.run(generate_single_audio(phrase["swedish"], SWEDISH_VOICE, str(swedish_file)))
        if not sv_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(swedish_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        sv_duration = get_audio_duration(str(swedish_file))

        # Add pause between English and Swedish
        pause_between = 0.5
        total_duration = en_duration + pause_between + sv_duration

        # Combine audio files
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(swedish_file),
            "-filter_complex", f"[0:a]apad=pad_dur=0.5[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{swedish_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "swedish": str(swedish_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "sv_duration": sv_duration
        })

    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMPROVED BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    """Create Lingexa's exact light cream background"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Light cream gradient - NO circles, clean background
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    return img



def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with modern glassmorphic UI - Lingexa Inspired"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Load fonts
    english_font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    swedish_font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    # Refined font sizes
    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_swedish = load_font(swedish_font_paths, 82)
    font_pronunciation = load_font(swedish_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    swedish = phrase_data.get("swedish", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar (Top Left)
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    
    # Badge dimensions - fixed height for perfect centering
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    
    container_x = 60
    container_y = 60
    
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    # Draw text perfectly centered in the badge (with +2px vertical offset for visual balance)
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2), 
        cat_text, 
        fill=(255, 255, 255, 255), 
        font=font_category, 
        anchor="mm"
    )

    # Main Content Area - Center Vertical
    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    # 1. English Box
    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h
    
    # 2. Swedish Box
    sv_lines = wrap_text(swedish, font_swedish, VIDEO_WIDTH - 300)
    sv_line_h = 100
    sv_total_h = len(sv_lines) * sv_line_h
    
    # 3. Pronunciation Box
    py_text = f"[{pronunciation}]"
    py_lines = wrap_text(py_text, font_pronunciation, VIDEO_WIDTH - 400)
    py_line_h = 60
    py_total_h = len(py_lines) * py_line_h

    total_content_h = en_total_h + sv_total_h + py_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    # Draw English Section
    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2
    
    # English Box (Lingexa Dark Purple)
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2), 
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")
    
    y_cursor = y_start + en_box_h + GAP

    # Swedish Section (Lingexa Lighter Purple)
    sv_box_h = sv_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + sv_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(sv_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * sv_line_h) + sv_line_h // 2), 
                  line, fill=(255, 255, 255), font=font_swedish, anchor="mm")

    y_cursor += sv_box_h + (GAP // 2)

    # Pronunciation Section (Lingexa Peach)
    py_box_h = py_total_h + 40
    py_box_w = box_w - 200
    py_box_x = (VIDEO_WIDTH - py_box_w) // 2
    draw.rounded_rectangle(
        [(py_box_x, y_cursor), (py_box_x + py_box_w, y_cursor + py_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )

    for i, line in enumerate(py_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * py_line_h) + py_line_h // 2), 
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding (Bottom Right)
    brand_text = "VELOCITY SWEDISH"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text, 
              fill=(45, 35, 65, 255), font=font_branding)

    # Save
    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path



# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_swedish: str, output_path: str):
    """Generate a modern, high-impact thumbnail - Lingexa Inspired"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    # Use the same base background logic but with even more "pop"
    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Load fonts
    english_font_paths = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    swedish_font_paths = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(swedish_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    # Big Impact Title (Dark Purple)
    draw.text((VIDEO_WIDTH // 2, 220), "MASTER SWEDISH", fill=(45, 35, 65), font=font_huge, anchor="mm")
    
    # Category Badge (Lingexa Dark Purple)
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    # Swedish Translation (Dark Purple)
    draw.text((VIDEO_WIDTH // 2, 530), category_swedish, fill=(45, 35, 65), font=font_main, anchor="mm")

    # Features / Call to Action (Lingexa Peach)
    cta_text = "60 ESSENTIAL PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    # Bottom Branding (Dark Purple Bar)
    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY SWEDISH", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path



def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    """Extract a frame from the video as thumbnail using FFmpeg"""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  ✓ Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  ⚠️ Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  ⚠️ Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_swedish: str, phrases: list, duration_minutes: float, output_dir: str):
    """Generate viral YouTube title and description with all phrases - COMBINED in one file"""
    
    # Generate viral title variations
    titles = [
        f"Learn Swedish in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_swedish})",
        f"60 Swedish Phrases for {category_english} | Speak Swedish Like a Native! ({category_swedish})",
        f"Master Swedish {category_english} | 60 Essential Swedish Phrases with Pronunciation | Velocity Swedish",
        f"Swedish Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Swedish Fluently | {category_english} Phrases | English + Swedish + Pronunciation",
    ]

    # Generate comprehensive description
    description = f"""🇸🇪 Learn Swedish with Velocity Swedish! 🇸🇪

In this video, you'll learn 60 essential Swedish phrases about {category_english} ({category_swedish}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Swedish
• Correct pronunciation with Pronunciation
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    # Add timestamps for each phrase (every 10 phrases grouped)
    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += f"""
📝 ALL PHRASES IN THIS VIDEO:
"""

    # Add all phrases
    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Swedish: {phrase['swedish']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += f"""
🎯 PERFECT FOR:
• Swedish beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Swedish
• Language enthusiasts and polyglots
• Students preparing for Swedish language exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Swedish learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY SWEDISH:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Swedish Motivation Phrases
• Swedish Love Expressions
• Swedish Basics
• Basic Swedish Greetings

#LearnSwedish #SwedishPhrases #SwedishLanguage #{category_english.replace(' ', '')} #VelocitySwedish #SwedishForBeginners #SpeakSwedish #SwedishVocabulary #LanguageLearning #Swedish101 #SwedishLesson

---
© Velocity Swedish - Making Swedish learning accessible to everyone!
"""

    # Write to COMBINED file (title + description in one)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Combined YouTube upload file (title + description)
    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("📌 RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("📝 SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("📄 VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("🏷️ VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Swedish",
            "Swedish Phrases",
            "Swedish",
            category_english,
            "Velocity Swedish",
            "Swedish for Beginners",
            "Speak Swedish",
            "Swedish Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Swedish 101",
            "Swedish Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    # Metadata JSON (for easy parsing)
    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_swedish": category_swedish,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] ✓ Generated YouTube upload files")
    print(f"  📄 youtube_upload_info.txt (title + description + tags)")
    print(f"  📄 video_metadata.json")

    return metadata


# ============== VIDEO CREATION WITH TRANSITIONS ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating long-form video from {len(image_files)} images...")
    print(f"[video] Ensuring PERFECT audio-video synchronization...")

    temp_clips = []

    # Step 1: Create video clips for each image with EXACT audio duration
    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']  # Use EXACT duration from audio
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + SV: {audio_info.get('sv_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        # Create video clip from image with EXACT duration matching audio
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", f"{duration:.3f}",  # EXACT duration
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    # Step 2: Concatenate all video clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    # Step 3: Add the combined audio (which already has correct timing)
    print("[video] Adding audio...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-t", f"{audio_duration:.3f}",
        str(output_file)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Verify final video
    video_duration = get_audio_duration(str(output_file))
    print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup temp files
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    """Generate complete long-form YouTube video with thumbnail and metadata"""

    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    # Use provided phrases count or default
    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"🎬 LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_SWEDISH[category_english]})")
    print(f"🎯 Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['swedish']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    # Step 2: Generate images
    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    # Step 3: Generate thumbnail
    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_SWEDISH[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_SWEDISH[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Calculate actual duration
    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    # Step 5: Create video
    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )
    
    # Extract video frame as thumbnail
    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    # Step 6: Generate title and description
    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_metadata = generate_title_description(
        category_english,
        CATEGORIES_SWEDISH[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_swedish": CATEGORIES_SWEDISH[category_english],
        "timestamp": timestamp,
        "target_phrases": phrases_count,
        "actual_duration_seconds": total_duration,
        "actual_duration_minutes": total_duration / 60,
        "phrases_count": len(phrases),
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio),
        "thumbnail": str(thumbnail_path),
        "resolution": f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
        "fps": FPS
    }

    with open(video_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Save latest video info for upload
    latest_info = {
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "title": title_metadata["selected_title"],
        "description": title_metadata["description"],
        "tags": title_metadata["tags"],
        "category_english": category_english,
        "category_swedish": CATEGORIES_SWEDISH[category_english],
        "phrases_count": len(phrases),
        "duration_minutes": total_duration / 60
    }
    with open(OUTPUT_DIR / "latest_video.json", "w", encoding="utf-8") as f:
        json.dump(latest_info, f, indent=2, ensure_ascii=False)
    print(f"  📄 latest_video.json saved")

    print(f"\n{'='*80}")
    print(f"✅ LONG-FORM VIDEO COMPLETE!")
    print(f"  📁 {video_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🖼️  thumbnail.jpg (generated)")
    print(f"  🖼️  {video_thumbnail_path.name} (from video)")
    print(f"  📄 youtube_upload_info.txt (title + description + tags)")
    print(f"  ⏱️  Duration: {total_duration/60:.2f} minutes")
    print(f"  📊 Phrases: {len(phrases)}")
    print(f"  🏷️  Branding: Velocity Swedish")
    print(f"  📺 Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return metadata


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    """Generate multiple long-form videos"""
    print(f"\n🎬 Generating {count} long-form video(s)...")
    print("="*80)

    for i in range(count):
        print(f"\n{'='*80}")
        print(f"🎬 VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)

    print("\n" + "="*80)
    print(f"✅ ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Swedish YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate (determines video length, ~5.5s per phrase. 60 phrases = ~5.5 mins)")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate (e.g. 'Motivation', 'Friendship'). Random if not provided.")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("🇸🇪 VELOCITY SWEDISH - YOUTUBE LONG-FORM AUTOMATION 🇸🇪")
    print("="*80)
    print("\n✨ FEATURES:")
    print("  ✓ 16:9 format (1920x1080) for YouTube long-form")
    print(f"  ✓ Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  ✓ Lingexa Light Theme (Cream background, dark/light purple + peach containers)")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Smooth crossfade transitions")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print(f"\n📊 AVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_SWEDISH[cat]})")
    print(f"\n📈 VIDEO SPECIFICATIONS:")
    print(f"  • Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  • Frame Rate: {FPS} FPS")
    print(f"  • Target Phrases: {args.phrases}")
    print(f"  • Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  • Phrase History: PERMANENT (never deletes)")
    print("="*80)

    # Note: History tracking is built-in. Check output/history/all_generated_phrases.json
    generate_longform_video(category_english=args.category, target_phrases=args.phrases)