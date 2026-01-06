from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import TimedOut, NetworkError
import asyncio
from rules import determine_severity
from messages import QUESTIONS, ADVICE, DISCLAIMER
from ml_model import DengueMLPredictor
import csv
from datetime import datetime
import hashlib
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize ML predictor
ml_predictor = DengueMLPredictor()
ml_enabled = ml_predictor.load_model()  # Try to load trained model

user_state = {}
DATASETS_DIR = 'user_datasets'
INDIVIDUAL_DATASETS_DIR = 'individual_datasets'
RESEARCH_SUMMARY_FILE = 'research_summary.csv'

SYMPTOM_ORDER = [
    "Fever",
    "Headache",
    "EyePain",
    "Vomiting",
    "PersistentVomiting",
    "AbdominalPain",
    "Bleeding",
    "Fatigue",
    "FluidAccumulation",
]

YES_WORDS = ["yes", "y", "ha", "হ্যাঁ", "হ্যা"]
NO_WORDS = ["no", "n", 'na', "না"]
VOMITING_WORDS = {
    "once": "once",
    "frequent": "frequent",
    "continuous": "continuous",
    "ঘন ঘন": "frequent",
    "ক্রমাগত": "continuous",
    "একবার": "once"
}
RESTART_WORDS = ["test again", "আবার শুরু", "test", "শুরু"]

# Initialize research data
def init_research_data():
    os.makedirs(DATASETS_DIR, exist_ok=True)
    os.makedirs(INDIVIDUAL_DATASETS_DIR, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    if not os.path.exists(RESEARCH_SUMMARY_FILE):
        with open(RESEARCH_SUMMARY_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = [
                'dataset_id', 'user_hash', 'user_name', 'timestamp', 'language', 
                'fever', 'headache', 'eye_pain', 'vomiting', 'persistent_vomiting',
                'abdominal_pain', 'bleeding', 'fatigue', 'fluid_accumulation',
                'predicted_severity', 'ml_severity', 'ml_confidence',
                'conversation_duration_seconds', 'prediction_method',
                'telegram_username', 'first_name', 'last_name', 'dataset_filename'
            ]
            writer.writerow(headers)

def get_next_dataset_id():
    if not os.path.exists(RESEARCH_SUMMARY_FILE):
        return 1
    try:
        import pandas as pd
        df = pd.read_csv(RESEARCH_SUMMARY_FILE)
        if len(df) == 0:
            return 1
        return df['dataset_id'].max() + 1
    except:
        return 1

def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('_ ')
    if len(name) > 50:
        name = name[:50]
    if not name:
        name = 'anonymous'
    return name

def save_individual_dataset(user_name, answers, rule_severity, ml_severity, ml_confidence, prediction_method, final_severity, lang):
    """Save individual user dataset as name-dataset.txt (silently for research)"""
    try:
        safe_name = sanitize_filename(user_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_{timestamp}_dataset.txt"
        filepath = os.path.join(INDIVIDUAL_DATASETS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("INDIVIDUAL PATIENT DATASET\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("PATIENT INFORMATION\n")
            f.write("-" * 40 + "\n")
            f.write(f"Name: {user_name}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Language: {lang.upper()}\n\n")
            
            f.write("SYMPTOM RESPONSES\n")
            f.write("-" * 40 + "\n")
            for symptom in SYMPTOM_ORDER:
                value = answers.get(symptom)
                if value == 1:
                    response = "Yes"
                elif value == 0:
                    response = "No"
                elif value is None:
                    response = "Not applicable"
                else:
                    response = value.capitalize()
                
                symptom_name = symptom.replace('_', ' ').title()
                f.write(f"{symptom_name:20s}: {response}\n")
            f.write("\n")
            
            f.write("PREDICTION RESULTS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Rule-Based Prediction: {rule_severity}\n")
            if ml_severity:
                f.write(f"ML Prediction: {ml_severity} (Confidence: {ml_confidence:.1%})\n")
            f.write(f"Final Prediction: {final_severity}\n")
            f.write(f"Prediction Method: {prediction_method.upper()}\n\n")
            
            f.write("=" * 60 + "\n")
            f.write("END OF DATASET\n")
            f.write("=" * 60 + "\n")
        
        print(f"📄 Individual dataset saved: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error saving individual dataset: {e}")
        return None

def save_user_dataset_silently(user_id, state, rule_severity, ml_severity, ml_confidence, start_time, user_name):
    """Save dataset silently in background (not shown to user)"""
    try:
        timestamp = datetime.now()
        user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:10]
        dataset_id = get_next_dataset_id()
        
        safe_name = sanitize_filename(user_name)
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        dataset_filename = f"{safe_name}_{timestamp_str}.csv"
        dataset_path = os.path.join(DATASETS_DIR, dataset_filename)
        
        # Determine which prediction was used
        prediction_method = "ml" if ml_enabled and ml_severity else "rules"
        final_severity = ml_severity if prediction_method == "ml" else rule_severity
        
        # Extract answers
        answers = state.get("answers", {})
        user_info = state.get("user_info", {})
        duration = (datetime.now() - start_time).total_seconds()
        
        # Create dataset file
        with open(dataset_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow(["DENGUE TRIAGE CHATBOT - PATIENT DATASET"])
            writer.writerow(["=" * 60])
            writer.writerow(["PREDICTION METHOD", f"{prediction_method.upper()} BASED"])
            if prediction_method == "ml":
                writer.writerow(["ML Confidence", f"{ml_confidence:.1%}"])
            writer.writerow([])
            
            writer.writerow(["PATIENT INFORMATION"])
            writer.writerow(["Dataset ID", dataset_id])
            writer.writerow(["Patient Name", user_name])
            writer.writerow(["User Hash", user_hash])
            writer.writerow(["Timestamp", timestamp.isoformat()])
            writer.writerow(["Language", state.get("lang", "unknown")])
            writer.writerow(["Prediction Method", prediction_method])
            writer.writerow(["Final Severity", final_severity])
            writer.writerow(["Rule-Based Severity", rule_severity])
            if ml_severity:
                writer.writerow(["ML Severity", ml_severity])
                writer.writerow(["ML Confidence", f"{ml_confidence:.1%}"])
            writer.writerow([])
            
            writer.writerow(["SYMPTOM ASSESSMENT"])
            for symptom in SYMPTOM_ORDER:
                value = answers.get(symptom)
                question = QUESTIONS[state.get("lang", "en")].get(symptom, symptom)
                
                if value == 1:
                    response = "Yes" if state.get("lang") == "en" else "হ্যাঁ"
                elif value == 0:
                    response = "No" if state.get("lang") == "en" else "না"
                elif value is None:
                    response = "Not applicable"
                else:
                    response = value.capitalize()
                
                writer.writerow([symptom, question, response, value])
            
            writer.writerow([])
            writer.writerow(["PREDICTION COMPARISON"])
            writer.writerow(["Method", "Prediction", "Details"])
            writer.writerow(["Rule-Based", rule_severity, "WHO Guidelines"])
            if ml_severity:
                writer.writerow(["Machine Learning", ml_severity, f"Confidence: {ml_confidence:.1%}"])
            writer.writerow(["Final Used", final_severity, prediction_method.upper()])
        
        # Save to summary
        summary_row = [
            dataset_id, user_hash, user_name, timestamp.isoformat(),
            state.get("lang", "unknown"),
            answers.get("Fever", -1), answers.get("Headache", -1),
            answers.get("EyePain", -1), answers.get("Vomiting", -1),
            answers.get("PersistentVomiting", "not_applicable"),
            answers.get("AbdominalPain", -1), answers.get("Bleeding", -1),
            answers.get("Fatigue", -1), answers.get("FluidAccumulation", -1),
            rule_severity, ml_severity, ml_confidence,
            round(duration, 2), prediction_method,
            user_info.get("username", "anonymous"),
            user_info.get("first_name", ""), user_info.get("last_name", ""),
            dataset_filename
        ]
        
        with open(RESEARCH_SUMMARY_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(summary_row)
            
        # JSON log
        detailed_log = {
            'dataset_id': dataset_id,
            'user_name': user_name,
            'timestamp': timestamp.isoformat(),
            'rule_severity': rule_severity,
            'ml_severity': ml_severity,
            'ml_confidence': ml_confidence,
            'prediction_method': prediction_method,
            'answers': answers,
            'bot_version': '2.0'
        }
        
        log_filename = f'logs/{safe_name}_{timestamp.strftime("%Y%m%d_%H%M%S")}.json'
        with open(log_filename, 'w') as f:
            json.dump(detailed_log, f, indent=2)
        
        # Save individual dataset
        individual_filename = save_individual_dataset(
            user_name, answers, rule_severity, ml_severity, 
            ml_confidence, prediction_method, final_severity, 
            state.get("lang", "en")
        )
            
        print(f"📁 Dataset saved silently: {dataset_filename}")
        return True
        
    except Exception as e:
        print(f"Error saving dataset silently: {e}")
        return False

def format_summary_line(question, answer, lang, symptom):
    """Format summary line with better handling for skipped questions"""
    if answer == 1:
        ans_text = "Yes" if lang == "en" else "হ্যাঁ"
    elif answer == 0:
        ans_text = "No" if lang == "en" else "না"
    elif answer is None:
        # For PersistentVomiting when Vomiting is No
        if symptom == "PersistentVomiting":
            ans_text = "Not applicable" if lang == "en" else "প্রযোজ্য নয়"
        else:
            ans_text = "Not answered" if lang == "en" else "উত্তর দেওয়া হয়নি"
    else:
        ans_text = answer.capitalize()
    
    return f"{question} ➤ {ans_text}"

def generate_detailed_analysis(symptoms, severity, lang):
    """Generate detailed symptom analysis (without prediction)"""
    
    symptom_descriptions = {
        "Fever": {"en": "High fever (>38.5°C)", "bn": "উচ্চ জ্বর (৩৮.৫°সেলসিয়াসের বেশি)"},
        "Headache": {"en": "Severe headache", "bn": "তীব্র মাথাব্যথা"},
        "EyePain": {"en": "Pain behind eyes", "bn": "চোখের পিছনে ব্যথা"},
        "Vomiting": {"en": "Vomiting", "bn": "বমি"},
        "PersistentVomiting": {"en": "Persistent vomiting", "bn": "স্থায়ী বমি"},
        "AbdominalPain": {"en": "Severe abdominal pain", "bn": "তীব্র পেট ব্যথা"},
        "Bleeding": {"en": "Bleeding signs", "bn": "রক্তপাতের লক্ষণ"},
        "Fatigue": {"en": "Extreme weakness/restlessness", "bn": "অতিরিক্ত দুর্বলতা/অস্থিরতা"},
        "FluidAccumulation": {"en": "Swelling/breathing difficulty", "bn": "হাত-পা ফোলা/শ্বাসকষ্ট"}
    }
    
    analysis_lines = []
    for symptom in SYMPTOM_ORDER:
        value = symptoms.get(symptom)
        
        if value == 1:
            icon = "✅"
            status = "Present" if lang == "en" else "হ্যাঁ"
        elif value == 0:
            icon = "❌"
            status = "Absent" if lang == "en" else "না"
        elif value is None:
            icon = "➖"
            if symptom == "PersistentVomiting":
                status = "Not applicable" if lang == "en" else "প্রযোজ্য নয়"
            else:
                status = "Not answered" if lang == "en" else "উত্তর দেওয়া হয়নি"
        else:
            icon = "🔄"
            status = value.capitalize()
        
        symptom_text = symptom_descriptions[symptom][lang]
        analysis_lines.append(f"{icon} {symptom_text}: {status}")
    
    analysis = "📊 **Detailed Symptom Analysis:**\n\n" + "\n".join(analysis_lines)
    
    # Add a note about fever requirement for dengue if symptoms present but no fever
    fever_present = symptoms.get("Fever") == 1
    other_symptoms_present = any(symptoms.get(s) == 1 for s in ["Headache", "EyePain", "Vomiting", "AbdominalPain", "Bleeding", "Fatigue", "FluidAccumulation"])
    
    if not fever_present and other_symptoms_present:
        note = {
            "en": "\n\n⚠️ **Note:** These symptoms could indicate various conditions. For dengue diagnosis, fever is required according to WHO guidelines.",
            "bn": "\n\n⚠️ **দ্রষ্টব্য:** এই লক্ষণগুলি বিভিন্ন অবস্থার ইঙ্গিত দিতে পারে। WHO নির্দেশিকা অনুযায়ী ডেঙ্গু নির্ণয়ের জন্য জ্বর প্রয়োজন।"
        }
        analysis += note[lang]
    
    return analysis

def generate_prediction_message(severity, ml_confidence=None, prediction_method="rules", lang="en"):
    """Generate WHO-based prediction message for users"""
    
    # WHO-based severity names and icons
    who_classification = {
        "NoSymptoms": {
            "name": {"en": "No Symptoms Detected", "bn": "কোনো লক্ষণ পাওয়া যায়নি"},
            "icon": "✅",
            "explanation": {
                "en": "You don't have symptoms that suggest any acute illness. No special precautions needed.",
                "bn": "আপনার কোনো তীব্র অসুস্থতার লক্ষণ নেই। বিশেষ সতর্কতার প্রয়োজন নেই।"
            }
        },
        "FeverOnly": {
            "name": {"en": "Fever Detected", "bn": "জ্বর পাওয়া গেছে"},
            "icon": "🟢",
            "explanation": {
                "en": "**Assessment:** You have fever without other symptoms.\n\n**Note:** Fever alone could be due to various causes including early dengue, other viral infections, or bacterial infections. Monitor for additional symptoms.",
                "bn": "**মূল্যায়ন:** আপনার জ্বর আছে কিন্তু অন্য কোনো লক্ষণ নেই।\n\n**দ্রষ্টব্য:** শুধুমাত্র জ্বর বিভিন্ন কারণে হতে পারে যেমন প্রাথমিক ডেঙ্গু, অন্যান্য ভাইরাল সংক্রমণ বা ব্যাকটেরিয়া সংক্রমণ। অতিরিক্ত লক্ষণের জন্য পর্যবেক্ষণ করুন।"
            }
        },
        "OtherSymptoms": {
            "name": {"en": "Symptoms Without Fever", "bn": "জ্বর ছাড়া লক্ষণ"},
            "icon": "ℹ️",
            "explanation": {
                "en": "**Assessment:** You have symptoms but NO fever.\n\n**Important:** Dengue diagnosis requires fever according to WHO guidelines. Your symptoms could indicate other conditions. Consult a doctor if symptoms persist.",
                "bn": "**মূল্যায়ন:** আপনার লক্ষণ আছে কিন্তু জ্বর নেই।\n\n**গুরুত্বপূর্ণ:** WHO নির্দেশিকা অনুযায়ী ডেঙ্গু নির্ণয়ের জন্য জ্বর প্রয়োজন। আপনার লক্ষণ অন্যান্য অবস্থার ইঙ্গিত দিতে পারে। লক্ষণ স্থায়ী হলে ডাক্তারের সাথে পরামর্শ করুন।"
            }
        },
        "Mild": {
            "name": {"en": "Dengue without Warning Signs", "bn": "সতর্কতা লক্ষণবিহীন ডেঙ্গু"},
            "icon": "🟢",
            "explanation": {
                "en": "**WHO Classification: Dengue without warning signs**\n\n**Symptoms Present:** Fever with other symptoms\n**Risk Level:** Low\n**Action:** Rest, hydrate, monitor for warning signs\n\n**Note:** This is uncomplicated dengue. Most cases recover with proper care.",
                "bn": "**WHO শ্রেণীবিভাগ: সতর্কতা লক্ষণবিহীন ডেঙ্গু**\n\n**উপস্থিত লক্ষণ:** জ্বর সহ অন্যান্য লক্ষণ\n**ঝুঁকির মাত্রা:** কম\n**করনীয়:** বিশ্রাম নিন, তরল পান করুন, সতর্কতা লক্ষণের জন্য পর্যবেক্ষণ করুন\n\n**দ্রষ্টব্য:** এটি জটিলতাবিহীন ডেঙ্গু। বেশিরভাগ ক্ষেত্রে সঠিক যত্নে সুস্থ হয়ে ওঠে।"
            }
        },
        "Moderate": {
            "name": {"en": "Dengue with Warning Signs", "bn": "সতর্কতা লক্ষণযুক্ত ডেঙ্গু"},
            "icon": "🟡",
            "explanation": {
                "en": "**WHO Classification: Dengue with warning signs** ⚠️\n\n**Warning Signs Detected:** You have fever with warning signs\n**Risk Level:** Medium\n**Action Required:** Medical consultation recommended\n\n**Note:** Warning signs require medical evaluation to prevent complications.",
                "bn": "**WHO শ্রেণীবিভাগ: সতর্কতা লক্ষণযুক্ত ডেঙ্গু** ⚠️\n\n**শনাক্ত সতর্কতা লক্ষণ:** আপনার জ্বর সহ সতর্কতা লক্ষণ আছে\n**ঝুঁকির মাত্রা:** মাঝারি\n**প্রয়োজনীয় ব্যবস্থা:** চিকিৎসা পরামর্শের সুপারিশ\n\n**দ্রষ্টব্য:** জটিলতা রোধ করতে সতর্কতা লক্ষণগুলির চিকিৎসা মূল্যায়ন প্রয়োজন।"
            }
        },
        "Severe": {
            "name": {"en": "Severe Dengue", "bn": "গুরুতর ডেঙ্গু"},
            "icon": "🔴",
            "explanation": {
                "en": "**WHO Classification: Severe Dengue** 🚨\n\n**Severe Criteria Met:** You have severe dengue symptoms\n**Risk Level:** High\n**Immediate Action:** Hospital care required\n\n**Emergency:** Go to nearest hospital immediately or call emergency services.",
                "bn": "**WHO শ্রেণীবিভাগ: গুরুতর ডেঙ্গু** 🚨\n\n**গুরুতর মানদণ্ড পূরণ হয়েছে:** আপনার গুরুতর ডেঙ্গু লক্ষণ আছে\n**ঝুঁকির মাত্রা:** উচ্চ\n**তাৎক্ষণিক ব্যবস্থা:** হাসপাতালের যত্ন প্রয়োজন\n\n**জরুরি অবস্থা:** নিকটস্থ হাসপাতালে যান বা জরুরি সেবায় কল করুন।"
            }
        }
    }
    
    # Get classification data
    classification = who_classification.get(severity, {
        "name": {"en": severity, "bn": severity},
        "icon": "❓",
        "explanation": {"en": "", "bn": ""}
    })
    
    icon = classification["icon"]
    friendly_name = classification["name"].get(lang, severity)
    
    # Build prediction text
    prediction_text = f"{icon} **Assessment:** {friendly_name}\n"
    
    # Add method info
    if prediction_method == "ml" and ml_confidence:
        if ml_confidence > 0.8:
            confidence_text = "High confidence" if lang == "en" else "উচ্চ আত্মবিশ্বাস"
        elif ml_confidence > 0.6:
            confidence_text = "Moderate confidence" if lang == "en" else "মাঝারি আত্মবিশ্বাস"
        else:
            confidence_text = "Low confidence" if lang == "en" else "নিম্ন আত্মবিশ্বাস"
        
        prediction_text += f"🤖 *AI Analysis ({confidence_text})*\n\n"
    else:
        prediction_text += f"📋 *Based on WHO guidelines*\n\n"
    
    # Add explanation
    explanation = classification["explanation"].get(lang, "")
    if explanation:
        prediction_text += explanation
    
    return prediction_text

async def start_conversation(update):
    user_id = update.message.from_user.id
    user_state[user_id] = {
        "lang": None,
        "index": -1,
        "answers": {},
        "user_name": None,
        "start_time": datetime.now(),
        "user_info": {
            "username": update.message.from_user.username or "anonymous",
            "first_name": update.message.from_user.first_name or "",
            "last_name": update.message.from_user.last_name or ""
        }
    }
    
    welcome_msg = f"""
👋 Welcome to Dengue Triage Bot!
{'🤖 AI-Powered ' if ml_enabled else ''}Symptom Assessment

Choose language / ভাষা নির্বাচন করুন:
Type EN for English or BN for বাংলা

{'⚡ AI Model: ACTIVE' if ml_enabled else '⚡ AI Model: Training needed (using rules)'}
⚠️ **Important:** This is for educational purposes only. Always consult a doctor for medical advice.
    """
    
    await update.message.reply_text(welcome_msg)

async def start(update, context):
    await start_conversation(update)

async def handle_message(update, context):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if text.lower() in RESTART_WORDS:
        await start_conversation(update)
        return

    if user_id not in user_state:
        await update.message.reply_text("👋 Type 'test again' / 'আবার শুরু' to start the chatbot.")
        return

    state = user_state[user_id]

    # Language selection
    if state["lang"] is None:
        if text.lower() == "bn":
            state["lang"] = "bn"
            await update.message.reply_text(
                "ধন্যবাদ! আপনার উত্তর শুধুমাত্র গবেষণার জন্য ব্যবহার করা হবে।\n"
                f"{'🤖 এআই মডেল সক্রিয়' if ml_enabled else '⚡ নিয়ম-ভিত্তিক মূল্যায়ন'}\n\n"
                "আপনার নাম কি? (পুরো নাম দিন)"
            )
        elif text.lower() == "en":
            state["lang"] = "en"
            await update.message.reply_text(
                "Thank you! Your responses will be used for research purposes only.\n"
                f"{'🤖 AI Model Active' if ml_enabled else '⚡ Rule-Based Assessment'}\n\n"
                "What is your name? (Enter full name)"
            )
        else:
            await update.message.reply_text("Please type EN or BN")
        return
    
    # Name input
    if state["user_name"] is None:
        if text.strip():
            state["user_name"] = text.strip()
            lang = state["lang"]
            
            name_msg = {
                "en": f"Thank you, {state['user_name']}! Now let's assess your symptoms. Please answer each question honestly.",
                "bn": f"ধন্যবাদ, {state['user_name']}! এখন আপনার উপসর্গ মূল্যায়ন করা যাক। অনুগ্রহ করে প্রতিটি প্রশ্নের সত্য উত্তর দিন।"
            }
            
            await update.message.reply_text(name_msg[lang])
            
            state["index"] = 0
            await ask_next_question(update, state)
        else:
            await update.message.reply_text("Please enter your name.")
        return

    symptom = SYMPTOM_ORDER[state["index"]]

    # Skip PersistentVomiting if Vomiting is No
    if symptom == "PersistentVomiting" and state["answers"].get("Vomiting") == 0:
        state["answers"][symptom] = None
        state["index"] += 1
        if state["index"] >= len(SYMPTOM_ORDER):
            await complete_assessment(update, state)
            return
        symptom = SYMPTOM_ORDER[state["index"]]

    # PersistentVomiting
    if symptom == "PersistentVomiting":
        if text.lower() in VOMITING_WORDS:
            value = VOMITING_WORDS[text.lower()]
        else:
            await update.message.reply_text(
                "Please reply with 'once', 'frequent', 'continuous' or 'একবার', 'ঘন ঘন', 'ক্রমাগত'"
            )
            return
    else:
        if text.lower() in YES_WORDS:
            value = 1
        elif text.lower() in NO_WORDS:
            value = 0
        else:
            await update.message.reply_text("Please reply with yes/no or হ্যাঁ/না")
            return

    state["answers"][symptom] = value
    state["index"] += 1

    # Ask next question or complete
    if state["index"] < len(SYMPTOM_ORDER):
        await ask_next_question(update, state)
    else:
        await complete_assessment(update, state)

async def ask_next_question(update, state):
    """Ask the next symptom question"""
    if state["index"] < 0 or state["index"] >= len(SYMPTOM_ORDER):
        return
    
    next_symptom = SYMPTOM_ORDER[state["index"]]
    
    # Skip PersistentVomiting if Vomiting is No
    if next_symptom == "PersistentVomiting" and state["answers"].get("Vomiting") == 0:
        state["answers"][next_symptom] = None
        state["index"] += 1
        if state["index"] >= len(SYMPTOM_ORDER):
            await complete_assessment(update, state)
            return
        next_symptom = SYMPTOM_ORDER[state["index"]]
    
    try:
        await update.message.reply_text(QUESTIONS[state["lang"]][next_symptom])
    except Exception as e:
        print(f"Error asking question: {e}")

async def complete_assessment(update, state):
    """Complete the assessment and show results"""
    lang = state["lang"]
    user_name = state["user_name"]
    user_id = update.message.from_user.id
    
    # Get rule-based prediction
    rule_severity = determine_severity(state["answers"])
    
    # Get ML prediction if available
    ml_severity = None
    ml_confidence = 0.0
    if ml_enabled:
        try:
            ml_result = ml_predictor.predict(state["answers"])
            if ml_result[0] is not None:  # Check if prediction was successful
                ml_severity, ml_confidence, _ = ml_result  # Get first 2 of 3 values
        except Exception as e:
            print(f"ML prediction error: {e}")
    
    # Decide which prediction to use
    if ml_enabled and ml_severity and ml_confidence > 0.7:  # Use ML if confident
        final_severity = ml_severity
        prediction_method = "ml"
    else:  # Use rules
        final_severity = rule_severity
        prediction_method = "rules"
    
    # Show summary (without "Skipped" text)
    summary_lines = []
    for q in SYMPTOM_ORDER:
        ans = state["answers"][q]
        # Skip showing PersistentVomiting if it was skipped
        if q == "PersistentVomiting" and ans is None:
            continue
        summary_lines.append(format_summary_line(QUESTIONS[lang][q], ans, lang, q))

    summary_text = f"📝 **Summary for {user_name}:**\n\n" + "\n".join(summary_lines)
    await update.message.reply_text(summary_text)
    
    # Show detailed symptom analysis
    detailed_analysis = generate_detailed_analysis(state["answers"], final_severity, lang)
    await update.message.reply_text(detailed_analysis)
    
    # Show PREDICTION in separate, understandable message
    await update.message.reply_text("=" * 40)
    prediction_message = generate_prediction_message(
        final_severity, 
        ml_confidence if prediction_method == "ml" else None,
        prediction_method,
        lang
    )
    await update.message.reply_text(prediction_message)
    
    # Send medical advice
    advice_text = f"💡 **Medical Advice for {user_name}:**\n\n" + ADVICE[final_severity][lang] + "\n\n" + DISCLAIMER[lang]
    await update.message.reply_text(advice_text)
    
    # Save dataset SILENTLY in background (not shown to user)
    save_user_dataset_silently(
        user_id, state, rule_severity, ml_severity, ml_confidence,
        state["start_time"], user_name
    )
    
    # Clear user state
    if user_id in user_state:
        del user_state[user_id]

# ===== COMMAND HANDLERS =====

async def research_info(update, context):
    """Send research information to user"""
    message = """
🔬 **Educational Project Information:**
    
**Project:** Dengue Triage Chatbot
**Purpose:** Educational tool for understanding dengue symptoms
**Data Collection:** All responses are anonymized for academic research

⚕️ **Medical Disclaimer:**
This bot is for educational purposes only.
It is NOT a substitute for professional medical advice.
Always consult a healthcare professional for diagnosis.
"""
    await update.message.reply_text(message)

async def stats_command(update, context):
    """Show bot statistics (admin only)"""
    try:
        import pandas as pd
        if os.path.exists(RESEARCH_SUMMARY_FILE):
            df = pd.read_csv(RESEARCH_SUMMARY_FILE)
            total_users = len(df)
            
            stats_msg = f"""
📊 **Research Statistics (Admin Only):**
Total Assessments: {total_users}
ML Model: {'✅ Active' if ml_enabled else '❌ Not loaded'}
"""
            # Only show detailed stats if user is likely admin
            if total_users > 0:
                languages = df['language'].value_counts()
                methods = df['prediction_method'].value_counts()
                stats_msg += f"Languages: EN={languages.get('en', 0)}, BN={languages.get('bn', 0)}\n"
                stats_msg += f"Prediction Methods: {dict(methods)}\n"
        else:
            stats_msg = "📊 No assessment data yet."
    except Exception as e:
        stats_msg = f"❌ Error loading statistics: {e}"
    
    await update.message.reply_text(stats_msg)

async def train_model_command(update, context):
    """Train ML model from collected data (admin only)"""
    if not os.path.exists('dengue_research_dataset_v1.csv'):
        await update.message.reply_text("❌ Training data not found.")
        return
    
    try:
        await update.message.reply_text("🔄 Training AI model... Please wait.")
        
        predictor = DengueMLPredictor()
        accuracy = predictor.train_model()
        
        if accuracy:
            ml_predictor.load_model()  # Reload the model
            global ml_enabled
            ml_enabled = True
            
            await update.message.reply_text(
                f"✅ AI model trained successfully!\n"
                f"📊 Training Accuracy: {accuracy*100:.1f}%\n"
                f"🤖 AI analysis is now active!"
            )
        else:
            await update.message.reply_text("❌ Model training failed.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Training error: {e}")

async def help_command(update, context):
    """Show help information"""
    help_text = """
🤖 **Dengue Triage Bot Commands:**

/start - Start symptom assessment
/help - Show this help message
/research - Learn about this educational project

📱 **How to use:**
1. Type /start to begin
2. Choose language (EN or BN)
3. Enter your name
4. Answer symptom questions honestly
5. Get educational assessment

⚠️ **Important Disclaimer:**
This is an EDUCATIONAL tool only.
It is NOT medical diagnosis.
Always consult a doctor for health concerns.
"""
    await update.message.reply_text(help_text)

async def error_handler(update, context):
    """Handle errors"""
    print(f"Error occurred: {context.error}")
    
    # Send simple error message to user
    try:
        if update and hasattr(update, 'effective_message'):
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again with /start"
            )
    except:
        pass

def main():
    # Initialize
    init_research_data()
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("research", research_info))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("train", train_model_command))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print("🤖 DENGUE TRIAGE CHATBOT WITH ML INTEGRATION")
    print("=" * 60)
    print(f"📊 ML Model: {'✅ ACTIVE' if ml_enabled else '❌ NOT FOUND (using rules)'}")
    print(f"📁 CSV Datasets saved to: {DATASETS_DIR}/")
    print(f"📄 TXT Datasets saved to: {INDIVIDUAL_DATASETS_DIR}/")
    print(f"🧠 Model file: dengue_model.pkl")
    print(f"📊 Research summary: {RESEARCH_SUMMARY_FILE}")
    print("=" * 60)
    print("✅ Bot is running...")
    print("📱 Available commands: /start, /help, /research, /stats, /train")
    print("=" * 60)
    
    # Run the bot
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()