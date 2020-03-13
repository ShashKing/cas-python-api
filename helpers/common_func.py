from PIL import Image
import pdf2image
import os
import pytesseract
import threading

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract'
custom_oem_psm_config = r'--oem 3 --psm 1'
result = ''
index = 1

def pdfToPIL(PDF_PATH, PASS, total_pages):
    pil_images = pdf2image.convert_from_path(PDF_PATH, dpi=300, userpw=PASS)
    save_images(pil_images)
    if index - 1 == total_pages:
        return result
    else:
        print('unable to parse images,\ntotal_pages : '+total_pages)

def ocr(big_filename):
    global result
    data=pytesseract.image_to_string(Image.open(big_filename),config=custom_oem_psm_config)+'\n'
    result += data + '\n'
    print('result : ', result)
    os.remove(big_filename)

def save_images(pil_images):
    #This method helps in converting the images in PIL Image file format to the required image format
    #thread_start=[]
    for image in pil_images:
        image.save("page_" + str(index) + ".jpg")
        t=threading.Thread(target=ocr, args=("page_" + str(index) + ".jpg",))
        t.start()
        t.join()
        index += 1