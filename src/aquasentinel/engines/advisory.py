from aquasentinel.schemas import AdvisoryRequest, Severity

TEMPLATES = {
    "en": {
        "title": "Water risk advisory",
        "action": "Check local authority updates, repair avoidable leaks, and prioritize essential water use.",
        "limit": "This is decision support based on a synthetic demonstration dataset; verify against current local observations.",
    },
    "ta": {
        "title": "நீர் அபாய அறிவுரை",
        "action": "உள்ளூர் அதிகாரிகளின் தகவல்களைச் சரிபார்த்து, தவிர்க்கக்கூடிய கசிவுகளைச் சரிசெய்து, அத்தியாவசிய நீர் பயன்பாட்டிற்கு முன்னுரிமை அளிக்கவும்.",
        "limit": "இது செயற்கை விளக்கத் தரவின் அடிப்படையிலான முடிவு ஆதரவு; தற்போதைய உள்ளூர் கண்காணிப்புகளுடன் சரிபார்க்கவும்.",
    },
    "hi": {
        "title": "जल जोखिम परामर्श",
        "action": "स्थानीय प्राधिकरण के अपडेट देखें, रोके जा सकने वाले रिसाव ठीक करें और आवश्यक जल उपयोग को प्राथमिकता दें।",
        "limit": "यह कृत्रिम प्रदर्शन डेटा पर आधारित निर्णय सहायता है; वर्तमान स्थानीय अवलोकनों से सत्यापित करें।",
    },
}


def render_advisory(request: AdvisoryRequest) -> dict[str, object]:
    template = TEMPLATES[request.language]
    urgency = "immediate review" if request.severity in {Severity.HIGH, Severity.CRITICAL} else "routine preparedness"
    return {
        "location": request.region_id,
        "audience": request.audience,
        "risk_category": request.severity,
        "forecast_timeframe": request.timeframe,
        "title": template["title"],
        "explanation": f"Screening-level water stress is {request.severity.value} for {request.timeframe}.",
        "recommended_action": template["action"],
        "urgency": urgency,
        "limitations": template["limit"],
        "deterministic_template": True,
    }

