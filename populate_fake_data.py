from database_manager import DatabaseManager
db = DatabaseManager()

db.insert_fake_weight_data(user_id=6, trend="down", days=200, start_weight=84)

print("Added data.")
