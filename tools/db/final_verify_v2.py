import sqlite3

def check_headers():
    conn = sqlite3.connect(r'd:\LP\data\curriculum.db')
    c = conn.cursor()
    c.execute("SELECT procedure_html FROM lessons WHERE id = 'Math_3_U2_1hBoK4uk_L4'")
    content = c.fetchone()[0]
    
    print(f"H1 count: {content.count('<h1')}")
    print(f"H2 count: {content.count('<h2')}")
    print(f"H3 count: {content.count('<h3')}")
    print(f"H4 count: {content.count('<h4')}")
    print(f"Strong count: {content.count('<strong')}")
    print(f"Em count: {content.count('<em')}")
    
    if '<h' in content:
        print("Found headers!")
    else:
        print("No headers found in Lesson 4 procedure.")

check_headers()
