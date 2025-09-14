import os
import math
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = os.getenv("OPENROUTER_URL")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")

MONTH_NAMES = {
    "01":"января","02":"февраля","03":"марта","04":"апреля","05":"мая","06":"июня",
    "07":"июля","08":"августа","09":"сентября","10":"октября","11":"ноября","12":"декабря"
}

def fmt_currency(amount):
    try:
        amt = float(amount)
    except:
        amt = 0.0
    neg = amt < 0
    amt = abs(amt)
    whole = int(math.floor(amt))
    frac = int(round((amt-whole)*100))
    s = f"{whole:,}".replace(",", " ")
    if frac>0:
        s = f"{s},{frac:02d}"
    if neg:
        s = "-" + s
    return f"{s} ₸"

def make_template(product, signals, benefit):
    name = signals.get("name")
    month = signals.get("month_reference") or datetime.now().strftime("%m.%Y")
    month_parts = month.split('.')
    month_str = month
    if len(month_parts)==2 and month_parts[0] in MONTH_NAMES:
        month_str = f"{MONTH_NAMES.get(month_parts[0])} {month_parts[1]}"
    b = int(round(benefit))
    if product=="Карта для путешествий":
        trips_count = int(signals.get("trips_count",0))
        trips_sum = fmt_currency(signals.get("trips_sum",0)+signals.get("taxi_sum",0))
        return f"{name}, в {month_str} у вас {trips_count} поездок/такси на {trips_sum}. С картой для путешествий вернулись бы ≈{fmt_currency(b)}. Открыть"
    if product=="Премиальная карта":
        avg = fmt_currency(signals.get("avg_monthly_balance_KZT",0))
        rest = fmt_currency(signals.get("restaurant_sum",0))
        return f"{name}, у вас средний остаток {avg} и траты в ресторанах {rest}. Премиальная карта даст до 4% на рестораны и бесплатные снятия. Оформить"
    if product=="Кредитная карта":
        cats = signals.get("top3_cats",[])
        c1 = cats[0] or "разное"
        c2 = cats[1] or "разное"
        c3 = cats[2] or "разное"
        return f"{name}, ваши топ-категории: {c1}, {c2}, {c3}. Кредитная карта даёт до 10% в любимых категориях и рассрочку 3–24 мес. Оформить карту"
    if product=="Обмен валют":
        return f"{name}, вы часто проводите валютные операции. В приложении выгодный обмен 24/7 и авто-покупка по целевому курсу. Настроить обмен"
    if product=="Кредит наличными":
        return f"{name}, если нужны деньги на большие покупки — есть выгодные предложения по наличному кредиту. Оформить"
    if product.startswith("Депозит"):
        return f"{name}, у вас свободные средства {fmt_currency(signals.get('spare_cash',0))}. Депозит даст стабильный доход, можно выбрать срок и валюту. Посмотреть"
    if product=="Инвестиции":
        return f"{name}, у вас доступно {fmt_currency(signals.get('spare_cash',0))} для инвестиций. Диверсифицируйте портфель и начните с малого. Настроить"
    if product=="Золотые слитки":
        return f"{name}, в запасе {fmt_currency(signals.get('spare_cash',0))}. Покупка золотых слитков — способ диверсификации. Посмотреть"
    return f"{name}, у нас есть предложение по {product}. Посмотреть"

def validate_push_text(text):
    if text is None:
        return False
    l = len(text)
    if l<180 or l>220:
        return False
    if text.count('!')>1:
        return False
    if ':' in text:
        return False
    return True

def call_ai_paraphrase(system_prompt, user_prompt):
    if not OPENROUTER_API_KEY or not OPENROUTER_URL or not OPENROUTER_MODEL:
        return None
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    body = {"model": OPENROUTER_MODEL, "input": f"{system_prompt}\n\n{user_prompt}"}
    try:
        r = requests.post(f"{OPENROUTER_URL}/chat/completions", headers=headers, json=body, timeout=15)
        if r.status_code==200:
            j = r.json()
            if "output" in j and isinstance(j["output"], list) and len(j["output"])>0:
                return j["output"][0].get("content", "").strip()
            if "choices" in j and len(j["choices"])>0:
                return j["choices"][0].get("message",{}).get("content","").strip()
        return None
    except Exception:
        return None

def generate_push_for_client(client_scores, per_client_benefits, signals, use_ai=False):
    product = client_scores["chosen"]
    benefit = per_client_benefits[signals["client_code"]][product]
    template = make_template(product, signals, benefit)
    final = template
    if use_ai:
        system = "Вы — помощник, который преобразует шаблон в пуш уведомление строго 180–220 символов, по-русски, обращение по имени и 'вы' маленькими буквами, одна мысль, одна CTA (один глагол). Не менять выбранный продукт. Без CAPS. Не более 1 эмодзи."
        ai = call_ai_paraphrase(system, template)
        if ai and validate_push_text(ai):
            final = ai
    if not validate_push_text(final):
        final = template
    return {"product": product, "push": final}

def generate_pushes_batch(scores_dict, per_client_benefits, profiles_df, use_ai=False):
    results = {}
    for cid, sc in scores_dict.items():
        debug_p = os.path.join("debug", f"client_{cid}_scores.json")
        client_profile = None
        if os.path.exists(debug_p):
            with open(debug_p, "r", encoding="utf-8") as f:
                client_profile = json.load(f)
        name = None
        try:
            prof_row = profiles_df.loc[profiles_df["client_code"]==cid].iloc[0].to_dict()
            name = prof_row.get("name")
        except Exception:
            name = f"Клиент {cid}"
        signals = {"name": name}
        if client_profile:
            raw = client_profile.get("raw_signals", {})
            signals.update({
                "trips_count": raw.get("trips_count", 0),
                "trips_sum": raw.get("trips_sum", 0),
                "taxi_sum": raw.get("taxi_sum", 0),
                "avg_monthly_balance_KZT": raw.get("avg_monthly_balance_KZT", 0),
                "restaurant_sum": raw.get("restaurant_sum", 0),
                "spare_cash": raw.get("spare_cash", 0),
                "top3_cats": raw.get("top3_cats", []),
                "month_reference": raw.get("month_reference")
            })
        for k in ["trips_count","trips_sum","taxi_sum","avg_monthly_balance_KZT","restaurant_sum","spare_cash","top3_cats","month_reference"]:
            if k not in signals:
                signals[k]=0
        signals["client_code"]=cid
        out = generate_push_for_client(sc, per_client_benefits, signals, use_ai=use_ai)
        results[cid] = out
    return results
