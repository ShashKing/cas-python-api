import os
from flask import Flask, request, jsonify
from flask_restful import reqparse, Api, abort, Resource
from flask_cors import CORS, cross_origin
import re
import fitz
import pytesseract
from PIL import Image
import threading

#pytesseract.pytesseract.tesseract_cmd = '/app/.apt/usr/share/tesseract-ocr/4.00/tessdata'
#pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
custom_oem_psm_config = r'--oem 3 --psm 1'
result = ""
count = 0


# Initialize Flask app
app = Flask(__name__)
api = Api(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# Initialize parser
parser = reqparse.RequestParser()

'''
def tessaract(path, page_count):
    global result

    data = pytesseract.image_to_string(Image.open(path), config=custom_oem_psm_config) + '\n'
    result += data + '\n'
    global count
    count += 1
    print(result)
    print('total count : ', count)
    os.remove(path)
    if count == page_count:
        return extract_data()
'''        
def tessaract(page_list, page_count):
    global result
    data = pytesseract.image_to_string(Image.open(page_list), config=custom_oem_psm_config) + '\n'
    result += data + '\n'
    #global count
    #count += 1
    print(result)
    os.remove(page_list)
    return extract_data()

def extract_data():
    data = {
            'record': []
        }
    count = 1
    date_regex = r'^\d{2}-[A-Z][a-z]{2}-\d{4}|^\d{2}\.\d{2}\.\d{2}|^\d{2}\-[A-Z]{3}\-\d{4} '
    isin = ''
    folio = ''
    for line in result.split('\n'):
        if re.search(r'IN[A-Z|\d]+', line):
            isin = re.search(r'IN[A-Z|\d]+', line).group()
            # print(isin)
        # date=''
        if re.search(r'^Folio No : |^Folio\s', line):
            folio = re.search(r'\d+', line).group()

        if re.search(date_regex, line):
            date = re.search(date_regex, line).group()
            line = re.sub(date_regex, '', line)
            amount = re.findall(r'[\(\d]+\.\s[\)\d]+|[\d\(]+\.\d+\s[\d\)]$|[\(\d,]+?[\.\,\d\)]+', line)

            if len(amount) >= 4:
                data['record'].append({
                    u'count': count,
                    u'folio': folio,
                    u'isin': isin,
                    u'date': date.strip(),
                    u'transaction': str(line.split(amount[-4])[0]).strip().replace('| ',''),
                    u'amount': str(amount[-4]).strip(),
                    u'nav': str(amount[-3]).strip(),
                    u'price': str(amount[-2]).strip(),
                    u'unit': str(amount[-1]).strip()
                })
                count += 1
    
    return data

@app.route('/upload', methods=['POST', 'GET'])
@cross_origin()
def func():
    response_code = '0'
    server_message = 'Error'
    data = {}
    pdf_path = './src/file.pdf'
    page_count = 0
    page_no = 0

    mPdfFile = request.files['pdf_file']
    parser.add_argument('password', type=str)
    parser.add_argument('page_no')
    args = parser.parse_args()
    password = format(args['password'])
    page_no = format(args['page_no'])
    if request.method == 'POST' or request.method == 'GET':
        if mPdfFile is None:
            print('No pdf file received')
            server_message = 'pdf file is required.'
        else:
            try:
                page_num = int(page_no)
                mPdfFile.save(pdf_path)
                page_list = []
                pdf_file = fitz.open(pdf_path, filetype='pdf')
                pdf_file.authenticate(password)
                page_count = pdf_file.pageCount
                print('pages : ', page_count)
                page = pdf_file.loadPage(page_num - 1)
                zoom = 3   # zoom factor
                mat = fitz.Matrix(zoom, zoom)
                pix = page.getPixmap(mat)
                pix.writePNG('page_'+str(page_num)+'.png')
                #page_list.append('page_'+str(x)+'.png')
                #data = tessaract('page_'+str(x)+'.png', page_count)
                data = tessaract('page_'+str(page_no)+'.png', page_no)

            except Exception as e:
                #os.remove(pdf_path)
                print('Exception raised : '+str(e))
                server_message = 'Exception raised : '+str(e)
                return jsonify({'response_code':response_code,
                                'server_message':server_message,
                                u'page_count':page_no})
    else:
        server_message = 'Wrong method'
        #os.remove(pdf_path)
        return jsonify({'response_code':response_code,
                        'server_message':server_message})
    print('data : '+str(data))
    #os.remove(pdf_path)
    server_message = 'Success!'
    global result
    result = ''
    print('must be empty :- ', result)
    return jsonify({u'response_code':'200',
                        u'server_message':server_message,
                        u'data':data,
                        u'total_pages':page_count,
                        u'current_page':page_no})

if __name__ == "__main__":
    app.run()
