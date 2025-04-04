import sys
import spacy
import sqlite3
import hashlib
import os
    
if getattr(sys, 'frozen', False):  # PyInstaller로 빌드된 경우
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
    
if __name__=="__main__":
    model_path = os.path.join(base_path, "model", "en_core_web_sm", "en_core_web_sm-3.7.1")
    nlp=spacy.load(model_path)
    text=sys.argv[1]
    doc=nlp(text)
    result=doc.to_json()
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()
    
    try:
        cur.execute("""
                CREATE TABLE "texts" (
                    "textid"	INTEGER PRIMARY KEY AUTOINCREMENT,
                    "text"	TEXT NOT NULL,
                    "hash"	TEXT UNIQUE NOT NULL
                )
            """)
        cur.execute("""
                    CREATE TABLE parts (
                        textid INTEGER NOT NULL,
                        tokenid INTEGER,
                        start INTEGER NOT NULL,
                        end INTEGER,
                        token TEXT,
                        tag TEXT,
                        pos TEXT,
                        morph TEXT,
                        lemma TEXT,
                        dep TEXT,
                        head INTEGER,
                        PRIMARY KEY (textid, tokenid),
                        FOREIGN KEY (textid) REFERENCES texts (textid)
                    )
                """)
        cur.execute("""
                    CREATE TABLE sentence (
                        textid INTEGER NOT NULL,
                        sentid INTEGER,
                        start INTEGER NOT NULL,
                        end INTEGER,
                        sent TEXT,
                        PRIMARY KEY (textid, sentid),
                        FOREIGN KEY (textid) REFERENCES texts (textid)
                    )
                    """)
        conn.commit()
    except  sqlite3.Error as e:{
    }
    
    textid=0
    hashed=hashlib.sha256(text.encode('utf-8')).hexdigest()
    cur.execute("SELECT textid FROM texts WHERE hash = (?)",(hashed,))
    for row in cur.fetchall():
        print(row[0])
        sys.exit()
        
    try:
        cur.execute("""
            INSERT INTO texts (text, hash) VALUES (?,?)
        """,(text,hashed,))
        conn.commit()
        textid=cur.lastrowid
    except sqlite3.Error as e:
        print(f"SQLite 에러 발생: {e}")
        print(-2)
        sys.exit()
    
    # print(result["tokens"])
    try:
        for token in result["tokens"]:
            cur.execute("""
                            INSERT INTO parts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,(textid, token["id"],token["start"],token["end"], doc[token["id"]].text,token["tag"],token["pos"],token["morph"],token["lemma"],token["dep"],token["head"]))
            conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite 에러 발생: {e}")
        print(-1)
        sys.exit()
    for sent in doc.sents:
        print(sent.text)
    try:
        for sent in doc.sents:
            cur.execute("""
                            INSERT INTO sentence VALUES(?, ?, ?, ?, ?)
                        """,(textid, sent.id,sent.start,len(sent.text),sent.text))
            conn.commit()
    except sqlite3.Error as e:{}
        
    print(textid)