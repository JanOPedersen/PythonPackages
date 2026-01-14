import re
import os
import requests
import json
import sqlite3
from tqdm import notebook, tqdm
import re

url = "https://api.semanticscholar.org/graph/v1/paper/search/match"

#The following dicionary contains information for each of the folders 
# "C:\Users\janop\OneDrive\Documents\e-Papers\e-library" and "C:\Users\janop\OneDrive\Documents\e-books", 
# including the names of the involved databases and the folder paths

EDocsDict = {
    "papers": {
    "databaseName": "udc_papers.db",
    "path": r'C:\Users\janop\OneDrive\Documents\e-Papers\e-library',
    "pickle_name": "udc_papers.pickle",
    "udc_table_name": "udc_papers_table.txt"
    },
    "books": {
    "databaseName": "udc_books.db",
    "path": r'C:\Users\janop\OneDrive\Documents\e-books\e-library',
    "pickle_name": "udc_books.pickle",
    "udc_table_name": "udc_books_table.txt"
    },
}

def udc_class(fullpath):
    '''
    udc_class(...) returns the UDC numeric class string from the folder path, so that
    "C:\\Users\\janop\\OneDrive\\Documents\\e-Papers\\e-library\\0 Information\\04 Computer science and technology\\8 Artifical Intelligence\\3 Reasoning"
    is turned into "004.83"
    This ignores any folders with no numeric prefix.
    '''
    words = fullpath.split('\\')
    udc = ''.join([i[0] for i in [re.findall(r'^\d+', i) for i in words] if len(i)])
    udc = list(''.join(l + '.' * (n % 3 == 2) for n, l in enumerate([*udc])))
    if len(udc) % 4 == 0:
        udc = udc[ : -1]
    udc = ''.join(udc)
    return(udc)

def check_path(fullpath):
    '''
    check_path(...) validates that the last folder has a numeric prefix. 
    This is used for generating the class table, because any non-numeric folders 
    would be ignored and hence duplicated in the final class table.
    '''
    words = fullpath.split('\\')
    last_word = words[-1]
    return not not re.findall(r'^\d+', last_word)

def extract_top_name(fullpath):
    '''
    The following helper extracts the last folder name and extracts the non-numeric part in that name
    '''
    words = fullpath.split('\\')
    last_word = words[-1]
    result = re.search(r"^\d+\s(.+)", last_word)
    if result:
        groups = result.groups()
        if len(groups) > 0:
            return groups[0]
    else:
        return ''
    
def create_table(currentType):
    '''
    Create a table printout just like UDC Part 2: Main Tables
    '''
    table = {}
    for rootdir, dirs, _ in os.walk(EDocsDict[currentType]["path"]):  
        for subdir in dirs:
            fullpath = os.path.join(rootdir, subdir)
            if check_path(fullpath):
                table[udc_class(fullpath)] = extract_top_name(fullpath)
                
    return dict(sorted(table.items()))

def all_classes(elibPath):
    '''
    The following prints out all classes at all levels
    '''
    classes = []
    for rootdir, dirs, files in os.walk(elibPath):  
        for subdir in dirs:
            fullpath = os.path.join(rootdir, subdir)
            if check_path(fullpath):
                classes.append(udc_class(fullpath))
    return classes

def normalizeFileName(fileName):
    '''
    The following normalizes a file name by removing special characters and replacing spaces with a single space
    '''
    fileName = os.path.splitext(fileName)[0]
    return re.sub(' +', ' ', fileName).lower().replace('_', '').replace('(', '').replace(')', '').replace(',', ''). \
    replace("'", '').replace('&', 'and').replace(';', '').replace('?', '').replace('!', '').replace(':', ''). \
    replace('.', '').replace('’', '').replace('“', '').replace('”', '').replace('–', '').replace('—', '')

def display_database(currentType):
    '''
    The following displays the database of the UDC classes and file names
    '''
    conn = sqlite3.connect(EDocsDict[currentType]["databaseName"])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM udc')
    for row in cursor.fetchall():
        print(row)
    conn.close()

def fetch_rows(currentType):
    '''
    The following returns all rows from the database in the form of a list
    '''
    conn = sqlite3.connect(EDocsDict[currentType]["databaseName"])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM udc')
    rows = [row for row in cursor.fetchall()]
    conn.close()
    return rows
    
def count_documents(elibPath):
    '''
    Count all pdf documents in the elibPath folder and sub-folders
    '''
    counter = 1
    for rootdir, _, files in os.walk(elibPath):  
        for file in files:
            if file.endswith(".pdf"):
                counter += 1
    return counter
    
def create_database(currentType):
    '''
    The following creates a database of papers in the e-library folder
    All papers are PDF files. For datetime we use ISO8601 strings like 'YYYY-MM-DD HH:MM:SS'.
    '''
    conn = sqlite3.connect(EDocsDict[currentType]["databaseName"])
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS udc")
    conn.commit()
    cursor.execute('CREATE TABLE IF NOT EXISTS udc (id INTEGER PRIMARY KEY, title TEXT, FileName TEXT, NormalizedFileName TEXT, Path TEXT, UDC TEXT, citationCount INTEGER, publicationDate TEXT, paperId TEXT)')
    conn.commit()
    cursor.execute("CREATE INDEX paperId ON udc(paperId);")
    conn.commit()
    cursor.execute("CREATE INDEX Path ON udc(Path);")
    conn.commit()
    cursor.execute("CREATE INDEX NormalizedFileName ON udc(NormalizedFileName);")
    conn.commit()
    conn.close()
    
def delete_duplicates():
    '''
    The following deletes duplicate entries in the udc database. We use NormalizedFileName as the
    paper names identify the same paper.
    '''
    conn = sqlite3.connect('udc.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM udc WHERE id NOT IN (SELECT MIN(id) FROM udc GROUP BY NormalizedFileName)")
    conn.commit()
    
def populate_database(currentType):
    '''
    The following populates the udc.db database with the file names, normalized file names, paths, and UDC classes.
    Also we populate the database with the citation count, publication date, and paper ID from the Semantic Scholar API.
    '''
    conn = sqlite3.connect(EDocsDict[currentType]["databaseName"])
    cursor = conn.cursor()

    # Define the API endpoint URL
    url = "https://api.semanticscholar.org/graph/v1/paper/search/match"
    nof_docs = count_documents(EDocsDict[currentType]["path"])
    pbar = tqdm(os.walk(EDocsDict[currentType]["path"]), total=nof_docs)

    for rootdir, _, files in os.walk(EDocsDict[currentType]["path"]):  
        for file in files:
            if file.lower().endswith(".pdf"):
                fileNoExt = os.path.splitext(file)[0]
            
                query_params = {
                    "query": f'"{fileNoExt}"',
                    "fields": "title,url,publicationTypes,publicationDate,citationCount",
                }

                try:
                    response = requests.get(url, params=query_params).json()
                    title = response['data'][0]['title']
                    citationCount = response['data'][0]['citationCount']
                    publicationDate = response['data'][0]['publicationDate']
                    paperId = response['data'][0]['paperId']

                    cursor.execute("INSERT INTO udc (title, FileName, NormalizedFileName, Path, UDC, citationCount, publicationDate, paperId) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                               (title, file, normalizeFileName(file), rootdir, udc_class(rootdir), citationCount, publicationDate, paperId))

                except (requests.exceptions.HTTPError, Exception)  as err:
                    cursor.execute("INSERT INTO udc (title, FileName, NormalizedFileName, Path, UDC, citationCount, publicationDate, paperId) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                               ("n/a", file, normalizeFileName(file), rootdir, udc_class(rootdir), 0, "n/a", "n/a"))
                
                conn.commit()
                pbar.update(1)

    conn.close()

def update_udc_row(rootdir, file, currentType):
    '''
    Given a PDF file in a folder (rootdir), this function updates
    the udc database with the metadata of the file.
    '''
    conn = sqlite3.connect(EDocsDict[currentType]["databaseName"])
    cursor = conn.cursor()
    
    fileNoExt = os.path.splitext(file)[0]
    query_params = {
        "query": f'"{fileNoExt}"',
        "fields": "title,url,publicationTypes,publicationDate,citationCount",
    }

    try:
        response = requests.get(url, params=query_params).json()
        title = response['data'][0]['title']
        citationCount = response['data'][0]['citationCount']
        publicationDate = response['data'][0]['publicationDate']
        paperId = response['data'][0]['paperId']

        cursor.execute("INSERT INTO udc (title, FileName, NormalizedFileName, Path, UDC, citationCount, publicationDate, paperId) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
            (title, file, normalizeFileName(file), rootdir, udc_class(rootdir), citationCount, publicationDate, paperId))

    except (requests.exceptions.HTTPError, Exception)  as err:
        cursor.execute("INSERT INTO udc (title, FileName, NormalizedFileName, Path, UDC, citationCount, publicationDate, paperId) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
            ("n/a", file, normalizeFileName(file), rootdir, udc_class(rootdir), 0, "n/a", "n/a"))
                
    conn.commit()
    conn.close()
    
def update_database(currentType):
    '''
    Given a path to look into this function adds any missing files 
    to the database. This includes any metadata that is scraped 
    from semanticscholar
    
    Below, we implement a new function update_database(...) that updates the database. The difference between this one
    and the the populate_database(...) function is that the later does not use any progressbar (small changes assumed).
    Also it asures consistency between the database and the folder structure
    '''
    url = "https://api.semanticscholar.org/graph/v1/paper/search/match"
    for rootdir, _, files in os.walk(EDocsDict[currentType]["path"]):  
        for file in files:
            if file.lower().endswith(".pdf"):
                normalizeFileName_value = normalizeFileName(file)
                subpath = rootdir[len(EDocsDict[currentType]["path"]) + 1:]
                subfolders = subpath.split('\\')
                # Check if all subfolders start with a number
                if all(re.match(r'^\d+', folder) for folder in subfolders):
                    conn = sqlite3.connect(EDocsDict[currentType]["databaseName"])
                    cursor = conn.cursor()
                    cursor.execute(r"SELECT EXISTS(SELECT 1 FROM udc WHERE Path = ? and NormalizedFileName = ?)", (rootdir,normalizeFileName_value,))
                    conn.commit()
                    exists = cursor.fetchone()[0] 
                    conn.close()
                    if exists == 0:
                        print("File not in database: ", os.path.join(rootdir, file))
                        update_udc_row(rootdir, file, currentType)

def update_folders(elibPath):
    '''
    Given a path to look into this function deletes any folders that are not in the database
    '''
    for rootdir, _, files in os.walk(elibPath):  
        for file in files:
            if file.lower().endswith(".pdf"):
                normalizeFileName_value = normalizeFileName(file)
                subpath = rootdir[len(elibPath) + 1:]
                subfolders = subpath.split('\\')
                if all(re.match(r'^\d+', folder) for folder in subfolders):
                    conn = sqlite3.connect('udc.db')
                    cursor = conn.cursor()
                    cursor.execute(r"SELECT EXISTS(SELECT 1 FROM udc WHERE Path = ? and NormalizedFileName = ?)", (rootdir,normalizeFileName_value,))
                    conn.commit()
                    if cursor.fetchone()[0] == 0:
                        fullpath = os.path.join(rootdir, file)
                        print("Not found in database: ", fullpath)
                        try:
                            os.remove(fullpath)  # Remove the file
                        except Exception as e:
                            print("Can not delete: ", fullpath)
                    conn.close()