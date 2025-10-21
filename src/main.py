from src.views import get_main_page_json
import json

if __name__ == "__main__":
    path = r"C:\Users\User\PycharmProjects\Transaction_service\data\operations.xlsx"
    result = get_main_page_json("2025-05-20 12:00:00", path)
    print(json.dumps(result, ensure_ascii=False, indent=4))
