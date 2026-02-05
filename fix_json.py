import json
import os

def fix_json_encoding(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully fixed encoding for {file_path}")
    except Exception as e:
        print(f"Error fixing encoding for {file_path}: {e}")

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "comment_parser", "storage", "comments_db.json")
    fix_json_encoding(db_path)
