import csv
import random

# Define categories and example descriptions
categories = {
    "Food & Drink": [
        "Starbucks coffee", "McDonald's meal", "Pizza hut", "Burger King", "Subway meal",
        "Local bakery", "Food delivery app", "Coffee shop", "KFC meal", "Domino's pizza"
    ],
    "Transport": [
        "Uber ride", "Bolt ride", "Taxi ride", "Train ticket", "Bus ticket",
        "Flight ticket", "Bike rental", "Metro card", "Gas station", "Car service"
    ],
    "Groceries": [
        "Grocery store", "Supermarket", "Farmers market", "Costco groceries", "Whole Foods",
        "Local market", "Trader Joe's", "Online grocery", "Walmart groceries", "Fresh market"
    ],
    "Entertainment": [
        "Netflix subscription", "Disney+ subscription", "Spotify subscription", "Movie theater",
        "Hulu subscription", "Concert ticket", "Cinema ticket", "Video game purchase",
        "Amusement park", "Streaming service subscription"
    ],
    "Shopping": [
        "Amazon purchase", "Apple store", "H&M store", "Zara store", "Adidas store",
        "Electronics store", "Clothing store", "Online shopping", "Ebay purchase", "Target store"
    ],
    "Healthcare": [
        "Pharmacy purchase", "Doctor visit", "Medical checkup", "Dental appointment",
        "Optician visit", "Hospital bill", "Health insurance", "Medicine purchase", "Clinic visit", "Therapy session"
    ],
    "Fitness": [
        "Gym membership", "Yoga class", "Crossfit gym", "Fitness equipment", "Yoga retreat",
        "Swimming pool", "Martial arts class", "Personal trainer", "Pilates class", "Cycling class"
    ],
    "Education": [
        "Online course", "School books", "Workshop fee", "Tuition payment", "Seminar fee",
        "Exam registration", "E-learning subscription", "University fee", "Study materials", "Course materials"
    ]
}

# Generate 200+ transactions
transactions = []
for _ in range(220):  # You can increase this number
    category = random.choice(list(categories.keys()))
    description = random.choice(categories[category])
    transactions.append([description, category])

# Save to CSV
with open("transactions.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["description", "category"])
    writer.writerows(transactions)

print("✅ transactions.csv generated with 220+ entries!")
