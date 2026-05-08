import pandas as pd
import numpy as np

# mapping keywords to categories - took some time to figure out all possible names
categories = {
    "Food & Dining": ["swiggy", "zomato", "restaurant", "dinner", "food", "instamart", "cafe", "dominos", "pizza"],
    "Transport": ["uber", "ola", "cab", "petrol", "fuel", "metro", "rapido"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "shopping", "mall"],
    "Bills & Utilities": ["electricity", "water", "internet", "mobile recharge", "broadband"],
    "Entertainment": ["netflix", "hotstar", "spotify", "bookmyshow", "movie", "prime"],
    "Health": ["pharmacy", "medical", "doctor", "hospital", "checkup"],
    "Fitness": ["gym", "fitness", "yoga"],
    "Groceries": ["grocery", "bigbasket", "dmart", "supermarket"],
    "ATM & Cash": ["atm", "cash withdrawal"],
    "Income": ["salary", "freelance", "payment received", "upi transfer received"],
}

def get_category(desc):
    desc = desc.lower()
    for cat, words in categories.items():
        for w in words:
            if w in desc:
                return cat
    return "Others"

def load_data(file):
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        df['Date'] = pd.to_datetime(df['Date'])
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Category'] = df['Description'].apply(get_category)
        df['Month'] = df['Date'].dt.strftime('%b %Y')
        df['MonthNum'] = df['Date'].dt.to_period('M')
        return df
    except:
        return None

def get_summary(df):
    inc = df[df['Amount'] > 0]['Amount'].sum()
    exp = df[df['Amount'] < 0]['Amount'].sum()
    saved = inc + exp
    rate = (saved / inc * 100) if inc > 0 else 0
    return {
        "total_income": round(inc, 2),
        "total_expense": round(abs(exp), 2),
        "net_savings": round(saved, 2),
        "savings_rate": round(rate, 2),
        "total_transactions": len(df),
    }

def category_breakdown(df):
    ex = df[df['Amount'] < 0].copy()
    ex['Amount'] = ex['Amount'].abs()
    result = ex.groupby('Category')['Amount'].sum().reset_index()
    result.columns = ['Category', 'Amount']
    return result.sort_values('Amount', ascending=False)

def monthly_trend(df):
    data = df.groupby('MonthNum').agg(
        Income=('Amount', lambda x: x[x > 0].sum()),
        Expense=('Amount', lambda x: abs(x[x < 0].sum()))
    ).reset_index()
    data['Savings'] = data['Income'] - data['Expense']
    data['Month'] = data['MonthNum'].astype(str)
    return data

# using zscore to catch unusual spending - learned this from stats class
def detect_anomalies(df):
    ex = df[df['Amount'] < 0].copy()
    ex['Amount'] = ex['Amount'].abs()

    stats = ex.groupby('Category')['Amount'].agg(['mean', 'std']).reset_index()
    stats.columns = ['Category', 'Mean', 'Std']

    merged = ex.merge(stats, on='Category')
    merged['Std'] = merged['Std'].fillna(0)

    def zscore(row):
        if row['Std'] > 0:
            return (row['Amount'] - row['Mean']) / row['Std']
        return 0

    merged['ZScore'] = merged.apply(zscore, axis=1)
    flagged = merged[merged['ZScore'] > 2.0].copy()
    return flagged[['Date', 'Description', 'Amount', 'Category', 'ZScore']].sort_values('ZScore', ascending=False)

def top_expenses(df, n=10):
    ex = df[df['Amount'] < 0].copy()
    ex['Amount'] = ex['Amount'].abs()
    return ex.nlargest(n, 'Amount')[['Date', 'Description', 'Amount', 'Category']]

def saving_tips(cat_df):
    tips = []
    d = dict(zip(cat_df['Category'], cat_df['Amount']))
    total = sum(d.values())

    if total == 0:
        return ["No expense data found."]

    if d.get("Food & Dining", 0) / total > 0.25:
        tips.append("You're spending over 25% on food. Try cooking at home more often.")
    if d.get("Shopping", 0) / total > 0.20:
        tips.append("Shopping is 20%+ of budget. Try the 48hr rule before buying.")
    if d.get("Entertainment", 0) > 1500:
        tips.append("Check your subscriptions — cancel ones you barely use.")
    if d.get("Transport", 0) / total > 0.15:
        tips.append("Transport is high. Monthly pass or carpooling might help.")
    if d.get("ATM & Cash", 0) > 3000:
        tips.append("Too much cash usage — harder to track. Prefer UPI.")
    if not tips:
        tips.append("Spending looks balanced. Keep it up!")
    return tips
