QUESTIONS = {
    "en": {
        "Fever": "Do you have a high fever (above 38.5°C)? (yes/no)",
        "Headache": "Do you have a severe headache? (yes/no)",
        "EyePain": "Do you feel pain behind the eyes? (yes/no)",
        "Vomiting": "Have you vomited at least once? (yes/no)",
        "PersistentVomiting": "Is the vomiting frequent or continuous? (frequent/continuous/once)",
        "AbdominalPain": "Do you have severe or persistent abdominal pain? (yes/no)",
        "Bleeding": "Do you notice any bleeding (nose, gums, vomiting blood, black stool)? (yes/no)",
        "Fatigue": "Do you feel extreme weakness or restlessness? (yes/no)",
        "FluidAccumulation": "Do you notice ANY of these signs:\n• Swelling in hands/feet (rings/shoes feel tight)\n• Puffy face or eyes\n• Shortness of breath or difficulty lying flat\n• Feeling of abdominal fullness/bloating\n(yes/no)"
    },
    "bn": {
        "Fever": "আপনার কি ৩৮.৫°সেলসিয়াসের বেশি জ্বর আছে? (হ্যাঁ/না)",
        "Headache": "আপনার কি তীব্র মাথাব্যথা আছে? (হ্যাঁ/না)",
        "EyePain": "চোখের পেছনে কি ব্যথা অনুভব করছেন? (হ্যাঁ/না)",
        "Vomiting": "আপনার কি অন্তত একবার বমি হয়েছে? (হ্যাঁ/না)",
        "PersistentVomiting": "বমি কি ঘন ঘন, ক্রমাগত, নাকি একবার হয়েছে? (ঘন ঘন/ক্রমাগত/একবার)",
        "AbdominalPain": "আপনার কি তীব্র বা স্থায়ী পেট ব্যথা আছে? (হ্যাঁ/না)",
        "Bleeding": "নাক, মাড়ি, বমি বা পায়খানায় কি রক্ত দেখা যাচ্ছে? (হ্যাঁ/না)",
        "Fatigue": "আপনি কি অতিরিক্ত দুর্বল বা অস্থির অনুভব করছেন? (হ্যাঁ/না)",
        "FluidAccumulation": "আপনি কি নিচের কোন লক্ষণ লক্ষ্য করেছেন:\n• হাত/পা ফুলে যাওয়া (আংটি/জুতা টাইট লাগছে)\n• মুখ বা চোখ ফোলা\n• শ্বাসকষ্ট বা চিত হয়ে শুতে অসুবিধা\n• পেট ভরা বা ফাঁপা অনুভব\n(হ্যাঁ/না)"
    }
}


ADVICE = {
    "Mild": {
        "en": (
            "🟢 Mild dengue symptoms detected.\n\n"
            "• Get plenty of rest\n"
            "• Drink oral rehydration fluids\n"
            "• Monitor symptoms daily\n"
            "• Use paracetamol ONLY for fever\n"
            "• Avoid aspirin or ibuprofen\n"
        ),
        "bn": (
            "🟢 হালকা ডেঙ্গু উপসর্গ পাওয়া গেছে।\n\n"
            "• পর্যাপ্ত বিশ্রাম নিন\n"
            "• বেশি করে তরল পান করুন\n"
            "• প্রতিদিন উপসর্গ পর্যবেক্ষণ করুন\n"
            "• জ্বরের জন্য শুধুমাত্র প্যারাসিটামল নিন\n"
            "• অ্যাসপিরিন বা আইবুপ্রোফেন এড়িয়ে চলুন\n"
        )
    },
    "Moderate": {
        "en": (
            "🟡 Dengue with warning signs detected.\n\n"
            "• Consult a doctor as soon as possible\n"
            "• Blood tests may be required\n"
            "• Do not delay medical consultation\n"
            "• Maintain hydration\n"
        ),
        "bn": (
            "🟡 সতর্কতামূলক উপসর্গসহ ডেঙ্গু পাওয়া গেছে।\n\n"
            "• যত দ্রুত সম্ভব ডাক্তারের পরামর্শ নিন\n"
            "• রক্ত পরীক্ষা প্রয়োজন হতে পারে\n"
            "• দেরি না করে চিকিৎসা নিন\n"
            "• পর্যাপ্ত তরল গ্রহণ করুন\n"
        )
    },
    "Severe": {
        "en": (
            "🔴 SEVERE DENGUE WARNING!\n\n"
            "• Seek emergency medical care immediately\n"
            "• Hospital admission may be required\n"
            "• This condition can be life-threatening\n"
            "• Do NOT wait at home\n"
        ),
        "bn": (
            "🔴 গুরুতর ডেঙ্গুর সতর্কতা!\n\n"
            "• দ্রুত নিকটস্থ হাসপাতালে যান\n"
            "• হাসপাতালে ভর্তি প্রয়োজন হতে পারে\n"
            "• এটি প্রাণঘাতী হতে পারে\n"
            "• বাসায় অপেক্ষা করবেন না\n"
        )
    },
    "NoSymptoms": {
        "en": "✅ You do not appear to have any symptoms.",
        "bn": "✅ কোনো উপসর্গ দেখা যাচ্ছে না।"
    },
    "FeverOnly": {
        "en": "⚠️ You have fever. Monitor and consult a doctor if necessary.",
        "bn": "⚠️ আপনার জ্বর আছে। পর্যবেক্ষণ করুন এবং প্রয়োজনে ডাক্তারের পরামর্শ নিন।"
    },
    "OtherSymptoms": {
        "en": "⚠️ Some symptoms detected. Monitor your health and consult a doctor if necessary.",
        "bn": "⚠️ কিছু উপসর্গ দেখা গেছে। আপনার স্বাস্থ্য পর্যবেক্ষণ করুন এবং প্রয়োজনে ডাক্তারের পরামর্শ নিন।"
    }
}

DISCLAIMER = {
    "en": (
        "⚠️ Disclaimer:\n"
        "This chatbot provides preliminary triage guidance only "
        "and does not replace a medical professional. "
        "Always consult a healthcare provider for proper diagnosis."
    ),
    "bn": (
        "⚠️ সতর্কীকরণ:\n"
        "এই চ্যাটবট প্রাথমিক ট্রায়াজ নির্দেশনা দেয় "
        "এবং চিকিৎসকের বিকল্প নয়। "
        "সঠিক রোগ নির্ণয়ের জন্য সর্বদা একজন স্বাস্থ্যসেবা প্রদানকারীর পরামর্শ নিন।"
    )
}